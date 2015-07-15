sonar-access/
=========================
sonar_access.py gets the data from a SonarQube analysis and converts the
information into Grip measurements formatted as JSON.

This script assumes that the project analysis has already been completed and
that SonarQube has had time to store the results of the analysis in its
database.

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
