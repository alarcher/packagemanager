#!/usr/bin/python
#
# program to generate input files for Solaris.py to 
# move companion to /usr
#

import getopt
import os
import sys
import fnmatch

from pkg.sysvpkg import SolarisPackage
from pkg.bundle.SolarisPackageDirBundle import SolarisPackageDirBundle

transform = [['opt/sfw',          'usr'],
             ['opt/sfw/var',      'var'],
             ['opt/sfw/var/*',    'var/'],
             ['opt/sfw/bin',      'usr/bin'],
             ['opt/sfw/bin/*',    'usr/bin/'],
             ['opt/sfw/etc',      'etc'],
             ['opt/sfw/etc/*',    'etc/'],
             ['opt/sfw/sbin',     'usr/sbin'],
             ['opt/sfw/sbin/*',   'usr/sbin/'],
             ['opt/sfw/src',      'usr/share/src', 'add dir mode=0755 owner=root group=bin path=usr/share'],
             ['opt/sfw/src/*',    'usr/share/src/'],
             ['opt/sfw/man',      'usr/share/man', 'add dir mode=0755 owner=root group=bin path=usr/share'],
             ['opt/sfw/man/*',    'usr/share/man/'],
             ['opt/sfw/share',    'usr/share'],
             ['opt/sfw/share/*',  'usr/share/'],
             ['opt/sfw/READMEs',  'usr/share/READMEs', 'add dir mode=0755 owner=root group=bin path=usr/share'],
             ['opt/sfw/READMEs/*','usr/share/READMEs/'],
             ['opt/sfw/lib',      'usr/lib'],
             ['opt/sfw/lib/*',    'usr/lib/'],
             ['opt/sfw/include',  'usr/include'],
             ['opt/sfw/include/*','usr/include/'],
             ['opt/sfw/info',     'usr/share/info', 'add dir mode=0755 owner=root group=bin path=usr/share'],
             ['opt/sfw/info/*',   'usr/share/info/'],
             ['opt/sfw/libexec',  'usr/lib/libexec'],
             ['opt/sfw/libexec/*','usr/lib/libexec/'],
             ['opt/sfw/doc',      'usr/share/doc'],
             ['opt/sfw/doc/*',    'usr/share/doc/'],
             ['opt/sfw/docs',     'usr/share/doc'],
             ['opt/sfw/docs/*',   'usr/share/doc/'],
             ['opt/sfw/teTeX',    'usr/teTeX'],
             ['opt/sfw/teTeX/*',  'usr/teTeX/'],
             ['usr',              'usr'],
             ['usr/share',        'usr/share'],
             ['usr/share/*',      'usr/share/'],
             ['opt/sfw/vnc',      'usr/vnc'],
             ['opt/sfw/vnc/*',    'usr/vnc/'],
             ['opt/sfw/netpbm',   'usr/netpbm'],
             ['opt/sfw/netpbm/*', 'usr/netpbm/'],

]


def mappkg(out, orig, new):
        if orig != new:
            out.write("chattr %s path=%s\n" % (orig, new))


def chattr(out, s, pkgpath): # map companion files to usr
        for l in transform:
                if fnmatch.fnmatch(s, l[0]):
                        if '*' in l[0]:
                               mappkg(out, s, s.replace(l[0].split('*')[0], l[1]))
                        else:
                               mappkg(out, s, l[1])

		        for i in range(2, len(l)):
                                if l[i] not in additions: # print each addition just once
                                       out.write(l[i] + "\n")
                                       additions.add(l[i])
                        return True

        print "pkg %s: No transform for %s" % (pkgpath, s)
        return False

def process_package(pkgpath):
        additions.clear()
        p = SolarisPackage(pkgpath)
        out = open(os.path.basename(pkgpath), 'w', 0644)

        out.write("package %s\n" % p.pkginfo['PKG'])
        out.write("import  %s\n" % pkgpath)

        for f in p.manifest:
                if f.type != "i":
                      chattr(out, f.pathname, pkgpath)
        out.write("end package\n")
        out.close()



additions = set()

for arg in sys.argv[1:]:
        process_package(arg)
