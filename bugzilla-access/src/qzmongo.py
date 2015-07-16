#!/usr/bin/env python
""" qzmongo.py - this module contains the functions for interacting with the 
                 MongoDB module, specifically through pymongo

Module Functions:
-- prepcollection
-- querydb
-- saveissues
-- saveitem
-- savelist


Module Classes:
-- QZDiter


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

import os
import sys

import pymongo

import qzutils
import bzconn

# String for module name
"""
if __name__ == '__main__':
    osf = sys.modules['__main__'].__file__
    pth,file = os.path.split(osf)
    modnm, ext = os.path.splitext(file)
else:
    modnm = __name__
# end if main
"""
_MODNM = __name__.upper()
# Module name string for formatted printing
_MNS = ''.join([_MODNM, ": "])
# Base Error String
_ERS = ''.join([_MODNM, " ERROR: "])


class QZDiter(object):
    """ Class QZDiter is the iterator for DB interfaces.

    Hopefully, it can be redefined, as needed, for future alternate databases
    while leaving the main program's code largely unchanged.
    
    """
    def __init__(self, dbcursor, silent=True):
        # Arguments:
        #  dbcursor -- PyMongo Cursor Object - the cursor returned from the
        #              query.  May be None, if there were any issues
        #  silent -- Boolean - If True, error messages are not printed for the
        #              None internal cursor.  This might be useful if you want
        #              to rely on None returns from nxt() to control execution
        #              flow for both end of iteration and no valid cursor
        #              conditions.
        #              NOTE: You can always check whether the internal cursor
        #                    is None using the ok() method
        self.mycurs = dbcursor
        self.silent = silent

    def ok(self):
        # Since this cursor could have been initialized with None, we have
        #  a convenience method to check whether the cursor is OK.  Note that,
        #  due to the exception handler, just calling the nxt() method on the
        #  "bad" instance will return None, as well
        if self.mycurs is not None:
            return True
        else:
            return False

    def nxt(self):
        # iterator function: Returns the current item and increments so that
        #  the subsequent call returns the "next" item
        #  Returns None if we're at the end of the cursor, or if there was
        #  a problem with the original query
        try:
            # raises "StopIteration" when out of data
            return self.mycurs.next()
        except StopIteration:
            return None
        except AttributeError:
            if not self.silent:
                sys.stderr.write("{0}No Valid PyMongo Cursor!\n".format(_ERS))
            return None

    def cnt(self):
        # returns the number of objects associated with the current cursor,
        #  returns -1 if the Cursor is None - which might happen if there
        #  was a problem with the original query.  This allows for comparison
        #  with a value, like 0.
        try:
            return self.mycurs.count()
        except AttributeError:
            if not self.silent:
                sys.stderr.write("{0}No Valid PyMongo Cursor!\n".format(_ERS))
            return -1

    def rst(self):
        # reset the cursor to the beginning of the retrieved data
        try:
            self.mycurs.rewind()
        except AttributeError:
            if not self.silent:
                sys.stderr.write("{0}No Valid PyMongo Cursor!\n".format(_ERS))

    def tog_slnt(self):
        # toggle silent mode for this cursor
        if self.silent:
            self.silent = False
        else:
            self.silent = True
# end DBiter

def prepcollection(database, collection):
    """Prepare the specified MongoDB collection for save/find
    Returns the collection object, if successful, otherwise, None
    
    Arguments:
    database - String identifying the MongoDB database to access
    collection - String identifying the MongoDB collection to access
    """

    clxn = None
    if ((database is not None) and (collection is not None)):
        # we have something, let's try to get the collection
        #  Note:  This is lazy evaluation, so we won't know whether it was
        #         valid, until we try to use it.
        #
        try:
            clxn = pymongo.MongoClient()[database][collection]
        except pymongo.errors.PyMongoError:
            # Base class, should catch everthing bad with the DB, we're in
            #  serious trouble if this fails, so we'll just stick with
            #  the base class
            sys.stderr.write("{0}PyMongo Unexpected Error!\n".format(_ERS))

    return clxn
# end of prepcollection

def savelist(doclst, collection, nodup=None):
    """Iterates through the specified list and saves all of the documents
    in the specified collection
    Returns True if the save seemed to be successful, False otherwise

    Arguments:
    doclst - Iterable containing the documents to save
             NOTE: must be a dictionary
    collection - MongoDB collection object to receive the objects
    nodup - Specifies the key to check for duplicates.  If none, no checking
            is performed.  If existing doc is detected, will attempt to update
    """

    retval = False
    for doc in doclst:
        if not saveitem(doc, collection, nodup):
            break
    else:
        # only executed if loop terminated through exhaustion of list
        retval = True

    return retval
# end of savelist


def saveissues(isslst, collection, nodup=None):
    """Iterate through the specified list and save all of the issues
    in the specified collection
    Returns True if the save seemed to be successful, False otherwise

    Arguments:
    isslst - Iterable containing the documents to save
             NOTE: issue object must have the __dict__ attribute
    collection - MongoDB collection object to receive the objects
    nodup - Specifies the key to check for duplicates.  If none, no checking
            is performed.  If a duplicate is detected, calls update.
    """

    retval = False
    for issue in isslst:
        try:
            idict = issue.__dict__
        except AttributeError as a:
            sys.stderr.write("{0}Improper Object Type passed to saveissues():\n"
                             .format(_ERS))
            sys.stderr.write(qzutils.EXCFMTS.format(' '*len(_ERS), a))
            retval = False
            break
        else:
            if not saveitem(idict, collection, nodup):
                retval = False
                break
    else:
        # only executed if loop terminated through exhaustion of list
        retval = True

    return retval
# end of saveissues


def saveitem(doc, clxn, nodup=None):
    """Save the specified document in the given collection.
    Returns True if the save seemed to be successful, False otherwise

    Arguments:
    doc - Document to save  NOTE: must be a dictionary
    clxn - MongoDB collection object to receive the object
    nodup - Specifies the key to check for duplicates.  If none, no checking
            is performed.  If a duplicate is detected, calls update.
    """
    # start saveitem main function code
    retval = False
    rv = False
    try:
        if nodup is not None:
            # We're upserting, so we have a key/value query to check for
            #  presence in the collection
            rv = clxn.update({nodup:doc[nodup]},doc,upsert=True,
                             manipulate=False)
        else:
            # This may create a duplicate document.  Only use if you're either
            #  OK with dupes, or you know that the document isn't already
            #  there.
            rv = clxn.save(doc,manipulate=False)
        # end nodup
    except KeyError as k:
        # given key is not in the given document's dictionary
        sys.stderr.write("{0}Unknown Dup lookup key: {1}\n".format(_ERS,k))
    except pymongo.errors.OperationFailure as pmx:
        sys.stderr.write("{0}PyMongo Operation Failure: {1}\n"
                         .format(_ERS, pmx))
    except pymongo.errors.CollectionInvalid:
        sys.stderr.write("{0}PyMongo Invalid Collection!\n".format(_ERS))
    except pymongo.errors.ConfigurationError:
        sys.stderr.write("{0}PyMongo Configuration Error!\n".format(_ERS))
    except pymongo.errors.ConnectionFailure:
        sys.stderr.write("{0}PyMongo Connection Failure!\n".format(_ERS))
    except pymongo.errors.InvalidOperation:
        sys.stderr.write("{0}PyMongo Invalid Operation!\n".format(_ERS))
    except pymongo.errors.InvalidName:
        sys.stderr.write("{0}PyMongo Invalid Name!\n".format(_ERS))
    except pymongo.errors.InvalidURI:
        sys.stderr.write("{0}PyMongo Invalid URI!\n".format(_ERS))
    except pymongo.errors.UnsupportedOption:
        sys.stderr.write("{0}PyMongo Unsupported Option!\n".format(_ERS))
    except pymongo.errors.TimeoutError as pmx:
        sys.stderr.write("{0}PyMongo Timeout Error: {1}\n".format(_ERS, pmx))
    except pymongo.errors.PyMongoError:
        # Base class, should catch everthing bad with the DB
        sys.stderr.write("{0}PyMongo Unexpected Error!\n".format(_ERS))
    # end try/except block for the save
    try:
        if ((rv is None) or (rv['ok'] == 1.0) or (rv['err'] is None)):
            # rv is set to none for a successful save, or some cases of update
            # rv['ok'] is 1.0 for successful updates, just to be extra safe,
            #   we'll also "or" in the err value as None
            retval = True
    except (KeyError, TypeError):
        retval = False
    # end try to evaluate rv
        
    return retval
# end of saveitem


def querydb(query, collection, mongo_curs=True):
    """Submit the specified query parameters to the given MongoDB collection
    Returns the cursor for the query, if successful, otherwise, None.
        NOTE:  the argument mongo_curs controls whether this is a pymongo
               iterator (mongo_curs == True) or one of our own QZDiter
               (mongo_curs == False).  You may prefer to use receive an
               instance of QZDiter if you're planning to iterate with
               a while loop, or if you want to be as portable as possible
               to other DBs

    It might be worthwhile to remember the difference between a query that is
    successful, but just doesn't return anything (count is zero), and a query
    that actually fails.  The former will return a cursor, the latter will
    return None

    Arguments:
    query - List containing the components of the QZ query, will generate the
            appropriate DB query from the given QZ query list.
    collection - String identifying the MongoDB collection to access
    mongo_curs - True means return a pymongo iterator, False means return
                 an instance of QZDiter
    """
    # initialize to none so that we know whether we assigned to fndit for the
    #  "ALL" case.  For all other cases, we're just defining a spec variable, 
    #  and we'll use that as the argument to find()
    #  Later, we'll use the fndit variable in an eval() to actually execute the
    #  DB search.  
    fndit = None
    
    # The python
    if query[0] == 'ISSUE_RANGE':
        # make sure that the range is lowest -> highest
        beg = min(query[1:])
        end = max(query[1:])
        spec = {'$and': [{'id':{'$gte':beg}}, {'id':{'$lte':end}}]}
    elif  query[0] == 'ISSUE_LIST':
        # create a list with a dictionary entry for each issue on the issue
        #  list, skipping the first element, which is the query identifier
        nl = [{'id':iid} for iid in query[1:]]
        # The spec is "or" any of the ids in the new list
        spec = {'$or':nl}
    elif  query[0] == 'DATE_RANGE':
        # Make sure that the dates are ordered earliest to latest, and convert
        #  them to datetime objects
        beg = bzconn.mk_datetime(min(query[1:]))
        end = bzconn.mk_datetime(max(query[1:]))
        spec = {'$and': [{'creation_time':{'$gte':beg}}, 
                         {'creation_time':{'$lte':end}}]}
    elif  query[0] == 'ALL':
        # ALL has no spec, instead, we recover everything in the collection
        fndit = 'collection.find()'
    else:
        sys.stderr.write("{0}Unknown Query specifier: {1}\n".format(_ERS, url))
    
    # we know whether we need a spec, and that it's defined, if we do need it
    if fndit is None:
        # we're not querying all, so use the spec defined above
        fndit = 'collection.find(spec)'
    
    # evaluate the fndit expression to get the appropriate cursor.
    pmcurs = None
    try:
        # get the pymongo cursor
        pmcurs = eval(fndit)
    except pymongo.errors.OperationFailure as pmx:
        sys.stderr.write("{0}PyMongo Operation Failure: {1}\n".format(_ERS, pmx))
    except pymongo.errors.CollectionInvalid:
        sys.stderr.write("{0}PyMongo Invalid Collection!\n".format(_ERS))
    except pymongo.errors.ConfigurationError:
        sys.stderr.write("{0}PyMongo Configuration Error!\n".format(_ERS))
    except pymongo.errors.ConnectionFailure:
        sys.stderr.write("{0}PyMongo Connection Failure!\n".format(_ERS))
    except pymongo.errors.InvalidOperation:
        sys.stderr.write("{0}PyMongo Invalid Operation!\n".format(_ERS))
    except pymongo.errors.InvalidName:
        sys.stderr.write("{0}PyMongo Invalid Name!\n".format(_ERS))
    except pymongo.errors.InvalidURI:
        sys.stderr.write("{0}PyMongo Invalid URI!\n".format(_ERS))
    except pymongo.errors.UnsupportedOption:
        sys.stderr.write("{0}PyMongo Unsupported Option!\n".format(_ERS))
    except pymongo.errors.TimeoutError as pmx:
        sys.stderr.write("{0}PyMongo Timeout Error: {1}\n".format(_ERS, pmx))
    except pymongo.errors.PyMongoError:
        # Base class, should catch everthing bad with the DB
        sys.stderr.write("{0}PyMongo Unexpected Error!\n".format(_ERS))

    if pmcurs is not None:
        sys.stdout.write("{0}Retrieved {1} records from MongoDB\n"
                         .format(_MNS, pmcurs.count()))
    else:
        sys.stdout.write("{0}No records retrieved from MongoDB\n"
                         .format(_MNS))
    # Return the cursor as directed by the mongo_curs arg.  If specified, 
    #  generate one of our own cursors, and return it, set to not
    #  print errors
    return pmcurs if mongo_curs else QZDiter(pmcurs,silent=True)
#end of querydb
