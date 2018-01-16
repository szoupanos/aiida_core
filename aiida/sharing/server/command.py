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

class HandlePushCommand(Command):

    cmd_name = 'HANDLE_PUSH'

    connection = None

    def __init__(self, connection):
        super(HandlePushCommand, self).__init__()
        self.connection = connection
        self.logger.debug("Initialized the receive command")

    def execute(self):
        filename = "/home/aiida/sharing_rec.out"

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
        with open(filename, 'w') as f:
            while bytes_read < file_size:
                chunk = self.connection.receive()
                self.logger.debug("Received: " + msg)
                f.write(chunk)
                bytes_read += len(chunk)

        # Sending OK that the file was read
        self.logger.debug("File was read OK. Exiting receive command.")

        # Execute the import
        from aiida import load_dbenv, is_dbenv_loaded
        from aiida.backends import settings
        if not is_dbenv_loaded():
            load_dbenv(profile=settings.AIIDADB_PROFILE)

        from aiida.backends.settings import BACKEND
        from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
        from aiida.sharing.importexport import import_data_dj, import_data_sqla

        if BACKEND == BACKEND_SQLA:
            import_data_sqla(filename)
        elif BACKEND == BACKEND_DJANGO:
            import_data_dj(filename)
