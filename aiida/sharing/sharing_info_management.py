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

class SharingInfoManagement:

    conf_filepath = None
    conf_info = None

    # Sharing config file keywords
    USER_INFO = "user_info"
    USERNAME = "username"
    KEY = "key"
    PROFILES = "profiles"
    PROFILE_NAME = "profile_name"
    PERMISSION = "permission"

    # The schema of the JSON file containing the sharing information
    schema = {
        "type": "object",
        "required": ["user_info"],
        "properties": {
            "user_info": {
                "type": "array",
                "uniqueItems": True,
                "items": {
                    "type": "object",
                    "required": ["username", "key", "profiles"],
                    "properties": {
                        "username": { "type": "string" },
                        "key": { "type": "string" },
                        "profiles": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["profile_name", "permission"],
                                "properties": {
                                    "profile_name": {"type": "string"},
                                    "permission": {
                                        "type": "string",
                                        "enum": ["read", "write", "none"]
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

    def update_user_rights(self, conf, username, repository, new_rights):
        pass

    def update_user_key(self, conf, username, new_key):
        pass
