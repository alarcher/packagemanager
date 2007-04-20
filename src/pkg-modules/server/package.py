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
# Copyright 2007 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.

import os
import re
import sha
import shutil
import time
import urllib

import pkg.fmri as fmri
import pkg.server.catalog as catalog

class SPackage(object):
        """An SPackage is the server's representation of a versioned package
        sequence."""

        def __init__(self, cfg):
                self.name = ""
                self.cfg = cfg
                self.versions = ()
                return

        def set_name(self, fmri):
                """Set the name member based on the non-versioned portion of the
                FMRI."""
                return

        def load(self):
                """Iterate through directory and build version list."""
                return

        def update(self, trans):
                return

        def get_state(self, version):
                return 0;

        def get_manifest(self, version):
                return
