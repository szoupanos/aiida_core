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

    def __init__(self):
        self.valid_subcommands = {
            # 'sub_com_a': (self.cli, self.complete_none),
            'user': (self.cli, self.complete_none),
            'authorize': (self.cli, self.complete_none),
            'deauthorize': (self.cli, self.complete_none),
            'push': (self.cli, self.complete_none),
            'pull': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()

# @share.command('name_of_subcommand', context_settings=CONTEXT_SETTINGS)

# @share.command(context_settings=CONTEXT_SETTINGS)
# @click.option('-p', '--past-days', type=int, default=1,
#               help="add a filter to show only workflows created in the past N"
#                    " days")
# @click.option('-a', '--all', 'all_nodes', is_flag=True, help='Return all nodes. Overrides the -l flag')
# @click.option('-l', '--limit', type=int, default=None,
#               help="Limit to this many results")
# def sub_com_a(past_days, all_nodes, limit):
#     pass


@share.group('user')
def share_user():
    """
    This is the user management command sub-group.
    """
    pass


@share_user.command('add')
def share_user_add():
    """
    Add a sharing AiiDA user.
    """
    click.echo('command: share user add')


@share_user.command('remove')
def share_user_remove():
    """
    Remove a sharing AiiDA user.
    """
    click.echo('command: share user remove')


@share_user.command('list')
def share_user_list():
    """
    List the available sharing AiiDA users.
    """
    click.echo('command: share user list')


@share.command('authorize')
def share_authorize():
    """
    Allow an AiIDA sharing user to read or write to a specific repository.
    """
    click.echo('command: share authorize')


@share.command('deauthorize')
def share_deauthorize():
    """
    Remove access to a specific repository from a user.
    """
    click.echo('command: share deauthorize')


@share.command('push')
def share_push():
    """
    Push the local nodes to a remote repository, indicated by the remote
    profile name.
    """
    click.echo('command: share push')


@share.command('pull')
def share_pull():
    """
    Pull nodes from the repository related to the remote profile found at the
    specified remote AiiDA instance.
    """
    click.echo('command: share deauthorize')