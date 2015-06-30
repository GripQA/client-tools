#!/usr/bin/python3
"""jira_access.py retrieves and processes issue data from a JIRA installation

The retrieved information is scanned to determine data points that include
the number ofopen defects and the number of requirements.  This extracted
data is transformed into standard GripQA measurement records formatted as
JSON.

The JIRA data is accessed using a RESTful API.  The most recent revision of
the API at the time this code was developed (JIRA REST API Version 2) provides
the best support, but some effort was made to work, on a limited basis, with
earlier revisions of the API.  We implemented a set of simple adapters for
older API versions that "should" work.

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
import requests
import isodate
import configparser
import datetime

import textwrap
import re
from collections import namedtuple
from collections import OrderedDict
from operator import itemgetter

from grip_import import GLOBALS
from grip_import import ERR_LABEL
from grip_import import NOTE_LABEL
from grip_import import gen_timestamp
from grip_import import get_rest
from grip_import import get_requirement_cnt
from grip_import import load_config
from grip_import import gen_json
from grip_import import make_measurement
from grip_import import get_basename_arg
from qz_utils import openfile


# Should script output be measurements, or a dump
MEASUREMENTS_OUT = True


#
# Set of adapter methods to encapsulate the GripMeasurement object
# creation for each of the measurement types.
#
def defects_added(timestamp, metadata):
    return make_measurement(name="measurement.defects_added"
                            ,metadata=metadata
                            ,timestamp=timestamp
                            )


def defects_closed(timestamp, metadata):
    return make_measurement(name="measurement.defects_closed"
                            ,metadata=metadata
                            ,timestamp=timestamp
                            )


def defects_total(value, timestamp, metadata):
    return make_measurement(name="measurement.defects"
                            ,metadata=metadata
                            ,value=float(value)
                            ,timestamp=timestamp
                            )


def requirements_added(value, timestamp, metadata):
    return make_measurement(name="measurement.requirements_added"
                            ,metadata=metadata
                            ,value=float(value)
                            ,timestamp=timestamp
                            )


def requirements_closed(value, timestamp, metadata):
    return make_measurement(name="measurement.requirements_closed"
                            ,metadata=metadata
                            ,value=float(value)
                            ,timestamp=timestamp
                            )


def requirements_total(value, timestamp, metadata):
    return make_measurement(name="measurement.requirements"
                            ,metadata=metadata
                            ,value=float(value)
                            ,timestamp=timestamp
                            )


def sprints_closed(timestamp, metadata):
    return make_measurement(name="measurement.sprints_closed"
                            ,metadata=metadata
                            ,timestamp=timestamp
                            )


# Counters
class Counter(object):
    def __init__(self):
        self._created = 0
        self._open = 0
        self._closed = 0
        self._total = 0
    @property
    def created(self):
        return self._created
    @created.setter
    def created(self, newval):
        self._created = newval
    @property
    def open(self):
        return self._open
    @open.setter
    def open(self, newval):
        self._open = newval
    @property
    def closed(self):
        return self._closed
    @closed.setter
    def closed(self, newval):
        self._closed = newval
    @property
    def total(self):
        return self._total
    @total.setter
    def total(self, newval):
        self._total = newval


class Counters(object):
    def __init__(self):
        self._defects = Counter()
        self._issues = Counter()
        self._requirements = Counter()
        self._sprints = Counter()
        self._measurements = []
        self._contributors = {}
    @property
    def defects(self):
        return self._defects
    @property
    def issues(self):
        return self._issues
    @property
    def requirements(self):
        return self._requirements
    @property
    def sprints(self):
        return self._sprints
    @property
    def measurements(self):
        return self._measurements
    @property
    def contributors(self):
        return self._contributors


def build_proj_name2key_map(projects):
    """Creates a map of project names to project keys

    Args:
        projects - iterable containing collection of projects

    Returns:
        Dictionary that maps from project names to project keys, or, as we
        use the terms, full project names ("Really Important New Project") to
        project names ("RINP").
    """
    proj_name2key_map = {}
    for proj in projects:
        proj_name2key_map[proj['name']] = proj['key']

    return proj_name2key_map
        

def get_proj_from_view(view, proj_name2key_map):
    """Utility method to go from a view to a project

    Args:
        view - sprint view object
        proj_name2key_map - dictionary mapping project names to project keys

    Returns:
        String containing the project key
    """
    return proj_name2key_map[view['name']]


def get_name(field):
    """Utility method to extract a contributor name and email address from
    a JIRA field

    Args:
        field - dictionary representing data returned as a JIRA field

    Returns:
        Tuple containing the extracted contributor's name and email address as
        strings
    """
    return field['displayName'], field['emailAddress']


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
         GLOBALS['VERBOSE'] = cfg.verbose

    return cfg


def get_project(issue):
    """Utility method to return the project key from an issue

    Should handle both current and alpha1 API data using try: except: blocks

    Args:
        fields - dictionary representing an issue

    Returns:
        String containing the issue's project key.  None should never be
        returned
    """
    proj = None
    try:
        # This should handle the current API
        proj = issue['fields']['project']['key']
    except KeyError:
        # This shouldn't happen, but...
        proj = None

    return proj


def make_metadata(project):
    """Utility method to create a metadata dictionary appropriate for
    measurements generated by this script

    This is where you'd edit to change the format / contents of the 
    measurement's metadata field

    Args:
        project - project that is associated with this issue

    Returns:
        Dictionary containing the defined metadata
        strings
    """
    return {"project":project}


def check_open_requirements(issue
                            ,issues_w_requirements
                            ,requirements_counter
                            ,measurements
                            ):
    """If the issue has requirements, adds to the open and total requirements
    counts

    Unfortunately, this evaluation is not strictly accurate, since they could
    have added the requirement any time after creation.  However, short of
    walking backwards through the list of changes attempting to determine
    when requirements were added, we'll just look at the current state of
    the issue.

    Args:
        cfg_path - string containing the path to the configuration file

    Returns:
        No return value
    """
    i_fields = issue['fields']
    reqmnt_cnt = get_requirement_cnt(i_fields['description']
                                     ,issues_w_requirements
                                     ,i_fields['issuetype']['name']
                                     )
    if reqmnt_cnt > 0:
        if GLOBALS['VERBOSE']:
            fstr = "Adding {0} requirements for: {1}"
            print(fstr.format(reqmnt_cnt, issue['key']))
        requirements_counter.open += reqmnt_cnt
        requirements_counter.total += reqmnt_cnt        

        ts = gen_timestamp(i_fields['created'])
        metadata = make_metadata(get_project(issue))
        measurements.append(requirements_added(reqmnt_cnt, ts , metadata))
        total = requirements_counter.total
        measurements.append(requirements_total(total, ts, metadata))


def check_requirements_closed(issue
                              ,close_date
                              ,issues_w_requirements
                              ,requirements_counter
                              ,measurements
                              ):
    """Check the specified closed issue for requirements that might also have
    been closed

    Args:
        issue - dictionary representing the issue to be checked
        close_date - date the issue was closed
        issues_w_requirements - collection of issue types that have requirements
        requirements_counter - counter object for requirements
        measurements - collection of measurements

    Returns:
        No return value
    """
    reqmnt_cnt = get_requirement_cnt(issue['fields']['description']
                                     ,issues_w_requirements
                                     ,issue['fields']['issuetype']['name'])
    if reqmnt_cnt > 0:
        requirements_counter.closed += reqmnt_cnt
        requirements_counter.open -= reqmnt_cnt

        ts = gen_timestamp(close_date)
        metadata = make_metadata(get_project(issue))
        measurements.append(requirements_closed(reqmnt_cnt, ts, metadata))


def is_defect(issue, defect_types):
    """Determines whether the specified issue represents a defect

    This is based on comparing the issue type to a collection of issue
    types believed to represent defects in the target JIRA installation
    Handles both modern API values and values returned by the alpha1 API

    Args:
        issue - dictionary representing the issue to be checked
        defect_types - collection containing issue types to be considered 
                       defects

    Returns:
        True if the specified issue is a defect.  False otherwise
    """
    if issue['fields']['issuetype']['name'] in defect_types:
        return True
    else:
        return False


def get_datetime(issue, field):
    """Utility method to extract the specified field's datetime from the issue
    data

    Attempts to handle the situation where the specified field isn't present
    in the target issue dictionary

    Args:
        issue - dictionary representing the issue to be processed
        field - string containing the name of the datetime field to get

    Returns:
        Datetime string extracted from the issue, or None if the field
        isn't present in the issue.
    """
    datetime_field = issue['fields'].get(field, None)
    if GLOBALS['VERBOSE'] and datetime_field is None:
        fstr = "{0}Issue '{1}' does not have a/an '{2}' field"
        print(fstr.format(NOTE_LABEL, issue['key'], field))
    # else:
    #     fstr = "Issue: {0} - {1} on: {2}"
    #     print(fstr.format(issue['key'], field, rtn_datetime))
    return datetime_field


#
# Set of utility functions that (may) generate measurements and increment
# the appropriate counters for artifacts of interest in the JIRA data
#
def log_defect_created(issue, defect_counter, measurements):
    defect_counter.total += 1
    defect_counter.created += 1

    create_datetime = get_datetime(issue, "created")
    if GLOBALS['VERBOSE']:
        fstr = "New Defect: {0} at {1}"
        print(fstr.format(issue['key'], create_datetime))
    ts = gen_timestamp(create_datetime)
    metadata = make_metadata(get_project(issue))
    measurements.append(defects_added(ts, metadata))
    total = defect_counter.total
    measurements.append(defects_total(total, ts, metadata))


def log_defect_closed(issue, close_date, defect_counter, measurements):
    defect_counter.closed += 1
    ts = gen_timestamp(close_date)
    metadata = make_metadata(get_project(issue))
    measurements.append(defects_closed(ts, metadata))


def log_issue_created(issue_counter):
    # no measurement to produce, just update counters
    issue_counter.total += 1
    issue_counter.created += 1
    issue_counter.open += 1


def log_issue_closed(issue_counter):
    issue_counter.open -= 1
    issue_counter.closed += 1


def log_sprint_closed(close_timestamp, project, sprint_counter, measurements):
    # Note: project - string giving name of the project to use to create
    #                 metadata
    sprint_counter.total += 1
    metadata = make_metadata(project)
    # close_timestamp should already come in as a timestamp
    measurements.append(sprints_closed(close_timestamp, metadata))


def get_sprint_list(api, proj_name2key_map, authenticate):
    """Retrieves the projects sprints

    Sprint data "may" be available through another REST API. We use this
    API to retrieve information about the project's sprints

    Args:
        api - string containing the URL component for the desired API
        proj_name2key_map - maps from poject names to project keys
        authenticate - tuple containing username & password to log into JIRA

    Returns:
        List containing sprint dictionaries
    """
    sprint_list = []
    view_id_rest = get_rest(api+"rapidviews/list", authenticate)
    for v in view_id_rest['views']:
        v_id = v['id']
        url = api + "sprintquery/{0}?includeHistoricSprints=true".format(v_id)
        sprint_id_rest = get_rest(url, authenticate)
        proj = get_proj_from_view(v, proj_name2key_map)
        for s in sprint_id_rest['sprints']:
            sprint_list.append((v_id, s['id'], proj))
            
    return sprint_list
    

def proc_sprints(api, proj_name2key_map, authenticate, counters):
    """Retrieves and processes the sprint information

    Retrieves the list of sprints associated with the current project, then
    scans the list to extract sprint endTime dates.  These represent the 
    sprint_closed measurement

    Args:
        api - string containing the URL component for the desired API
        proj_name2key_map - maps from project names to project keys
        authenticate - tuple containing username & password to log into JIRA
        counters - object containing occurrence counters

    Returns:
        No return value
    """
    sprint_list = get_sprint_list(api, proj_name2key_map, authenticate)
    url_str = ("rapid/charts/scopechangeburndownchart.json?"
               "rapidViewId={0}&sprintId={1}")
    for sp in sprint_list:
        url = api + url_str.format(sp[0], sp[1])
        sprint_rest = get_rest(url, authenticate)
        log_sprint_closed(sprint_rest['endTime']
                          ,sp[2]
                          ,counters.sprints
                          ,counters.measurements)


def proc_histories(issue, config, counters):
    """Walks through the issues history and extracts artifacts of interest

    The issue's history is a dated collection of events that have occurred
    with the issue.  Only a subset of those are interesting to us.  This
    function walks the collection of events and handles those that concern
    us.  This method does examine all history records to populate the
    collection of collaborators.

    Note the early return if the issue doesn't appear to have a changelog.
    This allows the function to work with issues returned from versions of
    the REST API that don't support the changelog/history

    Args:
        issue - dictionary representing the issue to be checked
        config - configuration object
        counters - object containing occurrence counters

    Returns:
        No return value
    """
    close_date = None
    if not issue['changelog']['histories']:
        # The list of history items is empty, so we can't traverse the list
        # looking for a closed date
        if GLOBALS['VERBOSE']:
            note_str = ("{0}Issue '{1}' does not appear to have a history "
                        "list.\n{2}No history processed")
            print(note_str.format(NOTE_LABEL
                                  ,issue['key']
                                  ,len(NOTE_LABEL)*' '
                                  ))
        # Without a changelog, we might still be able to guess at the
        # closed date.
        # Unfortunately, the heuristic for determining the date the issue
        # was closed is a bit tricky:
        # If the issue has a resolution date, use that date, as long as
        # the issue has a closed status.  We have to check both the date and
        # the status because JIRA doesn't allow users to remove the resolution
        # date, even if the issue is later re-opened.
        # If there is no resolution date, but the issue has a closed status,
        # we'll be forced to use the updated date as the close date
        if issue['fields']['status'] in config.closed_status:
            # The issue is closed
            resol_date = get_datetime(issue, "resolutiondate")
            if resol_date is not None:
                close_date = resol_date
            else:
                close_date = get_datetime(issue, "updated")

    for c in issue['changelog']['histories']:
        # if the histories list is empty, this block will never be executed,
        # but writing it this way spares me even deeper nesting.
        for i in c['items']:
            author = get_name(c['author'])
            counters.contributors[author[1]] = author[0]
            if i['field'] == "status":
                if i['toString'] in config.closed_status:
                    # Closing the issue, either it's not currently closed,
                    # or we have a later close date.  Note that c['created']
                    # is the date when of this change record to the issue
                    change_created = c['created']
                    if close_date is None or change_created > close_date:
                        close_date = change_created
                else:
                    # Didn't close the issue, may have re-opened it, so
                    # no close_date
                    close_date = None

    if close_date is not None:
        log_issue_closed(counters.issues)

        if is_defect(issue, config.defect_types):
            if GLOBALS['VERBOSE']:
                log_str = "Logging defect closed for {0} on {1}"
                print(log_str.format(issue['key'], close_date))
            log_defect_closed(issue
                              ,close_date
                              ,counters.defects
                              ,counters.measurements
                              )

        check_requirements_closed(issue
                                  ,close_date
                                  ,config.issues_with_requirements
                                  ,counters.requirements
                                  ,counters.measurements
                                  )


def proc_issue(issue, config, counters):
    """Examines an individual issue

    Extracts information about the contributors involved, creation date,
    history, issue type and requirements specified

    Args:
        issue - dictionary representing the issue to be checked
        config - configuration object
        counters - object containing occurrence counters

    Returns:
        No return value
    """
    #issue_id = issue['key']
    i_fields = issue['fields']

    # Record contributors for this issue
    creator = get_name(i_fields['creator'])
    counters.contributors[creator[1]] = creator[0]
    reporter = get_name(i_fields['reporter'])
    counters.contributors[reporter[1]] = reporter[0]

    log_issue_created(counters.issues)

    if is_defect(issue, config.defect_types):
        log_defect_created(issue, counters.defects, counters.measurements)

    check_open_requirements(issue
                            ,config.issues_with_requirements
                            ,counters.requirements
                            ,counters.measurements)
    proc_histories(issue, config, counters)


def adapt_2alpha1_issue(issue_ref, config, auth, counters):
    """Adapts an issue from the old version of the API into a structure
    that can be processed by code expecting to work on current data

    Transforms the structure of the issue to conform to that of an issue
    from the current version of the API.  All differences in data of
    interest will be handled in this function.  Due to information missing
    from the older version, we're forced to make some assumptions to fill
    in the gaps

    Args:
        issue_ref - dictionary representing the issue to be checked
        config - configuration object
        auth - tuple with username / password for basic authentication
        counters - object containing occurrence counters

    Returns:
        An issue compatible with the current vesion of the API
    """
    def progress_counter():
        # Since this function needs to make several REST requests for each
        # issue, it can be quite slow.  This progress count periodically
        # indicates the progress on stdout, so the user knows that we're
        # still going
        try:
            adapt_2alpha1_issue.iter_counter += 1
        except AttributeError:
            reset_progress_counter()

        if (adapt_2alpha1_issue.iter_counter % 10) == 0:
            f_str = "{0}Processing {1}th issue"
            print(f_str.format(NOTE_LABEL, adapt_2alpha1_issue.iter_counter))

    def reset_progress_counter():
        # Resets the iter_counter variable to 1, can also be used to initialize
        # the counter
        adapt_2alpha1_issue.iter_counter = 1
            
    def handle_issuetype(issue):
        # Adapts the issue type to the modern format
        tmp_i = issue['fields']['issuetype']
        tmp_i['name'] = tmp_i['value']['name']

    def handle_project(issue):
        # Adapts the project data to the modern format
        tmp_p = issue['fields']['project']
        tmp_p['key'] =  tmp_p['value']['key']

    def handle_name_field(issue, name_field, auth, contributors):
        # Adapts the name/email address data to a modern
        # format.  Also adds the name/email addr tuple to the
        # collection of contributors
        #
        # name_field - specifies which field we'll be transfering
        #
        # Need to make an API call to get the details of the name
        tmp_n = issue['fields'][name_field]
        url = tmp_n['value']['self']
        name_info = get_rest(url, auth)
        name = name_info['displayName']
        email = name_info['emailAddress']
        # adapt the specified issue
        tmp_n['displayName'] = name
        tmp_n['emailAddress'] = email
        # update the contributors collection
        contributors[email] = name

    def handle_description(issue):
        # Some customer issues don't seem to have any text in their
        # description fields, so I'm not sure what the description is
        # supposed to look like in an alpha API issue.  I'm kind of
        # guessing here.
        #
        # Cache the current info in a new key, since we'll be replacing
        # the value of the description key
        descr = issue['fields']['description']
        issue['fields']['description-alpha'] = descr
        # use the "['fields']['description']['value'] field to populate
        # the new format description
        issue['fields']['description'] = descr.get("value")

    def handle_status(issue):
        # Adapt the status field to the current format
        #
        # Cache the current info in a new key, since we'll be replacing
        # the value of the status key
        descr = issue['fields']['status']
        issue['fields']['status-alpha'] = descr
        # use the "['fields']['status']['value'] field to populate
        # the new format status
        issue['fields']['status'] = descr.get("value")['name']

    def handle_datetime(issue, field):
        # Adapts a datetime field to the new format, preserves the old
        # field values in a new field named <field_name>-alpha.
        #
        # field - the name of the datetime field to handle.
        #
        tmp_datetime_field = issue['fields'].get(field, None)
        if tmp_datetime_field is not None:
            tmp_datetime = issue['fields'][field]['value']
            stash_field = field + "-alpha"
            issue['fields'][stash_field] = issue['fields'][field]
            # use the "['fields'][field]['value'] field to populate
            # the new format description
            issue['fields'][field] = tmp_datetime
        elif GLOBALS['VERBOSE']:
            fstr = "{0}Issue '{1}' does not have a/an '{2}' field"
            print(fstr.format(NOTE_LABEL, issue['key'], field))

    def handle_all_datetimes(issue):
        # Adapts all datetime fields of interest to the new format
        for dtm in ["created", "updated", "resolutiondate"]:
            handle_datetime(issue, dtm)

    def make_creator_field(issue):
        # transfers data from the reporter field to the issue's creator field
        # MUST be run after the reporter field has been populated correctly
        reporter = get_name(issue['fields']['reporter'])
        issue['fields']['creator'] = {"displayName":reporter[0]
                                      ,"emailAddress":reporter[1]
                                      }

    def make_history(issue):
        # Although issues obtained through the alpha REST API don't have
        # changelogs & histories, we need dummy values for later processing
        issue['changelog'] = {"histories":[]}

    alpha_issue = get_rest(issue_ref['self'], auth)
    if alpha_issue is not None:
        progress_counter()
        handle_issuetype(alpha_issue)
        handle_project(alpha_issue)
        handle_name_field(alpha_issue, "reporter", auth, counters.contributors)
        make_creator_field(alpha_issue)
        handle_all_datetimes(alpha_issue)
        # Since we won't have a history to process for the alpha issues:
        handle_name_field(alpha_issue, "assignee", auth, counters.contributors)
        handle_description(alpha_issue)
        handle_status(alpha_issue)
        make_history(alpha_issue)
        
    return alpha_issue


def handle_contributors(contributors):
    """Formats the collection of contributors for pretty printing

    Args:
        contributors - collection containing names and email addresses of
                       the project's contributors

    Returns:
        No return value
    """
    print("\n\nContributors:")
    for k,v in contributors.items():
          print("   {0} - {1}".format(v, k))
    print("\n")


def dump_issue(issue, config, counters):
    """Formats the specified issue for pretty printing

    Also processes the issue to extract contributor information

    Args:
        issue - dictionary representing the issue to be checked
        config - configuration object
        counters - object containing occurrence counters

    Returns:
        No return value
    """
    issue_id = issue['key']
    i_fields = issue['fields']
    creator = get_name(i_fields['creator'])
    counters.contributors[creator[1]] = creator[0]
    reporter = get_name(i_fields['reporter'])
    counters.contributors[reporter[1]] = reporter[0]

    fstr = ("\nIssue: {0}, a '{1},' was created by {2} on {3}. Its current "
            "status is '{4}'\n"
            "           Reported by: {5}\n"
            "           Description:")
    print(fstr.format(issue_id
                      ,i_fields['issuetype']['name']
                      ,creator[0]
                      ,i_fields['created']
                      ,i_fields['status']['name']
                      ,reporter[0]
                  ))
    raw_descr = i_fields['description']
    if raw_descr is not None:
        fmt_descr = textwrap.wrap(raw_descr)
    else:
        fmt_descr = ["'{}'".format(raw_descr)]
        for l in fmt_descr:
            print("              {0}".format(l))

    for c in issue['changelog']['histories']:
        for i in c['items']:
            author = get_name(c['author'])
            counters.contributors[author[1]] = author[0]
            if i['field'] in config.fields_of_interest:
                print("   On {0}, {1} changed {2} from '{3}' to '{4}'"
                      .format(c['created'], author[0]
                              ,i['field']
                              ,i['fromString']
                              ,i['toString']))


def jira_main(config):
    """Main function for processing JIRA information

    Uses REST APIs to GET a project's issues and sprint information.
    Analyzes both to gather measurements that are interesting to Grip then
    produces a file containing a JSON representation of the extracted
    measurements

    Args:
        config - configuration object

    Returns:
        No return value
    """
    # set up the counters
    counters = Counters()
    # prepare for getting issues
    authenticate = (config.username, config.password)
    server = config.server
    api = config.jira_rest_api
    #
    # Get the list of projects.  We'll process issues for each project
    proj_url = "{0}{1}project".format(server, api)
    projects = get_rest(proj_url, authenticate)
    print("{0}Found {1} projects.".format(NOTE_LABEL, len(projects)))
    proj_name2key_map = build_proj_name2key_map(projects)
    # flag will be set to True if we find any issues in the projects
    found_issues = False
    for proj in projects:
        if proj['key'] in config.projects_to_analyze:
            query_str = ("search?jql=project={0}+order+by+created+asc"
                         "&startAt=0&expand=changelog&maxResults=-1")
            query = query_str.format(proj['key'])
            url = "{0}{1}{2}".format(server, api, query)
            print("\nProcessing project: {0}".format(proj['key']))
            print("Making Request for: {0}".format(url))    
            issues_rest = get_rest(url, authenticate)
            if issues_rest is not None:
                found_issues = True
                fstr = "{0}Retrieved {1} issues..."
                print(fstr.format(NOTE_LABEL, len(issues_rest['issues'])))
                for i in issues_rest['issues']:
                    # There should be a more elegant way of doing this, but the
                    # REST API apparently doesn't have a way to query for its
                    # own version
                    if api == "rest/api/2.0.alpha1/":
                        # obsolete version of the API, we'll need to adapt the
                        # issue for processing by these functions
                        i = adapt_2alpha1_issue(i
                                                ,config
                                                ,authenticate
                                                ,counters
                                                )
                    # Current version of the API
                    if i is not None:
                        if MEASUREMENTS_OUT:
                            proc_issue(i, config, counters)
                        else:
                            dump_issue(i, config, counters)
                    else:
                        err_str = "{0}Bad Issue Reference\n"
                        sys.stderr.write(err_str.format(ERR_LABEL))

    if found_issues:
        # Take care of the sprints
        sprint_api = config.sprint_api
        # "rest/greenhopper/1.0/"
        # If sprint_api isn't set in the configuration file, we'll skip
        # this step
        if sprint_api is not None:
            proc_sprints(server+sprint_api
                         ,proj_name2key_map
                         ,authenticate
                         ,counters
                         )
        # and the contributors
        handle_contributors(counters.contributors)

        # if we have measurements to pass along
        if counters.measurements:
            # Measurements were placed on the list in order of issue
            # processing.  Re-order by sorting on timestamp
            counters.measurements.sort(key=itemgetter(3))
            if GLOBALS['VERBOSE']:
                for i in counters.measurements:
                    print(i)

            gen_json(counters.measurements, config.json_basename + "-jira")
            
            # Dump the summary results
            fstr = ("\n\nCounter Class Summary:\n"
                    "  ISSUES OPEN   = {0}\n"
                    "  ISSUES CLOSED = {1}\n"
                    "  ISSUES TOTAL  = {2}\n\n"
                    "  REQUIREMENTS OPEN: {3}\n"
                    "  REQUIREMENTS CLOSED: {4}\n"
                    "  REQUIREMENTS TOTAL:  {5}\n\n"
                    "  DEFECTS CREATED = {6}\n"
                    "  DEFECTS CLOSED  = {7}\n"
                    "  DEFECTS TOTAL   = {8}\n\n"
                    "  SPRINTS TOTAL   = {9}\n\n"
                   )
            print(fstr.format(counters.issues.open
                              ,counters.issues.closed
                              ,counters.issues.total
                              ,counters.requirements.open
                              ,counters.requirements.closed
                              ,counters.requirements.total
                              ,counters.defects.created
                              ,counters.defects.closed
                              ,counters.defects.total
                              ,counters.sprints.total))

    else:
        err_str = "ERROR: Unable to retrieve issues for {0}.\n"
        sys.stderr.write(err_str.format(ACCOUNT_NAME))


if __name__ == '__main__':
    basename = get_basename_arg(__file__, sys.argv)
    if basename is not None:
        cfg_path = basename + ".cfg"
        config = get_config(cfg_path)
        if config is not None:
            jira_main(config)
        else:
            err_str = ("{0}Failed to load configuration file: '{1}'\n"
                       "{2}Exiting...\n")
            sys.stderr.write(err_str.format(ERR_LABEL
                                            ,cfg_path
                                            ,len(ERR_LABEL)*' '
                                            ))
