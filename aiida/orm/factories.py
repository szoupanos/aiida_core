# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all common top level AiiDA entity classes and methods"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import singledispatch

from aiida.orm.implementation.computers import BackendComputer
from aiida.orm.implementation.groups import BackendGroup
from aiida.orm.implementation.users import BackendUser
from aiida.orm.node import Node

from . import groups
from . import computers
from . import users


class EntityFactory(object):
    """
    A factory to create entities
    """

    @staticmethod
    def get_orm_from_backend_entity(backend_entity_instance):
        """
        Create ORM entities that their type corresponds to the backend type.
        """
        # Node doesn't have a backend type and it is already an ORM entity
        if isinstance(backend_entity_instance, Node):
            return backend_entity_instance
        return get_corresponding_orm_class(backend_entity_instance).from_backend_entity(backend_entity_instance)


##################################################################
# Singledispatch to get the ORM instance from the backend instance
##################################################################
@singledispatch.singledispatch
def get_corresponding_orm_class(_):
    return None


@get_corresponding_orm_class.register(BackendGroup)
def _(_):
    return groups.Group


@get_corresponding_orm_class.register(BackendComputer)
def _(_):
    return computers.Computer


@get_corresponding_orm_class.register(BackendUser)
def _(_):
    return users.User
