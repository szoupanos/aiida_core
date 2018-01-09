# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

class SharingLoggingFactory:
    __loggers  = dict()

    def __init__(self):
        raise RuntimeError('Not intended to create objects of this class')

    @classmethod
    def get_logger(cls, logger_name):
        if len(cls.__loggers.keys()) == 0:
            import logging
            import inspect
            import os

            # Get the current path - Needed to place the log file
            path = os.path.dirname(inspect.getfile(cls))

            logging.basicConfig(
                filename=os.path.join(path,'sharing_debug.log'),
                format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                datefmt='%d-%m-%Y:%H:%M:%S',
                level=logging.DEBUG)

        if not cls.__loggers.has_key(logger_name):
            logger = logging.getLogger(logger_name)
            cls.__loggers[logger_name] = logger
            return logger

        return cls.__loggers[logger_name]

    @staticmethod
    def get_fullclass_name(given_class):
        return given_class.__module__ + "." + given_class.__class__.__name__
