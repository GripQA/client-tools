#!/usr/bin/env python
"""cfg.py - generate a config file from the coded values
Usage:  cfg.py [cfg_file_path]

If cfg_file_path not specified, will use default path/filename.

Edit the gen_cfg() function body to modify the contents of the generated
cfg file.


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
import ConfigParser

_DEFAULT_PATH = './.bz.cfg'


def gen_cfg(cfgf=_DEFAULT_PATH):
    config = ConfigParser.SafeConfigParser()
    config.add_section('Query')
    # config.set('Query','query','ALL')
    config.set('Query','query','LIST')
    # config.set('Query','query','RANGE')
    # config.set('Query','query','DATE')
    config.set('Query','organization','Mozilla')
    config.set('Query','base_url','http://python.org/REST_API')
    config.set('Query','list','231,728,999,2001')
    # config.set('Query','range','7070,8080')
    # config.set('Query','date','2012-05-25,2012-05-30')
    config.add_section('Database')
    config.set('Database','databasepath','../test/qztest.pkl')
    config.add_section('Metrics')
    # config.set('Metrics','M_ALL','False')
    config.set('Metrics','M_TTR','True')
    config.set('Metrics','M_YDR','True')
    config.set('Metrics','M_MDR','True')
    config.set('Metrics','M_DDR','True')
    
    try:
        cfgf = open(cfgf,'w')
        config.write(cfgf)
        cfgf.close
    except Exception as ex:
        sys.stderr.write("ERROR:  Unable to write to cfg file: {0}\n".format(fpath))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # just the module name, use default path
        gen_cfg()
    elif len(sys.argv) == 2:
        # use the second argument for the path
        gen_cfg(sys.argv[1])
    else:
        sys.stderr.write("ERROR:  Expected 1 argument. {0} given.\n".format(len(sys.argv) - 1))
        sys.stdout.write("{0}\n".format(__doc__))
