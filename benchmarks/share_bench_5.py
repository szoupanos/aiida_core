# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.node import Node
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import os

# This is a third approach for calculating the UUIDs of the nodes to be
# sent to the receiver side.
#
# Let TS be the set of UUIDs sent by the sender and DB the set of UUIDs that
# are at the receiver side.
#
# In this approach we get from SQLA the DB set and we calculate the C at the
# Python level, where C = TS - DB

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    print("Start Query")


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    print("Query Completed!")
    print("==> Query Time (secs): {}".format(total))


# Repeat the following experiment for various UUID sizes
for lim in [100, 1000, 10000, 100000, 1000000, None]:
# for lim in [100, 1000, 10000]:
# for lim in [None, 1000000, 100000, 10000, 1000, 100]:
    print "<================== Round with limit", lim, "==================>"
    # Get some UUIDs -  This represents the set  of nodes that we
    # plan to send to the receiver
    start_q1 = time.time()
    qb = QueryBuilder(limit=lim)
    qb.append(Node, project=['uuid'])
    print "Got", qb.count(), "results"
    res = [_[0] for _ in qb.all()]
    end_q1 = time.time()
    print "==> Elapsed time for export query (secs)", end_q1 - start_q1

    # Store the UUIds in a file (emulate that they were send over the network
    print "Storing UUIDs to the file"
    start_s1 = time.time()
    count_s1 = 0
    with open('tmp_uuid_file.txt', 'wb') as output_file:
        for r in res:
            output_file.write(str(r)+"\n")
            count_s1 += 1
    end_s1 = time.time()
    print "Finished writing to file"
    print "Stored", count_s1, "number of lines"
    print "==> Elapsed time for writing to file (secs)", end_s1 - start_s1
    print "==> File size (bytes): ", os.path.getsize('tmp_uuid_file.txt')

    # Retrieve the UUIDs from the file
    print "Reading UUIDs from file"
    start_s2 = time.time()
    ts = set()
    count_s2 = 0
    with open('tmp_uuid_file.txt', 'rb') as input_file:
        for line in input_file:
            # obtained_uuids.append(UUID(line[:-1]))
            ts.add(line[:-1])
            count_s2 += 1
    end_s2 = time.time()
    print "Read", count_s2, "number of lines"
    print "==> Elapsed time for reading from file (secs)", end_s2 - start_s2

    start_rec = time.time()
    # Get DB from database
    start_q2 = time.time()
    qb = QueryBuilder()
    qb.append(Node, project=['uuid'])
    db = set(str(_[0]) for _ in qb.all())
    end_q2 = time.time()
    print len(db), "DB size"
    print "==> Elapsed time for the calculation of DB (secs)", end_q2 - start_q2

    c = ts - db
    end_rec = time.time()
    print "==> Elapsed time for the receiver queries (secs)", end_rec - start_rec

    print "Not found UUIDs :" + str(len(c))