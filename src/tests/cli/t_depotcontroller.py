#!/usr/bin/python2.4
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

# Copyright 2008 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.

import testutils
if __name__ == "__main__":
	testutils.setup_environment("../../../proto")

import unittest
import os
import shutil

import pkg.depotcontroller as dc

class TestDepotController(testutils.CliTestCase):

        def setUp(self):
                testutils.CliTestCase.setUp(self)

                self.__dc = dc.DepotController()
                self.__pid = os.getpid()
		self.__dc.set_depotd_path(testutils.g_proto_area + \
                    "/usr/lib/pkg.depotd")

                depotpath = os.path.join(self.get_test_prefix(), "depot")
                logpath = os.path.join(self.get_test_prefix(), self.id())

                try:
                        os.makedirs(depotpath, 0755)
                except:
                        pass

                self.__dc.set_repodir(depotpath)
                self.__dc.set_logpath(logpath)

        def tearDown(self):
                testutils.CliTestCase.tearDown(self)

                self.__dc.kill()
                shutil.rmtree(self.__dc.get_repodir())
                os.remove(self.__dc.get_logpath())


        def testStartStop(self):
                self.__dc.set_port(12000)
                for i in range(0, 5):
                        self.__dc.start()
                        self.assert_(self.__dc.is_alive())
                        self.__dc.stop()
                        self.assert_(not self.__dc.is_alive())

        def testBadArgs(self):
                self.__dc.set_readonly()
                self.__dc.set_rebuild()
                self.__dc.set_norefresh_index()

                self.assert_(self.__dc.start_expected_fail())

                self.__dc.set_readonly()
                self.__dc.set_norebuild()
                self.__dc.set_refresh_index()

                self.assert_(self.__dc.start_expected_fail())

                self.__dc.set_readonly()
                self.__dc.set_rebuild()
                self.__dc.set_refresh_index()

                self.assert_(self.__dc.start_expected_fail())

                self.__dc.set_readwrite()
                self.__dc.set_rebuild()
                self.__dc.set_refresh_index()

                self.assert_(self.__dc.start_expected_fail())

                self.__dc.set_mirror()
                self.__dc.set_rebuild()
                self.__dc.set_norefresh_index()

                self.assert_(self.__dc.start_expected_fail())

                self.__dc.set_mirror()
                self.__dc.set_norebuild()
                self.__dc.set_refresh_index()

                self.assert_(self.__dc.start_expected_fail())

if __name__ == "__main__":
        unittest.main()
