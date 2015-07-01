GripQA Client Tools
=========================

Introduction / Description
----------------------

Grip QA's Client Tools code demonstrates a few of the techniques that we use
to access, and interact with, some
of the data resources that provide input to our analyses. We've also included
a group of utility programs/scripts that we've found useful for our operations.

Each of the sub-directories in this repo represent either a group of access
tools, or a group of shared utilities. Of course, we'll continue to add to
these resources as we
develop more applicable code *(or make our existing code somewhat more suitable
for external scrutiny)*.

Available Tools
----------------------

* **sonar_access/** - Our adapter for accessing data from a SonarQube server

* **jira_access/** - Our adapter for accessing data from a network JIRA instance

* **grip_util/** - Several utility scripts and programs that we've found useful.
  Also includes shared library definitions. *Note: For convenience, we've copied
the shared library files into each sub-directory where they're used. These
copies are kept up to date by our release scripts.

Coming Soon
----------------------

* **bugzilla_access/** - Our adapter for bugzilla, along with several rudimentary
analysis tools

Usability
----------------------

While every reasonable effort has been made to write tools that are robust for
our own use, we recognize that they are, in all likelihood, not universally
useful in their current form. We encourage all appropriate applications of these
tools,
both directly and as samples/templates for your own work. Given our specialized
application, the most common usage is likely to be as an example for how to
accomplish a specific task

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
