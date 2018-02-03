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
from aiida.sharing.sharing_logging import SharingLoggingFactory
from aiida.sharing.sharing_info_file_management import (
    SharingInfoFileManagement)
from aiida.sharing.key_management import AuthorizedKeysFileManager
from aiida.sharing.sharing_permission_management import (
    SharingPermissionManagement)

class Share(VerdiCommandWithSubcommands):
    """
    Share part of your AiiDA graph with other AiiDA instances
    """

    def __init__(self):
        # # logging.basicConfig(filename='/home/aiida/foo9/sharing_debug.log', level=logging.DEBUG)
        # # FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
        # # logging.basicConfig(format=FORMAT)
        # logging.basicConfig(
        #     filename='/home/aiida/foo10/sharing_debug.log',
        #     format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        #     datefmt='%d-%m-%Y:%H:%M:%S',
        #     level=logging.DEBUG)

        self.valid_subcommands = {
            # 'sub_com_a': (self.cli, self.complete_none),
            'user': (self.cli, self.complete_none),
            'authorize': (self.cli, self.complete_none),
            'deauthorize': (self.cli, self.complete_none),
            'push': (self.cli, self.complete_none),
            'push_file': (self.cli, self.complete_none),
            'sharing_handler': (self.cli, self.complete_none),
            'pull': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()

logger = SharingLoggingFactory.get_logger(
    SharingLoggingFactory.get_fullclass_name(Share))

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
@click.argument('username')
@click.argument('public_key')
def share_user_add(username, public_key):
    """
    Add a sharing AiiDA user.
    """
    sim = SharingInfoFileManagement()
    conf = sim.load_conf()
    if sim.add_user(conf, username, public_key) == 0:
        sim.save_conf(conf)
        click.echo("User added successfully")
    else:
        click.echo("User already exists")


@share_user.command('remove')
@click.argument('username')
def share_user_remove(username):
    """
    Remove a sharing AiiDA user.
    """
    sim = SharingInfoFileManagement()
    conf = sim.load_conf()
    if sim.del_user(conf, username) == 0:
        sim.save_conf(conf)
        click.echo("User deleted successfully")
    else:
        click.echo("User not found")


@share_user.command('list')
@click.option('-v', '--verbose', is_flag=True, help='List also the user '
                                                    'permissions per profile')
def share_user_list(verbose):
    """
    List the available sharing AiiDA users.
    """
    user_list = SharingPermissionManagement.user_list()
    click.echo("The following sharing users were found:")
    for user in user_list.keys():
        click.echo("> " + user)
        if verbose:
            user_info = user_list[user]
            for prof, perms in user_info:
                click.echo("  Profile: " + prof +
                           " , Permissions: " + perms)
            if len(user_info) == 0:
                click.echo("  No profiles found")

@share.command('authorize')
@click.argument('username')
@click.argument('profile')
@click.argument('new_permissions')
def share_authorize(username, profile, new_permissions):
    """
    Allow an AiIDA sharing user to read or write to a specific repository.
    """
    sim = SharingInfoFileManagement()
    if not new_permissions in [sim.READ_RIGHT, sim.WRITE_RIGHT]:
        click.echo('Only the following permisions are accepted: ' +
                   sim.READ_RIGHT + ', ' + sim.WRITE_RIGHT)
        return
    conf = sim.load_conf()
    res = sim.update_user_rights(conf, username, profile, new_permissions)
    if res == 0:
        sim.save_conf(conf)
        # Now updating the authorized_keys file
        raw_ssh_key = sim.get_user_key(conf, username)
        akf = AuthorizedKeysFileManager('aiida')
        akf.create_sharing_entry(raw_ssh_key, username, profile)

        click.echo('User permissions changed successfully')
    elif res == 1:
        click.echo('The given permissions are not valid. The choices are '
                   + sim.READ_RIGHT + ', ' + sim.WRITE_RIGHT)
    elif res == 2:
        click.echo('User ' + username + ' doesn\'t exist')

@share.command('deauthorize')
@click.argument('username')
@click.argument('profile')
def share_deauthorize(username, profile):
    """
    Remove access to a specific repository from a user.
    """
    sim = SharingInfoFileManagement()
    conf = sim.load_conf()
    res = sim.update_user_rights(conf, username, profile, sim.NO_RIGHT)
    if res == 0:
        # Saving the updated conf file
        sim.save_conf(conf)

        # Now updating the authorized_keys file
        akf = AuthorizedKeysFileManager('aiida')
        akf.delete_sharing_entry(username, profile)

        click.echo('User permissions changed successfully')
    elif res == 2:
        click.echo('User ' + username + ' doesn\'t exist')
    else:
        click.echo('Unknown error')

@share.command('push')
@click.argument('remote_uri')
@click.argument('local_group')
def share_push(remote_uri, local_group):
    """
    Push the local nodes to a remote repository, indicated by the remote
    profile name.
    """
    logger.debug('command: share push')
    from aiida.sharing.client.command_handler import ClientCommandHandler
    from aiida.sharing.client.command import PushCommand

    with ClientCommandHandler(
            remote_uri,
            '/home/aiida/.ssh/id_rsa_s4'
    ) as cch:
        cch.handle(
            PushCommand.cmd_name,
            local_group=local_group)

@share.command('push_file')
def share_push_file():
    """
    Push the local nodes to a remote repository, indicated by the remote
    profile name.
    """
    logger.debug('command: share push file')
    from aiida.sharing.client.command_handler import ClientCommandHandler
    from aiida.sharing.client.command import SendFileCommand

    with ClientCommandHandler(
            'localhost',
            '/home/aiida/.ssh/id_rsa_s4'
    ) as cch:
        cch.handle(
            SendFileCommand.cmd_name,
            # filename='/home/aiida/foo10/sample.txt')
            filename='/home/aiida/foo10/LARGE_elevation.jpg')

def share_push_old():
    """
    Push the local nodes to a remote repository, indicated by the remote
    profile name.
    """
    logger.debug('command: share push')
    # paramiko_push()
    paramiko_push_file('/home/aiida/foo10/sample.txt')


@share.command('pull')
def share_pull():
    """
    Pull nodes from the repository related to the remote profile found at the
    specified remote AiiDA instance.
    """
    click.echo('command: share deauthorize')


@share.command('sharing_handler')
# @click.argument('input', type=click.File('rb'))
def sharing_handler():
    from aiida.sharing.server.command_handler import ServerCommandHandler

    logger.debug('command: share sharing_handler')
    with ServerCommandHandler() as sch:
        sch.handle()

def server_handle_push():
    """
    Pull nodes from the repository related to the remote profile found at the
    specified remote AiiDA instance.
    """
    import sys
    logger.debug("[share_handle_push] " + 'command: share share_accept_push')
    # logging.info('So should this')
    # logging.warning('And this, too')
    # click.echo('command: share share_accept_push')

    # init_non_block_stdin()
    try:
        while True:
            logger.debug(
                "[share_handle_push] " + "sys.stdout.closed? " + str(sys.stdout.closed))
            logger.debug("[share_handle_push] " + "Reading message size")
            msg_size = int(sys.stdin.read(4))
            logger.debug("[share_handle_push] " + "Reply that you read message size")
            sys.stdout.write("OK")
            sys.stdout.flush()
            logger.debug("[share_handle_push] " + "Reading message")
            msg = sys.stdin.read(msg_size)
            logger.debug("[share_handle_push] " + "Read" + msg)
            if msg == "EXIT":
                logger.debug("[share_handle_push] " + "Received an exit command, exiting")
                sys.stdout.write("OK")
                sys.stdout.flush()
                break

            if msg == "FILE_SEND":
                sys.stdout.write("OK")
                sys.stdout.flush()

                logger.debug("[share_handle_push] " + "Reading the file size")
                # Read the size of the file
                file_size = int(sys.stdin.read(4))
                sys.stdout.write("OK")
                sys.stdout.flush()

                bytes_read = 0
                logger.debug("[share_handle_push] " + "Reading the file and "
                                                       "storing it locally.")
                with open('/home/aiida/foo10/output_file.bin', 'w') as f:
                    while bytes_read < file_size:
                        if file_size - bytes_read > 1024:
                            logger.debug("[share_handle_push] " +
                                          "Reading 1024 bytes")
                            chunk = sys.stdin.read(1024)
                        else:
                            logger.debug("[share_handle_push] " +
                                          "Reading " + str(file_size - bytes_read) + " bytes")
                            chunk = sys.stdin.read(file_size - bytes_read)
                        f.write(chunk)
                        logger.debug("[share_handle_push] " +
                                      "Received: " + str(chunk))
                        logger.debug("[share_handle_push] " +
                                      "Chunk length: " + str(len(chunk)))
                        bytes_read += len(chunk)

                # Sending OK that the file was read
                logger.debug("[share_handle_push] " +
                              "Sending OK that the file was read")
                sys.stdout.write("OK")
                sys.stdout.flush()

    except Exception as e:
        logger.debug("[share_handle_push] " + "Error occured: " + e)
        if e.__cause__:
            logger.debug("[share_handle_push] " + "Cause: " + e.__cause__)
        raise

    # sys.stdout.flush()
    logger.debug("[share_handle_push] " + "Finished while loop. Exiting")

def wait_for_ok(session_channel):
    logger.debug("[paramiko_push_file] " + "wait for the OK reply")
    while True:
        rec_msg = session_channel.recv(1024)
        logger.debug("[paramiko_push_file] " + "Received" + rec_msg)
        if rec_msg == "OK":
            break
        if session_channel.exit_status_ready():
            logger.debug("[paramiko_push_file] " +
                          "Remote process has exited, exiting too")
            return -1

    return 0


# Here we have to find a way to select the needed ssh key
def paramiko_push_file(filename):
    # Docs on paramiko:
    # http://docs.paramiko.org/en/2.0/api/channel.html
    # there are various notes on how to avoid locking, to choose the parameters,
    # to be efficient, ...
    import paramiko
    import time
    import sys
    import os

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
    logger.debug("[paramiko_push_file] " + "Connected")
    transport = client.get_transport()
    logger.debug("[paramiko_push_file] " + "Transport got")
    session_channel = transport.open_session()
    logger.debug("[paramiko_push_file] " + "Session open")

    session_channel.exec_command(command='cat')


    logger.debug("[paramiko_push_file] " +
                  "Sending the size of the bytes to read")
    session_channel.send("0009")
    if wait_for_ok(session_channel) == -1:
        return

    # sending the command to be executed
    logger.debug("[paramiko_push_file] " +
                  "Informing that the command to be executed is a FILE_SEND")

    session_channel.send("FILE_SEND")
    # wait for the OK reply
    if wait_for_ok(session_channel) == -1:
        return

    logger.debug("[paramiko_push_file] " + "Proceeding to the file sent")

    file_size = os.path.getsize(filename)
    logger.debug("[paramiko_push_file] " + "Sending the file size (" +
                  str(file_size) + " bytes)")
    session_channel.send(format(file_size, '4d'))

    logger.debug("[paramiko_push_file] " + "wait for the OK to send the file")
    if wait_for_ok(session_channel) == -1:
        return

    # Proceeding to the file sent
    t = time.time()
    bytes = 0
    try:
        f = open(filename, "rb")
        while True:
            chunk = f.read(1024)
            if not chunk:
                break

            bytes += sys.getsizeof(chunk)
            logger.debug("[paramiko_push_file] " + "Sending: " + chunk)
            byte_no = session_channel.send(chunk)
            logger.debug("[paramiko_push_file] " + "Sent " + str(byte_no)
                          + " bytes.")
    finally:
        logger.debug("[paramiko_push_file] " + "Sending finished, closing file")
        f.close()

    tottime = time.time() - t
    logger.debug("[paramiko_push_file] " + "Time spent: {} s, throughput: {} kB/s.".format(
        tottime, bytes / 1000 * tottime))

    logger.debug("[paramiko_push_file] " + "wait for the OK that the file "
                                            "was sent successfully.")

    while not session_channel.exit_status_ready():
        rec_msg = session_channel.recv(1024)
        logger.debug("[paramiko_push_file] " + "Received" + rec_msg)
        if rec_msg == "OK":
            break


    logger.debug("[paramiko_push_file] " +
                  "Sending the size of the bytes to read")
    session_channel.send("0004")
    if wait_for_ok(session_channel) == -1:
        return
    logger.debug("[paramiko_push_file] " +
                  "Informing that the command to be executed is an EXIT")
    session_channel.send("EXIT")
    # wait for the OK reply
    logger.debug("[paramiko_push_file] " + "wait for the OK reply")
    while not session_channel.exit_status_ready():
        rec_msg = session_channel.recv(1024)
        logger.debug("[paramiko_push_file] " + "Received" + rec_msg)
        if rec_msg == "OK":
            break

    # Closing channels and exiting
    logger.debug("[paramiko_push_file] " + "Closing chanel")
    session_channel.close()
    client.close()
    logger.debug("[paramiko_push_file] " + "Exiting")


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

