# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.common.exceptions import InvalidOperation
from aiida.sharing.client.connection import ConnectionClient
from aiida.sharing.command_handler import CommandHandler

class ClientCommandHandler(CommandHandler):

    # The underlying connection to be used for the communication
    connection = None

    # Needed information to establish the connection
    hostname = None
    key_path = None

    def __init__(self, hostname, key_path):
        # Initialising the logger
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

    def handle(self, command, **kwargs):
        if command not in self.AVAILABLE_CMDS:
            self.logger.debug("The command requested is not supported, "
                              "exiting")
            raise InvalidOperation("The command requested is not supported.")

        # Create the command class
        cmd_class = self.cmd_selector(command)
        cmd_obj = cmd_class(self.connection)
        # Execute command
        cmd_obj.execute(**kwargs)
