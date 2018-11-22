# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend query implementation classes"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import singledispatch
import six
from sqlalchemy_utils.types.choice import Choice

from aiida.backends.djsite.db.models import DbAuthInfo as DjangoSchemaDbAuthInfo
from aiida.backends.djsite.db.models import DbComputer as DjangoSchemaDbComputer
from aiida.backends.djsite.db.models import DbGroup as DjangoSchemaDbGroup
from aiida.backends.djsite.db.models import DbNode as DjangoSchemaDbNode
from aiida.backends.djsite.db.models import DbUser as DjangoSchemaDbUser
from aiida.common import exceptions
from aiida.common.exceptions import DbContentError
from aiida.common.exceptions import InputValidationError
from aiida.common.utils import abstractclassmethod
from aiida.orm.implementation.django.authinfo import DjangoAuthInfo
from aiida.orm.implementation.django.computer import DjangoComputer
from aiida.orm.implementation.django.groups import DjangoGroup
from aiida.orm.implementation.django.users import DjangoUser
from aiida.plugins.loader import get_plugin_type_from_type_string, load_plugin

__all__ = ('BackendQueryBuilder',)


@six.add_metaclass(abc.ABCMeta)
class BackendQueryBuilder(object):
    """Backend query builder interface"""

    # pylint: disable=invalid-name

    def __init__(self, backend):
        self._backend = backend

    @abc.abstractmethod
    def Node(self):
        """
        Decorated as a property, returns the implementation for DbNode.
        It needs to return a subclass of sqlalchemy.Base, which means that for different ORM's
        a corresponding dummy-model  must be written.
        """
        pass

    @abc.abstractmethod
    def Link(self):
        """
        A property, decorated with @property. Returns the implementation for the DbLink
        """
        pass

    @abc.abstractmethod
    def Computer(self):
        """
        A property, decorated with @property. Returns the implementation for the Computer
        """
        pass

    @abc.abstractmethod
    def User(self):
        """
        A property, decorated with @property. Returns the implementation for the User
        """
        pass

    @abc.abstractmethod
    def Group(self):
        """
        A property, decorated with @property. Returns the implementation for the Group
        """
        pass

    @abc.abstractmethod
    def AuthInfo(self):
        """
        A property, decorated with @property. Returns the implementation for the Group
        """
        pass

    @abc.abstractmethod
    def table_groups_nodes(self):
        """
        A property, decorated with @property. Returns the implementation for the many-to-many
        relationship between group and nodes.
        """
        pass

    @abc.abstractmethod
    def AiidaNode(self):
        """
        A property, decorated with @property. Returns the implementation for the AiiDA-class for Node
        """
        pass

    @abc.abstractmethod
    def get_session(self):
        """
        :returns: a valid session, an instance of sqlalchemy.orm.session.Session
        """
        pass

    @abc.abstractmethod
    def modify_expansions(self, alias, expansions):
        """
        Modify names of projections if ** was specified.
        This is important for the schema having attributes in a different table.
        """
        pass

    @abstractclassmethod
    def get_filter_expr_from_attributes(cls, operator, value, attr_key, column=None, column_name=None, alias=None):  # pylint: disable=too-many-arguments
        """
        Returns an valid SQLAlchemy expression.

        :param operator: The operator provided by the user ('==',  '>', ...)
        :param value: The value to compare with, e.g. (5.0, 'foo', ['a','b'])
        :param str attr_key:
            The path to that attribute as a tuple of values.
            I.e. if that attribute I want to filter by is the 2nd element in a list stored under the
            key 'mylist', this is ('mylist', '2').
        :param column: Optional, an instance of sqlalchemy.orm.attributes.InstrumentedAttribute or
        :param str column_name: The name of the column, and the backend should get the InstrumentedAttribute.
        :param alias: The aliased class.

        :returns: An instance of sqlalchemy.sql.elements.BinaryExpression
        """
        pass

    @classmethod
    def get_filter_expr_from_column(cls, operator, value, column):
        """
        A method that returns an valid SQLAlchemy expression.

        :param operator: The operator provided by the user ('==',  '>', ...)
        :param value: The value to compare with, e.g. (5.0, 'foo', ['a','b'])
        :param column: an instance of sqlalchemy.orm.attributes.InstrumentedAttribute or

        :returns: An instance of sqlalchemy.sql.elements.BinaryExpression
        """
        # Label is used because it is what is returned for the
        # 'state' column by the hybrid_column construct

        # Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
        # pylint: disable=no-name-in-module,import-error
        from sqlalchemy.sql.elements import Cast, Label
        from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute
        from sqlalchemy.sql.expression import ColumnClause
        from sqlalchemy.types import String

        if not isinstance(column, (Cast, InstrumentedAttribute, QueryableAttribute, Label, ColumnClause)):
            raise TypeError('column ({}) {} is not a valid column'.format(type(column), column))
        database_entity = column
        if operator == '==':
            expr = database_entity == value
        elif operator == '>':
            expr = database_entity > value
        elif operator == '<':
            expr = database_entity < value
        elif operator == '>=':
            expr = database_entity >= value
        elif operator == '<=':
            expr = database_entity <= value
        elif operator == 'like':
            # the like operator expects a string, so we cast to avoid problems
            # with fields like UUID, which don't support the like operator
            expr = database_entity.cast(String).like(value)
        elif operator == 'ilike':
            expr = database_entity.ilike(value)
        elif operator == 'in':
            expr = database_entity.in_(value)
        else:
            raise InputValidationError('Unknown operator {} for filters on columns'.format(operator))
        return expr

    @abc.abstractmethod
    def get_projectable_attribute(self, alias, column_name, attrpath, cast=None, **kwargs):
        pass

    def get_backend_entity_res(self, _, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param key: the key that this entry would be returned with
        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        # from aiida.orm.groups import Group
        # from aiida.orm.computers import Computer
        # from aiida.orm.users import User
        # from aiida.orm.node import Node

        from aiida.orm.implementation.users import BackendUser
        from aiida.orm.implementation.groups import BackendGroup
        from aiida.orm.implementation.computers import BackendComputer
        from aiida.orm.node import Node

        # if it is a Choice SQL type then return the value of it
        if isinstance(res, Choice):
            returnval = res.value
        # otherwise it should be a model type and we need the AiiDA class instance
        else:
            backend_entity = get_backend_entity(res, self._backend)
            if not isinstance(backend_entity, (Node, BackendGroup, BackendComputer, BackendUser)):
                return res
            returnval = backend_entity

        return returnval

    @abc.abstractmethod
    def yield_per(self, query, batch_size):
        """
        :param int batch_size: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        pass

    @abc.abstractmethod
    def count(self, query):
        """
        :returns: the number of results
        """
        pass

    @abc.abstractmethod
    def first(self, query):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """

        pass

    @abc.abstractmethod
    def iterall(self, query, batch_size, tag_to_index_dict):
        """
        :return: An iterator over all the results of a list of lists.
        """
        pass

    @abc.abstractmethod
    def iterdict(self, query, batch_size, tag_to_projected_entity_dict):
        """
        :returns: An iterator over all the results of a list of dictionaries.
        """
        pass

    def get_column(self, colname, alias):  # pylint: disable=no-self-use
        """
        Return the column for a given projection.
        """
        try:
            return getattr(alias, colname)
        except AttributeError:
            raise exceptions.InputValidationError("{} is not a column of {}\n"
                                                  "Valid columns are:\n"
                                                  "{}".format(
                                                      colname,
                                                      alias,
                                                      '\n'.join(alias._sa_class_manager.mapper.c.keys())  # pylint: disable=protected-access
                                                  ))


#####################################################################
# Singledispatch to get the backend instance from the Models instance
#####################################################################
@singledispatch.singledispatch
def get_backend_entity(dbmodel_instance, _):
    """
    Default get_backend_entity
    """
    return dbmodel_instance


##################################
# Singledispatch for Django Models
##################################
@get_backend_entity.register(DjangoSchemaDbUser)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbUser
    """
    return DjangoUser.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbGroup)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbGroup
    """
    return DjangoGroup.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbComputer)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbGroup
    """
    return DjangoComputer.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbNode)
def _(dbmodel_instance, _):
    """
    get_backend_entity for Django DbNode. It will return an ORM instance since
    there is not Node backend entity yet.
    """
    try:
        plugin_type = get_plugin_type_from_type_string(dbmodel_instance.type)
    except DbContentError:
        raise DbContentError("The type name of node with pk= {} is "
                             "not valid: '{}'".format(dbmodel_instance.pk, dbmodel_instance.type))

    plugin_class = load_plugin(plugin_type, safe=True)
    return plugin_class(dbnode=dbmodel_instance)


@get_backend_entity.register(DjangoSchemaDbAuthInfo)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbAuthInfo
    """
    return DjangoAuthInfo.from_dbmodel(dbmodel_instance, backend_instance)


##########################################
# Singledispatch for Aldjemy Django Models
##########################################
@get_backend_entity.register(DjangoSchemaDbUser.sa)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Aldjemy DbNode.
    It created the Django Models instance on the fly and it converts it to Django
    backend instance. Aldjemy instances are created when QueryBuilder queries the
    Django backend.
    """
    djuser_instance = DjangoSchemaDbUser(
        id=dbmodel_instance.id,
        email=dbmodel_instance.email,
        password=dbmodel_instance.password,
        first_name=dbmodel_instance.first_name,
        last_name=dbmodel_instance.last_name,
        institution=dbmodel_instance.institution,
        is_staff=dbmodel_instance.is_staff,
        is_active=dbmodel_instance.is_active,
        last_login=dbmodel_instance.last_login,
        date_joined=dbmodel_instance.date_joined)
    return DjangoUser.from_dbmodel(djuser_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbGroup.sa)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Aldjemy DbGroup.
    It created the Django Models instance on the fly and it converts it to Django
    backend instance. Aldjemy instances are created when QueryBuilder queries the
    Django backend.
    """
    djgroup_instance = DjangoSchemaDbGroup(
        id=dbmodel_instance.id,
        type=dbmodel_instance.type,
        uuid=dbmodel_instance.uuid,
        name=dbmodel_instance.name,
        time=dbmodel_instance.time,
        description=dbmodel_instance.description,
        user_id=dbmodel_instance.user_id,
    )
    return DjangoGroup.from_dbmodel(djgroup_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbComputer.sa)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Aldjemy DbComputer.
    It created the Django Models instance on the fly and it converts it to Django
    backend instance. Aldjemy instances are created when QueryBuilder queries the
    Django backend.
    """
    djcomputer_instance = DjangoSchemaDbComputer(
        id=dbmodel_instance.id,
        uuid=dbmodel_instance.uuid,
        name=dbmodel_instance.name,
        hostname=dbmodel_instance.hostname,
        description=dbmodel_instance.description,
        enabled=dbmodel_instance.enabled,
        transport_type=dbmodel_instance.transport_type,
        scheduler_type=dbmodel_instance.scheduler_type,
        transport_params=dbmodel_instance.transport_params,
        metadata=dbmodel_instance._metadata)  # pylint: disable=protected-access
    return DjangoComputer.from_dbmodel(djcomputer_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbNode.sa)
def _(dbmodel_instance, _):
    """
    get_backend_entity for Aldjemy DbNode.
    It created the Django Models instance on the fly and it converts it to Django
    backend instance. Aldjemy instances are created when QueryBuilder queries the
    Django backend.
    """
    djnode_instance = DjangoSchemaDbNode(
        id=dbmodel_instance.id,
        type=dbmodel_instance.type,
        process_type=dbmodel_instance.process_type,
        uuid=dbmodel_instance.uuid,
        ctime=dbmodel_instance.ctime,
        mtime=dbmodel_instance.mtime,
        label=dbmodel_instance.label,
        description=dbmodel_instance.description,
        dbcomputer_id=dbmodel_instance.dbcomputer_id,
        user_id=dbmodel_instance.user_id,
        public=dbmodel_instance.public,
        nodeversion=dbmodel_instance.nodeversion)

    try:
        plugin_type = get_plugin_type_from_type_string(djnode_instance.type)
    except DbContentError:
        raise DbContentError("The type name of node with pk= {} is "
                             "not valid: '{}'".format(djnode_instance.pk, djnode_instance.type))

    plugin_class = load_plugin(plugin_type, safe=True)
    return plugin_class(dbnode=djnode_instance)


@get_backend_entity.register(DjangoSchemaDbAuthInfo.sa)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Aldjemy DbAuthInfo.
    It created the Django Models instance on the fly and it converts it to Django
    backend instance. Aldjemy instances are created when QueryBuilder queries the
    Django backend.
    """
    djauthinfo_instance = DjangoSchemaDbAuthInfo(
        id=dbmodel_instance.id,
        aiidauser_id=dbmodel_instance.aiidauser_id,
        dbcomputer_id=dbmodel_instance.dbcomputer_id,
        metadata=dbmodel_instance._metadata,  # pylint: disable=protected-access
        auth_params=dbmodel_instance.auth_params,
        enabled=dbmodel_instance.enabled,
    )
    return DjangoAuthInfo.from_dbmodel(djauthinfo_instance, backend_instance)
