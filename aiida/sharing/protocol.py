# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import logging

class Protocol:

    # The buffer size
    BUFFER_SIZE = 1024

    # This is the reserved number of bytes for chunk message
    # that will be sent by the sender to the receiver
    BYTES_FOR_CHUNK_SIZE_MSG = 10

    # Acknowledgement message
    OK_MSG = 'OK'

    # Channel information needed for the command execution
    channel = None

    def __init__(self):
        pass

    def wait_for_ok(self, channel):
        """
        This method waits for an OK from the other side of the channel
        :param channel: The channel to be used
        :return: The exit code.
        """
        logging.debug("[wait_for_ok] " + "wait for the OK reply")
        while True:
            rec_msg = channel.recv(1024)
            logging.debug("[wait_for_ok] " + "Received" + rec_msg)
            if rec_msg == self.OK_MSG:
                break
            if channel.exit_status_ready():
                logging.debug("[wait_for_ok] " +
                              "Remote process has exited, exiting too")
                return 1

        return 0

    def send(self, channel, chunk, size_of_chunck = None):
        """
        This method sends a chunk to the receiver using the provided channel.
        It will send size_of_chunck bytes. If the size is not given, then it
        will measure the size of chunk.
        :param channel: The channel to be used.
        :param chunk: What needs to be sent.
        :param size_of_chunck: The size of the bytes in the chunk that need to
        be sent
        :return: 0 if everything went well. 1 if something went wrong
        """
        import sys

        bytes_to_send = size_of_chunck
        if size_of_chunck is None:
            bytes_to_send = sys.getsizeof(chunk)

        logging.debug("[send] " + "Sending the chunk size (" +
                      str(bytes_to_send) + " bytes)")
        channel.send(format(bytes_to_send,
                            str(self.BYTES_FOR_CHUNK_SIZE_MSG) + 'd'))

        logging.debug("[send] " + "wait for the OK to send the chunk.")
        if self.wait_for_ok(channel) == -1:
            return 1

        byte_no = channel.send(chunk)
        logging.debug("[send] " + "Sent " + str(byte_no) + " bytes.")

        logging.debug(
            "[send] " + "wait for the OK to send the file")
        if self.wait_for_ok(channel) == 1:
            return 1

        return 0

    def receive(self):
        """
        This methods receives a chunk that we sent with the respective send
        command. The receive command uses the standard input to receive
        data.
        :return: The message (chunk) received.
        """
        import sys

        logging.debug("[receive] " + "Reading message size")
        msg_size = int(sys.stdin.read(self.BYTES_FOR_CHUNK_SIZE_MSG))
        logging.debug("[receive] " + "Reply that you read message size")
        sys.stdout.write(self.OK_MSG)
        sys.stdout.flush()
        logging.debug("[receive] " + "Reading message")
        msg = sys.stdin.read(msg_size)
        logging.debug("[receive] " + "Read" + msg)

        return msg

    @staticmethod
    def open_connection(hostname, key_path):
        """
        This method opens a connection to the remote host identified by the
        hostname. The key found at the specific key_path is used for
        idenitification
        :param hostname: The remote host.
        :param key_path: The path to the key.
        :return: The open channel to the remote host open for further usage.
        """
        import paramiko

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        key = paramiko.RSAKey.from_private_key_file(key_path)

        # Also params here, e.g. key_filename=, timeout=, ...
        client.connect(hostname, pkey=key)
        logging.debug("[open_connection] " + "Connected")
        transport = client.get_transport()
        logging.debug("[open_connection] " + "Transport got")
        channel = transport.open_session()
        logging.debug("[open_connection] " + "Session/channel open")

        channel.exec_command(command='cat')

        return client, channel

    @staticmethod
    def close_connection(client, channel):
        """
        Closing channels and exiting
        """
        if channel is not None:
            logging.debug("[close_connection] " + "Closing chanel")
            channel.close()
        if client is not None:
            logging.debug("[close_connection] " + "Closing client")
            client.close()

        logging.debug("[close_connection] " + "Exiting")

    def submit_cmd(self, channel, command):
        """
        This is the general command
        :param channel:
        :param command:
        :return:
        """
        if command not in self.AVAILABLE_CMDS:
            logging.debug("[submit_cmd] " + "Not a valid command, exiting")
            return 1

        # Inform the receiver about the command to be executed
        self.send(channel, command, size_of_chunck = len(command))

        # Execute the command

class Command:

    # The underlying protocol to be used for the communication
    protocol = None

    # Selected command
    command = None

    # Available commands
    SEND_FILE = 'SEND_FILE'
    SEND_BUFF = 'SEND_BUFF'

    # Set of commands
    AVAILABLE_CMDS = set(SEND_FILE, SEND_BUFF)

    def __init__(self, channel, command, protocol):
        from aiida.common.exceptions import InvalidOperation

        if channel is None or command is None:
            logging.debug("[Command] " + "You must provide a command and a "
                                         "channel, exiting")
            raise InvalidOperation("You must provide a command and a channel.")
        if command not in self.AVAILABLE_CMDS:
            logging.debug("[Command] " + "The command requested is not "
                                         "supported, exiting")
            raise InvalidOperation("The command requested is not supported.")

        self.channel = channel
        self.command = command

    def submit(self, command, **kwargs):
        """
        This is the general command
        :param channel:
        :param command:
        :return:
        """
        # Inform the receiver about the command to be executed
        self.send(self.channel, self.command, size_of_chunck = len(command))

        # Execute the command
        self.send_cmd_selector(**kwargs)

    def send_cmd_selector(self, argument):
        switcher = {
            self.SEND_FILE : self.send_file_cmd,
            self.SEND_BUFF: self.send_buff_cmd,
        }
        # Get the right send command
        send_cmd = switcher.get(argument)
        # Execute the method
        return send_cmd()

    def send_file_cmd(self, filename):
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
                logging.debug("[send_file_cmd] " + "Sending: " + chunk)
                byte_no = session_channel.send(chunk)
                logging.debug("[send_file_cmd] " + "Sent " + str(byte_no)
                              + " bytes.")
        finally:
            logging.debug(
                "[send_file_cmd] " + "Sending finished, closing file")
            f.close()

    def send_buff_cmd(self, **kwargs):
        pass


def paramiko_push_file(filename):
    """
    This function sends a file
    :param filename:
    :return:
    """
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
    logging.debug("[paramiko_push_file] " + "Connected")
    transport = client.get_transport()
    logging.debug("[paramiko_push_file] " + "Transport got")
    session_channel = transport.open_session()
    logging.debug("[paramiko_push_file] " + "Session open")

    session_channel.exec_command(command='cat')


    logging.debug("[paramiko_push_file] " +
                  "Sending the size of the bytes to read")
    session_channel.send("0009")
    if wait_for_ok(session_channel) == -1:
        return

    # sending the command to be executed
    logging.debug("[paramiko_push_file] " +
                  "Informing that the command to be executed is a FILE_SEND")

    session_channel.send("FILE_SEND")
    # wait for the OK reply
    if wait_for_ok(session_channel) == -1:
        return

    logging.debug("[paramiko_push_file] " + "Proceeding to the file sent")

    file_size = os.path.getsize(filename)
    logging.debug("[paramiko_push_file] " + "Sending the file size (" +
                  str(file_size) + " bytes)")
    session_channel.send(format(file_size, '4d'))

    logging.debug("[paramiko_push_file] " + "wait for the OK to send the file")
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
            logging.debug("[paramiko_push_file] " + "Sending: " + chunk)
            byte_no = session_channel.send(chunk)
            logging.debug("[paramiko_push_file] " + "Sent " + str(byte_no)
                          + " bytes.")
    finally:
        logging.debug("[paramiko_push_file] " + "Sending finished, closing file")
        f.close()

    tottime = time.time() - t
    logging.debug("[paramiko_push_file] " + "Time spent: {} s, throughput: {} kB/s.".format(
        tottime, bytes / 1000 * tottime))

    logging.debug("[paramiko_push_file] " + "wait for the OK that the file "
                                            "was sent successfully.")

    while not session_channel.exit_status_ready():
        rec_msg = session_channel.recv(1024)
        logging.debug("[paramiko_push_file] " + "Received" + rec_msg)
        if rec_msg == "OK":
            break


    logging.debug("[paramiko_push_file] " +
                  "Sending the size of the bytes to read")
    session_channel.send("0004")
    if wait_for_ok(session_channel) == -1:
        return
    logging.debug("[paramiko_push_file] " +
                  "Informing that the command to be executed is an EXIT")
    session_channel.send("EXIT")
    # wait for the OK reply
    logging.debug("[paramiko_push_file] " + "wait for the OK reply")
    while not session_channel.exit_status_ready():
        rec_msg = session_channel.recv(1024)
        logging.debug("[paramiko_push_file] " + "Received" + rec_msg)
        if rec_msg == "OK":
            break

    # Closing channels and exiting
    logging.debug("[paramiko_push_file] " + "Closing chanel")
    session_channel.close()
    client.close()
    logging.debug("[paramiko_push_file] " + "Exiting")




# Here we have to find a way to select the needed ssh key
def paramiko_push_file_old(filename):
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
    logging.debug("[paramiko_push_file] " + "Connected")
    transport = client.get_transport()
    logging.debug("[paramiko_push_file] " + "Transport got")
    session_channel = transport.open_session()
    logging.debug("[paramiko_push_file] " + "Session open")

    session_channel.exec_command(command='cat')


    logging.debug("[paramiko_push_file] " +
                  "Sending the size of the bytes to read")
    session_channel.send("0009")
    if wait_for_ok(session_channel) == -1:
        return

    # sending the command to be executed
    logging.debug("[paramiko_push_file] " +
                  "Informing that the command to be executed is a FILE_SEND")

    session_channel.send("FILE_SEND")
    # wait for the OK reply
    if wait_for_ok(session_channel) == -1:
        return

    logging.debug("[paramiko_push_file] " + "Proceeding to the file sent")

    file_size = os.path.getsize(filename)
    logging.debug("[paramiko_push_file] " + "Sending the file size (" +
                  str(file_size) + " bytes)")
    session_channel.send(format(file_size, '4d'))

    logging.debug("[paramiko_push_file] " + "wait for the OK to send the file")
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
            logging.debug("[paramiko_push_file] " + "Sending: " + chunk)
            byte_no = session_channel.send(chunk)
            logging.debug("[paramiko_push_file] " + "Sent " + str(byte_no)
                          + " bytes.")
    finally:
        logging.debug("[paramiko_push_file] " + "Sending finished, closing file")
        f.close()

    tottime = time.time() - t
    logging.debug("[paramiko_push_file] " + "Time spent: {} s, throughput: {} kB/s.".format(
        tottime, bytes / 1000 * tottime))

    logging.debug("[paramiko_push_file] " + "wait for the OK that the file "
                                            "was sent successfully.")

    while not session_channel.exit_status_ready():
        rec_msg = session_channel.recv(1024)
        logging.debug("[paramiko_push_file] " + "Received" + rec_msg)
        if rec_msg == "OK":
            break


    logging.debug("[paramiko_push_file] " +
                  "Sending the size of the bytes to read")
    session_channel.send("0004")
    if wait_for_ok(session_channel) == -1:
        return
    logging.debug("[paramiko_push_file] " +
                  "Informing that the command to be executed is an EXIT")
    session_channel.send("EXIT")
    # wait for the OK reply
    logging.debug("[paramiko_push_file] " + "wait for the OK reply")
    while not session_channel.exit_status_ready():
        rec_msg = session_channel.recv(1024)
        logging.debug("[paramiko_push_file] " + "Received" + rec_msg)
        if rec_msg == "OK":
            break

    # Closing channels and exiting
    logging.debug("[paramiko_push_file] " + "Closing chanel")
    session_channel.close()
    client.close()
    logging.debug("[paramiko_push_file] " + "Exiting")


def share_handle_push():
    """
    Pull nodes from the repository related to the remote profile found at the
    specified remote AiiDA instance.
    """
    import sys
    logging.debug("[share_handle_push] " + 'command: share share_accept_push')
    # logging.info('So should this')
    # logging.warning('And this, too')
    # click.echo('command: share share_accept_push')

    # init_non_block_stdin()
    try:
        while True:
            logging.debug(
                "[share_handle_push] " + "sys.stdout.closed? " + str(sys.stdout.closed))
            logging.debug("[share_handle_push] " + "Reading message size")
            msg_size = int(sys.stdin.read(4))
            logging.debug("[share_handle_push] " + "Reply that you read message size")
            sys.stdout.write("OK")
            sys.stdout.flush()
            logging.debug("[share_handle_push] " + "Reading message")
            msg = sys.stdin.read(msg_size)
            logging.debug("[share_handle_push] " + "Read" + msg)
            if msg == "EXIT":
                logging.debug("[share_handle_push] " + "Received an exit command, exiting")
                sys.stdout.write("OK")
                sys.stdout.flush()
                break

            if msg == "FILE_SEND":
                sys.stdout.write("OK")
                sys.stdout.flush()

                logging.debug("[share_handle_push] " + "Reading the file size")
                # Read the size of the file
                file_size = int(sys.stdin.read(4))
                sys.stdout.write("OK")
                sys.stdout.flush()

                bytes_read = 0
                logging.debug("[share_handle_push] " + "Reading the file and "
                                                       "storing it locally.")
                with open('/home/aiida/foo10/output_file.bin', 'w') as f:
                    while bytes_read < file_size:
                        if file_size - bytes_read > 1024:
                            logging.debug("[share_handle_push] " +
                                          "Reading 1024 bytes")
                            chunk = sys.stdin.read(1024)
                        else:
                            logging.debug("[share_handle_push] " +
                                          "Reading " + str(file_size - bytes_read) + " bytes")
                            chunk = sys.stdin.read(file_size - bytes_read)
                        f.write(chunk)
                        logging.debug("[share_handle_push] " +
                                      "Received: " + str(chunk))
                        logging.debug("[share_handle_push] " +
                                      "Chunk length: " + str(len(chunk)))
                        bytes_read += len(chunk)

                # Sending OK that the file was read
                logging.debug("[share_handle_push] " +
                              "Sending OK that the file was read")
                sys.stdout.write("OK")
                sys.stdout.flush()

    except Exception as e:
        logging.debug("[share_handle_push] " + "Error occured: " + e)
        if e.__cause__:
            logging.debug("[share_handle_push] " + "Cause: " + e.__cause__)
        raise

    # sys.stdout.flush()
    logging.debug("[share_handle_push] " + "Finished while loop. Exiting")



