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

import tempfile
import unittest
import os
import pwd

from aiida.sharing.key_management import (AuthorizedKeysFileManager,
                                          AIIDA_SHARING_CMD)


class SSHAuthorizedKeysGoodUsersTest(unittest.TestCase):
    valid_dummy_key_1 = (
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDW7Y0E8nThXSJPtvF3g'
        'pLLhj7E1VlTVG36wArMZ71LByjaqtfFI/PcWLIu6Bf5YdRNsv/M8sdk4mRslWFofEL8Uk'
        'rwAl4BXDuXU6hU/+dCF6b+gLJvWaGzuKiQyfDYrm8= valid dummy key 1')

    valid_dummy_key_2 = (
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxudLF'
        '1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidIpgDhXdj9UFzcKfgo3H'
        'f0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLlzs4zE= dummy debugging key 2')

    valid_dummy_sharing_key_1 = (
        'command="source /home/aiida/aiidapy/bin/activate; '
        'verdi share handle_push", '
        'no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ' 
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxudLF'
        '1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidIpgDhXdj9UFzcKfgo3H'
        'f0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLlzs4zE= dummy debugging key 3')

    not_valid_dummy_key_1 = (
        'ssh-rsa this_is_a_not_valid_key= not a valid dummy key')

    valid_dummy_just_hash_1 = (
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxudLF'
        '1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidIpgDhXdj9UFzcKfgo3H'
        'f0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLlzs4zE'
    )

    not_valid_dummy_just_hash_1 = (
        'ssh-rsa this_is_a_not_valid_key'
    )

    dummy_user = "dummy_user"
    dummy_profile = "dummy_profile"
    valid_dummy_sharing_key_1 = (AIIDA_SHARING_CMD + valid_dummy_just_hash_1
                                 + " {}@{}".format())



    class dummy_user():
        pw_name = 'toresbe'
        pw_passwd = 'x'
        pw_uid = 1000
        pw_gid = 1000
        pw_gecos = 'Legitimate User With Unfurnished Home'
        pw_dir = None
        pw_shell = '/bin/bash'

    def empty_dir(self, username):
        return self.dummy_user

    def setUp(self):
        self.dummy_user.pw_dir = tempfile.mkdtemp()
        pwd.getpwnam = self.empty_dir

    def tearDown(self):
        tmpdir = self.dummy_user.pw_dir
        # print 'Cleaning up, deleting directory ',
        try:
            os.unlink(tmpdir + '/.ssh/authorized_keys')
        except Exception as e:
            pass

        try:
            os.rmdir(tmpdir + '/.ssh')
        except Exception as e:
            pass
        try:
            os.rmdir(tmpdir)
        except Exception as e:
            pass

    def testConstruction(self):
        f = AuthorizedKeysFileManager('aiida')
        self.assertIsInstance(f, AuthorizedKeysFileManager)

    def testAddOneValidKey(self):
        f = AuthorizedKeysFileManager('aiida')
        self.assertEqual(len(f.keys), 0)
        f.append(self.valid_dummy_key_1)
        self.assertEqual(len(f.keys), 1)

    def testRefuseDuplicateKey(self):
        f = AuthorizedKeysFileManager('aiida')
        self.assertEqual(len(f.keys), 0)
        f.append(self.valid_dummy_key_1)
        self.assertRaises(ValueError, f.append, self.valid_dummy_key_1)

    def testNewKeysPersist(self):
        f = AuthorizedKeysFileManager('aiida')
        self.assertEqual(len(f.keys), 0)
        f.append(self.valid_dummy_key_1)
        del f
        f = AuthorizedKeysFileManager('aiida')
        self.assertEqual(len(f.keys), 1)

    def testIndexErrorFromBadIndex(self):
        f = AuthorizedKeysFileManager('aiida')
        self.assertRaises(IndexError, f.__getitem__, 1)

    def testCorrectKeyRemoved(self):
        f = AuthorizedKeysFileManager('aiida')
        f.append(self.valid_dummy_key_1)
        f.append(self.valid_dummy_key_2)
        f.append(self.not_valid_dummy_key_1)
        del f[0]
        del f
        f = AuthorizedKeysFileManager('aiida')
        self.assertEqual(len(f.keys), 2)
        self.assertEqual(f[0].keydata, self.valid_dummy_key_2)
        self.assertEqual(f[1].keydata, self.not_valid_dummy_key_1)
        del f[1]
        del f
        f = AuthorizedKeysFileManager('aiida')
        self.assertEqual(f[0].keydata, self.valid_dummy_key_2)

    def testCreateSharingEntry(self):
        f = AuthorizedKeysFileManager('aiida')

        # Add some valid keys
        f.append(self.valid_dummy_key_1)
        f.append(self.valid_dummy_key_2)
        # Create a valid sharing entry
        f.create_sharing_entry(self.valid_dummy_just_hash_1, 'user_aiida',
                               'profile_1')
        del f

        # Reload the authorized_key file
        f = AuthorizedKeysFileManager('aiida')
        # Check the existence of all the keys
        self.assertEqual(len(f.keys), 3)
        self.assertEqual(f[0].keydata, self.valid_dummy_key_1)
        self.assertEqual(f[0].keydata, self.valid_dummy_key_2)
        self.assertEqual(f[1].keydata, self.not_valid_dummy_key_1)

        f.append(self.valid_dummy_key_1)
        f.append(self.valid_dummy_key_2)
        f.append()



    def testKeyRemovalPersists(self):
        f = AuthorizedKeysFileManager('aiida')
        f.append(self.valid_dummy_key_1)
        del f[0]
        del f
        f = AuthorizedKeysFileManager('aiida')
        self.assertEqual(len(f.keys), 0)

    def testKeyListing(self):
        f = AuthorizedKeysFileManager('aiida')
        keys = [self.valid_dummy_key_1, self.valid_dummy_key_2,
                self.valid_dummy_sharing_key_1, self.not_valid_dummy_key_1]
        for key in keys:
            f.append(key)

        f = AuthorizedKeysFileManager('aiida')
        for k in f.get_keys():
            self.assertIn(str(k.keydata).strip(), keys,
                          "Key " + k.keydata + " not found in " + str(keys))

    # def test_not_valid_key(self):
    #     from aiida.sharing.key_management import AuthorizedKey
    #     ssh_key = AuthorizedKey(self.not_valid_dummy_key_1)
    #     print "====>" + ssh_key.keydata
    #     print(ssh_key.bits)
    #     # print(ssh_key.hash_md5())
    #     # print(ssh_key.hash_sha256())
    #     # print(ssh_key.hash_sha512())
    #     print(ssh_key.comment)
    #     print(ssh_key.options_raw)
    #     print(ssh_key.options)


# class SSHAuthorizedKeysGoodUsersTest(unittest.TestCase):
#     valid_dummy_key_1 = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDW7Y0E8nThXSJPtvF3g' + \
#                         'pLLhj7E1VlTVG36wArMZ71LByjaqtfFI/PcWLIu6Bf5YdRNsv/M8sdk4mRslWFofEL8Uk' + \
#                         'rwAl4BXDuXU6hU/+dCF6b+gLJvWaGzuKiQyfDYrm8= dummy debugging key'
#
#     valid_dummy_key_2 = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxudLF' + \
#                         '1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidIpgDhXdj9UFzcKfgo3H' + \
#                         'f0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLlzs4zE= dummy debugging key 2'
#
#     valid_dummy_key_3 = 'command="source /home/aiida/aiidapy/bin/activate; ' \
#                         'verdi share handle_push", ' \
#                         'no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ' \
#                         'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxudLF'  \
#                         '1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidIpgDhXdj9UFzcKfgo3H'  \
#                         'f0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLlzs4zE= dummy debugging key 3'
#
#     class dummy_user():
#         pw_name = 'toresbe'
#         pw_passwd = 'x'
#         pw_uid = 1000
#         pw_gid = 1000
#         pw_gecos = 'Legitimate User With Unfurnished Home'
#         pw_dir = None
#         pw_shell = '/bin/bash'
#
#     def empty_dir(self, username):
#         return self.dummy_user
#
#     def setUp(self):
#         self.dummy_user.pw_dir = tempfile.mkdtemp()
#         pwd.getpwnam = self.empty_dir
#
#     def tearDown(self):
#         tmpdir = self.dummy_user.pw_dir
#         # print 'Cleaning up, deleting directory ',
#         try:
#             os.unlink(tmpdir + '/.ssh/authorized_keys')
#         except Exception as e:
#             pass
#
#         try:
#             os.rmdir(tmpdir + '/.ssh')
#         except Exception as e:
#             pass
#         try:
#             os.rmdir(tmpdir)
#         except Exception as e:
#             pass
#
#     def testConstruction(self):
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertIsInstance(f, SSHAuthorizedKeysFile)
#
#     def testAddOneValidKey(self):
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertEqual(len(f.keys), 0)
#         f.append(self.valid_dummy_key_1)
#         self.assertEqual(len(f.keys), 1)
#
#     def testRefuseDuplicateKey(self):
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertEqual(len(f.keys), 0)
#         f.append(self.valid_dummy_key_1)
#         self.assertRaises(ValueError, f.append, self.valid_dummy_key_1)
#
#     def testNewKeysPersist(self):
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertEqual(len(f.keys), 0)
#         f.append(self.valid_dummy_key_1)
#         del f
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertEqual(len(f.keys), 1)
#
#     def testIndexErrorFromBadIndex(self):
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertRaises(IndexError, f.__getitem__, 1)
#
#     @unittest.skip("Have to look why this fails")
#     def testCorrectKeyRemoved(self):
#         f = SSHAuthorizedKeysFile('yada')
#         f.append(self.valid_dummy_key_1)
#         f.append(self.valid_dummy_key_2)
#         del f[0]
#         del f
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertEqual(len(f.keys), 1)
#         self.assertEqual(f[0].keydata, self.valid_dummy_key_2)
#
#     def testKeyRemovalPersists(self):
#         f = SSHAuthorizedKeysFile('yada')
#         f.append(self.valid_dummy_key_1)
#         del f[0]
#         del f
#         f = SSHAuthorizedKeysFile('yada')
#         self.assertEqual(len(f.keys), 0)
#
#     def testCreatesInitialSSHDir(self):
#         self.assertIsInstance(SSHAuthorizedKeysFile('yada'),
#                               SSHAuthorizedKeysFile)
#         self.failUnless(os.path.isdir(self.dummy_user.pw_dir + '/.ssh'))
#
#     def testKeyListing(self):
#         f = SSHAuthorizedKeysFile('aiida')
#         keys = [self.valid_dummy_key_1, self.valid_dummy_key_2,
#                 self.valid_dummy_key_3]
#         for key in keys:
#             f.append(key)
#
#         f = SSHAuthorizedKeysFile('aiida')
#         for k in f.get_keys():
#             self.assertIn(str(k.keydata).strip(), keys,
#                           "Key " + k.keydata + " not found in " + str(keys))
#
# class SSHAuthorizedKeysBadUsersTest(unittest.TestCase):
#     # good to make sure
#     def testTrueIsTrue(self):
#         self.failUnless(True)
#
#     def testUserNoHome(self):
#         class homeless_user():
#             pw_name = 'toresbe'
#             pw_passwd = 'x'
#             pw_uid = 1000
#             pw_gid = 1000
#             pw_gecos = 'Legitimate Homeless User'
#             pw_dir = '/this/really/should/not/exist/on/your/system'
#             pw_shell = '/bin/bash'
#
#         def no_such_dir(username):
#             return homeless_user
#
#         pwd.getpwnam = no_such_dir
#         self.assertRaises(ValueError, SSHAuthorizedKeysFile, 'dummy_username')
#
#     def testNonexistantUser(self):
#         def no_such_user(username):
#             raise KeyError
#
#         pwd.getpwnam = no_such_user
#         self.assertRaises(KeyError, SSHAuthorizedKeysFile, 'dummy_username')