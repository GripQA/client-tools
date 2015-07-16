#!/usr/bin/env python
""" bzconn.py - this module contains the implementation of the Bugzilla
connector.

The functions in this class connect to a Bugzilla data source.  Currently,
we're using a REST API to accomplish this.

Module Functions:
-- get_issues
-- load_from_bugzilla

"Internal" Module Functions:
-- _bz2qz
-- _get_resolve_dt


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

import urllib
import urllib2
import json

from datetime import date
from datetime import timedelta
from time import sleep

from operator import itemgetter
from inspect import currentframe

import issue
import qzutils
import qzmongo


_MODNM = __name__.upper()
# Module name string for formatted printing
_MNS = ''.join([_MODNM, ": "])
# Base Error / Warning Strings
_ERS = ''.join([_MODNM, " ERROR: "])
_WRS = ''.join([_MODNM, " WARNING: "])


# defined here so we don't build a list for each iteration
# Starting list of status values for fixed bugs - I noticed that some
#  bugs that are marked as fixed may have any of these:
#_STAT_RSLVD = ['VERIFIED', 'CLOSED', 'RESOLVED']
_STAT_RSLVD = frozenset(['VERIFIED', 'CLOSED', 'RESOLVED'])



def _get_resolve_dt(bug, verbose):
    """Walks through the issue's history to see if/when it was resolved 
    
    Starting with the most recent history entry, moves backward until it either
    finds when the issue was RESOLVED/FIXED, or it reaches the beginning of
    the history
    
    Returns the resolved date, if found, None, otherwise
    
    Arguments:
    bug -- the issue to examine
    verbose -- print information about the search, default is False
    
    """
    resolution = None
    status = None
    res_dt = None
    if ((not 'history' in bug) or (bug['history'] is None)
                               or (not bug['history'])):
        # there is no history field in this issue OR history has been set to
        #   None OR the history list is empty.  All are distinct
        #   possibilitities
        if verbose:
            sys.stdout.write("{0}No history data for Issue Id #{1}\n"
                             .format(_WRS, _bug['id']))
        return res_dt
    if verbose:
        sys.stdout.write("*** Issue Id #{} ***\n".format(bug['id']))
    for hidx, hist in reversed(list(enumerate(bug['history']))):
        if verbose:
            sys.stdout.write("History record {}:\n".format(hidx))
        for cidx, chg in list(enumerate(hist['changes'])):
            # iterate through the changes for this history record and
            #   look for an indication that the issue was RESOLVED/FIXED
            if (chg['field_name'] == 'status' and chg['added'] in _STAT_RSLVD):
                    status = hist['change_time']
            elif (chg['field_name'] == 'resolution' and
                  chg['added'] == 'FIXED'):
                    resolution = hist['change_time']
            
            if verbose:
                sys.stdout.write("   Change record {}:\n".format(cidx))
                cdntrmstr = "      Could not print 'removed' field: {0}\n"
                if 'removed' in chg.keys():
                    try:
                        # We're not currently supporting unicode, so these
                        #   have caused issues.
                        sys.stdout.write("      Removed: {}\n"
                                         .format(chg['removed']))
                    except Exception as ex:
                        sys.stdout.write(cdntrmstr.format(ex))
                # end removed in keys
                if 'field_name' in chg.keys():
                    try:
                        # We're not currently supporting unicode, so these
                        #   have caused issues.
                        sys.stdout.write("      Field Name: {}\n"
                                         .format(chg['field_name']))
                    except Exception as ex:
                        sys.stdout.write(cdntrmstr.format(ex))
                # end field_name in keys
                if 'added' in chg.keys():
                    try:
                        # We're not currently supporting unicode, so these
                        #   have caused issues.
                        sys.stdout.write("      Added: {}\n"
                                         .format(chg['added']))
                    except Exception as ex:
                        sys.stdout.write(cdntrmstr.format(ex))
                # end added in keys
                if len(chg.keys()) != 3:
                   sys.stdout.write("*** OOPS: Wrong number of keys:  {}\n"
                                    .format(chg.keys()))
            if ((resolution is not None) and (status is not None)): break
        # end iterate through changes
        if ((resolution is not None) and (status is not None)):
            # the issue's resolution is fixed it's status is in the list of
            #   resolved statuses
            # the resolution time is the later of the two times.
            dr = qzutils.mk_datetime(resolution)
            ds = qzutils.mk_datetime(status)
            res_dt = max(ds,dr)
            break
    # end iterate through history
    # if res_dt:
        # print "Issue Resolved/Fixed"
    # else:
        # print "Issue Not Fixed"
    return res_dt


_reuse_issue = issue.Issue()

def _bz2qz(bzbug, organization, rtn_tuple, dstore, verbose=False):
    """Create a new Issue instance with default values for all data
    attributes.  Walk through each dictionary key that we know about in the
    Bugzilla issue and, if it exists, transfer the value to the corrresponding
    instance attribute of the new Issue.
    
    Once the new instance is created, and validated, a named tuple is optionally
    generated that contains the keys & values for the instance's data
    attributes.  This new named tuple is a more memory efficient way to store
    the data, at least for now.
    
    Returns the newly created named tuple, or if directed by the rtn_tuple
    argument, returns the new Issue instance, unless we're storing to db.
    If we're storing, returns True on success, False in the event of
    failure
    
    Arguments:
    bzbug -- the dictionary for the Bugzilla bug
    organization -- str - the name of the organization that "owns" this
                          repository
    rtn_tuple -- if true, return a named tuple, otherwise, return the Issue
                 instance, unless we're storing (see above)
    dstore -- object - data store to use for issues
    verbose -- print diagnostic messages
    
    """
    if rtn_tuple:
        nqbug = _reuse_issue
        nqbug.__init__()
    else:
        nqbug = issue.Issue()

    def attr_exc(keynm):
        # print an appropriate error message if an exception is raised over
        #   the given Bugzilla key names.  Accesses bzbug and verbose from
        #   the parent namespace
        if verbose:
            fstr = ("{0}Attribute: {1} is not present in the Bugzilla\n"
                    "{2}issue dictionary.\n")
            sys.stderr.write(fstr.format(_ERS, keynm, ' '*len(_ERS)))
        # end if verbose
    # end attr_exc

    def cpattr(qattr, bkey, bkey2=None, xform=None):
        # Copies the value for the specified key from the incoming Bugzilla
        #   dictionary item to the corresponding attribute of our issue.
        #   Destination argument is first in the list, following the argument
        #   order of setattr()
        # Arguments:
        #   qattr -- string - name of the attribute in the QZ Issue
        #   bkey -- string - name of the key in the Bugzilla Issue
        #
        #   NOTE:  Both of these are names, not the values.  They could be
        #          the same, if we're transfering values that have the same
        #          name for the respective attribute and key.
        #
        #   bkey2 -- string - optional name of a Bugzilla Issue sub-key.
        #          Default is None, when there is not a sub-key to worry
        #          about
        #   xform -- function - optional function to be applied to the value
        #          obtained from the Bugzilla Issue, before it's assigned
        #          to our issue.  Should take a single argument and return
        #          a single value.  NOTE:  We won't handle exceptions
        #          generated by the transform to avoid masking bugs in
        #          your code.
        #          Default is None
        #
        # Accesses both nqbug & bzbug from the parent namespace, but doesn't
        #   assign directly to either, variable, so no scoping issues
        #
        # No return value.  We expect it to succeed, we're handling
        #   anticipated exceptions, and the callers wouldn't do anything
        #    different if it failed.  No point in the overhead, at this time.
        try:
            bzval = bzbug[bkey] if bkey2 is None else bzbug[bkey][bkey2]
        except KeyError as k:
            attr_exc(k)
        else:
            if xform is not None:
                bzval = xform(bzval)
            setattr(nqbug, qattr, bzval)
        # end of try/except
    # end of cpattr
    
    # Transfer attributes from the incoming bugzilla object
    for atk in vars(nqbug).keys():
        cpattr(atk, atk)
    # end for atk in keys
    
    # No corresponding attribute for the owning organization in the bugzilla
    #   issue
    setattr(nqbug, 'organization', organization)
    
    # Fix attributes that don't transfer directly.  Note that cpattr() handles
    #   KeyError exceptions if the attribute is not present in the bugzilla
    #   issue.  Also, remember that the fields of our issue are initialized,
    #   so we just leave them alone if the transfer fails.  This allows us
    #   to process records with different versions of the issue data fields
    # Field mapping issues:
    cpattr('os', 'op_sys')
    cpattr('ref_url', 'ref')
    # Collapse dictionary layers, need to check both layers
    cpattr('assigned_to', 'assigned_to', 'name')
    cpattr('assigned_to_realname', 'assigned_to', 'real_name')
    cpattr('creator', 'creator', 'name')
    # for some reason, creator_realname is a top level field, it's handled
    #   by the bulk copy above
    cpattr('qa_contact', 'qa_contact', 'name')
    # for some reason, qa_contact_realname is a top level field, it's handled
    #   by the bulk copy above
    # datetime conversions
    crt = 'creation_time'
    cpattr(crt, crt, bkey2=None, xform=qzutils.mk_datetime)
    lct = 'last_change_time'
    cpattr(lct, lct, bkey2=None, xform=qzutils.mk_datetime)
    
    # Attempt to set the resolution date
    try:
        # First, see if resolution is marked as fixed
        resl = bzbug['resolution'] == 'FIXED'
        # Also see if the status is set to one of the resolved statuses
        #   _STAT_RSLVD is defined near the top of this module
        stat = bzbug['status'] in _STAT_RSLVD
    except KeyError as k:
        attr_exc(k)
        # Can't perform the calculation, so set both to False
        resl = False
        stat = False
    # end try/except
    res_dt = None
    if resl and stat:
        # try to find the resolution date
        try:
            res_dt = _get_resolve_dt(bzbug, verbose)
        except KeyError as k:
            res_dt = None
            attr_exc(k)
        # end try/except
    # end if resl & stat
    setattr(nqbug, 'resolved_time', res_dt)
    
    if dstore is not None:
        # Store the new issue
        if qzmongo.saveitem(nqbug.__dict__, dstore, 'id'):
            return True
        else:
            sys.stderr.write("{0}Database Save Failed for ID# {1}!\n"
                             .format(_ERS, nqbug.id))
            return False
    elif rtn_tuple:
        return nqbug.get_ntpl()
    else:
        return nqbug
# end of _bz2qz


def _bz2qz_depr(bzbug, organization, rtn_tuple, dstore, verbose=False):
    """NOTE:  This function has been deprecated.  It should be functionally
    completely replaced by _bz2qz.  However, I'm leaving it here, at least
    temporarily, to provide comparison testing against the replacement
    function.

    Create a new Issue instance with default values for all data
    attributes.  Walk through each dictionary key that we know about in the
    Bugzilla issue and, if it exists, transfer the value to the corrresponding
    instance attribute of the new Issue.
    
    Once the new instance is created, and validated, a named tuple is optionally
    generated that contains the keys & values for the instance's data
    attributes.  This new named tuple is a more memory efficient way to store
    the data, at least for now.
    
    Returns the newly created named tuple, or if directed by the rtn_tuple
    argument, returns the new Issue instance, unless we're storing to db.
    If we're storing, returns True on success, False in the event of
    failure
    
    Arguments:
    bzbug -- the dictionary for the Bugzilla bug
    organization -- str - the name of the organization that "owns" this
                          repository
    rtn_tuple -- if true, return a named tuple, otherwise, return the Issue
                 instance, unless we're storing (see above)
    dstore -- object - data store to use for issues
    verbose -- print diagnostic messages
    
    """
    if rtn_tuple:
        nqbug = _reuse_issue
        nqbug.__init__()
    else:
        nqbug = issue.Issue()
    
    def cpattr(attr):
        # Copies the specified attribute from the incoming bugzilla directory
        # item to the corresponding issue object data attribute
        setattr(nqbug,attr,bzbug[attr])
    # end of cpattr
    
    # Transfer attributes from the incoming bugzilla object
    for atk in vars(nqbug).keys():
        if atk in bzbug:
            cpattr(atk)
        elif verbose:
            fstr = ("Attribute: {0} was not present in Bugzilla bug "
                    "dictionary...\n")
            sys.stdout.write((fstr.format(atk)))
    
    # Fix attributes that don't transfer directly.  Note that we check each key
    #   to see whether it is actually in the Bugzilla dictionary.  This allows
    #   us to process records with different versions of the issue data fields
    # set the owning organization
    setattr(nqbug, 'organization', organization)
    # Field mapping issues:
    if 'op_sys' in bzbug:
        setattr(nqbug, 'os', bzbug['op_sys'])
    if 'ref' in bzbug:
        setattr(nqbug, 'ref_url', bzbug['ref'])
    # Collapse dictionary layers, need to check both layers
    if 'assigned_to' in bzbug and 'name' in bzbug['assigned_to']:
        setattr(nqbug, 'assigned_to', bzbug['assigned_to']['name'])
    if 'assigned_to' in bzbug and 'real_name' in bzbug['assigned_to']:
        setattr(nqbug, 'assigned_to_realname',
                 bzbug['assigned_to']['real_name'])
    if 'creator' in bzbug and 'name' in bzbug['creator']:
        setattr(nqbug, 'creator', bzbug['creator']['name'])
    # for some reason, creator_realname is a top level field
    if 'qa_contact' in bzbug and 'name' in bzbug['qa_contact']:
        setattr(nqbug, 'qa_contact', bzbug['qa_contact']['name'])
    # for some reason, qa_contact_realname is a top level field
    # datetime conversions
    if 'creation_time' in bzbug:
        setattr(nqbug, 'creation_time',
                qzutils.mk_datetime(bzbug['creation_time']))
    if 'last_change_time' in bzbug:
        setattr(nqbug, 'last_change_time',
                qzutils.mk_datetime(bzbug['last_change_time']))
    
        # Attempt to set the resolution date
    # _STAT_RSLVD is defined near the top of this module
    if ((bzbug['resolution'] == 'FIXED') and (bzbug['status'] in _STAT_RSLVD)):
        # try to find the resolution date
        res_dt = _get_resolve_dt(bzbug, verbose)
        setattr(nqbug, 'resolved_time', res_dt)
    else:
        setattr(nqbug, 'resolved_time', None)
    
    if dstore is not None:
        # Store the new issue
        if qzmongo.saveitem(nqbug.__dict__, dstore, 'id'):
            return True
        else:
            sys.stderr.write("{0}Database Save Failed for ID# {1}!\n"
                             .format(_ERS, nqbug.id))
            return False
    elif rtn_tuple:
        return nqbug.get_ntpl()
    else:
        return nqbug
# end of _bz2qzo






def load_from_bugzilla(query_url, verbose=False):
    """Attempt to read the issue data at the query URL. This function also
     handles the JSON processing
    
    Returns a list of Bugzilla format issues.  Returns None if there were any
    problems
    
    Arguments:
    query_url -- String containing the full URL for the query
    verbose -- print information about processing, default is False
    
    """
    max_rpt = 3
    try_cnt = 0
    retry_tm = 60
    bugz = None
    resp = None
    while ((resp is None) and (try_cnt < 3)):
        # REST is notoriously unreliable, so we'll try 3 times to make the
        #   query
        if try_cnt > 0:
            fstr = ("NOTE:  Attempt #{0} to retrieve (in {1} seconds...) "
                    "from:\n       {2}\n")
            sys.stdout.write(fstr
                             .format(try_cnt+1, try_cnt*retry_tm, query_url))
            # wait a bit to see if we can make the connection
            sleep(try_cnt*retry_tm*1.0)
        # end try_cnt > 0
        resp = qzutils.restful_get(query_url, verbose)
        try_cnt += 1
    # end while
    if resp is not None:
        if isinstance(resp,dict):
            if ((len(resp) == 1) and ('bugs' in resp)):
                # More than one bug was returned, so strip the dictionary to
                # get at the list of bugs
                bugz = resp['bugs']
            else:
                # Only one bug was returned, so this is the issue dictionary,
                # so we need to make it into a list
                bugz = [resp]
            if verbose:
                sys.stdout.write("Retrieved {0} issue(s)!\n"
                                 .format(len(bugz)))
        else:
            fstr = "{0}JSON conversion failed to produce usable data\n"
            sys.stderr.write(fstr.format(_ERS))
        # end we got back a dictionary (or a list)
    # end if resp is not None
    return bugz
# end load_from_bugzilla


def get_issues(base_url, query, organization, rtn_tuple,
               dstore, verbose=False):
    """Generates a query URL, makes the request, transforms the Bugzilla
    issues.  If dstore is not None, stores the transformed issues in the
    local database.
    The query URL is built up as a list of components that are joined before
    the HTTP request is made
    
    Returns a list of Issue tuples, unless dstore is not None.  If dstore has
    a value, tranformed issues will be stored in the specified db and the
    number of issues downloaded will be returned as a single element list
    to indicate success.
    Returns None if there were any problems
    
    Arguments:
    base_url -- str - the root URL for the query
    query -- list - the query, which is a list whose first element describes
                the type of query to run.  Subsequent elements of the list
                depend on the query type, as follows:
            ALL - no need for subsequent members
            ISSUE_LIST - subsequent members are issue ID numbers
            ISSUE_RANGE - 2 subsequent members, the first is start #, the
                last is end #
            DATE_RANGE - 2 subsequent members, Start Date and End Date.
                these are both strings with the exact format: YYYY-MM-DD
                For example:  2013-05-11
                NOTE:  Since we can't know how many issues are present in
                    a given date range, too broad of a range is likely to
                    result in an exception, since the Bugzilla REST
                    API will fail if too many records are requested in
                    one GET
    rtn_tuple -- if true, return a named tuple, otherwise, return the Issue
                 instance, unless we're storing in which case this arg is
                 a no-op
    dstore -- object - data store to use for issues
    organization -- str - the name of the organization that "owns" this
            repository
    verbose -- print information about processing, default is False
    
    """
    # Constants for composing query URLs
    BUG_QUERY = frozenset(['ALL', 'ISSUE_LIST', 'ISSUE_RANGE', 'DATE_RANGE'])
    # Avoid hitting server / HTTP limits on data returned
    MAX_BLOCK_RANGE = 500
    # Make sure we don't exceed maximum # of characters in HTTP string
    MAX_BLOCK_IDS = 250
    # Constants for forming query strings
    CR_DT_Q_STR = 'f1=creation_ts&o1=substring&query_format=advanced&v1={0}'
    QS_FLDS = '&include_fields=_default,history'
    
    if base_url[-1] != '/':
        # the base URL is not slash terminated.
        base_url = ''.join([base_url,'/'])
    qsbase = [base_url]
    # qzlst will contain the list of named tuples representing this
    #   query's results, if we're returning tuples/issues. It will hold a
    #   running count of the number of issues downloaded if we're
    #   directly storing records
    if dstore is not None:
        qzlst = [0]
    else:
        qzlst = []
    
    
    def _cvt_add_store(bzbugz, organization, rtn_tuple, dstore, verbose):
        # Walk through a list of Bugzilla format bugs and convert each into a
        #   a new QZ issue.  This new issue may:
        #      1. Be stored in the specified datastore, if dstore is not None.
        #   or, if dstore is None:
        #      2. Be added to a list of converted issues that is maintained by
        #         the parent function - if rtn_tuple is False
        #      3. Be additionally transformed into a named tuple which is then
        #         added to the list of converted issues that is maintained by
        #         the parent function - if rtn_tuple is True.
        #
        # Returns True, if successful.  Success is defined as either at least
        #   one issue is stored, or at least one issue/tuple was added to the
        #   issue list.  Returns None otherwise.
        #
        # Arguments:
        #   bzbugz -- List of Bugzilla format bugs
        #   organization -- str - the name of the organization that "owns" this
        #           repository
        #   rtn_tuple -- if true, return a named tuple, otherwise, return the
        #           Issue instance
        #   dstore -- object - data store to use for issues
        #   verbose -- print information about processing, default is False
        
        retval = None
        if (bzbugz is not None) and bzbugz:
            # The bugzilla bug list is not none, and it is not empty. We have
            #   something to provess
            if dstore is not None:
                # Bzbugz is not empty, so we'll iterate through it
                for bug in bzbugz:
                    # store bug
                    stored = _bz2qz(bug, organization, rtn_tuple,
                                   dstore, verbose)
                    if ((retval is None) and stored):
                        # The first time that we successfully store an object,
                        #   we'll set retval to true.  Once retval has a value
                        #   we won't need to execute this again.  It doesn't
                        #   matter, at this level, whether subsequent stores
                        #   succeed, or fail.
                        retval = True
                # end for bug in bzbugs
                qzlst[0] += len(bzbugz)
            else:
                # We wont be storing, lets do the conversion and extension of
                #   the bug list.
                # Sort the incoming bug list
                bzbugz.sort(key = lambda bug: bug['id'])
                # Add the converted issues to the running list. We create
                qzlst.extend([_bz2qz(bug, organization, rtn_tuple, None,
                                     verbose)
                              for bug in bzbugz])
                retval = True
            # end if dstore / else
        #end if bzbugz list has something in it
        
        return retval
    # end _cvt_add_store
    
    def _get_bugs(count, max_get_block, urlbase, start, ilist, organization,
                  rtn_tuple, dstore, verbose):
        # Construct a query URL and execute the GET REST request.
        # If ilist is not None, request the issues in the list
        #   in appropriately sized batches.
        # Otherwise, use range queries.
        #
        # Returns True, if successful, None otherwise.  Success means at
        #   least one record added to qzlst.  No issue data returned
        #   because this function either stores the data, or directly extends
        #   the qzlst with newlygenerated named tuples / objects
        # Arguments:
        #   count -- last of the records to retrieve.  This is equired because
        #           ilist could be None.  Note that if start = 1, this will
        #           be the count of the records to retrieve, hence the name.
        #   max_get_block - max # of issues to request in each request.
        #           different types of requests may have different limits
        #           due to constraints from the server and URL string max
        #           lengths
        #   urlbase -- str - The base URL composed prior to this call.
        #   start -- starting point for range queries, 1 for everything else
        #   ilist -- list of issue ids.  If this is None, this function
        #           will generate a list of ids from 1 to count
        #   organization -- str - the name of the organization that "owns" this
        #           repository
        #   rtn_tuple -- if true, return a named tuple, otherwise, return the
        #           Issue instance, unless we're storing, then this argument
        #           is a no-op
        #   dstore -- object - data repository to store new items in
        #   verbose -- print information about processing, default is False
        
        rtn_val = None
        # start is an arg, but a local reference is made in this function,
        #   so we can modify it to operate the loop
        # end is the final element index for each loop iteration
        end = min((max_get_block + start -1), count)
        while start <= count:
            # initialize the first member of the list of query URL components
            qsl = [urlbase]
            if ilist is None:
                # generate an appropriate range of ids & add it to the
                #   query component list
                qst1 = 'f1=bug_id&o1=greaterthan&v1={0}&'
                qst2 = 'f2=bug_id&o2=lessthan&v2={1}'
                qsl.append(''.join([qst1,qst2]).format(start-1,end+1))
            else:
                # generate an appropriate list of ids as strings from
                #   the ids in the slice we're interested in & append it
                #   to the url component list
                qsl.append(','.join([str(idx) for idx in ilist[start-1:end]]))
                #Query URL: https://api-dev.bugzilla.mozilla.org/latest/bug?id=35,37,39,41,43&include_fields=_default,history
            # Append the field specification
            qsl.append(QS_FLDS)
            fstr = ("...Attempting to retrieve issues #{0} - #{1} from "
                    "Bugzilla\n")
            sys.stdout.write(fstr.format(start,end))
            # Get the issues from Bugzilla.
            bzbugs = load_from_bugzilla(''.join(qsl), verbose=verbose)
            # convert new issues and either store, or add to the list
            rval = _cvt_add_store(bzbugs, organization, rtn_tuple, dstore,
                                  verbose)
            # If we got back an ok status, set our return value to True
            if ((rval is not None) and (rtn_val is None)):
                # the first time that this call succeeds, we need to set
                #   rtn_val to True.  Once true, it indicates that at least
                #   one call succeeded, so we don't keep setting it.
                rtn_val = True
            # no worries, should be immutable
            start = end + 1
            end = min(end+max_get_block, count)
        # end while
        return rtn_val
    # end _get_bugs
    
    def _get_bugs_by_date(urlbase, dt_range, organization,
                  rtn_tuple, dstore, verbose):
        # Construct a query URL and execute the GET REST request.
        #
        # Goes through the specified date range a day at a time and requests
        #   each day's issues.  This helps get around the limits on how many
        #   records can be returned with a single request.
        #
        # Returns True, if successful, None otherwise.  Success means at
        #   least one record added to qzlst.  No issue data is returned
        #   because this function either stores the data, or directly extends
        #   the qzlst with newly generated named tuples / objects
        # Arguments:
        #   urlbase -- str - The base URL composed prior to this call.
        #   dt_range -- list containing start & end dates for the query
        #           formatted as: ['2013-03-12', '2013-06-12']
        #   organization -- str - the name of the organization that "owns" this
        #           repository
        #   rtn_tuple -- if true, return a named tuple, otherwise, return the
        #           Issue instance, unless we're storing, then this argument
        #           is a no-op
        #   dstore -- object - data repository to store new items in
        #   verbose -- print information about processing, default is False
        #
        # just for fun, let's make sure that the list is in the right order so
        #   that we can walk through the dates by incrementing the day. Also
        #   convert to datetime, so that we can do timedelta arithmetic easily
        #
        start = qzutils.mk_datetime(min(dt_range))
        end = qzutils.mk_datetime(max(dt_range))
        
        rtn_val = None
        ddelt = timedelta(1)
        cday = start
        dcnt = 0
        while cday <= end:
            # initialize the first member of the list of query URL components
            #   We build a new query for each loop iteration
            qsl = [urlbase]
            # we'll use this value again when we print progress
            dtstr = qzutils.mk_dtstr(cday)
            qsl.append(CR_DT_Q_STR.format(dtstr))
            qsl.append(QS_FLDS)
            # Get the issues for the given day from bugzilla, convert them
            #   to our named tuple format and add them to the list.  We know
            #   that we want rtn_tuple to be true,
            
            # print the date currently retrieved to give them some sense of
            #   progress.
            if dcnt == 0:
                sys.stdout.write("Retrieving...")
            sys.stdout.write(dtstr)
            sys.stdout.flush()
            if dcnt == 6:
                # after 7 days, start a new line
                sys.stdout.write("\n")
                dcnt = 0
            else:
                sys.stdout.write(",")
                sys.stdout.flush()
                dcnt += 1
            # Get the issues from Bugzilla.
            bzbugs = load_from_bugzilla(''.join(qsl), verbose)
            # convert new issues and either store, or add to the list
            rval = _cvt_add_store(bzbugs, organization, rtn_tuple, dstore,
                                  verbose)
            # rval = _cvt_tuple_add(load_from_bugzilla(''.join(qsl),
            #                                         verbose=verbose),
            #                      organization, _RTN_TUPLE, verbose)
            # Query URL: https://api-dev.bugzilla.mozilla.org/latest/bug?f1=creation_ts&o1=substring&query_format=advanced&v1=2013-06-08&include_fields=_default,history'
            if ((rval is not None) and (rtn_val is None)):
                # the first time that this call succeeds, we need to set
                #   rtn_val to True.  Once true, it indicates that at least
                #   one call succeeded, so we don't keep setting it.
                rtn_val = True
            cday += ddelt
        # end while cday not at end
        sys.stdout.write("\n")
        return rtn_val
    # end _get_bugs_by_date
    
    def _get_max_id(urlbase, verbose):
        # Attempt to find the highest issue ID in the repository.
        # Start with today's date, and work backwards until we find a
        #   day with bugs submitted, then sort the list and grab the
        #   last one.
        # Return the largest ID value found, or None, if no issues are
        #   found within the specified period
        # Argument:
        #   urlbase -- string representing the base URL composed prior to
        #           this call.
        #   verbose -- print information about processing, default is False
        
        max_id = None
        cday = date.today()
        ddelt = timedelta(1)
        for dd in range(90):
            dtstr = cday.strftime('%Y-%m-%d')
            dt_url = ''.join([urlbase, CR_DT_Q_STR.format(dtstr)])
            cday_bugz = qzutils.restful_get(dt_url, verbose)
            if cday_bugz is not None:
                # we got issues back, let's strip out the issue list
                cday_bugz = cday_bugz['bugs']
            if ((cday_bugz is not None) and cday_bugz):
                # There are issues reported on the current day,
                #   cday_bugz isn't None, and it's not an empty list
                cday_bugz.sort(key=itemgetter('id'))
                max_id = cday_bugz[-1]['id']
                break
            else:
                # It appears that no bugs were filed on cday, go back a day
                #   earlier
                cday -= ddelt
            # end if cday_bugz
        # end for 90 days
        return max_id
    # end of _get_max_id
    # ------------------
    # BODY of get_issues
    q_success = None
    if query[0] in BUG_QUERY:
        # query by issue ID
        qsbase.append('bug?')
        if query[0] == 'ALL':
            # We're going to go for them all, so we need to find out how many
            max_id = None
            max_id = _get_max_id(''.join(qsbase), verbose)
            if max_id is None:
                fstr = ("{0}No issues filed within 90 days of {1}.\n"
                        "{2}Cannot determine highest Issue ID, will use "
                        "repository\n{2}issue count instead.\n")
                dtstr = date.today().strftime('%Y-%m-%d')
                sys.stdout.write(fstr.format(_WRS, dtstr, ' '*len(_WRS)))
                cnt_url = None
                cnt_url = ''.join([base_url, 'count'])
                max_id = qzutils.restful_get(cnt_url, verbose)
            if max_id is not None:
                # not simply an else of the above, because the above
                #   conditional might have defined max_id, so we need
                #   to actually test again here.
                q_success = _get_bugs(max_id, MAX_BLOCK_RANGE, ''.join(qsbase),
                                      1, None, organization, rtn_tuple, dstore,
                                      verbose)
            else:
                fstr = ("{0}Could not determine highest Issue ID # for:\n"
                        "{2}   {1}\n{2}Unable to continue.\n")
                sys.stderr.write(fstr.format(_ERS, ''.join(qsbase),
                                             ' '*len(_ERS)))
        # end of if 'ALL'
        elif query[0] == 'ISSUE_RANGE':
            # Ensure that the range boundaries are ordered min,max.  Then
            #   figure out the size of the range
            qmin = min(query[1:])
            qmax = max(query[1:])
            cnt = qmax - qmin + 1
            if cnt >= 1:
                q_success = _get_bugs(qmax, MAX_BLOCK_RANGE,
                                      ''.join(qsbase), qmin, None,
                                      organization, rtn_tuple, dstore,
                                      verbose)
        elif query[0] == 'ISSUE_LIST':
            qsbase.append('id=')
            # the first element of the list is the type of query, so we
            #   actually have len -1 elements to process
            cnt = len(query) - 1
            if cnt >= 1:
                q_success = _get_bugs(cnt, MAX_BLOCK_IDS, ''.join(qsbase),
                                      1, query[1:], organization, rtn_tuple,
                                      dstore, verbose)
        elif query [0] == 'DATE_RANGE':
            # Get the issues within the date range from bugzilla, convert them
            #   and, if we're not storing issues, add them to the list.
            q_success = _get_bugs_by_date(''.join(qsbase), sorted(query[1:]),
                                          organization, rtn_tuple, dstore,
                                          verbose)
        else:
            fstr = ("{0}Unrecognized query specifier '{1}'.  "
                    "Terminating\n")
            sys.stderr.write(fstr.format(_ERS, query[0]))
            return None
    else:
        fstr = ("{0}Unrecognized query specifier '{1}'.  "
                "Terminating\n")
        sys.stderr.write(fstr.format(_ERS, query[0]))
        return None
    
    if q_success and dstore:
        # If successful, and we're storing, return download count
        return qzlst
    elif ((not dstore) and (qzlst is not None) and qzlst):
        # If successful, return the list of issue tuples
        if q_success is None:
            fstr = ("{0}Code failed, Query Success Flag not set, but list"
                    " of\n{3}new records has members.\n"
                    "{3}Module: {1} Line: {2}\n")
            sys.stderr.write(fstr.format(_ERS, __file__, 
                                         currentframe().f_lineno,
                                         ' '*len(_ERS)))
        return qzlst
    else:
        return None
# end get_issues
