#!/usr/bin/env python
""" issue.py defines the Issue class, the fundamental object for analysis.

Instances of this class are populated by the various connectors, then placed in
collections for either later analysis, or storage in the database. This is also
the object that represents data in the databse.

All data attributes were selected to represent the critical information for
analysis across a broad range of potential data sources.

If you feel a need to modify / add more information for a specific analysis,
please consider deriving from this class, rather than modifying the issue
data attributes that might be shared across numerous analysis algorithms.


Module Classes:
-- Issue - class that represents the programs issue objects

Module Functions:
-- _init_issuetuple - initializes the IssueTupe global.  Must be called before
            any 'real' objects are created, or tuples generated.
            NOTE:  Should not be called by other modules.  It's executed
            as part of the import process for this module.

Module Globals:
-- IssueTuple - global instance of the IssueTuple class, which is a named
            tuple representing the data attributes for a given issue.
            This must be a top level definition so that pickle will
            work correctly.


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

from collections import namedtuple
from datetime import datetime


_MODNM = __name__.upper()
# Module name string for formatted printing
_MNS = ''.join([_MODNM, ": "])
# Base Error String
_ERS = ''.join([_MODNM, " ERROR: "])

# We have to do some awkward stuff, temporarily, while we're storing issue
#   tuples with pickle.  This should go away when we implement a proper data
#   store.
#
# Global scope for this variable will allow pickle to access it.
#   Unfortunately, it has to be defined after the Issue class is defined,
#   but before an Issue tuple is created / pickled
IssueTuple = None


class Issue(object):
    """ Class Issue is the fundamental in memory object for analysis
    
    Instances of this class are created when data is imported from external
    data stores, as well as when read from the application's own data stores.
    
    The expected type for each of the data attributes is documented as in-line
    comments in the __init__() method.
    
    Note that, for now, we are using int for issue ids.  This may need to change.
    
    *** REALLY IMPORTANT NOTE: ***
        The data attribues listed below are key.  Don't create new attributes on
        the fly, or all kinds of things will break, including the definition of
        the issue tuple
    
    """

    def __init__(self):
        """ Initializes the instance data attributes to default values.
        
        I decided not to pass arguments to the constructor, since there are
        so many attributes that might need to be set.  Instead, instance
        creaters should set the attributes once the instance is created
        
        """
        # initialize to some "default" values
        self.alias = '---'        # str - unique name for issuealias
        self.assigned_to = '---'  # str - owner's name
        self.assigned_to_realname = '---' # str - owner's real name
        self.blocks = []           # list of ids - issue ids blocked by this one
        self.classification = '---'  # str - 
        self.comment = '---'       # str - user comments
        self.component = '---'     # str - 
        self.creation_time = datetime.min  # datetime - 
        self.creator = '---'       # str - name of person who created issue
        self.creator_realname = '---' # str - real name of person who created issue
        self.depends_on = []       # list of ids - must be resolved before this issue can be
        self.dupe_count = 0        # int - 
        self.duplicate_of = 0      # int - bug that this one is a duplicate of
        self.id = -1               # int - id of this issue
        self.keywords = '---'      # str - space delimited keywords
        self.last_change_time = datetime.min  # datetime
        self.organization = '---'  # str - organization owning this source
        self.os = '---'            # str - operating system
        self.priority = '---'      # str - importance
        self.product = '---'       # str - 
        self.qa_contact = '---'    # str - name of responsible QA resource
        self.qa_contact_realname = '---' # str - if some nick was used
        self.ref_url = '---'       # str - url for this issue
        self.resolution = '---'    # str - 
        self.resolved_time = datetime.min # datetime
        self.see_also = '---'      # str - comma separated urls of related issues
        self.severity = '---'      # str - 
        self.status = '---'        # str - 
        self.summary = '---'       # str - 
        self.target_milestone = '---'  # str - target for fix
        self.url = '---'           # str - link to associated data 
        self.version = '---'       # str - 
        self.votes = 0             # int - num votes for this issue
        self.whiteboard = '---'    # str - free form text field
    # end of __init__
    
    def _prep_repr(self):
        # prepare a list of strings that enumerate the key / data attribute
        #   pairs for this instance.  
        rs = ["Issue id #{0}:\n".format(self.id)]
        rs.append("   Instance of class {}:\n".format(self.__class__.__name__))
        # list comprehension to generate key / value pairs and then extend rs 
        #   with the new list
        rs.extend(["   s.{0} = {1}\n".format(key, getattr(self, key)) 
              for key in sorted(vars(self).keys())])
        return rs
    # end of prep_repr
    
    def __repr__(self):
        rs = self._prep_repr()
        return ''.join(rs)
    # end of __repr__
    
    def __str__(self):
        rs = self._prep_repr()
        rs.insert(0,'+++++++++\n')
        rs.append('=========\n') 
        return ''.join(rs)
    # end of __str__
    
    def get_ntpl(self):
        """Returns a named tuple containing the global tuple's fields and this
        instance's data attributes
        
        """
        global IssueTuple
        # kys = vars(self).keys()
        vals = vars(self).values()
        # issuetpl = namedtuple('issuetpl', kys, verbose=False)
        return IssueTuple._make(vals)
    # end of get_ntpl

    def cmp2(self, other):
        """Compares this object to another object of that is (hopefully) an
        instance of the same class.

        Returns True if self matches other.  Otherwise, False

        Arguments:
           other -- object - the object to compare against self
        
        """
        kmtch = False
        vmtch = False
        if sorted(vars(self).keys()) == sorted(vars(other).keys()):
            kmtch = True
            fstr = "{0} #{1} - The {2} attrib names seem to match"
            sys.stdout.write(fstr.format(_MNS, self.id,
                                         len(vars(self).keys())))
        else:
            ml = sorted(vars(self).keys())
            ol = sorted(vars(other).keys())
            if len(ml) == len(ol):
                fstr = ("{0}Length of attrib lists match: {1} entries, but "
                        "some of the\n{2}individual names appear to differ\n")
                sys.stderr.write(fstr.format(_ERS, len(ml), ' '*len(_ERS)))
            else:
                fstr = "{0}I have {1} attrib names - Other has {2}.\n"
                sys.stderr.write(fstr.format(_ERS, len(ml), len(ol)))
            # end if lengths match
            if len(ml) > len(ol):
                # we want to walk the key lists by the longest list - ll
                sl = ol
                ll = ml
                # We want my keys on the left, so the ll elements are to
                #   be printed first on the line
                lf = True
            else:
                # if they're the same length, it doesn't matter which is which
                sl = ml
                ll = ol
                # Since this is where we'll end up when key lengths are equal,
                #  it's good that the ll elements should be second on the line
                lf = False
            # end if len()
            for ix,kv in enumerate(ll):
                try:
                    if lf:
                        # We're enumerating the long list, so we put values
                        #  that list first on the line.
                        vl = kv
                        vr = sl[ix]
                    else:
                        vl = sl[ix]
                        vr = kv
                except IndexError as ie:
                    fstr = ("  ...Sorry, end of attributes in one of the "
                            "issues...\n")
                    sys.stderr.write(fstr)
                else:
                    fstr = "{0}{1}{3}{0}-{0}{2}{4}\n"
                    # The lengths of the attribute names are not consistent,
                    #   so proper columns are a challenge, a set padding of
                    #   spaces after the left entry on each line will have
                    #   to do.  The "pad-to" column is an arbitrary choice
                    padto = 14
                    pad = padto - len(vl)
                    if pad >= 1:
                        pad = ' '*pad
                    else:
                        pad = ''
                    # Highlight lines with mismatched attribute names
                    if vl == vr:
                        # If the names on this row match, just leave them
                        #   alone
                        hlt = ''
                    else:
                        # Otherwise, highlight the mismatch
                        hlt = ' '*2 + '*'*5
                    sys.stderr.write(fstr.format(' ', vl, vr, pad,hlt))
            # end for keys
        # end if keys match
        
        if  kmtch:
            # If the keys don't match, there's no point in testing the
            #   values
            # We can't sort the list of values because it contains a mix of
            #   data types.  However, we know that the lengths of the value
            #   lists must be the same (because the key lists match)
            # We'll walk through our list of keys, and compare the
            #   attributes of the two objects
            vok = True
            for ky in sorted(vars(self).keys()):
                if getattr(self,ky) != getattr(other,ky):
                    if vok:
                        # The attributes matched, but we've got a problem
                        #    with the values.  This is the first time
                        #    through this clause, so terminate the output line
                        #    about the attributes (we also call them keys)
                        sys.stdout.write(".\n")
                    # end if vok
                    vok = False
                    fstr = ("{0}Key: '{1}' Value Error!\n{2}"
                            "Me: {3} - Them: {4}\n")
                    sys.stderr.write(fstr.format(_ERS, ky, ' '*(len(_ERS)),
                                                 getattr(self,ky),
                                                 getattr(other,ky)))
                # end values don't match
            # end for ky
            if vok:
                # We know the attribs  match, since we got to this point,
                #   the values also match, so complete the line.
                fstr = ", as do the values.\n"
                sys.stdout.write(fstr)
            # No else: because the unmatched values is handled above
            vmtch = vok
        # end checking values

        return kmtch and vmtch
# end of Issue


def _init_issuetuple():
    """Initializes the global issuetpl variable that references the
    definition of the issue tuple.  Required (hopefully temporarily) so that
    pickle can get to a global definition of the named tuple
    
    NOTE:  Shouldn't need to be called by external programs, should be run
            during first import of this module
    
    No Return value
    
    """
    global IssueTuple
    # create a temporary issue, just to get at the instance data attributes
    tmp = Issue()
    kys = vars(tmp).keys()
    IssueTuple = namedtuple('IssueTuple', kys, verbose=False)
# end of init_issuetuple

# go ahead and initialize the global IssueTuple
_init_issuetuple()

