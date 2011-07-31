#!/usr/bin/env python
# Copyright (c) 2011, Jonathan Beluch
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
    # * Redistributions of source code must retain the above copyright
      # notice, this list of conditions and the following disclaimer.
    # * Redistributions in binary form must reproduce the above copyright
      # notice, this list of conditions and the following disclaimer in the
      # documentation and/or other materials provided with the distribution.
    # * Neither the name of the <organization> nor the
      # names of its contributors may be used to endorse or promote products
      # derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

    Meetup RSVP'er
    --------------

    The purpose of this script is to automatically RSVP yes to upcoming events
    on http://www.meetup.com.

    ## Setup
    1. You must edit API_KEY and MEMBER_ID to reflect your personal details.
       Instructions are below.
    2. Run the script with the --set-groups option. This is a onetime setup
       process where you specify which of your groups to auto RSVP for. You can
       rerun this option at any time, or manually edit the CONFIG_FILENAME.

    ## Execution:
    Simply run the script with no arguments. All script activity is printed
    to stdout. It would make sense to run this script with cron.

    ## Caveats
    * The Meetup API currently doesn't let you RSVP yes to an event where you
      would be added to the waiting list. The script will output a message when
      this happens. Then you would have to RSVP manualy through the website.
    * I have no idea how it handles events that require payments but I can
      guarantee it's not going to work.    
    * The Meetup API has a rate limit. It is fairly large, so you shouldn't run
      into any issues if you only run this hourly. However, the script does not
      check any of the rate limiting information. So, you might run into rate
      limits if you (1) Run the script too often (2) are a member of a large
      number of groups with a large number of upcoming events.

'''
from urllib2 import urlopen, HTTPError
from urllib import urlencode
from urlparse import urljoin
from datetime import datetime as dt
from ConfigParser import ConfigParser, NoSectionError
from optparse import OptionParser
import sys
import json

#### Start Configuration - Make sure this section is complete

# Get your API_KEY here: http://www.meetup.com/meetup_api/key/
API_KEY = ''
# Get your MEMBER_ID here: http://www.meetup.com/account/
MEMBER_ID = '' 

#### End Configuration

API_BASE_URL = 'https://api.meetup.com/'
EVENTS_URL = urljoin(API_BASE_URL, '/2/events')
RSVPS_URL = urljoin(API_BASE_URL, '/2/rsvps')
POST_RSVP_URL = urljoin(API_BASE_URL, '/rsvp')
GROUPS_URL = urljoin(API_BASE_URL, '/2/groups')
CONFIG_FILENAME = 'groups.config'

def log(msg):
    print '[%s]: %s' % (dt.utcnow().isoformat(), msg)

def get_config():
    '''Attempts to return a ConfigParser object read from CONFIG_FILENAME.'''
    config = ConfigParser()
    try:
        with open(CONFIG_FILENAME) as f:
            config.readfp(f)
    except IOError:
        sys.exit('Cannot read from %s. Please run this script with the '
                 '--set-groups option to generate a new config file.' % 
                 CONFIG_FILENAME)
    return config

def write_config(config):
    '''Writes a given config to CONFIG_FILENAME.'''
    with open(CONFIG_FILENAME, 'w') as f:
        config.write(f)

def _request(url, body=None):
    '''Returns the response for a given url. If body is given, it will be
    passed to urlopen and a POST request will be made instead of GET.
    
    If there is an HTTP Error, the response body will still be returned since
    the Meetup API will sometimes return a JSON body even when the response has
    an HTTP error code.
    '''
    try:
        u = urlopen(url, body)
    except HTTPError, e:
        return e.read()
    resp = u.read()
    u.close()
    return resp

## Meetup API stuff
def api_request_GET(url, params):
    '''Issues a GET request. params should be a dict and will get urlencoded
    and appened as a query string.

    Also, the specified API_KEY is added to params.
    '''
    params['key'] = API_KEY
    url = '%s?%s' % (url, urlencode(params))
    return json.loads(_request(url))

def api_request_POST(url, params):
    '''Issues a POST request. params should be a dict and will get urlencoded
    and appened as a query string.

    Also, the specified API_KEY is added to params.
    '''
    params['key'] = API_KEY
    url = '%s?%s' % (url, urlencode(params))
    # Use a space for the body arg to fool urllib into sending a POST.
    # I guess I could use httplib to have control over the HTTP method but this
    # works.
    return json.loads(_request(url, ' '))

## Higher level Meetup API methods
def get_events(group_id):
    '''Gets the JSON for all upcoming events for a given group_id.'''
    resp = api_request_GET(EVENTS_URL, {'group_id': group_id})
    events = resp['results']
    return events

def get_my_rsvp(event_id):
    '''Returns the current member's RSVP for a given event_id. An empty list is
    returned if the member hasn't RSVP'd yet.'''
    resp = api_request_GET(RSVPS_URL, {'event_id': event_id})
    rsvps = resp['results']
    # Since we can only get all the RSVPs for an event, we need to filter on
    # MEMBER_ID to determine if the current user has RSVP'd.
    my_rsvp = filter(lambda rsvp: str(rsvp['member']['member_id']) == 
                     MEMBER_ID, rsvps)
    return my_rsvp

def get_groups():
    '''Returns the current member's groups.'''
    resp = api_request_GET(GROUPS_URL, {'member_id': MEMBER_ID})
    groups = resp['results']
    return groups

def rsvp_yes(event_id):
    '''Will submit an RSVP of 'yes' for the current member for the specified
    event_id. Returns True if successful, False if not.

    The meetup API doesn't currently allow RSVP'ing to a full event even if
    there is a waiting list. This must be done manually.
    '''
    url = POST_RSVP_URL
    params = {'event_id': event_id, 'rsvp': 'yes'}
    resp = api_request_POST(url, params)
    if resp.get('description') == 'Successful RSVP':
        return True
    return False

## Script level functions
def rsvp_for_group_events(group_id):
    '''Loops through a group's (specified by group_id) upcoming events and 
    RSVP's yes if an event doesn't have a current RSVP. All activity in this
    function is printed to stdout.'''

    events = get_events(group_id)
   
    for event in events:
        group_name = event['group']['name']
        event_name = event['name']
        event_id = event['id']
        event_url = event['event_url']

        my_rsvp = get_my_rsvp(event['id'])
        if not my_rsvp:
            if event['yes_rsvp_count'] >= event['rsvp_limit']:
                log('[%s] Cannot RSVP to %s, the event is full. Please visit '
                    '%s to add yourself to the waiting list if one is '
                    'available.' % (
                    event['group']['name'], 
                    event['name'], 
                    event['event_url']
                ))
            elif rsvp_yes(event_id):
                log('[%s] RSVP\'d yes to "%s" (%s)' % (group_name, event_name,
                                                       event_url)
                )
            else:
                log('[%s] Problem RSVP\'ing to event %s: %s : %s' % (
                    group_name,
                    event_id,
                    event_name,
                    event_url
                ))
        else:
            log('[%s] No new non-RSVP\'d events.' % group_name)
        
def rsvp_for_groups():
    '''Parses the uncommented groups from the config file and 
    calls rsvp_for_group_events for each group found.
    '''
    config = get_config()

    try:
        groups = config.items('rsvp_groups')
    except NoSectionError:
        sys.exit('It seems your %s file is corrupt. Please run the script '
                 'with the --set-groups option to generate a new config file.'
                 % CONFIG_FILENAME)

    for group_id, group_name in groups:
        rsvp_for_group_events(group_id)

def set_auto_rsvp_groups():
    '''Generates a group config file from user input. The config file is saved
    to CONFIG_FILENAME specified above.

    All groups of the current member are printed to the config file. However,
    any groups the user doesn't want to auto RSVP will be commented out with a
    '#'.
    '''
    groups = get_groups()

    config_groups = []
    for group in groups:
        ans = raw_input(
            'Automatically RSVP yes for %s? [y/n]: ' % group['name']
        ).lower()

        while ans not in ['y', 'n']:
            print 'Please enter a \'y\' or \'n\'.'
            ans = raw_input(
                'Automatically RSVP yes for %s? [y/n]: ' % group['name']
            ).lower()
        
        if ans == 'y':
            # We want to auto-rsvp for this group
            config_groups.append((str(group['id']), group['name']))
        else:
            # Don't auto RSVP. We'll write add this group with a comment
            # preceding the line.
            config_groups.append(('#%s' % str(group['id']), group['name']))

    config = ConfigParser()
    config.add_section('rsvp_groups')
    [config.set('rsvp_groups', group_id, group_name) for group_id, group_name
        in config_groups]
    write_config(config)

def main():
    '''The script has two run modes.
    (1) Default, no arguments. Will attempt to RSVP yes for all upcoming
        events.
    (2) The --set-groups option is specified. This will generate the config
        file from user input.
    '''
    parser = OptionParser()
    parser.add_option('--set-groups', action='store_true', dest='set_groups',
        default=False, help='Run the setup process to pick which groups to '
                            'automatically RSVP yes for.')
    options, args = parser.parse_args()
    if options.set_groups:
        set_auto_rsvp_groups()
    else:
        rsvp_for_groups()
        

if __name__ == '__main__':
    main()
