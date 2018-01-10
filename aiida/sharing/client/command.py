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
from aiida.sharing.command import Command

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
        self.connection.send(
            self.cmd_name, size_of_chunck = len(self.cmd_name))

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
                self.logger.debug("Sending: " + chunk)
                byte_no = self.connection.send(chunk)
                self.logger.debug("Sent " + str(byte_no) + " bytes.")
        finally:
            self.logger.debug("Sending finished, closing file")
            f.close()
