jira-access/
=========================

jira_access.py
----------------------

Retrieves and processes issue data from a JIRA installation

The retrieved information is scanned to determine things like the number of
open defects and the number of requirements.  This extracted data is 
transformed into standard GripQA measurement records formatted as JSON.

The JIRA data is accessed using a RESTful API.  The most recent revision of
the API at the time this code was developed (JIRA REST API Version 2) provides
the best support, but some effort was made to work, on a limited basis, with
earlier revisions of the API.  We implemented a set of simple adapters for
older API versions that "should" work.

jira_descr.py
----------------------

Queries JIRA for issue description info

The information includes, values for:

- issue type
- status
- resolution
- priority

The information is retrieved and formatted for nice printing.  This is a
utility for configuring the JIRA access for a new project.

[JIRA RESTful API documentation](https://docs.atlassian.com/jira/REST/latest/#d2e1750)

Python Version Disclaimer
----------------------

This code was developed with Python 3.4, and, as may be reaonably expected,
might not be compatible with Python 2.x environments.

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
