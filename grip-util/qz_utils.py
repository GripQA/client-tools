""" qz_utils.py - this module contains the utility functions for the system


Module Functions:
-- openfile
-- restful_get
-- validpath


Module Classes:
-- QZUtilsExc

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
__copyright__ = "Copyright 2013, Quality Zen, LLC, Assigned to Grip QA"
__license__ = "Apache License, Version 2.0"
__status__ = "Prototype"
__version__ = "0.01"

import os
import sys
import math
import urllib.error
import urllib.parse
import urllib.request
import json
import re


# String for module name
if __name__ == '__main__':
    osf = sys.modules['__main__'].__file__
    pth,file = os.path.split(osf)
    modnm, ext = os.path.splitext(file)
else:
    modnm = __name__
# end if main
_MODNM = modnm.upper()
# Module name string for formatted printing
_MNS = ''.join([_MODNM, ": "])
# Base Error String
_ERS = ''.join([_MODNM, " ERROR: "])

# These modules raise a number of exceptions, so a common format str
#   Note: May be used by other modules
EXCFMTS = "{0}Exception: {1}\n"


class QZUtilsExc(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def restful_get(url, verbose=False):
    """Attempt to read the REST data at the given URL. This function also
    handlesthe JSON processing
    
    Returns a glob of data, processed through JSON.  Returns None
    if there were any problems
    
    Arguments:
    url -- String containing the full URL for the query
    verbose -- print diagnostics, default is False
    
    """
    ecd_rsp  = None
    dcd_resp = None
    rtn_blob = None
    open_url = None
    try:
        open_url = urllib.request.urlopen(url)
    except Exception as eget:
        sys.stderr.write("{0}Unable to open specified URL: {1}\n"
                         .format(_ERS, url))
        sys.stderr.write(EXCFMTS.format(' '*len(_ERS), eget))
    else:
        if verbose:
            sys.stdout.write("{0}URL Opened\n".format(_MNS))
        try:
            ecd_rsp = open_url.read()
        except Exception as rex:
            sys.stderr.write("{0}Unable to read from {1}\n"
                             .format(_ERS, url))
            sys.stderr.write(EXCFMTS.format(' '*len(_ERS), rex))
        else:
            if verbose:
                sys.stdout.write("{0}Data Read\n".format(_MNS))
        # end read exception handler
    # end open exception handler
    if ((open_url is not None) and (ecd_rsp is not None)):
        # we have a good url, and an encoded response
        encds = open_url.info()['Content-Type']
        if encds is not None:
            # we have a content type string
            fnd = re.search('(charset=)(\S*)(;|\Z)',encds)
            if fnd is not None:
                try:
                    dcd_rsp = ecd_rsp.decode(fnd.group(2))
                except Exception as dex:
                    sys.stderr.write("{0}Unable to decode {1}\n"
                                     .format(_ERS, url))
                    sys.stderr.write(EXCFMTS.format(' '*len(_ERS),dex))
                else:
                    if verbose:
                        sys.stdout.write("{0}Data Decoded\n".format(_MNS))
            # end fnd is not None
        # end encds is not None
    # end open_url and ecd_rsp
    if dcd_rsp is not None:
        # we have a decoded response, let's try to run it through JSON
        try:
            rtn_blob = json.loads(dcd_rsp)
        except Exception as jload:
            sys.stderr.write("{0}Unable to load JSON from {1}\n"
            .format(_ERS, url))
            sys.stderr.write(EXCFMTS.format(' '*len(_ERS), jload))
            # just to be really sure, since JSON failed
            rtn_blob = None
        else:
            if verbose:
                sys.stdout.write("{0}GET and JSON successful for: {1}\n"
                                 .format(_MNS, url))
        # end JSON exception handler
    # end response is not None
    return rtn_blob
# end restful_get


def validpath(pname,access=''):
    """Normalizes a pathname for the OS, verifies whether the pathname exists
    and (optionally) checks r/w acess
    Returns the normalized path, if pname exists, and we have the specified 
    access.  Otherwise return None
    
    Arguments:
    pname -- String containing the name of the file
    access -- string containing the r/w attributes to check.  'r' checks read,
            only. 'w' checks write only. 'rw' checks both.  if empty, we 
            check neither
    """
    # normalize the path and check for existance of the file
    npath = os.path.normpath(pname)
    retval = None
    if os.access(npath, os.F_OK):
        # We know that the path exists, let's see if it matches the attributes
        #   that we want
        if type(access) is str:
            if access:
                readOK = True
                writeOK = True
                if 'r' in access:
                    # check read attribute, if they asked us to
                    if not os.access(npath, os.R_OK):readOK = False
                if (('w' in access) or ('a' in access)):
                    # check write attribute, if they asked us to
                    if not os.access(npath, os.W_OK): writeOK = False
                if readOK and writeOK:
                    # both will only be true if both are truly OK, or if only
                    #   the one that we're actually checking is OK
                    retval = npath
            else:
                # we're dealing with an empty string, or garbage, so just let
                #   it go
                retval = npath
        else:
            # they sent us something that we can't understand for mode, just
            #   send back the normalized path, that we know exists
            retval = npath
    # if npath didn't exist, we'll drop straight to here, and retval is 
    #   initialized to None
    return retval
# end validpath


def openfile(filename, mode='r'):
    """Attempt to open the specified file and return a handle to the file, 
    if we succeed
    
    Returns a handle for the newly opened file, if successful, otherwise None
    Arguments:
    filename -- String containing the pathname of the file to be opened
    mode -- mode to open the file with: 'r', 'w', 'rw'
    """
    sys.stdout.write("{0}Attempting to Open file: {1}\n"
                     .format(_MNS, filename))
    # check for existance and read access.
    fpath = validpath(filename,mode)
    # initialize to avoid extraneous else's
    retval = None
    openit = False
    if fpath is None:
        # couldn't validate the path, but we might be creating the file with
        #   a write
        if 'w' in mode:
            # we couldn't validate the path, but we're writing, let's see if
            #   we have 'r' access
            fpath = validpath(filename,'r')
            if fpath is None:
                # we don't even have read access, either the file is locked
                #   up tight, or it doesn't exist.  Let's see what happens
                openit = True
                # set fpath to filename directly, since we can't validate
                #   a path
                fpath = filename
            # no else clause, because we already set openit to False.  The
            #   else would be that the path validated for read, which means
            #   that we don't have write access, so we can't open it for
            #   write.
    else:
        # we got back a handle, let's see if it works...
        openit = True

    if openit:
        #we're going to try to write the file, in which case we might be
        #   creating it, or the path exists, and we have read access to it.
        #   We'll use an exception handler to around the open, just in case.
        try:
            retval = open(fpath,mode)
        except IOError as ex:
            sys.stderr.write("{0}Access failed for file: {1}\n"
                             .format(_ERS, filename))
            sys.stderr.write(EXCFMTS.format(' '*len(_ERS), ex))
        finally:
            if not retval is None:
                # retval will only have a new value if open succeeded and 
                # did not throw an exception.
                sys.stdout.write("{0}Opened file: {1}\n"
                                 .format(_MNS, filename))

    if retval is None:
        # most likely the file didn't exist.  Could also be we can't read it,
        #    write it, or that a problem happened at open...
        sys.stderr.write("{0}Could not open file: {1}\n"
                         .format(_ERS, filename))
    
    # return the file handle, if all operations succeeded
    return retval
# end of openfile
