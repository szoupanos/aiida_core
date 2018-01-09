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

class Connection:
    __metaclass__ = ABCMeta

    # The buffer size
    BUFFER_SIZE = 1024

    # This is the reserved number of bytes for chunk message
    # that will be sent by the sender to the receiver
    BYTES_FOR_CHUNK_SIZE_MSG = 10

    # Acknowledgement message
    OK_MSG = 'OK'

    def __init__(self):
        self.logger = SharingLoggingFactory.get_logger(
            SharingLoggingFactory.get_fullclass_name(self.__class__))

    @abstractmethod
    def send(self):
        raise NotImplementedError("This should be properly implemented by "
                                  "the classes that inherit Connection")

    @abstractmethod
    def receive(self):
        raise NotImplementedError("This should be properly implemented by "
                                  "the classes that inherit Connection")

    @abstractmethod
    def wait_for_ok(self):
        raise NotImplementedError("This should be properly implemented by "
                                  "the classes that inherit Connection")
