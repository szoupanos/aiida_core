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
from aiida.cmdline.commands import share, verdi
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands.work import CONTEXT_SETTINGS


class Share(VerdiCommandWithSubcommands):
    """
    Share part of your AiiDA graph with other AiiDA instances
    """

    # def __init__(self):
    #     self.valid_subcommands = {
    #         'sub_com_a': (self.cli, self.complete_none),
    #         'main_command': (self.cli, self.complete_none)
    #     }

    def cli(self, *args):
        verdi()

# @share.command('name_of_subcommand', context_settings=CONTEXT_SETTINGS)


@click.group()
@click.option('--repo-home', envvar='REPO_HOME', default='.repo')
@click.option('--debug/--no-debug', default=False,
              envvar='REPO_DEBUG')
@click.pass_context
def cli(ctx, repo_home, debug):
    ctx.obj = Share(repo_home, debug)







################################### Old commands

@share.command(context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--past-days', type=int, default=1,
              help="add a filter to show only workflows created in the past N"
                   " days")
@click.option('-a', '--all', 'all_nodes', is_flag=True, help='Return all nodes. Overrides the -l flag')
@click.option('-l', '--limit', type=int, default=None,
              help="Limit to this many results")
def sub_com_a(past_days, all_nodes, limit):
    pass

@click.group(context_settings=CONTEXT_SETTINGS)
def main_command():
    pass

@main_command.command()
def foo():
    click.echo('Initialized the database')

# @cli.group()
# @click.pass_context
# def cloudflare(ctx):
#     pass

@share.command(context_settings=CONTEXT_SETTINGS)
def user():
    pass




@share.command(context_settings=CONTEXT_SETTINGS)
def user():
    pass

