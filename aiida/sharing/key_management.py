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

import os
import pwd
import sshpubkeys

AIIDA_SHARING_CMD = ('command="source /home/aiida/aiidapy/bin/activate; '
                     'verdi share sharing_handler",no-port-forwarding,'
                     'no-X11-forwarding,no-agent-forwarding,no-pty ')

class AuthorizedKey(sshpubkeys.SSHKey):
    def get_comment(self):
        return ' '.join(self.keydata.split('= ')[1:]).strip()

    def __repr__(self):
        reprstr = ('{comment}: {self.bits} bit {self.key_type} '
                   '({options_raw})')
        return reprstr.format(
            self=self,
            options_raw=(self.options_raw
            if self.options_raw is not None else "-"),
            comment=self.get_comment()
        )

class AuthorizedKeysFileManager:

    auth_keys_fullpath = None

    def __init__(self, given_username=None):
        import getpass

        if given_username is None:
            username = getpass.getuser()

        # Check if the user exist and if it has a working directory
        try:
            user = pwd.getpwnam(username)
        except KeyError:
            raise KeyError('User %s does not exist' % (username,))
        if not os.path.isdir(user.pw_dir):
            raise ValueError('User home directory does not exist')

        # Retrieve the authorized keys relative path
        self.auth_keys_fullpath = self._check_and_create_authorized_keys()

        if os.path.isfile(self.auth_keys_fullpath):
            self.keys = [AuthorizedKey(key.strip()) for key in
                         open(self.auth_keys_fullpath, 'r')]
        else:
            self.keys = []

    @staticmethod
    def _check_and_create_authorized_keys(username,
                                          given_auth_keys_relpath=None):
        if username is None:
            raise ValueError('A username has to be provided')

        if given_auth_keys_relpath is None:
            auth_keys_relpath = './ssh/authorized_keys'
        else:
            auth_keys_relpath = given_auth_keys_relpath

        user_info = pwd.getpwnam(username)
        auth_keys_fullpath = os.path.join(user_info.pw_dir, auth_keys_relpath)
        ssh_dir = os.path.dirname(auth_keys_fullpath)

        # If the .ssh directory doesn't exist, create it
        if not os.path.isdir(ssh_dir):
            os.mkdir(ssh_dir)
            os.chmod(ssh_dir, 0700)
            os.chown(ssh_dir, user_info.pw_uid, user_info.pw_gid)

        return auth_keys_fullpath

    def get_authorized_keys(self):
        with open(self.auth_keys_fullpath, 'r') as auth_keys:
            return auth_keys.read()

    def set_authorized_keys(self, auth_keys_content):
        with open(self.auth_keys_fullpath, 'w') as auth_keys:
            auth_keys.write(auth_keys_content)

    def append(self, keydata):
        if type(keydata) is str:
            if keydata.strip() in [k.keydata for k in self.keys]:
                raise ValueError('Key already in file')
            try:
                key = AuthorizedKey(keydata.strip())
            except Exception as e:
                raise ValueError(e)

        elif type(keydata) is AuthorizedKey:
            key = keydata
            if key.keydata.strip() in [k.keydata for k in self.keys]:
                raise ValueError('Key already in file')
            key.keydata = key.keydata.strip()
        else:
            raise TypeError('keydata must be string or SSH Key object')

        open(self.auth_keys_fullpath, 'a').write(key.keydata + '\n')
        self.keys.append(key)

    def get_keys(self):
        return self.keys

    def create_sharing_entry(self, key_hash, username):
        # Create a new key according the AiiDA sharing standards
        # These will be command + ssh_options + provided_pure_ssh_key +
        # username as options
        full_key = (AIIDA_SHARING_CMD + key_hash + " " + username)
        aiida_sharing_key = AuthorizedKey(keydata=full_key, strict_mode = True)
        self.append(aiida_sharing_key)

        # print "====>" + ssh_key.keydata
        # print(ssh_key.bits)  # 768
        # print(ssh_key.hash_md5())  # 56:84:1e:90:08:3b:60:c7:29:70:5f:5e:25:a6:3b:86
        # print(ssh_key.hash_sha256())  # SHA256:xk3IEJIdIoR9MmSRXTP98rjDdZocmXJje/28ohMQEwM
        # print(ssh_key.hash_sha512())  # SHA512:1C3lNBhjpDVQe39hnyy+xvlZYU3IPwzqK1rVneGavy6O3/ebjEQSFvmeWoyMTplIanmUK1hmr9nA8Skmj516HA
        # print(ssh_key.comment)  # ojar@ojar-laptop
        # print(ssh_key.options_raw)  # None (string of optional options at the beginning of public key)
        # print(ssh_key.options)  # None (options as a dictionary, parsed and validated), strict_mode=True)
        #
        # print "TTTTTT " + ssh_key.keydata


    def delete_sharing_entry(self, username):
        with open(self.auth_keys_fullpath, 'w') as key_file:
            for key in self.keys:
                if username == key.comment:
                    continue
                key_file.write(key.keydata + '\n')

    def __getitem__(self, key):
        return self.keys[key]

    def __delitem__(self, key):
        ssh_key = self.keys[key]

        with open(self.auth_keys_fullpath, 'r') as keyfile:
            keyfile_entries = [x.strip() for x in keyfile.readlines()]

        with open(self.auth_keys_fullpath, 'w') as keyfile:
            for keydata in keyfile_entries:
                if ssh_key.keydata != keydata:
                    keyfile.write(keydata + '\n')

        self.keys.remove(ssh_key)
