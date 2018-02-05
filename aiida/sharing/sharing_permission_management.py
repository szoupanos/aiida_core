# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.sharing.sharing_info_file_management import (
    SharingInfoFileManagement)
from aiida.sharing.key_management import AuthorizedKeysFileManager

class SharingPermissionManagement(object):

    @staticmethod
    def user_add(username, public_key):
        sim = SharingInfoFileManagement()
        conf = sim.load_conf()
        old_conf = str(conf)
        if sim.add_user(conf, username, public_key) == 0:
            # User added successfully
            akf = AuthorizedKeysFileManager()
            # Getting a copy of the authorized_keys file
            old_auth_keys = akf.get_authorized_keys()
            try:
                # Saving the sharing configuration
                sim.save_conf(conf)
                # Now updating the authorized_keys file
                akf.create_sharing_entry(public_key, username)
                return 0
            except:
                # If something goes wrong, restore the old files
                sim.save_conf(old_conf)
                akf.set_authorized_keys(old_auth_keys)
                return 2
        else:
            # User already exists
            return 1

    @staticmethod
    def user_list():
        """
        Returns the available users with their permissions
        :return: A dictionary of the type
        {username: [(prof_1, perm_1), ..., ()]}
        """
        sim = SharingInfoFileManagement()
        conf = sim.load_conf()

        res = dict()

        users = sim.get_users(conf)
        for user in users:
            prof_info = list()
            user_info = sim._get_user_info(conf, user)
            for profile in user_info[sim.PROFILES]:
                prof_info.append((profile[sim.PROFILE_NAME],
                                 profile[sim.PERMISSION]))
            res[user] = prof_info

        return res

    @staticmethod
    def user_remove(username):
        sim = SharingInfoFileManagement()
        conf = sim.load_conf()
        old_conf = str(conf)
        if sim.del_user(conf, username) == 0:
            sim.save_conf(conf)
            # User deleted successfully
            akf = AuthorizedKeysFileManager()
            # Getting a copy of the authorized_keys file
            old_auth_keys = akf.get_authorized_keys()
            try:
                # Saving the sharing configuration
                sim.save_conf(conf)
                # Now updating the authorized_keys file
                akf.delete_sharing_entry(username)
                return 0
            except:
                # If something goes wrong, restore the old files
                sim.save_conf(old_conf)
                akf.set_authorized_keys(old_auth_keys)
                return 2
        else:
            # User not found
            return 1

    @staticmethod
    def authorize(username, profile, new_permissions):
        # If the given permissions are not correct
        if not new_permissions in [SharingInfoFileManagement.READ_RIGHT,
                                   SharingInfoFileManagement.WRITE_RIGHT]:
            return 1
        return SharingInfoFileManagement._permission_change()

    @staticmethod
    def deauthorize(self):
        return SharingInfoFileManagement._permission_change(
            SharingInfoFileManagement.NO_RIGHT)

    @staticmethod
    def _permission_change(username, profile, new_permissions):
        sim = SharingInfoFileManagement()
        conf = sim.load_conf()
        res = sim.update_user_rights(conf, username, profile, new_permissions)
        if res == 0:
            # Successful permission change, saving
            sim.save_conf(conf)
        else:
            # Propagate the results
            return res