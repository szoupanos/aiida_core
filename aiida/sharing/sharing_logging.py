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
        if not cls.__loggers.has_key(logger_name):
            import logging
            import inspect
            import os

            # Get the current path - Needed to place the log file
            path = os.path.dirname(inspect.getfile(cls))
            logger = logging.getLogger(logger_name)
            hdlr = logging.FileHandler(os.path.join(path,'sharing_debug.log'))
            formatter = logging.Formatter(
                '%(asctime)s,%(msecs)d %(levelname)-8s '
                '[%(name)s:%(funcName)s] %(message)s')
            hdlr.setFormatter(formatter)
            logger.addHandler(hdlr)
            logger.setLevel(logging.DEBUG)
            cls.__loggers[logger_name] = logger
            return logger

        return cls.__loggers[logger_name]

    @staticmethod
    def get_fullclass_name(given_class):
        return given_class.__module__ + "." + given_class.__name__
