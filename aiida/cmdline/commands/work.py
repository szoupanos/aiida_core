# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
import logging
from tabulate import tabulate
from aiida.cmdline.commands import work, verdi
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
LIST_CMDLINE_PROJECT_CHOICES = ['id', 'ctime', 'label', 'sealed', 'uuid',
                                'finished', 'descr', 'mtime']

LOG_LEVEL_MAPPING = {
    levelname: i for levelname, i in [
        (logging.getLevelName(i), i) for i in range(logging.CRITICAL + 1)
    ]
    if not levelname.startswith('Level')
}
LOG_LEVELS = LOG_LEVEL_MAPPING.keys()


class Work(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA worflow manager
    """

    def __init__(self):
        self.valid_subcommands = {
            'list': (self.cli, self.complete_none),
            'report': (self.cli, self.complete_none),
            'tree': (self.cli, self.complete_none),
            'checkpoint': (self.cli, self.complete_none),
            'kill': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()


@work.command('list', context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--past-days', type=int, default=1,
              help="add a filter to show only workflows created in the past N"
                   " days")
@click.option('-a', '--all', 'all_nodes', is_flag=True, help='Return all nodes. Overrides the -l flag')
@click.option('-l', '--limit', type=int, default=None,
              help="Limit to this many results")
@click.option('-P', '--project', type=click.Choice(LIST_CMDLINE_PROJECT_CHOICES),
              multiple=True, help="Define the list of properties to show")
def do_list(past_days, all_nodes, limit, project):
    """
    Return a list of running workflows on screen
    """
    from aiida.common.utils import str_timedelta
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    import aiida.utils.timezone as timezone
    from aiida.orm.mixins import Sealable
    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)

    now = timezone.now()

    if all_nodes:
        past_days = None

    if not project:
        project = ('id', 'ctime', 'label')  # default projections


    # Mapping of projections to list table headers.
    hmap_dict = {
        'id': "PID",
        'ctime': "Creation time",
        'label': "Process Label",
        'uuid': "UUID",
        'descr': 'Description',
        'mtime': 'Modification time'
    }

    def map_header(p):
        try:
            return hmap_dict[p]
        except KeyError:
            return p.capitalize()

    # Mapping of querybuilder keys that differ from projections.
    pmap_dict = {
        'label': 'attributes._process_label',
        'sealed': _SEALED_ATTRIBUTE_KEY,
        'finished': 'attributes._finished',
        'descr': 'description',
    }

    def map_projection(p):
        try:
            return pmap_dict[p]
        except KeyError:
            return p

    # Mapping of to-string formatting of projections that do need it.
    rmap_dict = {
        'ctime': lambda calc: str_timedelta(timezone.delta(calc[map_projection('ctime')], now),
                                            negative_to_zero=True,
                                            max_num_fields=1),
        'mtime': lambda calc: str_timedelta(timezone.delta(calc[map_projection('mtime')], now),
                                            negative_to_zero=True,
                                            max_num_fields=1),
        'sealed': lambda calc: str(calc[map_projection('sealed')]),
        'finished': lambda calc: str(calc[map_projection('finished')]),
    }

    def map_result(p, obj):
        try:
            return rmap_dict[p](obj)
        except:
            return obj[map_projection(p)]


    mapped_projections = list(map(lambda p: map_projection(p), project))
    table = []

    for res in _build_query(limit=limit, projections=mapped_projections, past_days=past_days, order_by={'ctime': 'desc'}):
        calc = res['calculation']
        table.append(list(map(lambda p: map_result(p, calc), project)))

    # Revert table:
    # in this way, I order by 'desc', so I start by the most recent, but then
    # I print this as the las one (like 'verdi calculation list' does)
    # This is useful when 'limit' is set to not None
    table = table[::-1]
    print(tabulate(table, headers=(list(map(lambda p: map_header(p), project)))))


@work.command('report', context_settings=CONTEXT_SETTINGS)
@click.argument('pk', nargs=1, type=int)
@click.option('-i', '--indent-size', type=int, default=2)
@click.option('-l', '--levelname',
              type=click.Choice(LOG_LEVELS),
              default='REPORT',
              help='Filter the results by name of the log level'
              )
@click.option('-o', '--order-by',
              type=click.Choice(['id', 'time', 'levelname']),
              default='time',
              help='Order the results by column'
              )
def report(pk, levelname, order_by, indent_size):
    """
    Return a list of recorded log messages for the WorkChain with pk=PK
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    import itertools
    from aiida.orm.backend import construct
    from aiida.orm.log import OrderSpecifier, ASCENDING, DESCENDING
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation

    def get_report_messages(pk, depth, levelname):
        backend = construct()
        filters = {
            'objpk': pk,
        }

        entries = backend.log.find(filter_by=filters)
        entries = [
            entry for entry in entries
            if LOG_LEVEL_MAPPING[entry.levelname] >= LOG_LEVEL_MAPPING[levelname]
        ]
        return [(_, depth) for _ in entries]

    def get_subtree(pk, level=0):
        qb = QueryBuilder()
        qb.append(
            cls=WorkCalculation,
            filters={'id': pk},
            tag='workcalculation'
        )
        qb.append(
            cls=WorkCalculation,
            project=['id'],
            # In the future, we should specify here the type of link
            # for now, CALL links are the only ones allowing calc-calc
            # (we here really want instead to follow CALL links)
            output_of='workcalculation',
            tag='subworkchains'
        )
        result = list(itertools.chain(*qb.distinct().all()))

        # This will return a single flat list of tuples, where the first element
        # corresponds to the WorkChain pk and the second element is an integer
        # that represents its level of nesting within the chain
        return [(pk, level)] + list(itertools.chain(*[get_subtree(subpk, level=level + 1) for subpk in result]))

    def print_subtree(tree, prepend=""):
        print "{}{}".format(prepend, tree[0])
        for subtree in tree[1]:
            print_subtree(subtree, prepend=prepend + "  ")

    workchain_tree = get_subtree(pk)

    reports = list(itertools.chain(*[get_report_messages(pk, depth, levelname) for pk, depth in workchain_tree]))
    reports.sort(key=lambda r: r[0].time)

    if reports is None or len(reports) == 0:
        print "No log messages recorded for this work calculation"
        return

    object_ids = [entry[0].id for entry in reports]
    levelnames = [len(entry[0].levelname) for entry in reports]
    width_id = len(str(max(object_ids)))
    width_levelname = max(levelnames)
    for entry, depth in reports:
        print '{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]:{indent} {message}'.format(
            id=entry.id,
            levelname=entry.levelname,
            message=entry.message,
            time=entry.time,
            width_id=width_id,
            width_levelname=width_levelname,
            indent=' ' * (depth * indent_size)
        )

    return


@work.command('tree', context_settings=CONTEXT_SETTINGS)
@click.option('--node-label', default='_process_label', type=str)
@click.option('--depth', '-d', type=int, default=1)
@click.argument('pks', nargs=-1, type=int)
def tree(node_label, depth, pks):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    from aiida.utils.ascii_vis import build_tree
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.orm import load_node
    from ete3 import Tree

    for pk in pks:
        node = load_node(pk=pk)
        t = Tree("({});".format(build_tree(node, node_label, max_depth=depth)),
                 format=1)
        print(t.get_ascii(show_internal=True))


@work.command('checkpoint', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def checkpoint(pks):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    import aiida.work.persistence
    storage = aiida.work.persistence.get_default()

    for pk in pks:
        try:
            try:
                checkpoint = storage.get_checkpoint_state(pk)
            except BaseException as e:
                print("Failed to load checkpoint {}".format(pk))
                print("Exception: {}".format(e.message))
            else:
                print("Last checkpoint for calculation '{}'".format(pk))
                print(str(checkpoint))
        except ValueError:
            print("Unable to show checkpoint for calculation '{}'".format(pk))


def _build_query(projections=None, order_by=None, limit=None, past_days=None):
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation
    import aiida.utils.timezone as timezone
    import datetime

    now = timezone.now()

    # The things to filter by
    calculation_filters = {}

    if past_days is not None:
        n_days_ago = now - datetime.timedelta(days=past_days)
        calculation_filters['ctime'] = {'>': n_days_ago}

    qb = QueryBuilder()

    # Build the quiery
    qb.append(
        cls=WorkCalculation,
        filters=calculation_filters,
        project=projections,
        tag='calculation'
    )

    # ORDER
    if order_by is not None:
        qb.order_by({'calculation': order_by})

    # LIMIT
    if limit is not None:
        qb.limit(limit)

    return qb.iterdict()

@work.command('kill', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def kill(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    from aiida.orm import load_node
    from aiida.orm.calculation.work import WorkCalculation

    nodes = [load_node(pk) for pk in pks]
    workchain_nodes = [n for n in nodes if isinstance(n, WorkCalculation)]
    running_workchain_nodes = [n for n in nodes if not n.has_finished()]

    num_workchains = len(running_workchain_nodes)
    if num_workchains > 0:
        answer = click.prompt(
            'Are you sure you want to kill {} workflows and all their children? [y/n]'.format(
                num_workchains
            )
        ).lower()
        if answer == 'y':
            click.echo('Killing workflows.')
            for n in running_workchain_nodes:
                n.kill()
        else:
            click.echo('Abort!')
    else:
        click.echo('No pks of valid running workchains given.')
