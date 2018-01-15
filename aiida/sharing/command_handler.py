# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from abc import ABCMeta, abstractmethod
from aiida.sharing.sharing_logging import SharingLoggingFactory
from aiida.sharing.client.command import SendFileCommand
from aiida.sharing.server.command import ReceiveFileCommand

class CommandHandler:
    __metaclass__ = ABCMeta

    # Available commands
    SEND_FILE = SendFileCommand.cmd_name
    SEND_BUFF = 'SEND_BUFF'
    REC_FILE = ReceiveFileCommand.cmd_name

    # Command pairs
    CMD_PAIRS = {
        SEND_FILE: REC_FILE
    }

    # Set of commands
    AVAILABLE_CMDS = set((SEND_FILE, SEND_BUFF))

    def __init__(self):
        self.logger = SharingLoggingFactory.get_logger(
            SharingLoggingFactory.get_fullclass_name(self.__class__))

    @abstractmethod
    def handle(self, command, **kwargs):
        raise NotImplementedError("This should be properly implemented by "
                                  "the classes that inherit" + self.__class__)

    def cmd_selector(self, command_name):
        switcher = {
            self.SEND_FILE : SendFileCommand,
            self.REC_FILE : ReceiveFileCommand,
        }
        # Get the right command
        cmd_class = switcher.get(command_name)
        self.logger.debug("The " + cmd_class.__name__ + " was selected")
        return cmd_class
