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
from aiida.sharing.command import Command
from aiida.common.exceptions import InvalidOperation

class ReceiveFileCommand(Command):

    cmd_name = 'REC_FILE'

    connection = None

    def __init__(self, connection):
        super(ReceiveFileCommand, self).__init__()
        self.connection = connection
        self.logger.debug("Initialized the receive command")

    def execute(self):
        self.logger.debug("In the execute of the " + self.cmd_name +
                          " command")

        if self.connection is None:
            self.logger.debug(
                "The connection is not initialized, exiting")
            raise InvalidOperation("The connection is not initialized")

        # Receiving the size of the file
        self.logger.debug("Receiving the size of the file")
        msg = self.connection.receive()
        self.logger.debug("Received: " + msg)
        file_size = int(msg)

        bytes_read = 0
        self.logger.debug("Reading the file and storing it locally.")
        with open('/home/aiida/foo10/output_file.bin', 'w') as f:
            while bytes_read < file_size:
                chunk = self.connection.receive()
                self.logger.debug("Received: " + msg)
                f.write(chunk)
                bytes_read += len(chunk)

        # Sending OK that the file was read
        self.logger.debug("File was read OK. Exiting receive command.")

        # with open('/home/aiida/foo10/output_file.bin', 'w') as f:
        #     while bytes_read < file_size:
        #         if file_size - bytes_read > 1024:
        #             self.logger.debug("Reading 1024 bytes")
        #             chunk = sys.stdin.read(1024)
        #         else:
        #             self.logger.debug("[share_handle_push] " +
        #                           "Reading " + str(
        #                 file_size - bytes_read) + " bytes")
        #             chunk = sys.stdin.read(file_size - bytes_read)
        #         f.write(chunk)
        #         self.logger.debug("[share_handle_push] " +
        #                       "Received: " + str(chunk))
        #         self.logger.debug("[share_handle_push] " +
        #                       "Chunk length: " + str(len(chunk)))
        #         bytes_read += len(chunk)
        #
        # # Sending OK that the file was read
        # self.logger.debug("[share_handle_push] " +
        #               "Sending OK that the file was read")
        # sys.stdout.write("OK")
        # sys.stdout.flush()