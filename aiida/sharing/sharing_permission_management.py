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

class SharingPermissionManagement:

    def user_add(self, username, public_key):
        sim = SharingInfoFileManagement()
        conf = sim.load_conf()
        if sim.add_user(conf, username, public_key) == 0:
            sim.save_conf(conf)
            click.echo("User added successfully")
        else:
            click.echo("User already exists")

    def user_list(self):
        pass

    def user_remove(self):
        pass

    def authorize(self):
        pass

    def deauthorize(self):
        pass
