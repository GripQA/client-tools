#!/usr/bin/env python
""" qlytics.py - this module defines functions that perform higher analysis

Often, these functions work on information returned by scanners, or by
prior analysis runs.  They might be considered higher order analytics than
what the scanners in qscan do.

Module Functions:
-- calc_goodness()
-- get_norms()

Module Classes:


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


import qscan

def get_norms():
    # Creates a dictionary containing the 'Norm' values for each of the scanners
    #   listed in qscan_CHARTSCNL
    # Returns - the dictionary of 'Norm's
    # Arguments:
    #
    norms = [200.0, 180.0, 4000.0, 1000.0, 50000.0, 25000.0, 14.0, 10.0]
    kys = []
    for ky in qscan._CHARTSCNL:
        kys.append(ky)
        kys.append(''.join([ky,'SD']))
    # end for ky
    
    return dict(zip(kys, norms))
# end get_norms


def calc_goodness(scores):
    # Calculates a 'goodness' value from the information in the scores
    #   dictionary
    # Returns - integer representing the goodnes
    # Arguments:
    #   scores - dictionary containing the score data
    #
    rvals = []
    svals = []
    # we weigh defect discovery rate as the most important
    ddrwt = 40.0
    # time to resolve is slightly less important
    ttrwt = 30.0
    # standard deviation variances are even less critical
    sdwt = 10.0
    for ky in scores.keys():
        if ky.endswith('SD'):
            # we're dealing with a standard deviation, here it's better to be
            #   more predictable than the norm
            #   if our score > norm, we'll have positive results
            svals.append((float(scores[ky][1] - scores[ky][0])/
                         sum(scores[ky]))*sdwt)
        else:
            # normal metric, bad to be greater than the norm
            # if our score > norm, we'll have a negative result
            if ky.startswith('DDR'):
                wtf = ddrwt
            else:
                wtf = ttrwt
            rvals.append((float(scores[ky][0] - scores[ky][1])/
                         sum(scores[ky]))*wtf)
    # print rvals, sum(rvals), sum(rvals)*35.0
    # print svals, sum(svals), sum(svals)*10.0
    rval = 50.0 + sum(rvals) + sum(svals)
    if rval < 2.0:
        return 2.0
    elif rval > 100.0:
        return 100.0
    else:
        return rval
# end calc_goodness
