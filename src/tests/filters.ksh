#!/bin/ksh -px
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

# Copyright 2007 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.

eval `pkgsend open test/filter/A@0.1-1`
if [ $? != 0 ]; then
	echo \*\* script aborted:  couldn\'t open test/upgrade/A
	exit 1
fi

i386dir=/ws/onnv-gate/packages/i386/nightly
sparcdir=/ws/onnv-gate/packages/sparc/nightly
file=SUNWcsu/reloc/usr/bin/ls

echo $PKG_TRANS_ID
pkgsend add dir  0755 root sys /bin
pkgsend add file 0755 root sys /bin/ls $i386dir/$file debug=true
pkgsend add file 0755 root sys /bin/ls $i386dir-nd/$file debug=false
pkgsend add file 0755 root sys /bin/ls $sparcdir/$file debug=true
pkgsend add file 0755 root sys /bin/ls $sparcdir-nd/$file debug=false
pkgsend close