# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Adding JSONB field for Node.attributes and Node.Extras"""
from __future__ import absolute_import

import gc
import math

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import transaction
import django.contrib.postgres.fields.jsonb
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.34'
DOWN_REVISION = '1.0.33'


def lazy_bulk_fetch(max_obj, max_count, fetch_func, start=0):
    counter = start
    while counter < max_count:
        yield fetch_func()[counter:counter + max_obj]
        counter += max_obj


# def transition_attributes(profile=None, group_size=1000, debug=False, delete_table=False):
def transition_attributes(apps, _):
    """
    Migrate the DbAttribute table into the attributes column of db_dbnode.
    """
    print("\nStarting migration of attributes")
    # node_table_cols = inspector.get_columns(NODE_TABLE_NAME)

    DbNode = apps.get_model('db', 'DbNode')
    DbAttributes = apps.get_model('db', 'DbAttribute')

    group_size = 1000

    # session = sa.get_scoped_session()

    # with session.begin(subtransactions=True):
    with transaction.atomic():

        # from aiida.backends.sqlalchemy.models.node import DbNode
        # total_nodes = session.query(func.count(DbNode.id)).scalar()
        total_nodes = DbNode.objects.count()

        fetcher = lazy_bulk_fetch(50, DbNode.objects.count(), DbNode.objects.all)
        error = False

        for batch in fetcher:
            # Get the ids of the nodes
            print(batch)
            updated_nodes = list()
            for curr_dbnode in batch:
                print("node ==========>" + str(curr_dbnode))
                print("dbattr ==========>" + str(curr_dbnode.dbattributes.all()))
                print("attr ==========>" + str(curr_dbnode.attributes))

                # Migrating attributes
                dbattrs = list(curr_dbnode.dbattributes.all())
                attrs, err_ = attributes_to_dict(sorted(dbattrs, key=lambda a: a.key))
                error |= err_
                curr_dbnode.attributes = attrs

                # Migrating extras
                dbextr = list(curr_dbnode.dbextras.all())
                extr, err_ = attributes_to_dict(sorted(dbextr, key=lambda a: a.key))
                error |= err_
                curr_dbnode.extras = extr

                # Saving the result
                curr_dbnode.save()

                print("WWWWWWW 1 ===>", str(curr_dbnode.attributes))
                print("WWWWWWW 2 ===>", str(curr_dbnode.extras))

            # DbNode.objects.bulk_create()


        # total_groups = int(math.ceil(total_nodes / group_size))
        # error = False
        #
        # for i in range(total_groups):
        #     print("Migrating group {} of {}".format(i, total_groups))
        #
        #     node_ids = DbNode.objects.all()
        #
        #     nodes = DbNode.query.options(
        #         subqueryload('old_attrs'), load_only('id', 'attributes')
        #     ).order_by(DbNode.id)[i * group_size:(i + 1) * group_size]
        #
        #     for node in nodes:
        #         attrs, err_ = attributes_to_dict(sorted(node.old_attrs,
        #                                                 key=lambda a: a.key))
        #         error |= err_
        #
        #         node.attributes = attrs
        #         session.add(node)
        #
        #     # Remove the db_dbnode from sqlalchemy, to allow the GC to do its
        #     # job.
        #     session.flush()
        #     session.expunge_all()
        #
        #     del nodes
        #     gc.collect()
    print("Migration of attributes finished.")


def attributes_to_dict(attr_list):
    """
    Transform the attributes of a node into a dictionary. It assumes the key
    are ordered alphabetically, and that they all belong to the same node.
    """
    d = {}

    error = False
    for a in attr_list:
        try:
            tmp_d = select_from_key(a.key, d)
        except Exception:
            print("Couldn't transfer attribute {} with key {} for dbnode {}"
                  .format(a.id, a.key, a.dbnode_id))
            error = True
            continue
        key = a.key.split('.')[-1]

        if key.isdigit():
            key = int(key)

        dt = a.datatype

        if dt == "dict":
            tmp_d[key] = {}
        elif dt == "list":
            tmp_d[key] = [None] * a.ival
        else:
            val = None
            if dt == "txt":
                val = a.tval
            elif dt == "float":
                val = a.fval
                if math.isnan(val):
                    val = 'NaN'
            elif dt == "int":
                val = a.ival
            elif dt == "bool":
                val = a.bval
            elif dt == "date":
                val = a.dval

            tmp_d[key] = val

    return (d, error)


def select_from_key(key, d):
    """
    Return element of the dict to do the insertion on. If it is foo.1.bar, it
    will return d["foo"][1]. If it is only foo, it will return d directly.
    """
    path = key.split('.')[:-1]

    tmp_d = d
    for p in path:
        if p.isdigit():
            tmp_d = tmp_d[int(p)]
        else:
            tmp_d = tmp_d[p]

    return tmp_d

class Migration(migrations.Migration):
    """
    This migration changes Django backend to support the JSONB fields.
    It is a schema migration that removes the DbAttribute and DbExtra
    tables and their reference to the DbNode tables and adds the
    corresponding JSONB columns to the DbNode table.
    It is also a data migration that transforms and adds the data of
    the DbAttribute and DbExtra tables to the JSONB columns to the
    DbNode table.
    """

    dependencies = [
        ('db', '0033_replace_text_field_with_json_field'),
    ]

    operations = [
        # Create the DBNode.Attribute JSONB and DBNode.Extra JSONB fields
        migrations.AddField(
            model_name='dbnode',
            name='attributes',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='dbnode',
            name='extras',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, null=True),
        ),
        # ##############################################################
        # Migrate the data from the DbAttribute table to the JSONB field
        # ##############################################################
        migrations.RunPython(transition_attributes, reverse_code=migrations.RunPython.noop),

        # Delete the binding of Node-Attribute
        migrations.AlterUniqueTogether(
            name='dbattribute',
            unique_together=set([]),
        ),
        # Delete the foreign key to the node
        migrations.RemoveField(
            model_name='dbattribute',
            name='dbnode',
        ),
        # Delete the DbAttribute table
        migrations.DeleteModel(name='DbAttribute',),

        # Delete the binding of Node-Extra
        migrations.AlterUniqueTogether(
            name='dbextra',
            unique_together=set([]),
        ),
        # Delete the foreign key to the node
        migrations.RemoveField(
            model_name='dbextra',
            name='dbnode',
        ),
        # Delete the DbExtra table
        migrations.DeleteModel(name='DbExtra', ),

        upgrade_schema_version(REVISION, DOWN_REVISION),

        # The following is not needed because it was done by Sebastiaan too in migration 0033
        # I don't see any data migration for 00033. Is it done automatically?

        # # Change to DbComputer.transport_params and DbComputer.metadata to JSONB
        # migrations.AlterField(
        #     model_name='dbcomputer',
        #     name='transport_params',
        #     field=django.contrib.postgres.fields.jsonb.JSONField(default={}, null=True)),
        # migrations.AlterField(
        #     model_name='dbcomputer',
        #     name='metadata',
        #     field=django.contrib.postgres.fields.jsonb.JSONField(default={}, null=True)),
    ]
