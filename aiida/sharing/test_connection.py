# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import unittest

class ConnectionTest(unittest.TestCase):
    """
    Tests for the Protocol class.
    """
    @unittest.skip("Needs more work")
    def test_open_connection(self):
        """
        Simple test that check that the connection is opened and closed
        properly
        """
        from aiida.sharing.client.connection_client import ConnectionClient
        conn = ConnectionClient()
        try:
            conn.open_connection('localhost', '/home/aiida/.ssh/')
        finally:
            conn.close_connection()

    # # This needs more work on send & receive
    @unittest.skip("Needs more work")
    def test_send_receive(self):
        from aiida.sharing.client.connection_client import ConnectionClient
        prot = ConnectionClient()
        msg = "This is a message to send"
        try:
            client, channel = prot.open_connection(
                'localhost', '/home/aiida/.ssh/id_rsa')

            prot.send(channel=channel, chunk = msg)
        finally:

            prot.close_connection(client, channel)
