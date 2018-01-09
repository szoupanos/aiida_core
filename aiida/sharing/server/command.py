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
from aiida.sharing.sharing_logging import SharingLoggingFactory
from aiida.sharing.command import CommandHandler
from aiida.sharing.command import Command

class ServerCommandHandler(CommandHandler):

    def __init__(self):
        self.logger = SharingLoggingFactory.get_logger(
            SharingLoggingFactory.get_fullclass_name(self.__class__))

    def handle(self):
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

class ReceiveFileCommand(Command):

    cmd_name = 'REC_FILE'

    logger = None

    def __init__(self):
        self.logger = SharingLoggingFactory.get_logger(
            SharingLoggingFactory.get_fullclass_name(self.__class__))

    def execute(self):
        self.logger.debug("[share_handle_push] " + "Reading the file size")
        # Read the size of the file
        file_size = int(sys.stdin.read(4))
        sys.stdout.write("OK")
        sys.stdout.flush()

        bytes_read = 0
        self.logger.debug("[share_handle_push] " + "Reading the file and "
                                               "storing it locally.")
        with open('/home/aiida/foo10/output_file.bin', 'w') as f:
            while bytes_read < file_size:
                if file_size - bytes_read > 1024:
                    self.logger.debug("[share_handle_push] " +
                                  "Reading 1024 bytes")
                    chunk = sys.stdin.read(1024)
                else:
                    self.logger.debug("[share_handle_push] " +
                                  "Reading " + str(
                        file_size - bytes_read) + " bytes")
                    chunk = sys.stdin.read(file_size - bytes_read)
                f.write(chunk)
                self.logger.debug("[share_handle_push] " +
                              "Received: " + str(chunk))
                self.logger.debug("[share_handle_push] " +
                              "Chunk length: " + str(len(chunk)))
                bytes_read += len(chunk)

        # Sending OK that the file was read
        self.logger.debug("[share_handle_push] " +
                      "Sending OK that the file was read")
        sys.stdout.write("OK")
        sys.stdout.flush()