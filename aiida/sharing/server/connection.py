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
from aiida.sharing.connection import Connection

class ConnectionServer(Connection):

    def __init__(self):
        super(ConnectionServer, self).__init__()

    def send(self, chunk, size_of_chunck = None):
        bytes_to_send = size_of_chunck
        if size_of_chunck is None:
            bytes_to_send = sys.getsizeof(chunk)

        self.logger.debug("Sending the chunk size (" +
                      str(bytes_to_send) + " bytes)")
        sys.stdout.write(format(bytes_to_send,
                            str(self.BYTES_FOR_CHUNK_SIZE_MSG) + 'd'))
        sys.stdout.flush()

        self.logger.debug("wait for the OK to send the chunk.")
        if self.wait_for_ok() == -1:
            return 1

        sys.stdout.write(chunk)
        sys.stdout.flush()
        self.logger.debug("Sent " + str(sys.getsizeof(chunk)) +
                      " bytes.")

        self.logger.debug("wait for the OK to send the file")
        if self.wait_for_ok() == 1:
            return 1

        return 0

    def receive(self):
        """
        This methods receives a chunk that we sent with the respective send
        command. The receive command uses the standard input to receive
        data.
        :return: The message (chunk) received.
        """
        self.logger.debug("Reading message size")
        msg_size = int(sys.stdin.read(self.BYTES_FOR_CHUNK_SIZE_MSG))
        self.logger.debug("Reply that you read message size")
        sys.stdout.write(self.OK_MSG)
        sys.stdout.flush()
        self.logger.debug("Reading message")
        msg = sys.stdin.read(msg_size)
        self.logger.debug("Read: " + msg)

        return msg

    def wait_for_ok(self):
        self.logger.debug("wait for the OK reply")
        while True:
            rec_msg = sys.stdin.read(1024)
            self.logger.debug("Received: " + rec_msg)
            if rec_msg == self.OK_MSG:
                break
            if sys.stdin.closed:
                self.logger.debug("Channel is closed, exiting.")
                return 1

        return 0

