#!/usr/bin/env python
"""qzmain.py is the main executable module for the QZ product.

CMD LINE USAGE:  qzmain.py [-h] [-man | -C ConfigFile]

Optional Arguments:
  -h, --help            show this help message and exit
  -man                  Display the man page for the program
  -C ConfigFile         The pathname of a configuration file


qzmain.py analyzes a given data set and reports the results.  If directed,
it will extract the specified data from an external repository.

qzmain is responsible for setting up the run, calling the appropriate
connectors / analysis packages (if specified) and, finally, calling the
routines to display the results.

All program configuration directives are set in the config file.  You can
use the default config file ('./.bz.cfg'), or specify '-C cfgpath' to
designate a particular configuration file.


Configuration files have the following format:

[section]
option=value
...


For example:

[Query]
query = RANGE
range = 295111,415333
organization = Mozilla
base_url = https://api-dev.bugzilla.mozilla.org/latest

[Database]
database = bugzilla
collection = issues

[Metrics]
m_all = off
m_ttr = on
m_mdr = on
m_ddr = on

[Dashboard]
dashpath = ../../tst/


Section and option names are set by the program.  Option values are the
responsibility of the user.  However, values for the query option come
from a fixed set, as described below.


Query Section:

'query' - values can be one of the following: { ALL | LIST | RANGE | DATE }

    ALL      Process ALL available issues
    LIST     Process the issues with the specified id numbers. The list of
             issues is provided in an option named 'list'
       'list' - list of integer id values, separated by commas, to be
                 processed.
                 Example:  query = LIST
                           list = 8008,37,39,386,486,32032
    RANGE    Process the range of issues.  The range endpoints are provided
             in an option named 'range'
       'range' - pair of integer id values, separated by a comma, giving
                 the id boundaries of the range of issues to process.
                 Example:  query = RANGE
                           range = 295111,415333
    DATE     Extract issues within a date range. The date endpoints are
             provided in an option named 'date'
       'date' - pair of date values, separated by a comma, giving the date
                 boundaries of the range of issues to process.
                 Dates are specified in YYYY-MM-DD format.
                 Example:  query = DATE
                           date = 2009-03-31,2013-09-03

'organization' - value is the name of the entity to be associated with the
                 issues

'base_url' - value is the URL for the RESTful interface that is to be
             accessed for source data.  If this option/value pair is
             missing, or if the value is 'nodnld', no data will be
             downloaded.  Data already in the qz database that matches
             the query critieria will be analyzed


Database Section:

'database' - value is the name of the database that stores qz data

'collection' - value is the name of the collection in the database that
               is to be used for this session

             NOTE:  Both 'database' and 'collection' must be specified if
                    you want to work with the database for store/retrieve.
                    Exclude both of these key/value pairs from your
                    config file if you wish to only download from the
                    RESTful interace and do not want to store the
                    downloaded data.


Metrics Section:

    boolean values: 'on' to run the specific analysis, 'off' to skip it.
                    Note: true|false, 1|0, yes|no will also work

'm_all'      Run ALL metrics
'm_ttr'      Run Time to Resolve
'm_ddr'      Run Daily Discovery Rate
'm_mdr'      Run Monthly Discovery Rate
'm_ydr'      Run Yearly Discovery Rate


Dashboard Section:

'dashpath' - value is the filesystem pathname of the directory to receive
             the HTML dashboard page.  Specify 'nodash' as the value
             (or comment out/remove the <tt>dashpath</tt> option value pair)
             to skip dashboard generation.

             As a security precaution, the HTML dashboard's filesystem
             location is fixed when the application is running as a service.
             However, the 'nodash' value will be effective.


Option/Value pair lines can be commented out with the '#' character.
These lines are then ignored by the config file parser.  Please don't
specify an option without a corresponding value.

NOTES:
(1) - All configuration information is specified in the configuration file.
(2) - The pathname to the config file must either be relative to the
      current working directory, or be fully qualified.
(3) - If you don't have an external source for issues, you must have a
      database containing issue information.

Example: 'qzmain.py -C ../../cfgs/configfile.cfg'


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

# Since this is the main module, the docstring is used to generate the man
#   page.  We'll document module functions in this comment block:
#
# EXTERNAL FUNCTIONS:
#   run_qz - the main function in this module
#
# Internal Functions:
#   _analyze_scan
#   _display_dash
#   _dnld_data
#   _gen_dash
#   _gen_man_page
#   _run_scan
#   _setup_query
#

__author__ = "Dean Stevens"
__copyright__ = "Copyright 2013, Quality Zen, LLC; Assigned to Grip QA"
__license__ = "Apache License, Version 2.0"
__status__ = "Prototype"
__version__ = "0.01"


import sys
import os
import string
# --
import urllib
import urllib2
import json
import webbrowser

from datetime import date
from datetime import datetime
from subprocess import call
from collections import namedtuple

import issue
import qzmongo
import bzconn
import qzargs
import qscan
import qlytics
import qzchart


# Some constants for execution:

# Maps query type from the arguments to query type for the bugzilla
#   connector
_BZ_QUERY_MAP = {'ALL':'ALL', 'RANGE':'ISSUE_RANGE',
                'LIST':'ISSUE_LIST', 'DATE':'DATE_RANGE'
                }
# Verbose execution, prints LOTS of extra info
_VERBOSE = False
# Prints a little bit of extra info to help diagnose problems with args
#   / queries
_DIAGNOS = False
# Are we running on the desktop, or as a server.  Note that this variable
#   gets reset in the __main__ body, if we're running on the desktop.
_AS_FXN = True


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
_RTN_TPL = True


# Named tuple to contain return values from _query_scan()
QScnRtn = namedtuple('QscnRtn',['scn_ok','qcurs'])


def _gen_man_page(printit=True):
    # Generates a string that documents this program
    # Returns a printable string representing the documentation for
    #   this program.
    # Arguments:
    #   printit - If True, this function prints the string before returning
    #
    # Indent non-heading text by this # of spaces
    inds = ' '*3
    # start the list of "lines"
    man_lns = ["\nNAME:"]
    # Get the docstring for this module and split it into "lines"
    docs = __doc__
    ss = string.split(docs,'\n')
    # Generate a new list with the desired indentation for each line
    sss = [''.join([inds,ln]) for ln in ss]
    # add the docstring's title line to the running list of lines
    man_lns.extend(sss[:1])
    man_lns.append("\nFILE:")
    man_lns.append("{0}{1}".format(inds, os.path.abspath(__file__)))
    man_lns.append("\nDESCRIPTION:")
    
    # print __doc__
    # add the remaining lines of the docstring to the list
    man_lns.extend(sss[1:])
    # final data items
    man_lns.append("DATA:")
    man_lns.append("{0}Author:    {1}".format(inds, __author__))
    man_lns.append("{0}Copyright: {1}".format(inds, __copyright__))
    man_lns.append("{0}License:   {1}".format(inds, __license__))
    man_lns.append("{0}Status:    {1}".format(inds, __status__))
    man_lns.append("{0}Version:   {1}".format(inds, __version__))
    
    man_lns.append("")
    # join all of the list elements back into a string, separated by newline
    ret_str = string.join(man_lns,'\n')
    if printit:
        sys.stdout.write(ret_str)
    return ret_str
# end _gen_man_page


def _analyze_scan(mets, scores):
    """Runs through the list of scanners and triggers the analyze method
       in each.  Also, gets the "norm" data and.  Finally, fills out the
       scores dictionary with the results of the run
    
    No return value
    
    Arguments:
    mets  -- list - of metrics scanners to run
    scores -- dictionary - will contain the results of running the metrics
    """
    
    ndict = qlytics.get_norms()
    for scnr in mets:
        scnr.analyze()
        # if scnr.id in qscan.CHARTSCN:
            # for now, we're just doing DDR, and TTR, otherwise
            #   we have to scale everything
        if scnr.id in {'DDR','TTR'}:
            # we need to get the score data,
            # Make sure that the scanner has what we need,
            # First, get a list of the keys
            alst = vars(scnr).keys()
            if (('avg' in alst) and ('stdev' in alst)):
                # the data attributes that we need are there
                # start filling out the score dictionary, first for
                #   the scanner, item[0] is the norm, item[1] is the
                #   metric
                scores[scnr.id] = [ndict[scnr.id]]
                scores[scnr.id].append(scnr.avg)
                # next for the standard deviation
                sdky = ''.join([scnr.id, 'SD'])
                scores[sdky] = [ndict[sdky]]
                scores[sdky].append(scnr.stdev)
            # end avg & stdev in attributes
        # end it's a scanner we're interested in
        scnr.dump_state(printit=True)
    # end for scnrs
# end _analyze_scan


def _display_dash(hpath):
    """Attempts to bring up the results dashboard in the default browser
    
    Returns a completion status - 0 if the display seems to have succeeded, 
                                  1 otherwise
    
    Arguments:
    hpath -- string - the filesystem pathname to the dashboard html file
    
    """
    
    osp = "The pathname for the html file is:\n"
    html_up = False
    fhpath = hpath
    if hpath is not None:
        fhpath = os.path.abspath(hpath)
        if fhpath is not None:
            crv = 1
            wrv = False
            if sys.platform == 'cygwin':
                # cygwin will make the call out to windows, and
                #   get all of the pathname conversion stuff right
                #   AFAIK there isn't a cygwin browser that we could
                #   access directly
                crv = call(["cygstart", fhpath])
            else:
                # on posix platforms, we need to prepend the file:///
                #   and send it along to the default browser
                bpath = ''.join(['file:///', fhpath])
                wrv = webbrowser.open(bpath)
            # end not cygwin
            if crv == 0 or wrv:
                fstr = ("{0}A dashboard of results should be showing in "
                        "your browser.\n{3}{1}{3}{2}\n\n")
                sys.stdout.write(fstr.format(_MNS, osp, fhpath,
                                             ' '*len(_MNS)))
                html_up = True
            # we might be displaying results
        # end fhpath is something
    # end hpath is something
    if not html_up:
        fstr = ("{0}Unable to display html file in your browser.\n"
            "{3}{1}{3}{2}\n\n")
        if fhpath is None:
            fhpath = "'Unknown'"
        sys.stderr.write(fstr.format(_ERS, osp, fhpath, ' '*len(_ERS)))
    # end of html_up
    return 0 if html_up else 1
# end _display_dash


def _dnld_data(theargs, query, clxn, cnctor):
    """Applies the specified query to the external data source and
    either stores the results in the DB, or returns a list of the
    issues / tuples that were downloaded
    
    Returns dndata, which, after the query will have one of three
    possible states:
        1. It will be set to a list of issues, if we don't have a db
        2. It will be set to the number of records downloaded, if we
           succeeded in the query, but stored everything in the local
           database
        3. It will be None, if there was a problem with the download
    
    Arguments:
    theargs -- argument object - contains the configuration info
    query -- list - contains the processed query specification
    clxn -- MongoDB Collecction object - basically, the DB we'll be using
    cnctor -- string - module name of the connector to use for extraction
    
    """
    
    dndata = None
    try:
        qurl = theargs.base_url
    except AttributeError:
        # They didn't specify the base URL in the configuration file
        qurl = None
    # end try/except
    if ((qurl is not None) and (qurl.lower() != qzargs.SKIP_DNLD)):
        # They've specified a base url so we will attempt to extract
        #  something from the REST interface
        #
        dndata = eval(cnctor).get_issues(qurl, query, theargs.organization,
                                  _RTN_TPL, clxn, verbose=_VERBOSE)
        if dndata is not None:
            # We got something back, let's see how many issues we downloaded
            rtrvcnt = dndata[0] if (clxn is not None) else len(dndata)
        else:
            rtrvcnt = 0
        sys.stdout.write("{0}Downloaded {1} issues\n".format(_MNS, rtrvcnt))
    else:
        fstr = ("{0}As directed, no issues will be downloaded.\n"
                "{1}Proceeding to analysis.\n")
        sys.stdout.write(fstr.format(_NTE, ' '*len(_NTE)))
    # end the URL isn't None, or skip download
    
    return dndata
# end _dnld_data


def _gen_dash(orgarg, hpath, scores, dbcurs, dndata):
    """Generates the html file containing the dashboard for this run
    
    Returns a relative pathname to the created html dashboard, if successful,
        Otherwise, returns None.
    
    Arguments:
    orgarg -- string - name of the organization from the argument object
    hpath -- string - pathname to directory that will receive the html
               dashboard file
    scores -- dictionary - contains the results of running the metrics
    dbcurs -- cursor object - iterator for the query results returned from
               the query on the db
    dndata -- if we don't have a db, we might have a list of results
               returned from the download
    
    """
    
    if _AS_FXN:
        # running as a server, so we'll force create_chart to
        #  generate a relative HTML url
        org = None
        hpath = None
    else:
        # Running on the commandline
        # Try to figure out an organization name
        #    First preference is if there is an organization in config
        org = None
        if orgarg is not None:
            org = orgarg
        elif dbcurs is not None:
            dbcurs.rewind()
            try:
                org = dbcurs.next()['organization']
            except KeyError:
                org = None
        elif dndata is not None:
            try:
                org = dndata[0].organization
            except (TypeError, AttributeError):
                org = None
        else:
            org = None
        # end of org stuff
    # end fxn or cmdline

    # Attempt to generate the path & return the results
    return qzchart.create_chart_htm(org, hpath, scores,
                                    qlytics.calc_goodness(scores))
# end _gen_dash


def _query_scan(mets, query, clxn, dndata):
    """ Query the database, or if we don't have a db, try to work with the
        downloaded issues.  Run the scan on the appropriate collection of
        issues.  This function both determines which collection to process,
        and actually does the scanning
    
    Returns a QScnRtn tuple which contains a boolean indicating success of
        Query/Scan and a MongoDB cursor (iterator) which will be valid  if
        we successfully queried a db and None otherwise
    
    Arguments:
    mets -- list - of metrics scanners to run
    query -- list - contains the query specification
    clxn -- MongoDB Collecction object - basically, the DB we'll be using
    dndata -- if we don't have a db, we might have a list of results
               returned from the download
    
    """
    # --- Convenience Methods
    def runscan(objd, scnmets):
        # Convenience method to run the selected metrics scanners on an
        #   object
        #
        # Returns True if the scanner succeeded, False if there were any
        #   errors
        #
        # Arguments:
        #   objd -- dict - the dictionary object to be processed by the
        #                  scanner(s)
        #   scnmets -- list of the metrics scanner objects to run on each
        #              object
        rval = True
        for scnr in scnmets:
            if not scnr.proc_data(objd) and rval:
                # The first time proc_data() fails, this run will return
                #   False
                rval = False
        # end for scnr
        return rval
    # end of runscan
    # ------------
    
    dbcurs = None
    # Will be set to True if at least one scan succeeded, which implies
    #   that either the query succeeded, or there was something to
    #   analyze in dndata
    scn_ok = False
    if clxn is not None:
        # we have a database, initiate a query, getting back (hopefully)
        #  a pymongo cursor
        dbcurs = qzmongo.querydb(query, clxn, mongo_curs=True)
        if dbcurs is not None:
            # we seem to have executed a successful query
            for dobj in dbcurs:
                # iterate the cursor and run the scanner(s) on each object
                if (runscan(dobj, mets) and not scn_ok):
                    # Set to True the first time we have a successful
                    #    scan run
                    scn_ok = True
            # end for dobj
        # end if dbcurs is not None
    else:
        # No database, let's see if we have anything in dndata
        if dndata is not None:
            # We have results in the form of a list of downloaded items
            for ditem in dndata:
                if _RTN_TPL:
                    # We're have issue tuples, need to convert to dicts
                    rscn = runscan(ditem._asdict(), mets)
                else:
                    # We have QZ issue objects, need to convert to dicts
                    rscn = runscan(ditem.__dict__, mets)
                if rscn and not scn_ok:
                    # Set to True the first time we have a successful
                    #    scan run
                    scn_ok = True
            # end for ditem
        # end if dndata
    # end clxn not None
    return QScnRtn(scn_ok, dbcurs)
# end _query_scan


def _setup_query(theargs):
    """Generates a query specifier from the config information in theargs
    
    Returns a query specifier that can drive both downloads and analysis
    
    Arguments:
    theargs -- argument object - contains the configuration info
    
    """
    
    # Bundle up the arguments for the query
    #   First, figure out which type of we're making
    #   Look up the query specifier and make it a list
    query = [_BZ_QUERY_MAP[theargs.query]]
    #   Then add the Issues list
    query.extend(theargs.issues)
    if _DIAGNOS:
        # Display the configuration
        indt = ' '*4
        sys.stdout.write("\n")
        osl = ["Specified Configuration:"]
        osl.append("{0}Query:   {1}".format(indt, query))
        osl.append("{0}BaseURL: {1}".format(indt, theargs.base_url))
        osl.append("{0}DBase:   {1}".format(indt, theargs.database))
        osl.append("{0}Collexn: {1}".format(indt, theargs.collection))
        osl.append("{0}Org:     {1}".format(indt, theargs.organization))
        osl.append("{0}Verbose: {1}".format(indt, _VERBOSE))
        osl.append("")
        osl.append("")
        sys.stdout.write("\n".join(osl))
    # end if _DIAGNOS
    
    return query
# end _setup_query


def run_qz(theargs, verbose = False):
    """Given an argument object, actually runs the body of the QZ analysis
    
    Returns a completion status - 0 if everything was good.
    
    Arguments:
    theargs -- argument object containing the configuration info
    verbose -- print diagnostics, default is False
    
    """
    
    # This  function manages 4 tasks:
    #  1. If a URL is specified in the config file, attempt to download the
    #      specified data from the RESTful interface at the URL.
    #      Note:  The function can work fine without downloading, as long
    #             as it is given a "local" database to read from.  Conversely,
    #             it can work without a database, as long as there is data
    #             to download.  One, or the other, or both, is/are required.
    #  2. If a database is specified in the config file, records will be
    #     stored in the specified database as they are downloaded (better
    #     support for unreliable http connections - at least we'll have some
    #     of the data stored if we lose the connection
    #     NOTE:
    #      a) If we have a database, analysis will be performed on records
    #         retrieved from the db.  We assume that the records were either
    #         downloaded and stored, or already present in the database.
    #      b) If we do not have a database, the download function will be
    #         directed to return a list of issues that can be passed to the
    #         analysis section
    #  3. Perform the analyses specified in the metrics section of the
    #     config file.  See #2 above for a discussion of the data source for
    #     the analyses.
    #  4. Generating the html "score" page, and displaying it, if possible
    
    # After the query, dndata will have one of three states:
    #  1. It will be set to a list of issues, if we don't have a db
    #  2. It will be set to the number of records downloaded, if we succeeded
    #     in the query, but stored everything in the local database
    #  3. It will be None, if there was a problem with the download
    dndata = None
    # Will contain a list of query elements, created from information in the
    #   config file.
    query = None
    # We'll decrement retval and return it for completion status, so
    #   you can increment it for each failure.  If there are no failures,
    #   after the final decrement, we'll return 0
    retval = 1
    # Set up the collection for receiving / finding items, first initialize the
    #   variable just for hygiene
    clxn = None
    clxn = qzmongo.prepcollection(theargs.database,theargs.collection)
    
    # Let's see if there's anything to do.
    if theargs.query is None:
        # There's really nothing that we can do, since we use  the query both to
        #   drive downloads and to retrieve records from the db for analysis
        # Do an early return for this case so that we don't have to indent the
        #   rest of this function's body by 4 spaces - with the 80 column limit,
        #   every space counts
        fstr = ("{0}A QUERY configuration is required to perform any "
                "operations!\n{1}Please modify your config file to "
                "specify a query.\n{1}Exiting...\n")
        sys.stderr.write(fstr.format(_ERS,' '*len(_ERS)))
        return retval
    
    # We do have a potentially valid query, set up the query parameter list
    query = _setup_query(theargs)
    
    # Attempt to download the data specified in the query.
    #    Note:  _dnld_data() will handle the situation where the
    #           base_url is None, or the user has directed us
    #           to skip the download step.
    dndata = _dnld_data(theargs, query, clxn, 'bzconn')
    
    # We've taken care of downloading, and perhaps storing.  Now let's see about
    #   some analysis.
    # NOTE:  If we have a db, we'll pull information from the DB, using our
    #        existing query specification.  Otherwise, we will see whether
    #        we have anything returned in the dndata list
    scores = {}
    dbcurs = None
    if theargs.metrics:
        # Query the database, or if we don't have a db, try to process
        #   the downloaded issues.  Run the scan on the appropriate
        #   collection of issues.  We may need to use dbcurs later to
        #   retrieve an organization name.
        qsrval = _query_scan(theargs.metrics, query, clxn, dndata)
        if qsrval.scn_ok:
            _analyze_scan(theargs.metrics, scores)
            dbcurs = qsrval.qcurs
        # end if qsrval.scn_ok
    # end if theargs.metrics
    
    # See if we can get a pathname for the dashboard html directory
    try:
        hpath = theargs.dashpath
    except AttributeError:
        hpath = None
    # See if we have scores to display, and if the user has not explicitly
    #   directed us to skip the dashboard display
    if (scores and
        (not ((hpath is not None) and (hpath.lower() == qzargs.SKIP_DASH)))
       ):
        # There are some scores, and User has not explicitly said, "no
        #   dashboard"
        dashpath = _gen_dash(theargs.organization, hpath, scores, dbcurs,
                             dndata)
        # let's try to display the results in a browser
        retval += _display_dash(dashpath)
    elif not scores:
        fstr = "{0}No metrics results to display on the dashboard.\n"
        sys.stdout.write(fstr.format(_NTE))
    else:
        fstr = ("{0}As directed, the results dashboard will not be "
                "generated.\n")
        sys.stdout.write(fstr.format(_NTE))
    # end if we have scores to work with & we're going to try the dashboard
    
    if dndata is not None:
        # we got something back, so decrement retval.  If there were no other
        #   failures, this will signify a successful completion
        retval -= 1
    return retval
# end run_qz


if __name__ == '__main__':
    
    # This module is main, so we're running from the command line
    _AS_FXN = False

    # get the config file / cmd line args
    theargs = qzargs.proc_cfg_cmdln(sys.argv, verbose=_VERBOSE)
    if _DIAGNOS:
        sys.stdout.write("{0}\n".format(theargs))

    if theargs.display_man:
        # Display the "man page"
        _gen_man_page(printit=True)
        exstr1 = "\n >>>>> qzmain documentation - Scroll Up "
        exstr2 = "to read the complete doc <<<<<\n"
        sys.exit(''.join([exstr1, exstr2]))
    # end theargs is None
    elif theargs.cfg_loaded:
        # We have a config file, try to run
        rval = run_qz(theargs, verbose=_VERBOSE)
        sys.exit(rval)
    else:
        # No valid config file, nothing that we can do
        xstr = "Unable to load valid config file.  Exiting...\n"
        sys.exit(''.join(["\n", _ERS, xstr]))
