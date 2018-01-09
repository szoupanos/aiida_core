# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from abc import ABCMeta, abstractmethod
from aiida.sharing.sharing_logging import SharingLoggingFactory

class Command:
    __metaclass__ = ABCMeta

    cmd_name = None

    def __init__(self):
        self.logger = SharingLoggingFactory.get_logger(
            SharingLoggingFactory.get_fullclass_name(self.__class__))

    @abstractmethod
    def execute(self):
        raise NotImplementedError("This should be properly implemented by "
                                  "the classes that inherit Command")
