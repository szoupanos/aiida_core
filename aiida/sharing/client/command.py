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

# class CommandHandler:
#
#     def __init__(self):
#         self.logger = SharingLoggingFactory.get_logger(
#             SharingLoggingFactory.get_fullclass_name(self.__class__))

class CommandHandler:

    # The underlying protocol to be used for the communication
    protocol = None

    # Selected command
    command = None

    # Available commands
    SEND_FILE = 'SEND_FILE'
    SEND_BUFF = 'SEND_BUFF'

    # Set of commands
    AVAILABLE_CMDS = set(SEND_FILE, SEND_BUFF)

    # Command logger
    logger = None

    def __init__(self, channel, command, protocol):
        # Initialising the logger
        self.logger = SharingLoggingFactory.get_logger('command_logger')



        self.channel = channel
        self.command = command

    def execute(self, command, **kwargs):
        """
        This is the general command
        :param channel:
        :param command:
        :return:
        """
        if command not in self.AVAILABLE_CMDS:
            self.logger.debug("[Command] " + "The command requested is not "
                                         "supported, exiting")
            raise InvalidOperation("The command requested is not supported.")

        # Create the command class
        self.cmd_selector(**kwargs)

    def cmd_selector(self, argument):
        switcher = {
            self.SEND_FILE : SendFileCommand(),
        }
        # Get the right send command
        cnd_class = switcher.get(argument)
        # Execute the method
        return cnd_class()

class SendFileCommand(Command):

    channel = None
    filename = None

    def __init__(self, channel):
        super(SendFileCommand, self).__init__()
        self.cmd_name = 'SEND_FILE'

    def execute(self, connection, filename):
        import time
        import sys

        if channel is None:
            self.logger.debug(
                "[Command] " + "You must provide a connection, exiting")
            raise InvalidOperation("You must provide a connection.")

        # Inform the receiver about the command to be executed
        connection.send(self.command, size_of_chunck = len(command))

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
                byte_no = session_channel.send(chunk)
                self.logger.debug("[send_file_cmd] " + "Sent " + str(byte_no)
                                  + " bytes.")
        finally:
            logging.debug(
                "[send_file_cmd] " + "Sending finished, closing file")
            f.close()
