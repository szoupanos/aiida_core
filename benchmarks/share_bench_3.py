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
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import os

# This is a secondary approach for calculating the UUIDs of the nodes to be
# sent to the receiver side.
#
# Let TS be the set of UUIDs sent by the sender and DB the set of UUIDs that
# are at the receiver side.
#
# The set calculated by SQLA is the B = DB - TS
# At Python level we calculate the A = DB - B and finally the C = TS - A

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
# for lim in [100, 1000, 10000, 100000, 1000000, None]:
# for lim in [100, 1000, 10000]:
for lim in [None, 1000000, 100000, 10000, 1000, 100]:
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
    ts = list()
    count_s2 = 0
    with open('tmp_uuid_file.txt', 'rb') as input_file:
        for line in input_file:
            # obtained_uuids.append(UUID(line[:-1]))
            ts.append(line[:-1])
            count_s2 += 1
    end_s2 = time.time()
    print "Read", count_s2, "number of lines"
    print "==> Elapsed time for reading from file (secs)", end_s2 - start_s2

    start_rec = time.time()
    # Calculate the set B = DB - TS
    start_q2 = time.time()
    qb = QueryBuilder()
    qb.append(Node, filters={'uuid': {'!in': ts}}, project=['uuid'])
    b = set(str(_[0]) for _ in qb.all())
    end_q2 = time.time()
    print len(b), "B size, where B = DB - TS"
    print "==> Elapsed time for the calculation of B (secs)", end_q2 - start_q2

    # Calculate the set DB (the set of UUIDs that exist in the database)
    start_q3 = time.time()
    qb = QueryBuilder()
    qb.append(Node, project=['uuid'])
    db = set(str(_[0]) for _ in qb.all())
    end_q3 = time.time()
    print len(b), "DB size"
    print "==> Elapsed time for the calculation of DB (secs)", end_q3 - start_q3

    # Calculate the set A = DB - B
    start_q4 = time.time()
    a = db - b
    end_q4 = time.time()
    print len(b), "A size, where A = DB - B"
    print "==> Elapsed time for the calculation of A (secs)", end_q4 - start_q4

    # Calculate the set C = TS - A
    start_q5 = time.time()
    c = ts - a
    end_q5 = time.time()
    print len(b), "C size, where C = TS - A"
    print "==> Elapsed time for the calculation of C (secs)", end_q5 - start_q5

    end_rec = time.time()
    print "==> Elapsed time for the receiver queries (secs)", end_rec - start_rec
