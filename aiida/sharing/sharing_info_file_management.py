# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import os
import json
from aiida.common.setup import AIIDA_CONFIG_FOLDER

from jsonschema import validate
from jsonschema.exceptions import ValidationError as JValidationError
from aiida.common.exceptions import ValidationError as AValidationError

SHARING_CONF_FILENAME = "sharing_conf.json"

class SharingInfoFileManagement:

    conf_filepath = None
    conf_info = None

    # Sharing config file keywords
    USER_INFO = "user_info"
    USERNAME = "username"
    KEY = "key"
    PROFILES = "profiles"
    PROFILE_NAME = "profile_name"
    PERMISSION = "permission"

    # Available profile rights
    READ_RIGHT = "Read"
    WRITE_RIGHT = "Write"
    NO_RIGHT = "None"
    RIGHTS_ORDER = [NO_RIGHT, READ_RIGHT, WRITE_RIGHT]
    AVAIL_PROF_RIGHTS = set(RIGHTS_ORDER)

    # The schema of the JSON file containing the sharing information
    schema = {
        "type": "object",
        "required": [USER_INFO],
        "properties": {
            USER_INFO: {
                "type": "array",
                "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": [USERNAME, KEY, PROFILES],
                    "properties": {
                        USERNAME: { "type": "string" },
                        KEY: { "type": "string" },
                        PROFILES: {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": [PROFILE_NAME, PERMISSION],
                                "properties": {
                                    PROFILE_NAME: {"type": "string"},
                                    PERMISSION: {
                                        "type": "string",
                                        "enum": [READ_RIGHT, WRITE_RIGHT,
                                                 NO_RIGHT]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    def __init__(self):
        aiida_dir = os.path.expanduser(AIIDA_CONFIG_FOLDER)
        self.conf_filepath = os.path.join(aiida_dir, SHARING_CONF_FILENAME)

    def _get_rights_importance(self, given_rights):
        return self.RIGHTS_ORDER.index(given_rights)

    def load_conf(self):
        with open(self.conf_filepath, "r") as jsonFile:
            conf = json.load(jsonFile)
            try:
                validate(conf, self.schema)
            except JValidationError as jv:
                raise AValidationError("The sharing configuration file doesn't "
                                       "pass the validation check: " +
                                       jv.message)
            return conf

    def save_conf(self, conf):
        try:
            validate(conf, self.schema)
        except JValidationError as jv:
            raise AValidationError("The sharing configuration file doesn't "
                                   "pass the validation check: " +
                                   jv.message)
        with open(self.conf_filepath, "w") as jsonFile:
            json.dump(conf, jsonFile)

    def add_user(self, conf, username, key):
        if (len(conf[self.USER_INFO]) == 0 or
                username not in self.get_users(conf)):
            conf[self.USER_INFO].append({
                self.USERNAME: username,
                self.KEY: key,
                self.PROFILES: list()
            })
            return 0

        return 1

    def del_user(self, conf, username):
        if len(conf[self.USER_INFO]) == 0:
           return 1

        users = self.get_users(conf)
        if username not in users:
            return 1

        pos = users.index(username)
        conf[self.USER_INFO].pop(pos)

        return 0

    def get_users(self, conf):
        return [_[self.USERNAME] for _ in conf[self.USER_INFO]]

    def _get_user_info(self, conf, username):
        for user_info in conf[self.USER_INFO]:
            if user_info[self.USERNAME] == username:
                return user_info
        return None

    def update_user_rights(self, conf, username, profile, new_rights):
        """
        Update the user rights
        :param conf:
        :param username:
        :param profile:
        :param new_rights:
        :return: 1 if the given rights are not correct, 2 if the user doesn't
        exist.
        """
        if new_rights not in self.AVAIL_PROF_RIGHTS:
            return 1

        user_info = self._get_user_info(conf, username)
        if user_info is None:
            return 2

        for prof in user_info[self.PROFILES]:
            if prof[self.PROFILE_NAME] == profile:
                prof[self.PERMISSION] = new_rights
                return 0
        # If the profile doesn't exist, we add it
        user_info[self.PROFILES].append({
            self.PROFILE_NAME: profile,
            self.PERMISSION: new_rights
        })

        return 0

    def get_user_key(self, conf, username):
        user_info = self._get_user_info(conf, username)
        if user_info is None:
            return 1

        return user_info[self.KEY]

    def update_user_key(self, conf, username, new_key):
        user_info = self._get_user_info(conf, username)
        if user_info is None:
            return 1

        user_info[self.KEY] = new_key

        return 1

    def check_user_rights(self, conf, username, profile, needed_rights):
        """
        :param conf:
        :param username:
        :param profile:
        :param needed_rights:
        :return:
        0 If the user can access the repository
        1 If the user doesn't exist in the configuration
        2 If the user doesn't have the needed right for the provided profile
        3 If the user doesn't even have the profile in his available profiles
        (and, of course, doesn't have needed right to access it)
        """
        user_info = self._get_user_info(conf, username)
        # If the user is not found
        if user_info is None:
            return 1
        for prof in user_info[self.PROFILES]:
            # If the profile is found the
            if prof[self.PROFILE_NAME] == profile:
                # If the user has the permission to access the profile with
                # the given rights
                if (self._get_rights_importance(prof[self.PERMISSION]) >=
                        self._get_rights_importance(needed_rights)):
                    return 0
                # If the user doesn't have the permission to access the
                # profile with the given rights
                else:
                    return 2
        # The user doesn't have this profile listed in his profiles
        return 3