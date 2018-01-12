# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

###########################################################################
# This is also "heavily inspired" by                                      #
# https://github.com/toresbe/AuthorizedKeys                               #
# But that was used as a starting point but it was also enriched.         #
###########################################################################

import unittest

from aiida.sharing.sharing_info_management import SharingInfoManagement

class TestSharingUserManagement(unittest.TestCase):

    temp_conf = None

    valid_dummy_key = ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxu'
                       'dLF1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidI'
                       'pgDhXdj9UFzcKfgo3Hf0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLl'
                       'zs4zE= dummy debugging key')

    def setUp(self):
        self. temp_conf = {
            "user_info": [
                {
                    "username": "Spyros",
                    "key": "the_hash_key",
                    "profiles": [
                        {
                            "profile_name": "sqla_1",
                            "permission": "none"
                        }
                    ]
                }
            ]
        }

    def test_add_user_get_user_info(self):
        from jsonschema import validate

        sim = SharingInfoManagement()
        sim.add_user(self.temp_conf, 'Mark', self.valid_dummy_key)

        # Check that the schema is still valid
        validate(self.temp_conf, sim.schema)

        # Get the added record
        mark_record = sim._get_user_info(self.temp_conf, 'Mark')
        # Check that it is OK
        self.assertEqual(mark_record[sim.USERNAME], 'Mark')
        self.assertEqual(mark_record[sim.KEY], self.valid_dummy_key)
        self.assertEqual(mark_record[sim.PROFILES], list())

    def test_del_user_get_users(self):
        sim = SharingInfoManagement()

        # Adding one more user
        sim.add_user(self.temp_conf, 'Mark', self.valid_dummy_key)

        # Deleting the user that initially existed
        ret_code = sim.del_user(self.temp_conf, "Spyros")
        # Checking the result
        self.assertEqual(ret_code, 0)
        self.assertEqual(sim.get_users(self.temp_conf), ['Mark'])

        # Deleting the remaining user
        ret_code = sim.del_user(self.temp_conf, "Giovanni")
        # Checking the result
        self.assertEqual(ret_code, 1)
        self.assertEqual(sim.get_users(self.temp_conf), ['Mark'])

        # Deleting the remaining user
        ret_code = sim.del_user(self.temp_conf, "Mark")
        # Checking the result
        self.assertEqual(ret_code, 0)
        self.assertEqual(sim.get_users(self.temp_conf), [])




