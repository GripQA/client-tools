#!/usr/bin/env python
"""dnld_bz.py is a quick script for populating the database with downloaded
issue information.

CMD LINE USAGE:  dnld_bz.py [-h] | start_range end_range
  -h - generates usage line
  start_range - non-negative integer specifying the starting id for the
                range of issues to download
  end_range -  non-negative integer specifying the ending id for the
                range of issues to download

EXTERNAL FUNCTIONS:
  run_qz - the main function in this module


Copyright 2015 Grip QA

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__author__ = "Dean Stevens"
__copyright__ = "Copyright 2013, Quality Zen, LLC; Assigned to Grip QA"
__license__ = "Apache License, Version 2.0"
__status__ = "Prototype"
__version__ = "0.01"


import sys
import os

import pymongo

# machinations to add the QZ source directory to the search path
fdir = os.path.dirname(__file__)
srcp = '../src'
srcap = os.path.abspath(''.join([fdir, '/', srcp]))
sys.path.insert(1, srcap)

import bzconn
import qzargs

# String for module name
if __name__ == '__main__':
    osf = sys.modules['__main__'].__file__
    pth,file = os.path.split(osf)
    modnm, ext = os.path.splitext(file)
    # reset to False, since we're running the program directly
    _AS_FXN = False
else:
    modnm = __name__
# end if main
_MODNM = modnm.upper()
# Module name string for formatted printing
_MNS = ''.join([_MODNM, ": "])
# Base Error String
_ERS = ''.join([_MODNM, " ERROR: "])
# Base Note String
_NTE = ''.join([_MODNM, " NOTE: "])
# Return Named Tuples, or actual issue instances

_USTR = "Usage: {0} [-h] | start_range end_range".format(modnm)


def getit(beg, end):
    # Actually retrieves the specified range of issues
    # Returns the number of issues downloaded
    # Arguments:
    #  beg -- int - start of range
    #  end -- int - end of range
    
    base_url = 'https://api-dev.bugzilla.mozilla.org/latest'
    query = ['ISSUE_RANGE', beg, end]
    org = 'Mozilla'
    clxn = pymongo.MongoClient()['test']['utst']
    cntl = bzconn.get_issues(base_url, query, org, False, clxn, False)
    return cntl[0] if cntl is not None else 0
# end getit


if __name__ == '__main__':
    # The length of the argument list, incl. the program name
    _EXPARG = 3
    if len(sys.argv) == 2 and sys.argv[1] == '-h':
        sys.stdout.write("\n{0}\n\n".format(_USTR))
        exit(0)
    
    iargs = "{0}Arguments must be non-negative Integers; Not '{1}'\n"
    if len(sys.argv) < _EXPARG or len(sys.argv) > _EXPARG:
        nargs = "{0}Wrong number of arguments; Expected {1}, Received {2}\n"
        sys.stderr.write(nargs.format(_ERS, _EXPARG-1, len(sys.argv)-1))
        badargs = True
    else:
        badargs = False
        try:
            a1 = int(sys.argv[1])
        except ValueError:
            sys.stderr.write(iargs.format(_ERS, sys.argv[1]))
            badargs = True
        else:
            # it converted to an int, make sure it's non-negative
            if a1 < 0:
                sys.stderr.write(iargs.format(_ERS, sys.argv[1]))
                badargs = True
        try:
            a2 = int(sys.argv[2])
        except ValueError:
            sys.stderr.write(iargs.format(_ERS, sys.argv[2]))
            badargs = True
        else:
            # it converted to an int, make sure it's non-negative
            if a2 < 0:
                sys.stderr.write(iargs.format(_ERS, sys.argv[2]))
                badargs = True
    # end check args

    if not badargs:
        gotn = getit(min(a1,a2), max(a1,a2))
        sys.stdout.write("{0}Retrieved {1} issues\n".format(_NTE, gotn))
    else:
        sys.stderr.write("{0}Invalid arguments.  Unable to download\n"
                         .format(_ERS))
        sys.stdout.write("\n{0}\n\n".format(_USTR))
        exit(9)
