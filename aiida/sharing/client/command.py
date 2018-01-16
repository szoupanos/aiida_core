# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.common.exceptions import InvalidOperation
from aiida.sharing.command import Command
import os

class SendFileCommand(Command):

    cmd_name = 'SEND_FILE'

    filename = None
    connection = None

    def __init__(self, connection):
        super(SendFileCommand, self).__init__()
        self.connection = connection

    def execute(self, filename):
        import time
        import sys

        if self.connection is None:
            self.logger.debug(
                "The connection is not initialized, exiting")
            raise InvalidOperation("The connection is not initialized")

        # Inform the receiver about the command to be executed
        self.logger.debug("Informing the receiver about the command to be "
                          "executed: " + self.cmd_name)
        self.connection.send(
            self.cmd_name, size_of_chunck = len(self.cmd_name))

        # Sending the file size
        filesize = os.path.getsize(filename)
        self.logger.debug("Sending the file size: " + str(filesize))
        self.connection.send(
            str(filesize), size_of_chunck=len(str(filesize)))

        # Proceeding to the file sent
        self.logger.debug("Proceeding to the file sent")
        t = time.time()
        bytes = 0
        try:
            f = open(filename, "rb")

            while True:
                chunk = f.read(1024)
                if not chunk:
                    break

                bytes += sys.getsizeof(chunk)
                self.logger.debug("Sending: " + chunk)
                byte_no = self.connection.send(chunk)
                self.logger.debug("Sent " + str(byte_no) + " bytes.")
        finally:
            self.logger.debug("Sending finished, closing file")
            f.close()

class PushCommand(Command):

    cmd_name = 'PUSH'

    filename = None
    connection = None

    def __init__(self, connection):
        super(PushCommand, self).__init__()
        self.connection = connection

    def execute(self, local_group):
        import time
        import sys

        filename = "/home/aiida/sharing_send.out"

        if self.connection is None:
            self.logger.debug(
                "The connection is not initialized, exiting")
            raise InvalidOperation("The connection is not initialized")

        # Inform the receiver about the command to be executed
        self.logger.debug("Informing the receiver about the command to be "
                          "executed: " + self.cmd_name)
        self.connection.send(
            self.cmd_name, size_of_chunck = len(self.cmd_name))

        # Exporting the needed group
        from aiida import load_dbenv, is_dbenv_loaded
        from aiida.backends import settings
        if not is_dbenv_loaded():
            load_dbenv(profile=settings.AIIDADB_PROFILE)

        from aiida.orm import Group, Node
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.sharing.importexport import export
        # create(outfile=filename, group_names=local_group)

        node_id_set = set()
        group_dict = dict()

        qb = QueryBuilder()
        qb.append(Group, tag='group', project=['*'],
                  filters={'name': {'in': [local_group]}})
        qb.append(Node, tag='node', member_of='group', project=['id'])
        res = qb.dict()

        group_dict.update(
            {group['group']['*'].name: group['group']['*'].dbgroup for
             group in res})
        node_id_set.update([node['node']['id'] for node in res])

        # The db_groups that correspond to what was searched above
        dbgroups_list = group_dict.values()

        # Getting the nodes that correspond to the ids that were found above
        if len(node_id_set) > 0:
            qb = QueryBuilder()
            qb.append(Node, tag='node', project=['*'],
                      filters={'id': {'in': node_id_set}})
            node_list = [node[0] for node in qb.all()]
        else:
            node_list = list()

        # The dbnodes of the above node list
        dbnode_list = [node.dbnode for node in node_list]

        what_list = dbnode_list + dbgroups_list

        export(what=what_list,outfile=filename, overwrite=True)

        # Sending the file size
        filesize = os.path.getsize(filename)
        self.logger.debug("Sending the file size: " + str(filesize))
        self.connection.send(
            str(filesize), size_of_chunck=len(str(filesize)))

        # Proceeding to the file sent
        self.logger.debug("Proceeding to the file sent")
        t = time.time()
        bytes = 0
        try:
            f = open(filename, "rb")

            while True:
                chunk = f.read(1024)
                if not chunk:
                    break

                bytes += sys.getsizeof(chunk)
                self.logger.debug("Sending: " + chunk)
                byte_no = self.connection.send(chunk)
                self.logger.debug("Sent " + str(byte_no) + " bytes.")
        finally:
            self.logger.debug("Sending finished, closing file")
            f.close()
