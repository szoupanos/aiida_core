# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.sharing.connection import Connection

class ConnectionClient(Connection):

    # The underlying client and channel information
    client = None
    channel = None

    def __init__(self):
        super(ConnectionClient, self).__init__()

    def wait_for_ok(self):
        """
        This method waits for an OK from the other side of the channel
        :param channel: The channel to be used
        :return: The exit code.
        """
        self.logger.debug("wait for the OK reply")
        while True:
            rec_msg = self.channel.recv(self.BUFFER_SIZE)
            self.logger.debug("Received: " + rec_msg)
            if rec_msg == self.OK_MSG:
                break
            if self.channel.exit_status_ready():
                self.logger.debug("Remote process has exited, exiting too")
                return 1

        return 0

    def send(self, chunk, size_of_chunck = None):
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

        self.logger.debug("Sending the chunk size (" +
                      str(bytes_to_send) + " bytes)")
        self.channel.send(format(bytes_to_send,
                            str(self.BYTES_FOR_CHUNK_SIZE_MSG) + 'd'))

        self.logger.debug("wait for the OK to send the chunk.")
        if self.wait_for_ok() == -1:
            return 1

        byte_no = self.channel.send(chunk)
        self.logger.debug("Sent " + str(byte_no) + " bytes.")

        self.logger.debug("wait for the OK that chunk was received OK")
        if self.wait_for_ok() == 1:
            return 1

        return 0

    def receive(self):
        self.logger.debug("Reading message size")
        chunk_size = self.channel.recv(self.BYTES_FOR_CHUNK_SIZE_MSG)
        self.logger.debug("Reply that you read message size")
        self.channel.send(self.OK_MSG)
        self.logger.debug("Reading message")
        msg = self.channel.recv(chunk_size)
        self.logger.debug("Read: " + msg)

    def open_connection(self, hostname, key_path):
        """
        This method opens a connection to the remote host identified by the
        hostname. The key found at the specific key_path is used for
        identification
        :param hostname: The remote host.
        :param key_path: The path to the key.
        """
        import paramiko

        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        key = paramiko.RSAKey.from_private_key_file(key_path)

        # Also params here, e.g. key_filename=, timeout=, ...
        self.client.connect(hostname, pkey=key)
        self.logger.debug("Connected")
        transport = self.client.get_transport()
        self.logger.debug("Transport got")
        self.channel = transport.open_session()
        self.logger.debug("Session/channel open")

        self.channel.exec_command(command='cat')

    def close_connection(self):
        """
        Closing channels and exiting
        """
        if self.channel is not None:
            self.logger.debug("Closing chanel")
            self.channel.close()
        if self.client is not None:
            self.logger.debug("Closing client")
            self.client.close()

        self.logger.debug("Exiting")
