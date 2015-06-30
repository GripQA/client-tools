#!/usr/bin/python3
"""jira_descr.py queries JIRA for issue description info

The information includes, values for:
- issue type
- status
- resolution
- priority
The information is retrieved and formatted for nice printing.  This is a
utility for configuring the JIRA access for a new project.

Source documentation: https://docs.atlassian.com/jira/REST/latest/#d2e1750

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
import textwrap


from grip_import import ERR_LABEL
from grip_import import get_basename_arg
from grip_import import load_config
from grip_import import get_rest


def dump_data(jsn):
    wrapper = textwrap.TextWrapper(initial_indent = "   "
                                   ,subsequent_indent = ' '*16)
    for i in jsn:
        o_str = "{0} -- {1}".format(i['name'], i['description'])
        for l in wrapper.wrap(o_str):
          print(l)



def descr_main(config):
    """Main function for retrieving and displaying Java issue information

    Uses REST APIs to GET a project's names for various issue types, states and
    priorities.  Formats the output for easier reading.

    Args:
        config - configuration object

    Returns:
        No return value
    """
    labels = ["issuetype"
              ,"status"
              ,"resolution"
              ,"priority"
              ]
    api = config.jira_rest_api
    auth = (config.username, config.password)
    for l in labels:
        print("\n\n{0}:".format(l))
        url = "{0}{1}{2}".format(config.server, api, l)
        jsn = get_rest(url, auth)
        dump_data(jsn)
        


if __name__ == '__main__':
    basename = get_basename_arg(__file__, sys.argv)
    if basename is not None:
        cfg_path = basename + ".cfg"
        config = load_config(cfg_path)
        if config is not None:
            descr_main(config)
        else:
            err_str = ("{0}Failed to load configuration file: '{1}' "
                       "Exiting...")
            print(err_str.format(ERR_LABEL, cfg_path))
