# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

class Command:

    # The underlying protocol to be used for the communication
    protocol = None

    # Selected command
    command = None

    # Available commands
    SEND_FILE = 'SEND_FILE'
    SEND_BUFF = 'SEND_BUFF'

    # Set of commands
    AVAILABLE_CMDS = set(SEND_FILE, SEND_BUFF)

    def __init__(self, channel, command, protocol):
        from aiida.common.exceptions import InvalidOperation

        if channel is None or command is None:
            logging.debug("[Command] " + "You must provide a command and a "
                                         "channel, exiting")
            raise InvalidOperation("You must provide a command and a channel.")
        if command not in self.AVAILABLE_CMDS:
            logging.debug("[Command] " + "The command requested is not "
                                         "supported, exiting")
            raise InvalidOperation("The command requested is not supported.")

        self.channel = channel
        self.command = command

    def submit(self, command, **kwargs):
        """
        This is the general command
        :param channel:
        :param command:
        :return:
        """
        # Inform the receiver about the command to be executed
        self.send(self.channel, self.command, size_of_chunck = len(command))

        # Execute the command
        self.send_cmd_selector(**kwargs)

    def send_cmd_selector(self, argument):
        switcher = {
            self.SEND_FILE : self.send_file_cmd,
            self.SEND_BUFF: self.send_buff_cmd,
        }
        # Get the right send command
        send_cmd = switcher.get(argument)
        # Execute the method
        return send_cmd()

    def send_file_cmd(self, filename):
        # Proceeding to the file sent
        t = time.time()
        bytes = 0
        try:
            f = open(filename, "rb")
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break

                bytes += sys.getsizeof(chunk)
                logging.debug("[send_file_cmd] " + "Sending: " + chunk)
                byte_no = session_channel.send(chunk)
                logging.debug("[send_file_cmd] " + "Sent " + str(byte_no)
                              + " bytes.")
        finally:
            logging.debug(
                "[send_file_cmd] " + "Sending finished, closing file")
            f.close()

    def send_buff_cmd(self, **kwargs):
        pass
