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

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
import django.contrib.postgres.fields.jsonb
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.34'
DOWN_REVISION = '1.0.33'


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
        # Create the DBNode.Attribute JSONB field
        migrations.AddField(
            model_name='dbnode',
            name='attributes',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, null=True),
        ),
        # ##############################################################
        # Migrate the data from the DbAttribute table to the JSONB field
        # ##############################################################
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
        # ###########################################################
        # Migrate the data from the DbAExtra table to the JSONB field
        # ###########################################################
        # Create the DBNode.Extra JSONB field
        migrations.AddField(
            model_name='dbnode',
            name='extras',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=None, null=True)),
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
        migrations.DeleteModel(name='DbExtra',),
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
