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
import tempfile
import os

from aiida.sharing.sharing_info_management import (SharingInfoManagement,
                                                   SHARING_CONF_FILENAME)

VALID_DUMMY_KEY = ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxu'
                       'dLF1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidI'
                       'pgDhXdj9UFzcKfgo3Hf0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLl'
                       'zs4zE= dummy debugging key')

TEMP_CONF = {
            "user_info": [
                {
                    "username": "Spyros",
                    "key": "the_hash_key",
                    "profiles": [
                        {
                            "profile_name": "sqla_1",
                            "permission": "None"
                        }
                    ]
                }
            ]
        }

class TestSharingUserManagement(unittest.TestCase):

    temp_conf = None

    def setUp(self):
        import copy
        self. temp_conf = copy.deepcopy(TEMP_CONF)

    def test_add_user_get_user_info(self):
        from jsonschema import validate

        sim = SharingInfoManagement()
        sim.add_user(self.temp_conf, "Mark", VALID_DUMMY_KEY)

        # Check that the schema is still valid
        validate(self.temp_conf, sim.schema)

        # Get the added record
        mark_record = sim._get_user_info(self.temp_conf, "Mark")
        # Check that it is OK
        self.assertEqual(mark_record[sim.USERNAME], "Mark")
        self.assertEqual(mark_record[sim.KEY], VALID_DUMMY_KEY)
        self.assertEqual(mark_record[sim.PROFILES], list())

    def test_del_user_get_users(self):
        sim = SharingInfoManagement()

        # Adding one more user
        sim.add_user(self.temp_conf, "Mark", VALID_DUMMY_KEY)

        # Deleting the user that initially existed
        ret_code = sim.del_user(self.temp_conf, "Spyros")
        # Checking the result
        self.assertEqual(ret_code, 0)
        self.assertEqual(sim.get_users(self.temp_conf), ["Mark"])

        # Deleting the remaining user
        ret_code = sim.del_user(self.temp_conf, "Giovanni")
        # Checking the result
        self.assertEqual(ret_code, 1)
        self.assertEqual(sim.get_users(self.temp_conf), ["Mark"])

        # Deleting the remaining user
        ret_code = sim.del_user(self.temp_conf, "Mark")
        # Checking the result
        self.assertEqual(ret_code, 0)
        self.assertEqual(sim.get_users(self.temp_conf), [])

    def test_update_user_rights(self):
        sim = SharingInfoManagement()

        sim.update_user_rights(self.temp_conf, "Spyros", "sqla_1",
                               sim.READ_RIGHT)
        spyros_record = sim._get_user_info(self.temp_conf, "Spyros")
        self.assertEqual(spyros_record[sim.PROFILES][0][sim.PERMISSION],
                         sim.READ_RIGHT)

        sim.update_user_rights(self.temp_conf, "Spyros", "sqla_1",
                               sim.WRITE_RIGHT)
        spyros_record = sim._get_user_info(self.temp_conf, "Spyros")
        self.assertEqual(spyros_record[sim.PROFILES][0][sim.PERMISSION],
                         sim.WRITE_RIGHT)

        sim.update_user_rights(self.temp_conf, "Spyros", "sqla_1",
                               sim.NO_RIGHT)
        spyros_record = sim._get_user_info(self.temp_conf, "Spyros")
        self.assertEqual(spyros_record[sim.PROFILES][0][sim.PERMISSION],
                         sim.NO_RIGHT)

        # Test permissions that are not valid
        sim.update_user_rights(self.temp_conf, "Spyros", "sqla_1",
                               "Unknown right")
        spyros_record = sim._get_user_info(self.temp_conf, "Spyros")
        self.assertEqual(spyros_record[sim.PROFILES][0][sim.PERMISSION],
                         sim.NO_RIGHT)

        # Test a profile that doesn't exist
        sim.update_user_rights(self.temp_conf, "Spyros", "sqla_2",
                               sim.NO_RIGHT)
        spyros_record = sim._get_user_info(self.temp_conf, "Spyros")
        self.assertEqual(spyros_record[sim.PROFILES][0][sim.PERMISSION],
                         sim.NO_RIGHT)

    def test_update_user_key(self):
        sim = SharingInfoManagement()
        sim.update_user_key(self.temp_conf, "Spyros", VALID_DUMMY_KEY)
        spyros_record = sim._get_user_info(self.temp_conf, "Spyros")
        self.assertEqual(spyros_record[sim.KEY], VALID_DUMMY_KEY)

class TestSharingUserFile(unittest.TestCase):
    def setUp(self):
        # Creating a dummy .aiida folder
        self.sim = SharingInfoManagement()
        self.aiida_dir = tempfile.mkdtemp()
        self.sim.conf_filepath = os.path.join(self.aiida_dir,
                                              SHARING_CONF_FILENAME)

    def tearDown(self):
        # Cleaning up everything
        try:
            os.unlink(self.aiida_dir + SHARING_CONF_FILENAME)
        except Exception as e:
            pass
        try:
            os.rmdir(self.aiida_dir)
        except Exception as e:
            pass

    def test_sharing_conf_file_creation_and_loading_and_updating(self):
        # Create a simple conf file and check that it loads correctly
        self.sim.save_conf(TEMP_CONF)
        loaded_conf = self.sim.load_conf()
        self.assertEqual(TEMP_CONF, loaded_conf)

        # Add a new user to the configuration and store it
        self.sim.add_user(loaded_conf, "Mark", VALID_DUMMY_KEY)
        self.sim.update_user_rights(loaded_conf, "Mark", "sqla_2",
                                    self.sim.WRITE_RIGHT)
        self.sim.save_conf(loaded_conf)
        # Reload the conf file
        loaded_conf_v2 = self.sim.load_conf()

        # Check that the new user exists
        mark_record = self.sim._get_user_info(loaded_conf_v2, "Mark")
        # Check that it is OK
        self.assertEqual(mark_record[self.sim.USERNAME], "Mark")

        # Check the new user's rights
        mark_record = self.sim._get_user_info(loaded_conf_v2, "Mark")
        self.assertEqual(mark_record[self.sim.PROFILES][0][
                             self.sim.PERMISSION], self.sim.WRITE_RIGHT)