# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import contextlib
import six
from six.moves import zip, range
from django.db import models as m
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.contrib.postgres.fields import JSONField
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.contrib.postgres.fields import JSONField

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.common.exceptions import (ConfigurationError, DbContentError, AiidaException)
from aiida.backends.djsite.settings.settings import AUTH_USER_MODEL
import aiida.backends.djsite.db.migrations as migrations
from aiida.backends.utils import AIIDA_ATTRIBUTE_SEP

from aiida.backends.utils import datetime_to_isoformat, isoformat_to_datetime

# This variable identifies the schema version of this file.
# Every time you change the schema below in *ANY* way, REMEMBER TO CHANGE
# the version here in the migration file and update migrations/__init__.py.
# See the documentation for how to do all this.
#
# The version is checked at code load time to verify that the code schema
# version and the DB schema version are the same. (The DB schema version
# is stored in the DbSetting table and the check is done in the
# load_dbenv() function).
SCHEMA_VERSION = migrations.current_schema_version()


class AiidaQuerySet(QuerySet):
    def iterator(self):
        from aiida.orm.implementation.django import convert
        for obj in super(AiidaQuerySet, self).iterator():
            yield convert.get_backend_entity(obj, None)

    def __iter__(self):
        """Iterate for list comprehensions.

        Note: used to rely on the iterator in django 1.8 but does no longer in django 1.11.
        """
        from aiida.orm.implementation.django import convert
        return (convert.get_backend_entity(model, None) for model in super(AiidaQuerySet, self).__iter__())

    def __getitem__(self, key):
        """Get item for [] operator

        Note: used to rely on the iterator in django 1.8 but does no longer in django 1.11.
        """
        from aiida.orm.implementation.django import convert
        res = super(AiidaQuerySet, self).__getitem__(key)
        return convert.get_backend_entity(res, None)


class AiidaObjectManager(m.Manager):
    def get_queryset(self):
        return AiidaQuerySet(self.model, using=self._db)


class DbUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email (that is the
        username) and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = BaseUserManager.normalize_email(email)
        user = self.model(email=email,
                          is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, date_joined=now, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class DbUser(AbstractBaseUser, PermissionsMixin):
    """
    This class replaces the default User class of Django
    """
    # Set unique email field
    email = m.EmailField(unique=True, db_index=True)
    first_name = m.CharField(max_length=254, blank=True)
    last_name = m.CharField(max_length=254, blank=True)
    institution = m.CharField(max_length=254, blank=True)

    is_staff = m.BooleanField(default=False,
                              help_text='Designates whether the user can log into this admin '
                                        'site.')
    is_active = m.BooleanField(default=True,
                               help_text='Designates whether this user should be treated as '
                                         'active. Unselect this instead of deleting accounts.')
    date_joined = m.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'

    objects = DbUserManager()


@python_2_unicode_compatible
class DbNode(m.Model):
    """
    Generic node: data or calculation or code.

    Nodes can be linked (DbLink table)
    Naming convention for Node relationships: A --> C --> B.

    * A is 'input' of C.
    * C is 'output' of A.

    Internal attributes, that define the node itself,
    are stored in the DbAttribute table; further user-defined attributes,
    called 'extra', are stored in the DbExtra table (same schema and methods
    of the DbAttribute table, but the code does not rely on the content of the
    table, therefore the user can use it at his will to tag or annotate nodes.

    :note: Attributes in the DbAttribute table have to be thought as belonging
       to the DbNode, (this is the reason for which there is no 'user' field
       in the DbAttribute field). Moreover, Attributes define uniquely the
       Node so should be immutable
    """
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    # in the form data.upffile., data.structure., calculation., ...
    # Note that there is always a final dot, to allow to do queries of the
    # type (node_type__startswith="calculation.") and avoid problems with classes
    # starting with the same string
    # max_length required for index by MySql
    node_type = m.CharField(max_length=255, db_index=True)
    process_type = m.CharField(max_length=255, db_index=True, null=True)
    label = m.CharField(max_length=255, db_index=True, blank=True)
    description = m.TextField(blank=True)
    # creation time
    ctime = m.DateTimeField(default=timezone.now, db_index=True, editable=False)
    mtime = m.DateTimeField(auto_now=True, db_index=True, editable=False)
    # Cannot delete a user if something is associated to it
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.PROTECT,
                        related_name='dbnodes')

    # Direct links
    outputs = m.ManyToManyField('self', symmetrical=False,
                                related_name='inputs', through='DbLink')

    # Used only if dbnode is a calculation, or remotedata
    # Avoid that computers can be deleted if at least a node exists pointing
    # to it.
    dbcomputer = m.ForeignKey('DbComputer', null=True, on_delete=m.PROTECT,
                              related_name='dbnodes')

    # Index that is incremented every time a modification is done on itself or on attributes.
    # Managed by the aiida.orm.Node class. Do not modify
    nodeversion = m.IntegerField(default=1, editable=False)

    # For the API: whether this node
    public = m.BooleanField(default=False)

    # JSON Attributes
    attributes = JSONField(default=None, null=True)
    # JSON Extras
    extras = JSONField(default=None, null=True)

    objects = m.Manager()
    # Return aiida Node instances or their subclasses instead of DbNode instances
    aiidaobjects = AiidaObjectManager()

    def __init__(self, *args, **kwargs):
        super(DbNode, self).__init__(*args, **kwargs)

        if self.attributes is None:
            self.attributes = dict()
        else:
            self.attributes = datetime_to_isoformat(self.attributes)

        if self.extras is None:
            self.extras = dict()
        else:
            self.extras = datetime_to_isoformat(self.extras)

    def set_attribute(self, key, value):
        DbNode._set_attr(self.attributes, key, value)
        self.save()

    def reset_attributes(self, attributes):
        self.attributes = dict()
        self.set_attributes(attributes)

    def set_attributes(self, attributes):
        for key, value in attributes.items():
            DbNode._set_attr(self.attributes, key, value)
        self.save()

    def set_extra(self, key, value):
        DbNode._set_attr(self.extras, key, value)
        self.save()

    def set_extras(self, extras):
        for key, value in extras.items():
            DbNode._set_attr(self.extras, key, value)
        self.save()

    def reset_extras(self, new_extras):
        self.extras.clear()
        self.extras.update(new_extras)
        self.save()

    def del_attribute(self, key):
        DbNode._del_attr(self.attributes, key)
        self.save()

    def del_extra(self, key):
        DbNode._del_attr(self.extras, key)
        self.save()

    def get_attributes(self):
        return isoformat_to_datetime(self.attributes)
        # return self.attributes

    def get_extras(self):
        return isoformat_to_datetime(self.extras)
        # return self.extras

    @ staticmethod
    def _set_attr(d, key, value):
        if '.' in key:
            raise ValueError("We don't know how to treat key with dot in it yet")
        # This is important in order to properly handle datetime objects
        d[key] = datetime_to_isoformat(value)

    @ staticmethod
    def _del_attr(d, key):
        if '.' in key:
            raise ValueError("We don't know how to treat key with dot in it yet")
        if key not in d:
            raise AttributeError("Key {} does not exists".format(key))
        del d[key]

    def get_simple_name(self, invalid_result=None):
        """
        Return a string with the last part of the type name.

        If the type is empty, use 'Node'.
        If the type is invalid, return the content of the input variable
        ``invalid_result``.

        :param invalid_result: The value to be returned if the node type is
            not recognized.
        """
        thistype = self.node_type
        # Fix for base class
        if thistype == "":
            thistype = "node.Node."
        if not thistype.endswith("."):
            return invalid_result
        else:
            thistype = thistype[:-1]  # Strip final dot
            return thistype.rpartition('.')[2]

    def __str__(self):
        simplename = self.get_simple_name(invalid_result="Unknown")
        # node pk + type
        if self.label:
            return "{} node [{}]: {}".format(simplename, self.pk, self.label)
        else:
            return "{} node [{}]".format(simplename, self.pk)


@python_2_unicode_compatible
class DbLink(m.Model):
    """Direct connection between two dbnodes. The label is identifying thelink type."""

    # If I delete an output, delete also the link; if I delete an input, stop
    # NOTE: this will in most cases render a DbNode.objects.filter(...).delete()
    # call unusable because some nodes will be inputs; Nodes will have to
    #    be deleted in the proper order (or links will need to be deleted first)
    # The `input` and `output` columns do not need an explicit `db_index` as it is `True` by default for foreign keys
    input = m.ForeignKey('DbNode', related_name='output_links', on_delete=m.PROTECT)
    output = m.ForeignKey('DbNode', related_name='input_links', on_delete=m.CASCADE)
    label = m.CharField(max_length=255, db_index=True, blank=False)
    type = m.CharField(max_length=255, db_index=True, blank=True)

    def __str__(self):
        return "{} ({}) --> {} ({})".format(
            self.input.get_simple_name(invalid_result="Unknown node"),
            self.input.pk,
            self.output.get_simple_name(invalid_result="Unknown node"),
            self.output.pk, )


attrdatatype_choice = (
    ('float', 'float'),
    ('int', 'int'),
    ('txt', 'txt'),
    ('bool', 'bool'),
    ('date', 'date'),
    ('json', 'json'),
    ('dict', 'dict'),
    ('list', 'list'),
    ('none', 'none'))


class DeserializationException(AiidaException):
    pass


def _deserialize_attribute(mainitem, subitems, sep, original_class=None,
                           original_pk=None, lesserrors=False):
    """
    Deserialize a single attribute.

    :param mainitem: the main item (either the attribute itself for base
      types (None, string, ...) or the main item for lists and dicts.
      Must contain the 'key' key and also the following keys:
      datatype, tval, fval, ival, bval, dval.
      NOTE that a type check is not performed! tval is expected to be a string,
      dval a date, etc.
    :param subitems: must be a dictionary of dictionaries. In the top-level dictionary,
      the key must be the key of the attribute, stripped of all prefixes
      (i.e., if the mainitem has key 'a.b' and we pass subitems
      'a.b.0', 'a.b.1', 'a.b.1.c', their keys must be '0', '1', '1.c').
      It must be None if the value is not iterable (int, str,
      float, ...).
      It is an empty dictionary if there are no subitems.
    :param sep: a string, the separator between subfields (to separate the
      name of a dictionary from the keys it contains, for instance)
    :param original_class: if these elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass, pass here the class (note: the class,
      not the instance!). This is used only in case the wrong number of elements
      is found in the raw data, to print a more meaningful message (if the class
      has a dbnode associated to it)
    :param original_pk: if the elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass that has a dbnode associated to it,
      pass here the PK integer. This is used only in case the wrong number
      of elements is found in the raw data, to print a more meaningful message
    :param lesserrors: If set to True, in some cases where the content of the
      DB is not consistent but data is still recoverable,
      it will just log the message rather than raising
      an exception (e.g. if the number of elements of a dictionary is different
      from the number declared in the ival field).

    :return: the deserialized value
    :raise aiida.backends.djsite.db.models.DeserializationException: if an error occurs
    """
    from aiida.common import json
    from aiida.common.timezone import (
        is_naive, make_aware, get_current_timezone)

    from aiida.common import AIIDA_LOGGER

    if mainitem['datatype'] == 'none':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return None
    elif mainitem['datatype'] == 'bool':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['bval']
    elif mainitem['datatype'] == 'int':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['ival']
    elif mainitem['datatype'] == 'float':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['fval']
    elif mainitem['datatype'] == 'txt':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        return mainitem['tval']
    elif mainitem['datatype'] == 'date':
        if subitems:
            raise DeserializationException("'{}' is of a base type, "
                                           "but has subitems!".format(mainitem.key))
        if is_naive(mainitem['dval']):
            return make_aware(mainitem['dval'], get_current_timezone())
        else:
            return mainitem['dval']

    elif mainitem['datatype'] == 'list':
        # subitems contains all subitems, here I store only those of
        # deepness 1, i.e. if I have subitems '0', '1' and '1.c' I
        # store only '0' and '1'
        firstlevelsubdict = {k: v for k, v in subitems.items()
                             if sep not in k}

        # For checking, I verify the expected values
        expected_set = set(["{:d}".format(i)
                            for i in range(mainitem['ival'])])
        received_set = set(firstlevelsubdict.keys())
        # If there are more entries than expected, but all expected
        # ones are there, I just issue an error but I do not stop.

        if not expected_set.issubset(received_set):
            if (original_class is not None and original_class._subspecifier_field_name is not None):
                subspecifier_string = "{}={} and ".format(
                    original_class._subspecifier_field_name,
                    original_pk)
            else:
                subspecifier_string = ""
            if original_class is None:
                sourcestr = "the data passed"
            else:
                sourcestr = original_class.__name__

            raise DeserializationException("Wrong list elements stored in {} for "
                                           "{}key='{}' ({} vs {})".format(
                sourcestr,
                subspecifier_string,
                mainitem['key'], expected_set, received_set))
        if expected_set != received_set:
            if (original_class is not None and
                    original_class._subspecifier_field_name is not None):
                subspecifier_string = "{}={} and ".format(
                    original_class._subspecifier_field_name,
                    original_pk)
            else:
                subspecifier_string = ""
            if original_class is None:
                sourcestr = "the data passed"
            else:
                sourcestr = original_class.__name__

            msg = ("Wrong list elements stored in {} for "
                   "{}key='{}' ({} vs {})".format(
                sourcestr,
                subspecifier_string,
                mainitem['key'], expected_set, received_set))
            if lesserrors:
                AIIDA_LOGGER.error(msg)
            else:
                raise DeserializationException(msg)

        # I get the values in memory as a dictionary
        tempdict = {}
        for firstsubk, firstsubv in firstlevelsubdict.items():
            # I call recursively the same function to get subitems
            newsubitems = {k[len(firstsubk) + len(sep):]: v
                           for k, v in subitems.items()
                           if k.startswith(firstsubk + sep)}
            tempdict[firstsubk] = _deserialize_attribute(mainitem=firstsubv,
                                                         subitems=newsubitems, sep=sep, original_class=original_class,
                                                         original_pk=original_pk)

        # And then I put them in a list
        retlist = [tempdict["{:d}".format(i)] for i in range(mainitem['ival'])]
        return retlist
    elif mainitem['datatype'] == 'dict':
        # subitems contains all subitems, here I store only those of
        # deepness 1, i.e. if I have subitems '0', '1' and '1.c' I
        # store only '0' and '1'
        firstlevelsubdict = {k: v for k, v in subitems.items()
                             if sep not in k}

        if len(firstlevelsubdict) != mainitem['ival']:
            if (original_class is not None and
                    original_class._subspecifier_field_name is not None):
                subspecifier_string = "{}={} and ".format(
                    original_class._subspecifier_field_name,
                    original_pk)
            else:
                subspecifier_string = ""
            if original_class is None:
                sourcestr = "the data passed"
            else:
                sourcestr = original_class.__name__

            msg = ("Wrong dict length stored in {} for "
                   "{}key='{}' ({} vs {})".format(
                sourcestr,
                subspecifier_string,
                mainitem['key'], len(firstlevelsubdict),
                mainitem['ival']))
            if lesserrors:
                AIIDA_LOGGER.error(msg)
            else:
                raise DeserializationException(msg)

        # I get the values in memory as a dictionary
        tempdict = {}
        for firstsubk, firstsubv in firstlevelsubdict.items():
            # I call recursively the same function to get subitems
            newsubitems = {k[len(firstsubk) + len(sep):]: v
                           for k, v in subitems.items()
                           if k.startswith(firstsubk + sep)}
            tempdict[firstsubk] = _deserialize_attribute(mainitem=firstsubv,
                                                         subitems=newsubitems, sep=sep, original_class=original_class,
                                                         original_pk=original_pk)

        return tempdict
    elif mainitem['datatype'] == 'json':
        try:
            return json.loads(mainitem['tval'])
        except ValueError:
            raise DeserializationException("Error in the content of the json field")
    else:
        raise DeserializationException("The type field '{}' is not recognized".format(
            mainitem['datatype']))


def deserialize_attributes(data, sep, original_class=None, original_pk=None):
    """
    Deserialize the attributes from the format internally stored in the DB
    to the actual format (dictionaries, lists, integers, ...

    :param data: must be a dictionary of dictionaries. In the top-level dictionary,
      the key must be the key of the attribute. The value must be a dictionary
      with the following keys: datatype, tval, fval, ival, bval, dval. Other
      keys are ignored.
      NOTE that a type check is not performed! tval is expected to be a string,
      dval a date, etc.
    :param sep: a string, the separator between subfields (to separate the
      name of a dictionary from the keys it contains, for instance)
    :param original_class: if these elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass, pass here the class (note: the class,
      not the instance!). This is used only in case the wrong number of elements
      is found in the raw data, to print a more meaningful message (if the class
      has a dbnode associated to it)
    :param original_pk: if the elements come from a specific subclass
      of DbMultipleValueAttributeBaseClass that has a dbnode associated to it,
      pass here the PK integer. This is used only in case the wrong number
      of elements is found in the raw data, to print a more meaningful message

    :return: a dictionary, where for each entry the corresponding value is
      returned, deserialized back to lists, dictionaries, etc.
      Example: if ``data = {'a': {'datatype': "list", "ival": 2, ...},
      'a.0': {'datatype': "int", "ival": 2, ...},
      'a.1': {'datatype': "txt", "tval":  "yy"}]``,
      it will return ``{"a": [2, "yy"]}``
    """
    from collections import defaultdict

    # I group results by zero-level entity
    found_mainitems = {}
    found_subitems = defaultdict(dict)
    for mainkey, descriptiondict in data.items():
        prefix, thissep, postfix = mainkey.partition(sep)
        if thissep:
            found_subitems[prefix][postfix] = {k: v for k, v
                                               in descriptiondict.items() if k != "key"}
        else:
            mainitem = descriptiondict.copy()
            mainitem['key'] = prefix
            found_mainitems[prefix] = mainitem

    # There can be mainitems without subitems, but there should not be subitems
    # without mainitmes.
    lone_subitems = set(found_subitems.keys()) - set(found_mainitems.keys())
    if lone_subitems:
        raise DeserializationException("Missing base keys for the following "
                                       "items: {}".format(",".join(lone_subitems)))

    # For each zero-level entity, I call the _deserialize_attribute function
    retval = {}
    for k, v in found_mainitems.items():
        # Note: found_subitems[k] will return an empty dictionary it the
        # key does not exist, as it is a defaultdict
        retval[k] = _deserialize_attribute(mainitem=v,
                                           subitems=found_subitems[k], sep=sep, original_class=original_class,
                                           original_pk=original_pk)

    return retval


class DbMultipleValueAttributeBaseClass(m.Model):
    """
    Abstract base class for tables storing attribute + value data, of
    different data types (without any association to a Node).
    """
    key = m.CharField(max_length=1024, db_index=True, blank=False)
    datatype = m.CharField(max_length=10,
                           default='none',
                           choices=attrdatatype_choice, db_index=True)
    tval = m.TextField(default='', blank=True)
    fval = m.FloatField(default=None, null=True)
    ival = m.IntegerField(default=None, null=True)
    bval = m.NullBooleanField(default=None, null=True)
    dval = m.DateTimeField(default=None, null=True)

    # separator for subfields
    _sep = AIIDA_ATTRIBUTE_SEP

    class Meta:
        abstract = True
        unique_together = (('key',),)

    # There are no subspecifiers. If instead you want to group attributes
    # (e.g. by node, as it is done in the DbAttributeBaseClass), specify here
    # the field name
    _subspecifier_field_name = None

    @property
    def subspecifiers_dict(self):
        """
        Return a dict to narrow down the query to only those matching also the
        subspecifier.
        """
        if self._subspecifier_field_name is None:
            return {}
        else:
            return {self._subspecifier_field_name:
                        getattr(self, self._subspecifier_field_name)}

    @property
    def subspecifier_pk(self):
        """
        Return the subspecifier PK in the database (or None, if no
        subspecifier should be used)
        """
        if self._subspecifier_field_name is None:
            return None
        else:
            return getattr(self, self._subspecifier_field_name).pk

    @classmethod
    def validate_key(cls, key):
        """
        Validate the key string to check if it is valid (e.g., if it does not
        contain the separator symbol.).

        :return: None if the key is valid
        :raise aiida.common.ValidationError: if the key is not valid
        """
        from aiida.backends.utils import validate_attribute_key
        return validate_attribute_key(key)

    @classmethod
    def set_value(cls, key, value, with_transaction=True,
                  subspecifier_value=None, other_attribs={},
                  stop_if_existing=False):
        """
        Set a new value in the DB, possibly associated to the given subspecifier.

        :note: This method also stored directly in the DB.

        :param key: a string with the key to create (must be a level-0
          attribute, that is it cannot contain the separator cls._sep).
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param with_transaction: True if you want this function to be managed
          with transactions. Set to False if you already have a manual
          management of transactions in the block where you are calling this
          function (useful for speed improvements to avoid recursive
          transactions)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).
        :param stop_if_existing: if True, it will stop with an
           UniquenessError exception if the new entry would violate an
           uniqueness constraint in the DB (same key, or same key+node,
           depending on the specific subclass). Otherwise, it will
           first delete the old value, if existent. The use with True is
           useful if you want to use a given attribute as a "locking" value,
           e.g. to avoid to perform an action twice on the same node.
           Note that, if you are using transactions, you may get the error
           only when the transaction is committed.
        """
        from django.db import transaction

        cls.validate_key(key)

        try:
            if with_transaction:
                sid = transaction.savepoint()

            # create_value returns a list of nodes to store
            to_store = cls.create_value(key, value,
                                        subspecifier_value=subspecifier_value,
                                        other_attribs=other_attribs)

            if to_store:
                if not stop_if_existing:
                    # Delete the olf values if stop_if_existing is False,
                    # otherwise don't delete them and hope they don't
                    # exist. If they exist, I'll get an UniquenessError

                    ## NOTE! Be careful in case the extra/attribute to
                    ## store is not a simple attribute but a list or dict:
                    ## like this, it should be ok because if we are
                    ## overwriting an entry it will stop anyway to avoid
                    ## to overwrite the main entry, but otherwise
                    ## there is the risk that trailing pieces remain
                    ## so in general it is good to recursively clean
                    ## all sub-items.
                    cls.del_value(key,
                                  subspecifier_value=subspecifier_value)
                cls.objects.bulk_create(to_store)

            if with_transaction:
                transaction.savepoint_commit(sid)
        except BaseException as exc:  # All exceptions including CTRL+C, ...
            from django.db.utils import IntegrityError
            from aiida.common.exceptions import UniquenessError

            if with_transaction:
                transaction.savepoint_rollback(sid)
            if isinstance(exc, IntegrityError) and stop_if_existing:
                raise UniquenessError("Impossible to create the required "
                                      "entry "
                                      "in table '{}', "
                                      "another entry already exists and the creation would "
                                      "violate an uniqueness constraint.\nFurther details: "
                                      "{}".format(cls.__name__, exc))
            raise

    @classmethod
    def create_value(cls, key, value, subspecifier_value=None,
                     other_attribs={}):
        """
        Create a new list of attributes, without storing them, associated
        with the current key/value pair (and to the given subspecifier,
        e.g. the DbNode for DbAttributes and DbExtras).

        :note: No hits are done on the DB, in particular no check is done
          on the existence of the given nodes.

        :param key: a string with the key to create (can contain the
          separator cls._sep if this is a sub-attribute: indeed, this
          function calls itself recursively)
        :param value: the value to store (a basic data type or a list or a dict)
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        :param other_attribs: a dictionary of other parameters, to store
          only on the level-zero attribute (e.g. for description in DbSetting).

        :return: always a list of class instances; it is the user
          responsibility to store such entries (typically with a Django
          bulk_create() call).
        """
        import datetime

        from aiida.common import json
        from aiida.common.timezone import is_naive, make_aware, get_current_timezone

        if cls._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            new_entry = cls(key=key, **other_attribs)
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(cls.__name__,
                                                                cls._subspecifier_field_name))
            further_params = other_attribs.copy()
            further_params.update({cls._subspecifier_field_name:
                                       subspecifier_value})
            new_entry = cls(key=key, **further_params)

        list_to_return = [new_entry]

        if value is None:
            new_entry.datatype = 'none'
            new_entry.bval = None
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, bool):
            new_entry.datatype = 'bool'
            new_entry.bval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, six.integer_types):
            new_entry.datatype = 'int'
            new_entry.ival = value
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, float):
            new_entry.datatype = 'float'
            new_entry.fval = value
            new_entry.tval = ''
            new_entry.ival = None
            new_entry.bval = None
            new_entry.dval = None

        elif isinstance(value, six.string_types):
            new_entry.datatype = 'txt'
            new_entry.tval = value
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None
            new_entry.dval = None

        elif isinstance(value, datetime.datetime):

            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value, get_current_timezone())
            else:
                value_to_set = value

            new_entry.datatype = 'date'
            # TODO: time-aware and time-naive datetime objects, see
            # https://docs.djangoproject.com/en/dev/topics/i18n/timezones/#naive-and-aware-datetime-objects
            new_entry.dval = value_to_set
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        elif isinstance(value, (list, tuple)):

            new_entry.datatype = 'list'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for i, subv in enumerate(value):
                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(cls.create_value(
                    key=("{}{}{:d}".format(key, cls._sep, i)),
                    value=subv,
                    subspecifier_value=subspecifier_value))

        elif isinstance(value, dict):

            new_entry.datatype = 'dict'
            new_entry.dval = None
            new_entry.tval = ''
            new_entry.bval = None
            new_entry.ival = len(value)
            new_entry.fval = None

            for subk, subv in value.items():
                cls.validate_key(subk)

                # I do not need get_or_create here, because
                # above I deleted all children (and I
                # expect no concurrency)
                # NOTE: I do not pass other_attribs
                list_to_return.extend(cls.create_value(
                    key="{}{}{}".format(key, cls._sep, subk),
                    value=subv,
                    subspecifier_value=subspecifier_value))
        else:
            try:
                jsondata = json.dumps(value)
            except TypeError:
                raise ValueError("Unable to store the value: it must be either a basic datatype, or json-serializable: {}".format(value))

            new_entry.datatype = 'json'
            new_entry.tval = jsondata
            new_entry.bval = None
            new_entry.ival = None
            new_entry.fval = None

        return list_to_return

    @classmethod
    def get_query_dict(cls, value):
        """
        Return a dictionary that can be used in a django filter to query
        for a specific value. This takes care of checking the type of the
        input parameter 'value' and to convert it to the right query.

        :param value: The value that should be queried. Note: can only be
           base datatype, not a list or dict. For those, query directly for
           one of the sub-elements.

        :todo: see if we want to give the possibility to query for the existence
           of a (possibly empty) dictionary or list, of for their length.

        :note: this will of course not find a data if this was stored in the
           DB as a serialized JSON.

        :return: a dictionary to be used in the django .filter() method.
            For instance, if 'value' is a string, it will return the dictionary
            ``{'datatype': 'txt', 'tval': value}``.

        :raise: ValueError if value is not of a base datatype (string, integer,
            float, bool, None, or date)
        """
        import datetime
        from aiida.common.timezone import (
            is_naive, make_aware, get_current_timezone)

        if value is None:
            return {'datatype': 'none'}
        elif isinstance(value, bool):
            return {'datatype': 'bool', 'bval': value}
        elif isinstance(value, six.integer_types):
            return {'datatype': 'int', 'ival': value}
        elif isinstance(value, float):
            return {'datatype': 'float', 'fval': value}
        elif isinstance(value, six.string_types):
            return {'datatype': 'txt', 'tval': value}
        elif isinstance(value, datetime.datetime):
            # current timezone is taken from the settings file of django
            if is_naive(value):
                value_to_set = make_aware(value, get_current_timezone())
            else:
                value_to_set = value
            return {'datatype': 'date', 'dval': value_to_set}
        elif isinstance(value, list):
            raise ValueError("Lists are not supported for getting the "
                             "query_dict")
        elif isinstance(value, dict):
            raise ValueError("Dicts are not supported for getting the "
                             "query_dict")
        else:
            raise ValueError("Unsupported type for getting the "
                             "query_dict, it is {}".format(str(type(value))))

    def getvalue(self):
        """
        This can be called on a given row and will get the corresponding value,
        casting it correctly.
        """
        try:
            if self.datatype == 'list' or self.datatype == 'dict':
                prefix = "{}{}".format(self.key, self._sep)
                prefix_len = len(prefix)
                dballsubvalues = self.__class__.objects.filter(
                    key__startswith=prefix,
                    **self.subspecifiers_dict).values_list('key',
                                                           'datatype', 'tval', 'fval',
                                                           'ival', 'bval', 'dval')
                # Strip the FULL prefix and replace it with the simple
                # "attr" prefix
                data = {"attr.{}".format(_[0][prefix_len:]): {
                    "datatype": _[1],
                    "tval": _[2],
                    "fval": _[3],
                    "ival": _[4],
                    "bval": _[5],
                    "dval": _[6],
                } for _ in dballsubvalues
                }
                # for _ in dballsubvalues}
                # Append also the item itself
                data["attr"] = {
                    # Replace the key (which may contain the separator) with the
                    # simple "attr" key. In any case I do not need to return it!
                    "key": "attr",
                    "datatype": self.datatype,
                    "tval": self.tval,
                    "fval": self.fval,
                    "ival": self.ival,
                    "bval": self.bval,
                    "dval": self.dval}
                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self.__class__,
                                              original_pk=self.subspecifier_pk)['attr']
            else:
                data = {"attr": {
                    # Replace the key (which may contain the separator) with the
                    # simple "attr" key. In any case I do not need to return it!
                    "key": "attr",
                    "datatype": self.datatype,
                    "tval": self.tval,
                    "fval": self.fval,
                    "ival": self.ival,
                    "bval": self.bval,
                    "dval": self.dval}}

                return deserialize_attributes(data, sep=self._sep,
                                              original_class=self.__class__,
                                              original_pk=self.subspecifier_pk)['attr']
        except DeserializationException as exc:
            exc = DbContentError(exc)
            exc.original_exception = exc
            raise exc

    @classmethod
    def del_value(cls, key, only_children=False, subspecifier_value=None):
        """
        Delete a value associated with the given key (if existing).

        :note: No exceptions are raised if no entry is found.

        :param key: the key to delete. Can contain the separator cls._sep if
          you want to delete a subkey.
        :param only_children: if True, delete only children and not the
          entry itself.
        :param subspecifier_value: must be None if this class has no
          subspecifier set (e.g., the DbSetting class).
          Must be the value of the subspecifier (e.g., the dbnode) for classes
          that define it (e.g. DbAttribute and DbExtra)
        """
        from django.db.models import Q

        if cls._subspecifier_field_name is None:
            if subspecifier_value is not None:
                raise ValueError("You cannot specify a subspecifier value for "
                                 "class {} because it has no subspecifiers"
                                 "".format(cls.__name__))
            subspecifiers_dict = {}
        else:
            if subspecifier_value is None:
                raise ValueError("You also have to specify a subspecifier value "
                                 "for class {} (the {})".format(cls.__name__,
                                                                cls._subspecifier_field_name))
            subspecifiers_dict = {cls._subspecifier_field_name:
                                      subspecifier_value}

        query = Q(key__startswith="{parentkey}{sep}".format(
            parentkey=key, sep=cls._sep),
            **subspecifiers_dict)

        if not only_children:
            query.add(Q(key=key, **subspecifiers_dict), Q.OR)

        cls.objects.filter(query).delete()


@python_2_unicode_compatible
class DbSetting(DbMultipleValueAttributeBaseClass):
    """
    This will store generic settings that should be database-wide.
    """
    # I also add a description field for the variables
    description = m.TextField(blank=True)
    # Modification time of this attribute
    time = m.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "'{}'={}".format(self.key, self.getvalue())


@python_2_unicode_compatible
class DbGroup(m.Model):
    """
    A group of nodes.

    Any group of nodes can be created, but some groups may have specific meaning
    if they satisfy specific rules (for instance, groups of UpdData objects are
    pseudopotential families - if no two pseudos are included for the same
    atomic element).
    """
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    # max_length is required by MySql to have indexes and unique constraints
    label = m.CharField(max_length=255, db_index=True)
    # The type_string of group: a user group, a pseudopotential group,...
    # User groups have type_string equal to an empty string
    type_string = m.CharField(default="", max_length=255, db_index=True)
    dbnodes = m.ManyToManyField('DbNode', related_name='dbgroups')
    # Creation time
    time = m.DateTimeField(default=timezone.now, editable=False)
    description = m.TextField(blank=True)
    # The owner of the group, not of the calculations
    # On user deletion, remove his/her groups too (not the calcuations, only
    # the groups
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.CASCADE,
                        related_name='dbgroups')

    class Meta:
        unique_together = (("label", "type_string"),)

    def __str__(self):
        return '<DbGroup [type_string: {}] "{}">'.format(self.type_string, self.label)


@python_2_unicode_compatible
class DbComputer(m.Model):
    """
    Table of computers or clusters.

    Attributes:
    * name: A name to be used to refer to this computer. Must be unique.
    * hostname: Fully-qualified hostname of the host
    * transport_type: a string with a valid transport type


    Note: other things that may be set in the metadata:

        * mpirun command

        * num cores per node

        * max num cores

        * workdir: Full path of the aiida folder on the host. It can contain\
            the string {username} that will be substituted by the username\
            of the user on that machine.\
            The actual workdir is then obtained as\
            workdir.format(username=THE_ACTUAL_USERNAME)\
            Example: \
            workdir = "/scratch/{username}/aiida/"


        * allocate full node = True or False

        * ... (further limits per user etc.)

    """
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    name = m.CharField(max_length=255, unique=True, blank=False)
    hostname = m.CharField(max_length=255)
    description = m.TextField(blank=True)
    # TODO: next three fields should not be blank...
    transport_type = m.CharField(max_length=255)
    scheduler_type = m.CharField(max_length=255)
    transport_params = JSONField(default=dict)
    metadata = JSONField(default=dict)

    def __str__(self):
        return '{} ({})'.format(self.name, self.hostname)


@python_2_unicode_compatible
class DbAuthInfo(m.Model):
    """
    Table that pairs aiida users and computers, with all required authentication
    information.
    """
    # Delete the DbAuthInfo if either the user or the computer are removed
    aiidauser = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.CASCADE)
    dbcomputer = m.ForeignKey(DbComputer, on_delete=m.CASCADE)
    auth_params = JSONField(default=dict)  # contains mainly the remoteuser and the private_key

    # The keys defined in the metadata of the DbAuthInfo will override the
    # keys with the same name defined in the DbComputer (using a dict.update()
    # call of python).
    metadata = JSONField(default=dict)
    # Whether this computer is enabled (user-level enabling feature)
    enabled = m.BooleanField(default=True)

    class Meta:
        unique_together = (("aiidauser", "dbcomputer"),)

    def __str__(self):
        if self.enabled:
            return "DB authorization info for {} on {}".format(self.aiidauser.email, self.dbcomputer.name)
        else:
            return "DB authorization info for {} on {} [DISABLED]".format(self.aiidauser.email, self.dbcomputer.name)


@python_2_unicode_compatible
class DbComment(m.Model):
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    # Delete comments if the node is removed
    dbnode = m.ForeignKey(DbNode, related_name='dbcomments', on_delete=m.CASCADE)
    ctime = m.DateTimeField(default=timezone.now, editable=False)
    mtime = m.DateTimeField(auto_now=True, editable=False)
    # Delete the comments of a deleted user (TODO: check if this is a good policy)
    user = m.ForeignKey(AUTH_USER_MODEL, on_delete=m.CASCADE)
    content = m.TextField(blank=True)

    def __str__(self):
        return "DbComment for [{} {}] on {}".format(self.dbnode.get_simple_name(),
                                                    self.dbnode.pk, timezone.localtime(self.ctime).strftime("%Y-%m-%d"))


@python_2_unicode_compatible
class DbLog(m.Model):
    uuid = m.UUIDField(default=get_new_uuid, unique=True)
    time = m.DateTimeField(default=timezone.now, editable=False)
    loggername = m.CharField(max_length=255, db_index=True)
    levelname = m.CharField(max_length=50, db_index=True)
    dbnode = m.ForeignKey(DbNode, related_name='dblogs', on_delete=m.CASCADE)
    message = m.TextField(blank=True)
    metadata = JSONField(default=dict)

    def __str__(self):
        return 'DbLog: {} for node {}: {}'.format(self.levelname, self.dbnode.id, self.message)


@contextlib.contextmanager
def suppress_auto_now(list_of_models_fields):
    """
    This context manager disables the auto_now & editable flags for the
    fields of the given models.
    This is useful when we would like to update the datetime fields of an
    entry bypassing the automatic set of the date (with the current time).
    This is very useful when entries are imported and we would like to keep e.g.
    the modification time that we set during the import and not allow Django
    to set it to the datetime that corresponds to when the entry was saved.
    In the end the flags are returned to their original value.
    :param list_of_models_fields: A list of (model, fields) tuples for
    which the flags will be updated. The model is an object that corresponds
    to the model objects and fields is a list of strings with the field names.
    """
    # Here we store the original values of the fields of the models that will
    # be updated
    # E.g.
    # _original_model_values = {
    #   ModelA: [fieldA: {
    #                       'auto_now': orig_valA1
    #                       'editable': orig_valA2
    #            },
    #            fieldB: {
    #                       'auto_now': orig_valB1
    #                       'editable': orig_valB2
    #            }
    #    ]
    #   ...
    # }
    _original_model_values = dict()
    for model, fields in list_of_models_fields:
        _original_field_values = dict()
        for field in model._meta.local_fields:
            if field.name in fields:
                _original_field_values[field] = {
                    'auto_now': field.auto_now,
                    'editable': field.editable,
                }
                field.auto_now = False
                field.editable = True
        _original_model_values[model] = _original_field_values
    try:
        yield
    finally:
        for model in _original_model_values:
            for field in _original_model_values[model]:
                field.auto_now = _original_model_values[model][field]['auto_now']
                field.editable = _original_model_values[model][field]['editable']
