#!/usr/bin/python3
"""sonar_access.py gets the data from a SonarQube analysis and converts the
information into Grip measurements formatted as JSON.

This script assumes that the project analysis has already been completed and
that SonarQube has had time to store the results of the analysis in its
database.

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


import sys
import json
import datetime
from collections import namedtuple

from grip_import import GLOBALS
from grip_import import ERR_LABEL
from grip_import import load_config
from grip_import import get_rest
from grip_import import gen_timestamp
from grip_import import make_measurement
from grip_import import gen_json
from grip_import import get_basename_arg
from qz_utils import openfile


def get_val(sonar_rtn):
    """Utility method to extract a measurement value from the Sonar data
    structure

    Args:
        sonar_rtn - dictionary returned by Sonar for a given analysis result

    Returns:
        The extracted value
    """
    return sonar_rtn['val']


def prep_measurement(name, sonar_rtn):
    """Utility method to prepare a GripMeasurement

    Since all measurements from Sonar include the date of the analysis, we 
    encode the timestamp of that date for all measurements from this module

    Args:
        name - string containing the measurement name
        sonar_rtn - dictionary returned by Sonar for a given analysis result

    Returns:
        The extracted value
    """
    return make_measurement(name=name, value=get_val(sonar_rtn)
                            ,timestamp=GLOBALS['TIMESTAMP'])

#
# The following set of functions provide adapters for specific measurements.
# These are all represented in a look-up table that's used to dispatch
# each result to the proper measurement adapter
#
def lines_comments(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.lines_comments"
                                         ,sonar_rtn))
    

def loc(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.loc"
                                         ,sonar_rtn))


def duplicate_lines(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.duplicate_lines"
                                        ,sonar_rtn))


def complexity(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.complexity", sonar_rtn))


def file_complexity(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.file_complexity"
                                         ,sonar_rtn))


def class_complexity(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.class_complexity"
                                         ,sonar_rtn))


def function_complexity(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.function_complexity"
                                         ,sonar_rtn))


def test_cases(sonar_rtn, measurements):
    measurements.append(prep_measurement("measurement.test_cases", sonar_rtn))


def get_config(cfg_path):
    """Load and process the configuration file

    Includes specific settings specific for this module

    Args:
        cfg_path - string containing the path to the configuration file


    Returns:
        Fully populated GripConfig object with most of the configuration data,
        if config loading was successful.  None otherwise.  Also sets up
        some values in the GLOBALS dictionary
    """
    global GLOBALS
    cfg = load_config(cfg_path)
    if cfg is not None:
        GLOBALS['METADATA'] = cfg.sq_metadata
        print("Setting METADATA to: '{0}'".format(cfg.sq_metadata))

    return cfg


def sonar_main(config):
    """Main function to retrieve and process results of the SonarQube analysis

    Args:
        config - Fully Populated GripConfig object

    Returns:
        No returned value
    """
    global GLOBALS
    # Hardcoded to use default local SonarQube installation
    # You will likely need to change this for your specific situation
    authenticate = ("admin", "admin")
    url_str = ("http://localhost:9000/api/resources?scopes=PRJ&resource={0}"
               "&metrics=lines,ncloc,duplicated_lines,complexity,"
               "class_complexity,function_complexity,file_complexity,tests"
               "&format=json")
                                         
    url = url_str.format(config.sonarqube_project)
    print("Making Request for: '{0}'".format(url))
    sonar_data = get_rest(url, authenticate)

    if sonar_data is not None:
        print("Got back {} results...".format(len(sonar_data[0]['msr'])))
        # Define the look-up table that will map keys from the SonarQube
        # results to functions that will generate the corresponging
        # GripMeasurements
        lut = {"class_complexity":class_complexity
               ,"complexity":complexity
               ,"duplicated_lines":duplicate_lines
               ,"file_complexity":file_complexity
               ,"function_complexity":function_complexity
               ,"lines":lines_comments
               ,"ncloc":loc
               }
        GLOBALS['TIMESTAMP'] = gen_timestamp(sonar_data[0]['date'])
        measurements = []
        for v in sonar_data[0]['msr']:
            lut[v['key']](v, measurements)

        if measurements:
            for i in measurements:
                print(i)
            gen_json(measurements, config.json_basename + "-sq")
    else:
        err_str = "{0}Unable to retrieve issues for {1}.\n"
        sys.stderr.write(err_str.format(ERR_LABEL, ACCOUNT_NAME))


if __name__ == '__main__':
    basename = get_basename_arg(__file__, sys.argv)
    if basename is not None:
        cfg_path = basename + ".cfg"
        config = get_config(cfg_path)
        print("METADATA set to: '{0}'".format(GLOBALS['METADATA']))

        if config is not None:
            sonar_main(config)
        else:
            err_str = ("{0}Failed to load configuration file: '{1}'\n"
                       "{2}Exiting...\n")
            sys.stderr.write(err_str.format(ERR_LABEL
                                            ,cfg_path
                                            ,len(ERR_LABEL)*' '
                                            ))

