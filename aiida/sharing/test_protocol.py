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

class ProtocolTest(unittest.TestCase):
    """
    Tests for the Protocol class.
    """

    def test_open_connection(self):
        """
        Simple test that check that the connection is opened and closed
        properly
        """
        from aiida.sharing.protocol import Protocol
        prot = Protocol()
        try:
            client, channel = prot.open_connection(
                'localhost', '/home/aiida/.ssh/id_rsa')
        finally:
            prot.close_connection(client, channel)
