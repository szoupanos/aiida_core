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
            'handle_push': (self.cli, self.complete_none),
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
    # paramiko_push()
    paramiko_push_file('/home/aiida/foo9/sample.txt')


@share.command('pull')
def share_pull():
    """
    Pull nodes from the repository related to the remote profile found at the
    specified remote AiiDA instance.
    """
    click.echo('command: share deauthorize')


@share.command('handle_push')
# @click.argument('input', type=click.File('rb'))
def share_handle_push():
    """
    Pull nodes from the repository related to the remote profile found at the
    specified remote AiiDA instance.
    """
    import sys

    click.echo('command: share share_accept_push')

    while True:
        chunk = sys.stdin.read(1024)
        if not chunk:
            break
        click.echo(chunk)

# Here we have to find a way to select the needed ssh key
def paramiko_push_file(filename):
    # Docs on paramiko:
    # http://docs.paramiko.org/en/2.0/api/channel.html
    # there are various notes on how to avoid locking, to choose the parameters,
    # to be efficient, ...
    import paramiko
    import time
    import sys

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    # client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    k = paramiko.RSAKey.from_private_key_file(
        "/home/aiida/.ssh/id_rsa_s4")

    # Also params here, e.g. key_filename=, timeout=, ...
    client.connect('ubuntu-aiida-vm1.epfl.ch', pkey=k)
    # client.connect('ubuntu-aiida-vm1.epfl.ch')
    # client.connect('localhost')
    # client.connect('theossrv2.epfl.ch')
    print "Connected"
    transport = client.get_transport()
    print "Transport got"
    session_channel = transport.open_session()
    print "Session open"

    session_channel.exec_command(command='cat')

    t = time.time()
    bytes = 0
    f = open(filename, "rb")
    try:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
                bytes += sys.getsizeof(chunk)
            session_channel.send(chunk)
    finally:
        f.close()

    tottime = time.time() - t
    print "Time spent: {} s, throughput: {} kB/s.".format(tottime,
                                                          bytes / 1000 * tottime)

    session_channel.close()
    client.close()


def paramiko_push():
    # Docs on paramiko:
    # http://docs.paramiko.org/en/2.0/api/channel.html
    # there are various notes on how to avoid locking, to choose the parameters,
    # to be efficient, ...
    import paramiko
    import time

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    # client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Also params here, e.g. key_filename=, timeout=, ...
    client.connect('ubuntu-aiida-vm1.epfl.ch')
    # client.connect('localhost')
    # client.connect('theossrv2.epfl.ch')
    print "Connected"
    transport = client.get_transport()
    print "Transport got"
    session_channel = transport.open_session()
    print "Session open"

    session_channel.exec_command(command='cat')
    print "Connected to 'cat'"

    max_len = 10000
    num_loops = 1000
    kbs = num_loops * max_len / 1024.

    print "{} loops with {} bytes = {:.1f} kB".format(num_loops, max_len, kbs)

    t = time.time()
    for loop in range(num_loops):
        newstring = ""
        string = "a" * max_len
        bytes_sent = session_channel.send(string)
        assert bytes_sent == len(string), "send:{} vs {}".format(bytes_sent,
                                                                 len(string))
        # Note: this might not be the best strategy, it might lock forever, etc.
        # At least, create the channel with a timeout.
        # Also to check if this is the right way to use a socket or if there
        # are risks of blocking
        while len(newstring) < len(string):
            newstringpart = session_channel.recv(max_len)
            newstring += newstringpart

        assert newstring == string, "recv:{} vs {}".format(len(newstring),
                                                           len(string))
    tottime = time.time() - t
    print "Time spent: {} s, throughput: {} kB/s.".format(tottime,
                                                          kbs / tottime)

    session_channel.close()
    client.close()

# We should have methods to manage the authorized keys.

