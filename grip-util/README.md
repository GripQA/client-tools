grip-util/
=========================

Several utility scripts and programs that we've found useful. This directory
also includes shared library definitions.

Some of this code was originally developed with Python 2.6, but those components
have been ported to Python 3.4. Other components were developed directly under
Python 3.4. As may be reaonably expected, the code here
might not be compatible with Python 2.x environments.

Files include:
----------------------

grip_import.py
----------------------
Contains the common data / functions that support Grip QA's
import scripts.

Most of these functions are utilities that are shared by multiple import
scripts.

#### Module External Functions:
* **make_measurement** - factory method to produce the GripMeasurement
namedtuple, with appropriate defaults

* **usage_message** - prints out a standard usage message for import modules
 
* **get_basename_arg** - checks the argument list and extracts the root name
given

* **gen_timestamp** - produce a timestamp given an ISO date string

* **get_rest** - request data for the given URL

* **get_requirement_cnt** - scan the given text for requirements and return the
number of requirements discovered

* **load_config** - loads the configuration file and converts the information
into a format appropriate for the configuration object

* **gen_json** - convert a list of GripMeasurement namedtuple's into a JSON
string

#### Module Classes:
* **GripConfig** - Class containing information extracted from the configuration
   file

#### Module Globals:
* **GLOBALS** - Dictionary of global values to be shared by all import modules
* **ERR_LABEL** - String with error message prefix
* **NOTE_LABEL** - String with note message prefix

qz_utils.py
----------------------
This module contains the utility functions for the system


#### Module Functions:
* **openfile** - Attempt to open the specified file and return a handle to
the file, if we succeed

* **restful_get** - Attempt to read the REST data at the given URL. This
function also handles the JSON processing

* **validpath** - Normalizes a pathname for the OS, verifies whether the
pathname exists and (optionally) checks r/w acess


#### Module Classes:
* **QZUtilsExc** - Exception handler

Support
----------------------

If you have any questions, problems, or suggestions, please submit an
[issue](/GripQA/client-tools/issues) or contact us at support@grip.qa.

License & Copyright
----------------------

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

