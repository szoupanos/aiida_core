# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import logging

class ConnectionServer:

    def __init__(self):
        pass

    def send(self):
        pass

    def receive(self):
        """
        This methods receives a chunk that we sent with the respective send
        command. The receive command uses the standard input to receive
        data.
        :return: The message (chunk) received.
        """
        import sys

        logging.debug("[receive] " + "Reading message size")
        msg_size = int(sys.stdin.read(self.BYTES_FOR_CHUNK_SIZE_MSG))
        logging.debug("[receive] " + "Reply that you read message size")
        sys.stdout.write(self.OK_MSG)
        sys.stdout.flush()
        logging.debug("[receive] " + "Reading message")
        msg = sys.stdin.read(msg_size)
        logging.debug("[receive] " + "Read" + msg)

        return msg

