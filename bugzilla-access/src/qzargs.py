#!/usr/bin/env python
""" qzargs.py handles configuration file and command line arguments.

This module is responsible for parsing the application configuration file, if
present and also specifying / parsing command line arguments.

It returns an instance of the QZArgs class that contains the final
combination of config file information and command line arguments

Module External Functions:
-- proc_cfg_cmdln - The main entry point for this module.  Responsible for
                parsing the application configuration file, if present and
                also specifying / parsing command line arguments.

Module Classes:
-- CfgCmdArgs - An instance of this class collects config file specifications
                and command line arguments, resolves any conflicts and is
                returned to the caller.
-- QZArgsExc - Exception class for this module


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


import argparse
import ConfigParser
import sys
import os

import qzutils
import qscan

# Constants for some of the parameters
_QUERIES = ('ALL', 'RANGE', 'LIST', 'DATE')
_METRICS = ('M_TTR', 'M_DDR', 'M_MDR', 'M_YDR')
_METSCNRS = {'M_TTR':[True,qscan.TimeToResolve],
             'M_DDR':[True,qscan.BugDiscRateDay],
             'M_MDR':[True,qscan.BugDiscRateMonth],
             'M_YDR':[True,qscan.BugDiscRateYear]
            }
_MET_ARGS = tuple(['M_ALL'] + list(_METRICS))
_DEFAULT_CFG_PATH = './.bz.cfg'
# String constants for messages
_MOD_NM = "QZARGS"
_MOD_ER = ''.join([_MOD_NM," ERROR: "])
_MOD_NT = ''.join([_MOD_NM," NOTE: "])
# If they don't specify an organization name in the config file
_DEFAULT_ORG = 'unknown'
# The value for the dashboard html file pathname (dashpath) that directs us
#   to skip the dashboard generation/display
SKIP_DASH = 'nodash'
# The value for the base url (base_url) that directs us to skip the
#   download from the RESTful interface
SKIP_DNLD = 'nodnld'


def _reset_metscnr_dict(verbose=False):
    # Resets the "un-used" value for each scanner in the scanner dictionary
    # Arguments:
    #   verbose --  boolean controlling output of additional information
    #            about the processing.  Default is False
    for sn in _METSCNRS.iterkeys():
        _METSCNRS[sn][0] = True
    if verbose:
        sys.stdout.write("{0}: Resetting scanner dictionary\n{1}\n"
                         .format(_MOD_NM, _METSCNRS))
# end _reset_metscnr_dict
def _parse_args():
    # Function that handles setting up setting up, and executing, the command
    #   line parser.
    # Returns the parsed argument dictionary
    #
    # YES, I know that this function doesn't comply with the 80 column limit.
    #   It's an intentional readability tradeoff
    #
    descr = "qzmain.py analyzes a given data set and reports the results. \
             If directed, it will extract the specified data from an external \
             repository. All program configuration directives are set in the \
             config file. You can use the default config file ('./.bz.cfg'), \
             or  specify '-C cfgpath' to designate a particular configuration \
             file."
    epi = "NOTES: (1) All configuration information is specified in the \
             configuration file. (2) The pathname to the config file must \
             either be relative to the current working directory, or be \
             fully qualified. (3) If you don't have an external source for \
             issues, you must have a database containing issue information."
    parser = argparse.ArgumentParser(description=' '.join(descr.split()),
                                     epilog=' '.join(epi.split()),
                                     prefix_chars='-+')
    #
    # NOTE:
    #   With the transition to mostly running as a server, we're, at least
    #   temporarily, disabling most of the commandline switches.  Execution
    #   should be configured using the config file.
    # The switches:
    exgroup = parser.add_mutually_exclusive_group()
    exgroup.add_argument('-man',help="Display the man page for the program",
                        action='store_true')
    # parser.add_argument('+M_ALL',help="Run ALL metrics", action='store_true')
    # parser.add_argument('+M_TTR',help="Run Time to Resolve", action='store_true')
    # parser.add_argument('+M_DDR',help="Run Daily Discovery Rate", action='store_true')
    # parser.add_argument('+M_MDR',help="Run Monthly Discovery Rate", action='store_true')
    # parser.add_argument('+M_YDR',help="Run Yearly Discovery Rate", action='store_true')
    # Database
    # parser.add_argument('-D',metavar='database',dest='database',type=str,nargs=1,help="The pathname to the database")
    # Config file
    exgroup.add_argument('-C',metavar='ConfigFile',dest='cfgfile',type=str,
                         nargs=1,help="The pathname of a configuration file")
    # Query types
    # qp = parser.add_subparsers(help="Extraction queries",dest='Query')
    # qp_ALL = qp.add_parser('ALL',help="Extract ALL available issues")
    # qp_ALL.add_argument('Organization',help="The name of the owning organization")
    # qp_ALL.add_argument('BASE_URL',help="The URL for the Issue Repository REST API")
    # qp_LIST = qp.add_parser('LIST',help="Extract the specified issues(ID #s). NOTES: Org and Base URL REQUIRED BEFORE ID List")
    # qp_LIST.add_argument('Organization',help="The name of the owning organization")
    # qp_LIST.add_argument('BASE_URL',help="The URL for the Issue Repository REST API")
    # qp_LIST.add_argument('listids',type=int,nargs='+',help="List of Issue IDs separated by spaces. NOTES: Org and Base URL REQUIRED BEFORE IDs")
    # qp_RANGE =  qp.add_parser('RANGE',help="Extract the range of issues(StartID - EndID).  NOTES: Org and Base URL REQUIRED BEFORE RANGE boundaries")
    # qp_RANGE.add_argument('Organization',help="The name of the owning organization")
    # qp_RANGE.add_argument('BASE_URL',help="The URL for the Issue Repository REST API")
    # qp_RANGE.add_argument('Start_End',type=int,nargs=2,help="Start and End Issue IDs")
    # qp_DATE =  qp.add_parser('DATE',help="Extract issues within a date range. NOTES: Org and Base URL REQUIRED BEFORE dates. Dates in YYYY-MM-DD format")
    # qp_DATE.add_argument('Organization',help="The name of the owning organization")
    # qp_DATE.add_argument('BASE_URL',help="The URL for the Issue Repository REST API")
    # qp_DATE.add_argument('DATE',type=str,nargs=2,help="Date Range in YYYY-MM-DD format")
    # qp_CONFIG = qp.add_parser('CONFIG',help="Defer to config file for Query spec")
    # qp_NONE = qp.add_parser('NONE',help="Skip Extraction step")
    # qp_NONE.set_defaults(Query='NONE')
    args = parser.parse_args()
    return args
#

class QZArgsExc(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return ''.join(["QZArgs EXCEPTION:  ", repr(self.value)])

class CfgCmdArgs(object):
    """Instances of this class manage configuration file and command line
    arguments for later use by the program.  They handle all functionality
    related to parsing the config file(s) and command line arguments,
    resolving conflicts and bundling everything up to control program
    execution.
    
    """
    def __init__(self):
        # minimal initialization, because eventual data attributes will
        #   be determined by the arguments
        self.display_man = False
        self.database = None
        self.collection = None
        self.query = None
        self.dashpath = SKIP_DASH
        self.metrics = []
        self.cfg_loaded = False
    # end init
    
    def set_metric(self, metric):
        # Handles taking a metric argument and adding the corresponding
        #   scanner(s) to this object's list of scanners.  Ensures that
        #   the new scanner isn't already on the list.
        # Returns True if the add was successful, False otherwise.  Will
        #       raise an exception if something really bad happens
        # Arguments:
        #   metric -- string representing the metric (or ALL) to add, taken
        #           from the metrics listed in _METRICS
        #
        def _set_metric(self, met):
            # Does a dictionary look up to see which scanner implements the
            #   metric and adds it to this object's list of scanners.
            #   Ensures that the new scanner isn't already on the list.
            # Returns True if the add was successful, False otherwise.
            #
            # Arguments:
            #   met -- string representing the metric (or ALL) to add, taken
            #           from the metrics listed in _METRICS
            if met in _METRICS:
                if _METSCNRS[met][0]:
                    # we haven't already used this scanner
                    self.metrics.append(_METSCNRS[met][1](met))
                    # mark it as used
                    _METSCNRS[met][0] = False
                    return True
                # end if scanner has already been applied
            else:
                # Don't recognize the speccified metric
                return False
            # end else value was not in known metrics
        # end _set_metric
        #
        if metric == 'M_ALL':
            # if all metrics are specified, we need to try to put them all on
            #   the list.
            for nmet in _METRICS:
                set_ok = _set_metric(self, nmet)
                if not set_ok:
                    # that's bad, since we're just adding from our own list
                    exs1 = "Coding Error: Could not add "
                    exs2 = "{0} to metric list".format(nmet)
                    raise qzargs.QZArgsExc(''.join([exs1, exs2]))
            # end for nmet in...
            return True
        elif metric in _METRICS:
            return _set_metric(self, metric)
        else:
            return False
         # end if the metric is all, or at least known
    # end set_metric
    
    def set_qcommon(self, org, url, isslst):
        # Sets the organization and base_url fields that are common to all of
        #   the metrics
        # Arguments:
        #   org -- string with the owning organization name
        #   url -- string containing the base url to the REST API server
        #   isslst -- list of data to form query range/list/date
        self.organization = org
        self.base_url = url if url != '' else None
        self.issues = isslst
    # end set_qcommon
    
    def set_query(self, qt):
        # Sets the query type field for this object, and also initializes the
        #   individual query data fields to none
        # Arguments:
        #   qt -- string representing the query type to be performed
        if qt in _QUERIES:
            self.query = qt
            self.set_qcommon(None, None, None)
        else:
            sys.stderr.write("{0}Unknown Query: '{1}' setting to None\n"
                             .format(_MOD_ER, qt))
            self.query = None
    # end set_query
    
    def set_database(self, db):
        # Sets the database attribute, ensuring that it's not the empty
        #   string.  If  the argument is '', sets to None
        # Arguments:
        #   db -- string - identifying the database to use
        self.database = db if db != '' else None
    # end set_database
    
    def set_collection(self, cxn):
        # Sets the collection attribute, ensuring that it's not the empty
        #   string.  If  the argument is '', sets to None
        # Arguments:
        #   cxn -- string - identifying the collection to use
        self.collection = cxn if cxn != '' else None
    # end set_collection

    def dbattr_ok(self):
        # Tests the database and collection attributes.
        #   NOTE:  This does not mean that the DB is valid, just that we
        #          have attributes that are OK, and that might reference
        #          a valid db.
        # Returns True if both attributes are not None, otherwise, returns
        #   False
        if ((self.database is not None) and (self.collection is not None)):
            return True
        else:
            return False
    # end dbspec_ok
    
    def set_dashpath(self, dshp):
        # Sets the dashpath attribute, ensuring that it's not the empty
        #   string.  If  the argument is '', sets to SKIP_DASH
        # Arguments:
        #   dshp -- string - identifying the pathname for the dashboard html
        #           file
        self.dashpath = dshp if dshp != '' else SKIP_DASH
    # end set_dashpath
    
    def _prep_repr(self):
        # Prepare a list of strings that enumerate the key / data attribute
        #   pairs for this instance.
        indt = ' '*4
        rs = ["Argument Object"]
        rs.append("{0}Instance of class {1}:"
                  .format(indt, self.__class__.__name__))
        # list comprehension to generate key / value pairs and then extend rs
        #   with the new list
        rs.extend(["{0}s.{1} = {2}".format(indt, key, getattr(self, key))
              for key in sorted(vars(self).keys())])
        return rs
    # end of prep_repr
    
    def __repr__(self):
        # Returns the string that represents this object
        rs = self._prep_repr()
        return "\n".join(rs)
    # end of __repr__
    
    def __str__(self):
        # Returns a string that represents this object suitable for printing.
        rs = self._prep_repr()
        rs.insert(0,'+++++++++')
        rs.append('=========') 
        return "\n".join(rs)
    # end of __str__
    


def _load_cfg(arginst, cfg_path):
    # Attempts to load and parse a configuration file.
    # NOTE:  This may either be the default file, or one specified on the
    #       command line
    # 
    # Returns True if the the file was loaded and parsed successfully.
    #     False otherwise.
    #
    # Arguments:
    #   arginst - an instance of class CfgCmdArgs that will hold arguments
    #           parsed from the file
    #   cfg_path - pathname to the configuration file
    #
    cfg_loaded = False
    config = None
    # bad value format string
    ebstr = "Config file option='{0}' has bad value='{1}'\n"
    efbad = ''.join([_MOD_ER, ebstr])
    # missing config option format string
    efmis = ''.join([_MOD_ER, "Config file specifies {0}='{1}', but '{2}' ",
                     "option\n", ' '*len(_MOD_ER), "is missing\n"])
    # note format string
    efnot = ''.join([_MOD_NT, "Config file option: '{0}' not specified\n"])
    # need url/db format string
    nufs = ("{0}Either a Database, or a URL to a data source, or "
            "both,\n{1}must be specified in the config file.\n")

    # Initialize a config file parser
    config = ConfigParser.SafeConfigParser()
    # Let's try to load it
    try:
        fhndl = qzutils.openfile(cfg_path, mode='r')
        if fhndl is not None:
            # would be None if there were any problems
            config.readfp(fhndl)
            cfg_loaded = True
            sys.stdout.write("{0}: Opened and read config file: {1}\n"
                             .format(_MOD_NM, cfg_path))
            fhndl.close()
        # end if fhndl is good
    except Exception as ex:
        # currently not sure what specific exceptions could be raise. My bad
        config = None
        sys.stderr.write("{0}Could not process config file: {1}\n"
                         .format(_MOD_ER, cfg_path))
        sys.stderr.write(qzutils.EXCFMTS.format(' '*len(_MOD_ER), ex))
    # end try/except
    
    if config is not None:
        # We parsed a file, let's extract data...
        sects = config.sections()
        # This is the db for processed recors
        if 'Database' in sects:
            opts = config.options('Database')
            # To work with MongoDB, we need to specify both database and
            #  collection.
            # NOTE:  Query processing looks at arginst.database and
            #        arginst.collection to decide whether to issue
            #        errors for no base URL.  If you change these
            #        attributes, make sure that you also fix the
            #        error checking in the 'Query' section
            if 'database' in opts:
                arginst.set_database(config.get('Database','database'))
            if 'collection' in opts:
                arginst.set_collection(config.get('Database','collection'))
            if ((arginst.database is None) ^ (arginst.collection is None)):
                # We need both of these to connect, so both can be None
                #   (no DB) or both can be not None (potentially valid DB)
                #   But we can't have one None and one not None
                if arginst.database is None:
                    opterr = 'collection'
                    misopt = 'database'
                else:
                    opterr = 'database'
                    misopt = 'collection'
                sys.stderr.write(efmis.format(opterr,
                                              getattr(arginst, opterr),
                                              misopt))
                fstr = ("{0}To fully specify a database to use, you must "
                        "identify both the\n{1}database and the collection\n")
                sys.stderr.write(fstr.format(_MOD_ER, ' '*len(_MOD_ER)))
                return False
            # end if no db XOR no cxn
        # end Database section
        if 'Query' in sects:
            # The query section should contain the "options" for the query
            #   type, owning organization and base URL (the query will be
            #   appended to this base URL)
            opts = config.options('Query')
            if 'query' in opts:
                cqt = config.get('Query','query')
                arginst.set_query(cqt)
                # set_query() may have rejected the configuration query, and
                #   set it to None
                qt = arginst.query
                if qt != 'NONE':
                    org = None
                    url = None
                    if 'organization' in opts:
                        org = config.get('Query', 'organization')
                    else:
                        # Org is used both to fill a field in the issue
                        #   object so we may need it even if they're
                        #   using the DB
                        sys.stdout.write(efnot.format('organization'))
                        fstr = "{0}Will use '{1}' for organization name\n"
                        sys.stdout.write(fstr.format(' '*len(_MOD_NT),
                                                    _DEFAULT_ORG))
                        org = _DEFAULT_ORG
                    if 'base_url' in opts:
                        url = config.get('Query', 'base_url')
                        if ((url.lower() == SKIP_DNLD) and
                            (not arginst.dbattr_ok())):
                            # They told us to skip the download, but we don't
                            #   have a valid db
                            sys.stderr.write(efmis.format('base_url', url,
                                                       'database/collection'))
                            return False
                        # end if url == skip
                    elif arginst.dbattr_ok():
                        # No base URL, but we have a DB, so we'll pull from
                        #   that
                        sys.stdout.write(efnot.format('base_url'))
                        fstr = ("{0}Will directly query database for "
                                "analysis\n")
                        sys.stdout.write(fstr.format(' '*len(_MOD_NT)))
                    elif (not arginst.dbattr_ok()):
                        # No base URL, no db
                        #   nufs format str defined at top of fxn
                        sys.stderr.write(nufs.format(_MOD_ER, ' '*len(_MOD_ER)))
                        return False
                    else:
                        sys.stderr.write(efmis.format('query',cqt,'base_url'))
                        return False
                    arginst.set_qcommon(org, url, [])
                if qt == 'RANGE':
                    if 'range' in opts:
                        # range should be a comma separated pair of ids,
                        #   so we'll get the string, split it, then convert
                        #   the resulting list into a list of two ints
                        range_s = config.get('Query', 'range')
                        range_sl = range_s.split(',')
                        if len(range_sl) != 2:
                            sys.stderr.write(efbad.format('range',range_sl))
                            return False
                        try:
                            arginst.issues = [int(v) for v in range_sl]
                        except Exception as ex:
                            sys.stderr.write(efbad.format('range',range_sl))
                            sys.stderr.write(qzutils.EXCFMTS
                                             .format(' '*len(_MOD_ER), ex))
                            return False
                    else:
                        sys.stderr.write(efmis.format('query',cqt,'range'))
                        return False
                elif qt == 'LIST':
                        # list should be a comma separated of list ids, so
                        #   we'll get the string, split it, then convert
                        #   the resulting list into a list of ints
                    if 'list' in opts:
                        list_s = config.get('Query', 'list')
                        list_sl = list_s.split(',')
                        if ((not list_sl) or (list_sl[0] == '')):
                            # list must have >= 1 actual items
                            sys.stderr.write(efbad.format('list',list_sl))
                            return False
                        try:
                            arginst.issues = [int(v) for v in list_sl]
                        except Exception as ex:
                            sys.stderr.write(efbad.format('list',list_sl))
                            sys.stderr.write(qzutils.EXCFMTS
                                             .format(' '*len(_MOD_ER), ex))
                            return False
                    else:
                        sys.stderr.write(efmis.format('query',cqt,'list'))
                        return False
                elif qt == 'DATE':
                    if 'date' in opts:
                        # date should be a comma separated of pair of date
                        #   strings, so we'll get the string, split it, then
                        #   convert the resulting list into a list of two
                        #   date strings
                        date_s = config.get('Query', 'date')
                        date_sl = date_s.split(',')
                        if len(date_sl) == 2:
                            arginst.issues = date_sl
                        else:
                            sys.stderr.write(efbad.format('date',date_s))
                            return False
                    else:
                        sys.stderr.write(efmis.format('query',cqt,'date'))
                        return False
                # end specific cases for each query type
            # end query option
        # end query section
        if 'Metrics' in sects:
            opts = config.options('Metrics')
            # For each of the known metrics, see if it's present in the
            #   options section, and whether it is set to true.  If so, try
            #   to add the appropriate scanner to the list of scanners.  The
            #   set_metric() function takes care of not adding duplicates and
            #   correctly handles the ALL specification.
            for scn in _MET_ARGS:
                # convert to lower case for convention in the config file
                lmet = scn.lower()
                if lmet in opts:
                    # This particular scan is in the options specified in
                    #   the Metrics section
                    bmet = False
                    try:
                        bmet = config.getboolean('Metrics', lmet)
                    except ValueError:
                        # Something wrong with what they specified
                        mval = config.get('Metrics', lmet)
                        sys.stderr.write(efbad.format(lmet, mval))
                        bmet = False
                    else:
                        if bmet:
                            # Set the scan up in the arg instance
                            arginst.set_metric(scn)
                    # end try/except
                # if the scanner is in the options and True
            # end for metrics
        # end Metrics section
        if 'Dashboard' in sects:
            opts = config.options('Dashboard')
            # If we have a dashboard section, we are looking for a dashpath
            if 'dashpath' in opts:
                arginst.set_dashpath(config.get('Dashboard','dashpath'))
        # end Dashboard section
        # Some consistency checks, now that the config file is "loaded"
        if arginst.query is None:
            # We can't really do anything without a query.
            fstr = ("{0}Config file does not specify a query.\n{1}A query "
                    "spec is required for any download and/or analysis.\n")
            sys.stderr.write(fstr.format(_MOD_ER, ' '*len(_MOD_ER)))
            return False
        # end query is None
        if (not arginst.dbattr_ok()):
            # No db specified, do we have a URL?
            try:
                qurl = arginst.base_url
            except AttributeError:
                # No attribute. Entire Query section might be missing, or
                #   they might have just skipped the base_url option
                qurl = None
            # end try/except
            if qurl is None:
                # nufs format string defined at top of this fxn
                sys.stderr.write(nufs.format(_MOD_ER, ' '*len(_MOD_ER)))
            # end no url
    # end if config not None
    return cfg_loaded
# end _load_cfg


def proc_cfg_cmdln(arglst, verbose=False):
    """Responsible for parsing the application configuration file, if present
    and also specifying / parsing command line arguments.
    
    This is the main entry point for this module.
    
    Returns an instance of the QZArgs class that contains the final
    combination of config file information and command line arguments
    
    Arguments:
        arglst -- list of arguments specified at the commandline
        verbose -- boolean controlling output of additional information
                about the processing.  Default is False
    
    """
    # Set up the objects and initialize the variables
    _reset_metscnr_dict(verbose)
    cmd_args = None
    myargs = CfgCmdArgs()
    #cfg_loaded = False
    cmd_args = _parse_args()
    
    if 'man' in cmd_args and cmd_args.man:
        myargs.display_man = True
    elif (('cfgfile' in cmd_args) and (cmd_args.cfgfile is not None)):
        # They're trying to specify a config file.
        myargs.cfg_loaded = _load_cfg(myargs, cmd_args.cfgfile[0])
    else:
        # try to load the default configuration file
        myargs.cfg_loaded = _load_cfg(myargs, _DEFAULT_CFG_PATH)
    if ((not myargs.display_man) and (not myargs.cfg_loaded)):
        # We're not displaying the man page, but we failed to load a
        #   configuration file.  This is a problem
        #   I know that this could be reduced to not(a or b), but this form
        #   seems to be more readable &  readily understood.
        fstr = ("{0}No configuration file loaded.\n"
                "{1}Cannot perform analysis without a configuration.\n"
                "{1}Please provide a valid configuration and try again.\n\n")
        sys.stderr.write(fstr.format(_MOD_ER, ' '*len(_MOD_ER)))
    
    # if '-man' in arglst:
    #     # Set the argument object to dump the man page
    #     myargs.display_man = True
    #     # return immediately, since we won't be processing anything
    #     return myargs
    # # end '-man'
    # elif not {'-h','--help'}.intersection(arglst):
    #     # they are not just trying to get help
    #     if ((len(arglst) == 3) and (arglst[1] == '-C')):
    #         # They're trying to specify a config file.
    #         cfg_loaded = _load_cfg(myargs, arglst[2])
    #     else:
    #         # try to load the default configuration file
    #         cfg_loaded = _load_cfg(myargs, _DEFAULT_CFG_PATH)
    # # end not trying to see the manual, or get help
    # # Since we may be using the default config file, we won't
    # #   try to parse the command line arguments, unless they are
    # #   really needed.
    # #   (1) - There are no command line arguments, and no default
    # #           config file, will get a cmd line parse message
    # #   (2) - User is only specifying an alternate config file, 
    # #           but we couldn't load it. Will get a cmd line parse
    # #           message.
    # #   (3) - There are only two command line argements
    # #   (4+) - Let's try to parse what they gave us.
    # if (((len(arglst) == 1) and (not cfg_loaded)) or 
    #     ((len(arglst) == 3) and (arglst[1] == '-C') and (not cfg_loaded)) or
    #     (len(arglst) == 2) or
    #     ((len(arglst) == 3) and (arglst[1] != '-C')) or
    #     (len(arglst) > 3)):
    #     # there's not an obvious config file, so let's parse the args
    #     cmd_args = _parse_args()
    #     if verbose:
    #         sys.stdout.write("\n\n{0}: Command Line Args:\n{1}\n\n"
    #                          .format(_MOD_NM, cmd_args))
    #     # we need to strip 'NONE' out of the list of possible queries to run
    #     qlst = list(_QUERIES)
    #     qlst.remove('NONE')
    #     indt = ' '*4
    #     if cmd_args.Query in qlst:
    #         if verbose:
    #             fsl = ["{0}: Command Line Query Spec:".format(_MOD_NM)]
    #             fsl.append("{0}Query:        {1}")
    #             fsl.append("{0}Organization: {2}")
    #             fsl.append("{0}BASE_URL:     {3}")
    #             fsl.append("")
    #             fsf = "\n".join(fsl)
    #             sys.stdout.write(fsf.format(indt, cmd_args.Query,
    #                                         cmd_args.Organization,
    #                                         cmd_args.BASE_URL))
    #         # end if verbose
    #         myargs.query = cmd_args.Query
    #         myargs.set_qcommon(cmd_args.Organization, cmd_args.BASE_URL, [])
    #         if cmd_args.Query == 'LIST':
    #             myargs.issues = cmd_args.listids
    #         elif cmd_args.Query == 'RANGE':
    #             myargs.issues = cmd_args.Start_End
    #         elif cmd_args.Query == 'DATE':
    #             myargs.issues = cmd_args.DATE
    #         # the 'ALL' case is already taken care of when set_qcommon()
    #         #   sets myargs.issues to [] in the call above.  This will
    #         #   override any settings aleady in place from the cfg file
    #     else:
    #         myargs.query = 'NONE'
    #     if cmd_args.database is not None:
    #         # they specified a database
    #         myargs.database = cmd_args.database
    #         if verbose:
    #             sys.stdout.write("{0}Database:     {1}\n"
    #                              .format(indt, cmd_args.database))
    #     else:
    #         if verbose:
    #             sys.stdout.write("{0}Database:     {1}\n"
    #                              .format(indt, "Not Specified"))
    #     # end database is not None
    #     # Walk through the metrics scanners. If they are specified
    #     #   as switches, set them. set_metric() will take care of
    #     #   preventing duplicates.
    #     for m in _MET_ARGS:
    #         if vars(cmd_args)[m]:
    #             myargs.set_metric(m)
    #             if verbose:
    #                 sys.stdout.write("   Run {0} Metric(s)\n".format(m[2:]))
    #         # end if the switch for this command is true
    #     # end for the potential arguments
    # # end we're processing the command line arguments
    return myargs
# end of proc_cfg_cmdln


if __name__ == '__main__':

    verbose = False
    theargs = proc_cfg_cmdln(sys.argv, verbose)
    if verbose:
        sys.stdout.write("{}\n".format(theargs))
# end this module is running as main.
