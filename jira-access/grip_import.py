"""grp_import.py contains the common data / functions that support Grip QA's
import scripts.

Most of these functions are utilities that are shared by multiple import
scripts.

Module External Functions:
    make_measurement - factory method to produce the GripMeasurement namedtuple,
                       with appropriate defaults
    usage_message - prints out a standard usage message for import modules
    
    get_basename_arg - checks the argument list and extracts the root name given

    gen_timestamp - produce a timestamp given an ISO date string

    get_rest - request data for the given URL

    get_requirement_cnt - scan the given text for requirements and return the
                          number of requirements discovered

    load_config - loads the configuration file and converts the information
                  into a format appropriate for the configuration object

    gen_json - convert a list of GripMeasurement namedtuple's into a JSON
               string

Module Classes:
    GripConfig - Class containing information extracted from the configuration
                 file

Module Globals:
    GLOBALS - Dictionary of global values to be shared by all import modules
    ERR_LABEL - String with error message prefix
    NOTE_LABEL - String with note message prefix


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
__copyright__ = "Copyright 2015, Grip QA"
__license__ = "Apache License, Version 2.0"
__status__ = "Prototype"
__version__ = "0.01"

import json
import requests
import isodate
import configparser
import datetime

import textwrap
import re
from collections import namedtuple
from collections import OrderedDict
from operator import itemgetter

from qz_utils import openfile


# Structures for different measurements
GLOBALS = {'TIMESTAMP':0.0
           ,'ACCOUNT_NAME':None
           ,'VERBOSE':False
           }


ERR_LABEL = "ERROR:  "
NOTE_LABEL = "NOTE:  "

# Represents a measurement as an immutable Python data structure that can be
# efficiently converted to JSON for output
GripMeasurement = namedtuple('GripMeasurement'
                             ,['name'
                               ,'value'
                               ,'account'
                               ,'timestamp'
                               ,'metadata'])


def make_measurement(name
                     ,metadata
                     ,value=1.0
                     ,timestamp=GLOBALS['TIMESTAMP']):
    """ Factory method to produce a GripMeasurement namedtuple, with
    appropriate defaults to complement the specified values
    
    Args:
        name - required string with the name of the measurement
        metatdata - required dictionary containging the issue's metadata
        value - value (float) of the measurement; defaults to 1.0
        timestamp - integer time of the measurement, defaults to the global
                    value

    Returns:
        The new, immutable, namedtuple represending the measurement

    """
    return GripMeasurement(name=name
                           ,value=value
                           ,timestamp=timestamp
                           ,account=GLOBALS['ACCOUNT_NAME']
                           ,metadata=metadata)


class GripConfig(object):
    """Class containing the configuration information

    Additional attributes will probably be added by the load_config function
    """
    def __init__(self):
        self.defect_types = "Bug"
        self.issues_with_requirements = ["Story"]
        self.closed_status = ["Closed"]
        self.username = "grip"
        self.password = None
        self.server = None
        self.jira_rest_api = "rest/api/2/"
        self.sprint_api = None


def usage_message(program_file):
    """Prints a standard usage message for import modules
    
    Args:
        program_file - string representing the name of the current main
                       program

    Returns:
        No return value
    """
    print("\nUSAGE:  {0} basename".format(program_file))
    print("        You must provide the base name which will become the root "
          "for the configuration file and the JSON output\n")


def get_basename_arg(program_file, argv):
    """Attempts to extract the basename for files from the argv list
    
    Args:
        program_file - string representing the name of the current main
                       program
        argv - the system argv list, containing the command line args

    Returns:
        The basename string, if it was specified in the arg list.
        Otherwise, None
    """
    if len(argv) == 2:
        return argv[1]
    else:
        print("{0}Incorrect number of arguments.".format(ERR_LABEL))
        err_str = "{0}Expected 2 arguments. Received {1} args"
        print(err_str.format(len(ERR_LABEL)*' ', len(argv)))
        usage_message(program_file)
        return None

def gen_timestamp(date_str):
    """Converts an ISO datestring into a timestamp suitable for use as a 
    component of a measurement
    
    The measurement timestamps are in milliseconds, so we multiply the
    Python value by 1K

    Args:
        date_str - ISO date string

    Returns:
        Integer representing the timestamp
    """
    #print("gen_timestamp -- date_str == '{}'".format(date_str))
    dto = isodate.parse_datetime(date_str)
    return round(dto.timestamp() * 1000)


def get_rest(url, authenticate):
    """GETs the JSON information referenced by the url

    Attempts to GET the JSON formatted information linked to by the URL, using
    the specified authentication information.  Converts the JSON formatted
    data into a Python dictionary for further use.
    
    Args:
        url - string containing the full URL to GET
        authenticate - tuple containg username and password to access the URL

    Returns:
        Python dictionary representation of the JSON data, if the GET results
        in a good status.
        None otherwise
    """
    json = None
    r = requests.get(url , auth=authenticate)
    if r.status_code == 200:
        json = r.json()
        #j = json.loads(r.text)
    else:
        estr = ("{0}Bad Status: '{1}' returned from \n"
                "{2}Request: '{3}'\n")
        print(estr.format(ERR_LABEL, r.status_code, ' '*len(ERR_LABEL), url))
    return json


def get_requirement_cnt(description, issues_w_req, issue_type):
    """Gets the number of requirements specified in the description string

    If the description is from an issue type that might have requirements,
    this function uses a heuristic regex to scan the string looking for
    patterns that match our definition of a requirement.  Returns the
    number of successful matches.
    
    Args:
        description - string to be scanned
        issues_w_req - collection containing the issue types that might have
                       requirements
        issue_type - string with the type of the issue that had the description

    Returns:
        The number of requirements found in the description.  Returns 0 if
        description is None, 
    """
    requirement_cnt = 0
    if ((description is not None) and (issue_type in issues_w_req)):
        requirement_cnt = len(re.findall("(?m)^\s*[\-\*\#0-9]", description))
    
    return requirement_cnt


def load_config(cfg_path):
    """Loads the configuration file from the specified path

    Attempts to load the specified configuration file, then extracts and
    transforms the data into attributes of the GripConfig object.  Sets some
    appropriate global values and returns the fully specified configuration
    object.
    
    Args:
        cfg_path - string containing the path to the configuration file

    Returns:
        Fully populated GripConfig object with most of the configuation data,
        if config loading was successful.  None otherwise.  Also sets up
        most values in the GLOBALS dictionary
    """
    global GLOBALS

    print("Loading configuration from: '{}'".format(cfg_path))
    config = configparser.ConfigParser()
    cfg_read = config.read(cfg_path)
    print(cfg_read)
    if cfg_read:
        print("Configuration file '{}' loaded".format(cfg_read[0]))
        cfg = config['DEFAULT']
        cfg_obj = GripConfig()
        for attr in cfg.keys():
            setattr(cfg_obj, attr, cfg[attr])
            
        for attr in ['defect_types'
                     ,'closed_status'
                     ,'issues_with_requirements'
                     ,'projects_to_analyze'
                     ,'fields_of_interest'
                     ,'data_fields'
                     ,'contributors'
                     ,'ignore_names']:
            setattr(cfg_obj,attr,cfg[attr].split(','))

        for attr in ['sq_metadata', 'verbose']:
            setattr(cfg_obj,attr,eval(cfg[attr]))

        GLOBALS['ACCOUNT_NAME'] = cfg_obj.account_name

        return cfg_obj
    else:
        return None


def gen_json(measurements, json_basename):
    """Generates a JSON representation of the measurements and writes it out

    Converts each element of measurements from a GripMeasurement namedtuple
    into a JSON representation and then adds it to a list of JSON objects.
    Once all objects are on the new list, a dated output file is created
    and the new JSON list is written to the file.
    
    Args:
        measurements - collection containing a traversable group of
                       GripMeasurement namedtuples
        json_basename - string containing the root text to use in creating
                        the output filename

    Returns:
        No returned value
    """
    measurement_list = [m._asdict() for m in measurements]
    json_string = json.dumps(measurement_list)
    if GLOBALS['VERBOSE']:
        print("\n\n{0}\n\n".format(json_string))

    date_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    json_filename = json_basename + date_str + ".json"
    json_file = openfile(json_filename,'w')
    if json_file is not None:
        json_file.write(json_string)
        json_file.close()
    else:
        err_str = "{0}Unable to open JSON output file: '{1}'"
        print(err_str.format(ERR_LABEL, json_filename))
