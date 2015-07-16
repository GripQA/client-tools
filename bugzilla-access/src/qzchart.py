#!/usr/bin/env python
""" qzchart.py - this module produces chart output of the analysis

Once metric data is collected, it can be passed along to this module to
generate an html page that contains charts providing a visual presentation
of the metrics and how the specific metrics compare to the norms that
we have collected


Module Functions:
-- create_chart_htm

Module Classes:
-- 


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
import os

import string
from datetime import datetime

import qzutils


# String for module name
if __name__ == '__main__':
    osf = sys.modules['__main__'].__file__
    pth,file = os.path.split(osf)
    modnm, ext = os.path.splitext(file)
else:
    modnm = __name__
# end if main
_MODNM = modnm.upper()
# Module name string for formatted printing
_MNS = ''.join([_MODNM, ": "])
# Base Error String
_ERS = ''.join([_MODNM, " ERROR: "])


def _gen_chart(scores, goodness):
    """Produces a string that can be printed to produce an html file that
    displays charts of the results
    
    Returns a string whose contents are an html page
    
    Arguments:
        scores -- dict containing the results to be displayed
        goodness -- integer representing relative "goodness" of the results
    
    """
    # I know that I didn't stick to 80 columns.  It's all for readability,
    #   easier maintenance and laziness.
    
    # cache this now, we'll use it multiple times later on
    kset = set(scores.keys())
    ddrsc = False
    ttrsc = False
    chrt = []
    chrt.append("<html>")
    chrt.append("  <head><title>Quality Zen Analysis Charts</title>")
    chrt.append("    <script type='text/javascript' src='https://www.google.com/jsapi'></script>")
    chrt.append("    <script type='text/javascript'>")
    chrt.append("      google.load('visualization', '1.0', {'packages':['gauge']});")
    chrt.append("      google.load('visualization', '1.0', {'packages':['corechart']});")
    chrt.append("      google.setOnLoadCallback(drawGChart);")
    chrt.append("      google.setOnLoadCallback(drawChart);")
    chrt.append("      function drawChart() {")
    chrt.append("        var data = google.visualization.arrayToDataTable([")
    chrt.append("          ['Metric', 'Norm', 'Your Org'],")
    if {'DDR', 'DDRSD'}.issubset(kset):
        # both keys are in the scores dict. Seems dumb to print one, without the other
        chrt.append("          ['Daily Bugs', {0}, {1}],".format(scores['DDR'][0], scores['DDR'][1]))
        chrt.append("          ['Daily SD', {0}, {1}],".format(scores['DDRSD'][0], scores['DDRSD'][1]))
        ddrsc = True
    if {'TTR', 'TTRSD'}.issubset(kset):
        # both keys are in the scores dict. Seems dumb to print one, without the other
        chrt.append("          ['Time2Res', {0}, {1}],".format(scores['TTR'][0], scores['TTR'][1]))
        chrt.append("          ['Time2RSD', {0}, {1}]".format(scores['TTRSD'][0], scores['TTRSD'][1]))
        ttrsc = True
    chrt.append("        ]);")
    chrt.append("        var options = {")
    chrt.append("          title: 'Your Metrics',")
    chrt.append("          hAxis: {title: 'Metrics', titleTextStyle: {color: 'red'}}")
    chrt.append("        };")
    chrt.append("         var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));")
    chrt.append("        chart.draw(data, options);")
    chrt.append("      }")
    chrt.append("      function drawGChart() {")
    chrt.append("        var gdata = google.visualization.arrayToDataTable([")
    chrt.append("          ['Label', 'Value'],")
    chrt.append("          ['Goodness', {0:.1f}]".format(goodness))
    chrt.append("        ]);")
    chrt.append("        var options = {")
    chrt.append("          width: 400, height: 420,")
    chrt.append("          greenFrom: 60, greenTo: 100,")
    chrt.append("          yellowFrom:40, yellowTo: 60,")
    chrt.append("          redFrom:0, redTo:40,")
    chrt.append("          minorTicks: 5")
    chrt.append("        };")
    chrt.append("        var gchart = new google.visualization.Gauge(document.getElementById('gchart_div'));")
    chrt.append("        gchart.draw(gdata, options);")
    chrt.append("      }")
    chrt.append("    </script>")
    chrt.append("  </head>")
    chrt.append("")
    chrt.append("  <body>")
    chrt.append("    <p><strong>Chart prepared: {0}</strong></p>".format(string.split(str(datetime.now()),'.')[0]))
    if ddrsc or ttrsc:
        chrt.append("    <div id='chart_div' style='width: 900px; height: 500px;'></div>")
    chrt.append("    <div><p><strong>'Goodness' is a measure of how well you compare on overall metrics with the 'Norm' group. A higher number is better</strong></p></div>")
    chrt.append("    <div id='gchart_div'></div>")
    chrt.append("  </body>")
    chrt.append("</html>")
    return '\n'.join(chrt)
# end gen_chart


def _get_name(org):
    """Attempt to open the specified file and return a handle to the file, 
    if we succeed
    
    Returns the generated filename for the html file.
    
    Arguments:
        org -- string containing the name of the owning organization - this
                will become part of the htmlfilename, so don't pass
                anything really wierd
    """
    if org is not None:
        dtn = str(datetime.now())
        nms = [''.join(org.split())]
        nms.append(dtn[:4])
        nms.extend([dtn[x:x+2] for x in range(5,18,3)])
        nms.append(dtn[20:])
        nms.append('.html')
        retnm = ''.join(nms)
    else:
        retnm = 'qzchart.html'
    return retnm
# end get_name


def create_chart_htm(org, dhpath, scores, goodness):
    """Attempt to open the specified file and return a handle to the file,
    if we succeed
    
    Returns the relative pathname to the html file, if it's created.  Otherwise
        returns None
    Arguments:
        org -- string - containing the name of the owning organization - this
                will become part of the htmlfilename, so don't pass
                anything really wierd.  If org is none & dhpath is none,
                we'll create the file in the current directory with a
                hardcoded name
        dhpath -- string - containing the pathname of the target directory for
                the dashboard html file.  We'll process this to get a usable
                filesystem pathname.  If  None, we'll try to dump it in the
                directory at "../html/charts.d/", relative to the current
                working directory.  NOTE:  When running as a server, this
                last is the behavior that we want.
        scores -- dict containing the results to be displayed
        goodness -- integer representing relative "goodness" of the results
    """
    chrts = _gen_chart(scores, goodness)
    if dhpath is not None:
        # Now that dhpath comes in as a directory, rather than a path to a
        #   file, we don't use os.path.dirname(), at least for now.
        # bpath = os.path.dirname(dhpath)
        bpath = dhpath
    else:
        bpath = '../html/charts.d'
    hpath = '/'.join([bpath, _get_name(org)])
    retval = None
    try:
        fhndl = qzutils.openfile(hpath, mode='w')
        if fhndl is not None:
            # We opened the file, let's try to dump the data
            fhndl.write(chrts)
            fhndl.close()
            retval = hpath
        # end if fhndl is good
    except Exception as ex:
        exstr = "{0}Could not write HTML file: {1}\n   Exception: {2}\n"
        sys.stderr.write(exstr.format(_ERS, hpath, ex))
    return retval
    
# scr = {'ddr':[200,216],'ddrsd':[87,195],'ttr':[28,47],'ttrsd':[17,85]}
