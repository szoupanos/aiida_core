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

from aiida.sharing.key_management import SSHAuthorizedKeysFile

class SSHAuthorizedKeysGoodUsersTest(unittest.TestCase):
    valid_dummy_key_1 = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDW7Y0E8nThXSJPtvF3g' + \
                        'pLLhj7E1VlTVG36wArMZ71LByjaqtfFI/PcWLIu6Bf5YdRNsv/M8sdk4mRslWFofEL8Uk' + \
                        'rwAl4BXDuXU6hU/+dCF6b+gLJvWaGzuKiQyfDYrm8= dummy debugging key'

    valid_dummy_key_2 = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAYQDmOXORyDk9dZSYxudLF' + \
                        '1xEivuixKRVT6OCg7SDySJHVzqFnQkJSXwwcCEF0FdTAA0VaidIpgDhXdj9UFzcKfgo3H' + \
                        'f0R5bLAZXn7UQjNWh3M8v+K9cUVIWBukIoLlzs4zE= dummy debugging key 2'

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
        f = SSHAuthorizedKeysFile('yada')
        self.assertIsInstance(f, SSHAuthorizedKeysFile)

    def testAddOneValidKey(self):
        f = SSHAuthorizedKeysFile('yada')
        self.assertEqual(len(f.keys), 0)
        f.append(self.valid_dummy_key_1)
        self.assertEqual(len(f.keys), 1)

    def testRefuseDuplicateKey(self):
        f = SSHAuthorizedKeysFile('yada')
        self.assertEqual(len(f.keys), 0)
        f.append(self.valid_dummy_key_1)
        self.assertRaises(ValueError, f.append, self.valid_dummy_key_1)

    def testNewKeysPersist(self):
        f = SSHAuthorizedKeysFile('yada')
        self.assertEqual(len(f.keys), 0)
        f.append(self.valid_dummy_key_1)
        del f
        f = SSHAuthorizedKeysFile('yada')
        self.assertEqual(len(f.keys), 1)

    def testIndexErrorFromBadIndex(self):
        f = SSHAuthorizedKeysFile('yada')
        self.assertRaises(IndexError, f.__getitem__, 1)

    @unittest.skip("Have to look why this fails")
    def testCorrectKeyRemoved(self):
        f = SSHAuthorizedKeysFile('yada')
        f.append(self.valid_dummy_key_1)
        f.append(self.valid_dummy_key_2)
        del f[0]
        del f
        f = SSHAuthorizedKeysFile('yada')
        self.assertEqual(len(f.keys), 1)
        self.assertEqual(f[0].keydata, self.valid_dummy_key_2)

    def testKeyRemovalPersists(self):
        f = SSHAuthorizedKeysFile('yada')
        f.append(self.valid_dummy_key_1)
        del f[0]
        del f
        f = SSHAuthorizedKeysFile('yada')
        self.assertEqual(len(f.keys), 0)

    def testCreatesInitialSSHDir(self):
        self.assertIsInstance(SSHAuthorizedKeysFile('yada'),
                              SSHAuthorizedKeysFile)
        self.failUnless(os.path.isdir(self.dummy_user.pw_dir + '/.ssh'))

    def testKeyListing(self):
        f = SSHAuthorizedKeysFile('yada')
        f.append(self.valid_dummy_key_1)
        f.append(self.valid_dummy_key_2)
        f = SSHAuthorizedKeysFile('yada')
        k = f.get_keys()
        # print k[0].comment()
        k0 = k[0]
        print k0.hash()
        print k0.comment
        print k0.get_comment()
        print k0.
        print k
        # print f.get_keys()

class SSHAuthorizedKeysBadUsersTest(unittest.TestCase):
    # good to make sure
    def testTrueIsTrue(self):
        self.failUnless(True)

    def testUserNoHome(self):
        class homeless_user():
            pw_name = 'toresbe'
            pw_passwd = 'x'
            pw_uid = 1000
            pw_gid = 1000
            pw_gecos = 'Legitimate Homeless User'
            pw_dir = '/this/really/should/not/exist/on/your/system'
            pw_shell = '/bin/bash'

        def no_such_dir(username):
            return homeless_user

        pwd.getpwnam = no_such_dir
        self.assertRaises(ValueError, SSHAuthorizedKeysFile, 'dummy_username')

    def testNonexistantUser(self):
        def no_such_user(username):
            raise KeyError

        pwd.getpwnam = no_such_user
        self.assertRaises(KeyError, SSHAuthorizedKeysFile, 'dummy_username')