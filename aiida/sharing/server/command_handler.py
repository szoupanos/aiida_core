# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import sys
from aiida.sharing.command_handler import CommandHandler

class ServerCommandHandler(CommandHandler):

    def handle(self, command, **kwargs):
        self.logger.debug(
            "[share_handle_push] " + "sys.stdout.closed? " + str(
                sys.stdout.closed))
        self.logger.debug("[share_handle_push] " + "Reading message size")
        msg_size = int(sys.stdin.read(4))
        self.logger.debug(
            "[share_handle_push] " + "Reply that you read message size")
        sys.stdout.write("OK")
        sys.stdout.flush()
        self.logger.debug("[share_handle_push] " + "Reading message")
        msg = sys.stdin.read(msg_size)
        self.logger.debug("[share_handle_push] " + "Read" + msg)
        if msg == "EXIT":
            self.logger.debug(
                "[share_handle_push] " + "Received an exit command, exiting")
            sys.stdout.write("OK")
            sys.stdout.flush()
            return