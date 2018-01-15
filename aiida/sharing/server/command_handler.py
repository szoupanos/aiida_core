# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.sharing.command_handler import CommandHandler
from aiida.sharing.server.connection import ConnectionServer
from aiida.common.exceptions import InvalidOperation

class ServerCommandHandler(CommandHandler):

    # The underlying connection to be used for the communication
    connection = None

    def __init__(self):
        super(ServerCommandHandler, self).__init__()

    def __enter__(self):
        self.logger.debug("Creating the server connection object")
        self.connection = ConnectionServer()
        return self

    def __exit__(self, *exc):
        return False

    def handle(self, **kwargs):
        try:
            self.logger.debug("In the handle method")
            command = self.connection.receive()
            self.logger.debug("Received command " + command)

            if command not in self.AVAILABLE_CMDS:
                self.logger.debug("The command requested is not supported, "
                                  "exiting")
                raise InvalidOperation("The command requested is not supported.")

            # Create the command class
            srv_command = self.CMD_PAIRS[command]
            self.logger.debug("I will execute the " + srv_command + " command")
            srv_cmd_class = self.cmd_selector(srv_command)
            cmd_obj = srv_cmd_class(self.connection)
            # Execute command
            self.logger.debug("Calling the execute method of " + str(cmd_obj)
                              + " with the following arguments: " + str(kwargs))
            cmd_obj.execute(**kwargs)
        except Exception as e:
            self.logger.exception("An exception was caught")

        # self.logger.debug("sys.stdout.closed? " + str(sys.stdout.closed))
        # self.logger.debug("Reading message size")
        # msg_size = int(sys.stdin.read(10))
        # self.logger.debug("Reply that you read message size")
        # sys.stdout.write("OK")
        # sys.stdout.flush()
        # self.logger.debug("Reading message")
        # msg = sys.stdin.read(msg_size)
        # self.logger.debug("Read" + msg)
        # if msg == "EXIT":
        #     self.logger.debug("Received an exit command, exiting")
        #     sys.stdout.write("OK")
        #     sys.stdout.flush()
        #     return