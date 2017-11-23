# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.node import Node
from uuid import UUID

# Repeat the following experiment for various UUID sizes
for lim in [100, 10000, 1000000]:
    print "Round with limit ", lim
    # Get some UUIDs -  This represents the set  of nodes that we
    # plan to send to the receiver
    qb = QueryBuilder(limit=100)
    qb.append(Node, project=['uuid'])
    print "Got", qb.count(), "results \n"
    res = [_[0] for _ in qb.all()]

    # Store the UUIds in a file (emulate that they were send over the network
    print "Storing UUIDs to the file"
    with open('tmp_uuid_file.txt', 'wb') as output_file:
        for r in res:
            output_file.write(str(r)+"\n")
    print "Finished writing to file"

    # Retrieve the UUIDs from the file
    print "Reading UUIDs from file"
    obtained_uuids = list()
    with open('tmp_uuid_file.txt', 'rb') as input_file:
        for line in input_file:
            # obtained_uuids.append(UUID(line[:-1]))
            obtained_uuids.append(line[:-1])

    # Check which the UUIDs exist in the database and get the ones that
    qb = QueryBuilder(limit=100)
    qb.append(Node, filters={'uuid': {'in': obtained_uuids}}, project=['uuid'])
    existing_uuids = [str(_[0]) for _ in qb.all()]

    print "Found ", len(existing_uuids), " of the given UUIDs in the database"

    # print "obtained_uuids " + str(obtained_uuids)
    # print "existing_uuids " + str(existing_uuids)

    intersect  = list(set(obtained_uuids) - set(existing_uuids))
    print "Not found UUIDs " + str(intersect)


