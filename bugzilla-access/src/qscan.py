#!/usr/bin/env python
""" qscan.py - this module defines the scanner objects for analysis

Typically, these scanners are chained together and run serially across the
data set.  Each scanner collects and maintains the data required to
perform its specific calculation / analysis.


Module Functions:
-- get_norms()

Module Classes:
-- QScanExc - Module exception class
-- QScanBase - Base class for scanner objects
-- BugCounterBase - Base class for counter based scanners
-- BugDiscRateDay - Defect Discovery Rate - Daily
-- BugDiscRateMonth - Defect Discovery Rate - Monthly
-- BugDiscRateYear - Defect Discovery Rate - Yearly
-- TimeToResolve - Time from issue creation to resolution


Module Globals:
-- CHARTSCN - set containing the scanners supported for charting


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

from collections import Counter
from datetime import datetime
from datetime import timedelta
from inspect import currentframe

import qzutils
import qstats


_MODNM = __name__.upper()
# Module name string for formatted printing
_MNS = ''.join([_MODNM, ": "])
# Base Error / Warning Strings
_ERS = ''.join([_MODNM, " ERROR: "])

# set containing the ids of scanners that might be charted
_CHARTSCNL = ['DDR', 'MDR', 'YDR', 'TTR']
CHARTSCN = set(_CHARTSCNL)

class QScanExc(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return ''.join([_MODNM, " EXCEPTION:  ", repr(self.value)])


class QScanBase(object):
    """Base class for a pattern scan object
    Scanners derived from this class collect and manage the data required to
    completea specific analysis, or to generate a particular metric.  This
    base class definesthe template and common functions for the scanners, but
    does not attempt provide a template for member data attributes.
    
    """
    
    
    def __init__(self, name):
        # Minimal set up for the base class
        #
        # Returns - N/A
        #
        # Arguments:
        # name -- str - the name of this scanner, most often the
        #       metric / analysis
        
        # we'll do this as the default case.  Callers can change if they want.
        self.name = name
        self.total_scanned = 0
        self.id = 'BASE'
    #end init
    
    def proc_data(self, issue):
        # Template function for processing an Issue named tuple
        #   Increments the total scanned counter, so should be
        #   called from child classes
        #
        # Returns - True if processing completed successfully, None
        #           if we encountered errors.
        # Arguments:
        # issue -- dict - the issue data to process for this issue
        self.total_scanned += 1
        # The base class method should never be called, except by children
        return None
    # end proc_data
    
    def analyze(self):
        # Template function for generating the metric / analysis on
        #   the data stored with this object
        # Returns - Appropriate data if successful, None otherwise
        #
        # Don't call this on the base class!
        return None
    # end analyze
    
    def dump_state(self, printit=False):
        # Dumps the the current state of this scanner
        # Returns - A string containing the current state of this object
        # Arguments:
        #   printit -- boolean tells this method whether to print the string,
        #           or just return it.
        retstr = 'Scanner:  {0}'.format(self.name)
        if printit: sys.stdout.write("{0}\n".format(retstr))
        return retstr
    #end dump_state
    
    def dump_csv(self, csvfile=None):
        # dumps the the current state of this object
        # Returns - True if successful, false otherwise, or if this
        #           class doesn't explicitly implement dumpCSV
        # Arguments:
        #   csvfile - file handle of the csv file to receive ouptut,
        #       (optional) it's up to subclasses to determine how they
        #       want to implement this class, and whether they want to
        #       generatea CSV file, at all.
        # rtn:
        #   True if successful, false otherwise, or if this class doesn't
        #   explicitly implement dumpCSV
        return False
    #end dump_csv
#end QScanBase


class BugCounterBase(QScanBase):
    """General purpose scanner built around a counter collection
    Scanners derived from this class collect and manage data in a performance
    optimized dictionary collection called a counter.
    
    The simple analysis provided by the base class includes average and
    standard deviation computed over the values stored in the
    counter.  This works fine if the keys represent something like days,
    or months.  This probably will not work if the keys are, instead,
    something more like number of occurrences.  In this latter case, you'll
    need to generate a new list that expands so that each entry contains a
    separate instance of the 'count' - see class TimeToResolve.analyze()
    
    """
    
    
    def __init__(self, name='Defect Counter Based Scanner', population_sd=True):
        # Set up the foundation for the DDR scanners
        #
        # Returns - N/A
        #
        # Arguments:
        # name -- str - the name of this scanner, most often the
        #       metric / analysis
        # population_sd -- if True, we'll calculate the population
        #       standard deviation, otherwise calculate the sample
        #       standard deviation.
        #
        # Initialize the parent class
        QScanBase.__init__(self, name)
        self.id = 'BCBASE'
        
        # Counter collection, where the Keys are the numeric
        #   representation of the period in question. e.g. 201305 for
        #   May of 2013, or 20130514 for 14-May-2013.
        self.counter = Counter()
        # if True, calculate Population Std Dev, otherwise Sample SD
        self.pop_sd = population_sd
        self.avg = None
        self.stdev = None
    #end init
    
    def analyze(self):
        # Calculates average and standard deviation on the data stored
        #   in self.counter.
        # Stores newly calculated values in data attributes.
        #
        # Returns - Tuple containing average and standard deviation, if
        #           successful, None otherwise
        #
        rtn_val = None
        if self.pop_sd:
            rtn_val = qstats.std_dev_pop(self.counter.values())
        else:
            try:
                rtn_val = qstats.std_dev_samp(self.counter.values())
            except qstats.QStatsExc as exc:
                sys.stderr.write("{0}\n".format(exc))
                rtn_val = None
        if rtn_val is not None:
            self.avg, self.stdev = rtn_val
        return rtn_val
    # end analyze
    
    def dump_state(self, printit=False):
        # Dumps the the current state of this scanner
        # Returns - A string containing the current state of this object
        # Arguments:
        #   printit -- boolean tells this method whether to print the string,
        #           or just return it.
        fstr = "{0}: Total scanned={1} Average={2} {3} Standard Deviation={4}"
        retstr = fstr.format(self.name, self.total_scanned, self.avg,
                         'Population' if self.pop_sd else 'Sample', self.stdev)
        if printit: sys.stdout.write("{0}\n".format(retstr))
        return retstr
    #end dump_state
    
    def dump_csv(self, csvfile=None):
        # dumps the the current state of this object
        # Returns - True if successful, false otherwise, or if this
        #           class doesn't explicitly implement dumpCSV
        # Arguments:
        #   csvfile - file handle of the csv file to receive ouptut,
        #       (optional) it's up to subclasses to determine how they
        #       want to implement this class, and whether they want to
        #       generatea CSV file, at all.
        # rtn:
        #   True if successful, false otherwise, or if this class doesn't
        #   explicitly implement dumpCSV
        return False
    #end dump_csv
#end BugCounterBase


class BugDiscRateDay(BugCounterBase):
    """New defect discovery rate per day
    Iterates across the data and counts new defects reported in each day
    
    Analysis:
        Average Issues Discovered
        Standard Deviation on the Daily Discovery count
    
    """
    
    
    def __init__(self, name='Daily Defect Discovery Rate', population_sd=True):
        # Daily Defect Discovery Rate Scanner
        #
        # Returns - N/A
        #
        # Arguments:
        # name -- str - the name of this scanner, most often the
        #       metric / analysis
        #
        # Initialize the parent class
        BugCounterBase.__init__(self, name, population_sd)
        self.id = 'DDR'
        
    #end init
    
    def proc_data(self, issue):
        # Increment the created in bin for the day appropriate based
        #   on the issue create date.
        #
        # Returns - True if processing completed successfully, None
        #           if we encountered errors.
        # Arguments:
        # issue -- dict - the issue data to process for this issue
        #
        # Update the data in the base class
        BugCounterBase.proc_data(self, issue)
        try:
            ct = issue['creation_time']
        except KeyError:
            fstr = "NOTE:  'creation_time' attribute not available.\n"
            sys.stdout.write(fstr)
            return None
        else:
            # self.counter[(int(''.join([cts[0:4],cts[5:7],cts[8:10]]))] += 1
            self.counter[(ct.year*10000 + ct.month*100 + ct.day)] += 1
            return True
    # end proc_data
#end BugDiscRateDay


class BugDiscRateMonth(BugCounterBase):
    """New defect discovery rate per month
    Iterates across the data and counts new defects reported in each month
    
    Analysis:
        Average Issues Discovered
        Standard Deviation on the Monthly Discovery rate
    
    """
    
    
    def __init__(self, name='Monthly Defect Discovery Rate',
                 population_sd=True):
        # Monthly Defect Discovery Rate Scanner
        #
        # Returns - N/A
        #
        # Arguments:
        # name -- str - the name of this scanner, most often the
        #       metric / analysis
        #
        # Initialize the parent class
        BugCounterBase.__init__(self, name, population_sd)
        self.id = 'MDR'
        
    #end init
    
    def proc_data(self, issue):
        # Increment the created in bin for the month appropriate based
        #   on the issue create date.
        #
        # Returns - True if processing completed successfully, None
        #           if we encountered errors.
        # Arguments:
        # issue -- dict - the issue data to process for this issue
        #
        # Update the data in the base class
        BugCounterBase.proc_data(self, issue)
        try:
            ct = issue['creation_time']
        except KeyError:
            fstr = "NOTE:  'creation_time' attribute not available.\n"
            sys.stdout.write(fstr)
            return None
        else:
            self.counter[(ct.year*100 + ct.month)] += 1
            return True
    # end proc_data
#end BugDiscRateMonth


class BugDiscRateYear(BugCounterBase):
    """New defect discovery rate per year
    Iterates across the data and counts new defects reported in each year
    
    Analysis:
        Average Issues Discovered
        Standard Deviation on the Yearly Discovery rate
    
    """
    
    
    def __init__(self, name='Yearly Defect Discovery Rate', population_sd=True):
        # Yearly Defect Discovery Rate Scanner
        #
        # Returns - N/A
        #
        # Arguments:
        # name -- str - the name of this scanner, most often the
        #       metric / analysis
        #
        # Initialize the parent class
        BugCounterBase.__init__(self, name, population_sd)
        self.id = 'MDR'
        
    #end init
    
    def proc_data(self, issue):
        # Increment the created in bin for the Year appropriate based
        #   on the issue create date.
        #
        # Returns - True if processing completed successfully, None
        #           if we encountered errors.
        # Arguments:
        # issue -- dict - the issue data to process for this issue
        #
        # Update the data in the base class
        BugCounterBase.proc_data(self, issue)
        try:
            ct = issue['creation_time']
        except KeyError:
            fstr = "NOTE:  'creation_time' attribute not available.\n"
            sys.stdout.write(fstr)
            return None
        else:
            self.counter[ct.year] += 1
            return True
    # end proc_data
#end BugDiscRateYear


class TimeToResolve(BugCounterBase):
    """Time taken to resolve bugs
    Iterates across the data and extracts the time to resolve for Issues
        marked as resolution == FIXED and status is one of: VERIFIED,
        CLOSED or RESOLVED
    Note:  Since the initialization and the analysis are the same as the
        BugCounterBase class, we derived from there.
    Analysis:
        Average Time to Resolve
        Standard Deviation on the resolution time
        Number of resolved issues
        Number of unresolved issues
    """
    
    
    def __init__(self, name='TimeToResolve', population_sd=True):
        # Set up the TimeToResolve scanner
        #
        # Returns - N/A
        #
        # Arguments:
        # name -- str - the name of this scanner, most often the
        #       metric / analysis
        # population_sd -- if True, we'll calculate the population
        #       standard deviation, otherwise calculate the sample
        #       standard deviation.
        #
        # Initialize the parent class
        # Note:  For this scanner, the counter collection, has Keys that
        #   are the numericnumber of days to resolve and Values are the
        #   counts
        BugCounterBase.__init__(self, name, population_sd)
        self.id = 'TTR'
        
        self.total_resolved = 0
        self.total_unresolved = 0
    #end init
    
    def proc_data(self, issue):
        # Increment the days-to-resolve in bin for the calculated duration.
        #   The calculation is the difference between the creation time and
        #   the resolved time.
        #
        # Returns - True if processing completed successfully, None
        #           if we encountered errors.
        # Arguments:
        # issue -- dict - the issue data to process for this issue
        #
        # Update the data in the base class
        BugCounterBase.proc_data(self, issue)
        
        dt = None
        retval = None
        # make sure that the keys are there, and that the values are good
        try:
            ct = issue['creation_time']
            rt = issue['resolved_time']
        except KeyError:
            # It doesn't really matter which one raised the exception.  We
            #   need both for this metric
            ct = None
            rt = None
        # end of try/except
        if ((rt is not None) and (ct is not None)):
            # We have both, let's calculate
            dt = rt - ct
            if dt.days >= 0:
                self.counter[dt.days] += 1
                self.total_resolved += 1
                retval = True
            else:
                fstr = ("{0}Data Issue:\n{5}resolved_time: {1} \n"
                        "{5}is earlier than\n{5}creation_time: {2}.\n"
                        "{5}Module: {3} Line: {4}\n")
                sys.stderr.write(fstr.format(_ERS, rt, ct, __file__,
                                             currentframe().f_lineno,
                                             ' '*len(_ERS)))
                retval = None
        else:
            retval = None
        if retval is None:
            self.total_unresolved += 1
        return retval
    # end proc_data
    def analyze(self):
        # Calculates average and standard deviation on the data stored
        #   in self.counter.
        # Stores newly calculated values in data attributes.
        #
        # Returns - Tuple containing average and standard deviation, if
        #           successful, None otherwise
        #
        rtn_val = None
        # Because of the way that we populated the counter, where keys are
        #   'num days to resolve' and values are counts for each key,
        #   we first need to create a list that has the duration to
        #   resolution for each issue.
        dtrlst = []
        # Since we're extending dtrlst with multiple new elements, using a
        #   list comprehension is less than obvious here.  Thus, a for loop
        for kvp in self.counter.iteritems():
            dtrlst.extend([kvp[0]]*kvp[1])
        if self.pop_sd:
            rtn_val = qstats.std_dev_pop(dtrlst)
        else:
            try:
                rtn_val = qstats.std_dev_samp(dtrlst)
            except qstats.QStatsExc as exc:
                sys.stderr.write("{0}\n".format(exc))
                rtn_val = None
        if rtn_val is not None:
            self.avg, self.stdev = rtn_val
        return rtn_val
    # end analyze
    
    def dump_state(self, printit=False):
        # Dumps the the current state of this scanner
        # Returns - A string containing the current state of this object
        # Arguments:
        #   printit -- boolean tells this method whether to print the string,
        #           or just return it.
        fs1 = "{0}: Total scanned={1} Average={2} {3} Standard Deviation={4}\n"
        os1 = fs1.format(self.name, self.total_scanned, self.avg,
                         'Population' if self.pop_sd else 'Sample', self.stdev)
        fs2 = "{0}Total Resolved Issues={1} "
        os2 = fs2.format(' '*17, self.total_resolved)
        os3 = "Total Unresolved Issues={0}".format(self.total_unresolved)
        retstr = ''.join([os1, os2, os3])
        if printit: sys.stdout.write("{0}\n".format(retstr))
        return retstr
    #end dump_state
    
    def dump_csv(self, csvfile=None):
        # dumps the the current state of this object
        # Returns - True if successful, false otherwise, or if this
        #           class doesn't explicitly implement dumpCSV
        # Arguments:
        #   csvfile - file handle of the csv file to receive ouptut,
        #       (optional) it's up to subclasses to determine how they
        #       want to implement this class, and whether they want to
        #       generatea CSV file, at all.
        # rtn:
        #   True if successful, false otherwise, or if this class doesn't
        #   explicitly implement dumpCSV
        return False
    #end dump_csv
#end TimeToResolve
