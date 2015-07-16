bugzilla-access/
=========================

Introduction:
----------------------

bugzilla-access contains a web based proof of concept application that attempts
to use data analysis to predict the overall quality of a given software
project.  Based on the analysis performed, the system calculates an overall
"goodness" score.

The effort was originally a Quality Zen project.  All rights are now assigned
to GripQA.  Although no longer actively moving forward, planned 
enhancements included generating recommendations for improvement and
guidance regarding best practices.

Platform:
----------------------

The bulk of the code is written in Python, with supporting bits of PHP and
CGI.  The system was running on a shared server in the Amazon Web
Services compute cloud.  Although the Python code was ported to 3.0,
constraints on our Amazon instance caused us to make the first release
using Python 2.7.

Data extracted from external sources is normalized and
stored in MongoDB for future analysis and reference processing.  Our PHP
and CGI code assumes a relatively vanilla Apache web server, but it should
be reasonably portable to other servers.

Current State:
----------------------

It is somewhat self indulgent to refer to this codebase, in its current
state, as a prototype.  As indicated previously, it's really more of a
proof of concept.

The architecture supports an extremely flexible connection to almost any
data source, but we have thus far only implemented a connector for
Bugzilla.  Implementing connectors to other data sources is
straightforward, and the data normalization code is also easily extensible.

Likewise, the architecture supports easily extensible analysis algorithms,
either with our Python framework, or directly on the MongoDB that underlies
this project.

Future:
----------------------

Unlike our other projects, bugzilla-access was envisioned as a stand-alone
web app. It currently stores data in a unstructured DB rather than producing
data in a Grip exchange format for downstream processing. We're not currently
planning to move the entire codebase forward, but the front-end data
acquisition connector will almost certainly find its way into the GripQA
platform in some form.

Dependencies:
----------------------

Deployment and full execution requires the following external packages:
* [pymongo](http://api.mongodb.org/python/current/)
* [MongoDB](https://www.mongodb.org/)

Support
----------------------

If you have any questions, problems, or suggestions, please submit an
[issue](../../../issues) or contact us at support@grip.qa.

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
