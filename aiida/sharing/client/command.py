# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.sharing.sharing_logging import SharingLoggingFactory
from aiida.common.exceptions import InvalidOperation
from aiida.sharing.command import Command
from aiida.sharing.client.connection import ConnectionClient
from aiida.sharing.command import CommandHandler

class ClientCommandHandler(CommandHandler):

    # The underlying connection to be used for the communication
    connection = None

    # Needed information to establish the connection
    hostname = None
    key_path = None

    # Command logger
    logger = None

    def __init__(self, hostname, key_path):
        # Initialising the logger
        self.logger = SharingLoggingFactory.get_logger('command_logger')
        self.hostname = hostname
        self.key_path = key_path

    def __enter__(self):
        if (not self.hostname is None) and (not self.key_path is None):
            self.connection = ConnectionClient()
            self.connection.open_connection(self.hostname, self.key_path)
        return self

    def __exit__(self, *exc):
        if self.connection is not None:
            self.connection.close_connection()
        return False

    def execute(self, command, **kwargs):
        if command not in self.AVAILABLE_CMDS:
            self.logger.debug("[Command] " + "The command requested is not "
                                         "supported, exiting")
            raise InvalidOperation("The command requested is not supported.")

        # Create the command class
        cmd_class = self.cmd_selector(**kwargs)
        cmd_obj = cmd_class(self.connection)
        # Execute command
        cmd_obj.execute(**kwargs)

class SendFileCommand(Command):

    cmd_name = 'SEND_FILE'

    filename = None
    connection = None

    def __init__(self, connection):
        super(SendFileCommand, self).__init__()
        self.connection = connection

    def execute(self, filename):
        import time
        import sys

        if self.connection is None:
            self.logger.debug(
                "The connection is not initialized, exiting")
            raise InvalidOperation("The connection is not initialized")

        # Inform the receiver about the command to be executed
        self.connection.send(self.command, size_of_chunck = len(self.cmd_name))

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
                self.logger.debug("[send_file_cmd] " + "Sending: " + chunk)
                byte_no = self.connection.send(chunk)
                self.logger.debug("[send_file_cmd] " + "Sent " + str(byte_no)
                                  + " bytes.")
        finally:
            self.logger.debug(
                "[send_file_cmd] " + "Sending finished, closing file")
            f.close()
