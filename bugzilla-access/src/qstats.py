#!/usr/bin/env python
""" qstats.py - this module contains the statistics functions used for analysis


Module Functions:
-- average
-- std_dev_pop
-- std_dev_samp

Module Classes:
-- QStatsExc - Module exception class


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


import math


class QStatsExc(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return ''.join(["QSTATS EXCEPTION:  ", repr(self.value)])


def average(itr):
    """Computes the arithmetic mean of numbers in an iterable.
    Returns 0.0 if the iterable has 0 length
    
    >>> print average([20, 30, 70])
    40.0
    
    """
    if itr:
        return sum(itr,0.0) / len(itr)
    else:
        return 0.0


def std_dev_pop(itr):
    """Computes the population standard deviation of numbers in an iterable.
    Returns both average and population standard deviation for the iterable
    Returns 0.0 for both average and if the iterable has 0 length
    
    >>> res = std_dev_pop([1, 2, 3])
    >>> print ''.join(['(', '{0:.1f}'.format(res[0]), ', ', '{0:.2f}'.format(res[1]), ')'])
    (2.0, 0.82)
    
    """
    avg = average(itr)
    variance = map(lambda x: (x - avg)**2, itr)
    sd = math.sqrt(average(variance))
    return avg, sd


def std_dev_samp(itr):
    """Computes the sample standard deviation of numbers in an iterable.
    Returns both average and sample standard deviation for the iterable
    Raises an exception if the iterable has length < 2
    
    >>> print std_dev_samp([1,2,3])
    (2.0, 1.0)
    
    """
    sizit = len(itr)
    if sizit >= 2:
        avg = average(itr)
        variance = map(lambda x: (x - avg)**2, itr)
        sd = math.sqrt(sum(variance,0.0)/(sizit-1))
        return avg, sd
    else:
        raise QStatsExc('Sample must have at least two (2) ' + \
                        'members to compute Sample Standard Deviation')
