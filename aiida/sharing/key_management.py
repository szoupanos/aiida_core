# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

###########################################################################
# This is also "heavily inspired" by                                      #
# https://github.com/toresbe/AuthorizedKeys                               #
# But that was used as a starting point but it was also enriched.         #
###########################################################################

from os.path import isdir
import os
import pwd
import sshpubkeys


class SSHAuthorizedKeysEntry(sshpubkeys.SSHKey):
    def get_comment(self):
        return ' '.join(self.keydata.split(' ')[2:]).strip()

    def __repr__(self):
        reprstr = '{hash}: {self.bits} bit {self.key_type} ({comment})'
        return reprstr.format(self=self,
                              hash=self.hash(), comment=self.get_comment())

class SSHAuthorizedKeysFile():
    # This class makes the relatively acceptable assumption that
    # the AuthorizedHostKeys file in sshd's config file is not
    # changed from the default of %h/.ssh/authorized_keys
    def __init__(self, username):
        try:
            user = pwd.getpwnam(username)
        except KeyError:
            raise KeyError('User %s does not exist' % (username,))

        if not isdir(user.pw_dir):
            raise ValueError('User home directory does not exist')

        ssh_path = user.pw_dir + '/.ssh/'

        if not isdir(ssh_path):
            os.mkdir(ssh_path)
            os.chmod(ssh_path, 0700)
            os.chown(ssh_path, user.pw_uid, user.pw_gid)

        self.filename = ssh_path + 'authorized_keys'

        if os.path.isfile(self.filename):
            self.keys = [SSHAuthorizedKeysEntry(key) for key in
                         open(self.filename, 'r')]
        else:
            self.keys = []

    def append(self, keydata):
        if type(keydata) is str:
            if keydata in [k.keydata for k in self.keys]:
                raise ValueError('Key already in file')
            try:
                key = SSHAuthorizedKeysEntry(keydata)
            except Exception as e:
                raise ValueError(e)

        elif type(keydata) is SSHAuthorizedKeysEntry:
            key = keydata
            if key.keydata in [k.keydata.strip() for k in self.keys]:
                raise ValueError('Key already in file')

        else:
            raise TypeError('keydata must be string or SSH Key object')

        open(self.filename, 'a').write(key.keydata + '\n')
        self.keys.append(key)

    def get_keys(self):
        # return self.keys.keys()
        return self.keys


    def __getitem__(self, key):
        return self.keys[key]

    def __delitem__(self, key):
        ssh_key = self.keys[key]

        with open(self.filename, 'r') as keyfile:
            keyfile_entries = [x.strip() for x in keyfile.readlines()]

        with open(self.filename, 'w') as keyfile:
            for keydata in keyfile_entries:
                if ssh_key.keydata != keydata:
                    keyfile.write(keydata + '\n')

        self.keys.remove(ssh_key)
