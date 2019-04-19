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


from django.apps import apps
from django.db.migrations.executor import MigrationExecutor
from django.db import connection

from aiida.backends.testbase import AiidaTestCase


class TestMigrations(AiidaTestCase):
    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name.split('.')[-1]

    migrate_from = None
    migrate_to = None

    def setUp(self):
        """Go to a specific schema version before running tests."""
        from aiida.backends import sqlalchemy as sa
        from aiida.orm import autogroup

        self.current_autogroup = autogroup.current_autogroup
        autogroup.current_autogroup = None
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        self.apps = executor.loader.project_state(self.migrate_from).apps

        # Reset session for the migration
        sa.get_scoped_session().close()
        # Reverse to the original migration
        executor.migrate(self.migrate_from)
        # Reset session after the migration
        sa.get_scoped_session().close()

        self.default_user = self.backend.users.create('{}@aiida.net'.format(self.id())).store()
        self.DbNode = self.apps.get_model('db', 'DbNode')

        try:
            self.setUpBeforeMigration()
            # Run the migration to test
            executor = MigrationExecutor(connection)
            executor.loader.build_graph()

            # Reset session for the migration
            sa.get_scoped_session().close()
            executor.migrate(self.migrate_to)
            # Reset session after the migration
            sa.get_scoped_session().close()

            self.apps = executor.loader.project_state(self.migrate_to).apps
        except Exception as exception:
            # Bring back the DB to the correct state if this setup part fails
            import traceback
            traceback.print_stack()
            print('EXCEPTION', exception)
            self._revert_database_schema()
            raise

    def tearDown(self):
        """At the end make sure we go back to the latest schema version."""
        from aiida.orm import autogroup
        self._revert_database_schema()
        autogroup.current_autogroup = self.current_autogroup

    def setUpBeforeMigration(self):
        """Anything to do before running the migrations, which should be implemented in test subclasses."""

    def _revert_database_schema(self):
        """Bring back the DB to the correct state."""
        from ...migrations import LATEST_MIGRATION
        from aiida.backends import sqlalchemy as sa

        self.migrate_to = [(self.app, LATEST_MIGRATION)]

        # Reset session for the migration
        sa.get_scoped_session().close()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        # Reset session after the migration
        sa.get_scoped_session().close()

    def load_node(self, pk):
        return self.DbNode.objects.get(pk=pk)
