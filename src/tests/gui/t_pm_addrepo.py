#!/usr/bin/python
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

# Copyright (c) 2009, 2010, Oracle and/or its affiliates. All rights reserved.

import testutils
if __name__ == "__main__":
        testutils.setup_environment("../../../proto")
import pkg5unittest
import unittest

try:
        import ldtp
except ImportError:
        raise ImportError, "SUNWldtp package not installed."

class TestPkgGuiAddRepoBasics(pkg5unittest.SingleDepotTestCase):

        # pygtk requires unicode as the default encoding.
        default_utf8 = True

        foo10 = """
            open package1@1.0,5.11-0
            add set name="description" value="Some package1 description"
            close """

        def testAddRepository(self):
                repo_name = 'testadd'
                repo_url = self.dc.get_depot_url()
                self.pkgsend_bulk(repo_url, self.foo10)
                self.image_create(repo_url)

                ldtp.launchapp("%s/usr/bin/packagemanager" % pkg5unittest.g_proto_area)

                ldtp.selectmenuitem('frmPackageManager', 'mnuManageRepositories')

                ldtp.waittillguiexist('dlgManageRepositories')

                ldtp.settextvalue("dlgManageRepositories", "txtName", repo_name)
                ldtp.settextvalue("dlgManageRepositories", "txtURL", repo_url)
                ldtp.click('dlgManageRepositories', 'btnAdd')

                ldtp.click('dlgManageRepositories', 'btnClose')

                # Verify result
                self.pkg('publisher | grep %s' % repo_name)
                # Quit Package Manager
                ldtp.selectmenuitem('frmPackageManager', 'mnuQuit')

if __name__ == "__main__":
	unittest.main()
