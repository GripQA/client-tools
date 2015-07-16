#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2015 Grip QA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import cgitb

import qzmain
import qzchart
import qzargs

import os

cgitb.enable()
print("Content-type: text/html")
print("")
print ('<html><head><title>Quality Zen Analysis</title><meta http-equiv="refresh" content="20"></head><body><p>')
print("<strong>Quality Zen Software Quality Analysis:</strong><br><pre>")
theargs = qzargs.CfgCmdArgs()
cfg_load = qzargs._load_cfg(theargs, '../html/cfg.d/qzcfg.cfg')
print("Current WD is '" + os.getcwd() + "'")
rval = -1
if cfg_load:
    rval = qzmain.run_qz(theargs, False)
else:
    print("Failed to load configuration file...")
print("</pre></p>")
if rval == 0:
    print('<a href="../charts.d/qzchart.html" target="_blank" title="Quality Dashboard">View your <strong>Quality Dashboard</strong></a>  &nbsp;<em><font color="green">(Opens in new tab)</font></em>')
else:
    print("<br>Quality Zen Analysis Failed. Sorry. Please try again with different parameters.<br>")
print('<br><br><a href="../index.html" title="Quality Zen Home">Return to Quality Zen home page</a><br>')
print('<br><a href="../loadcfg.php" title="Quality Zen Config">Configure Quality Zen</a><br>')
print("</body></html>")
