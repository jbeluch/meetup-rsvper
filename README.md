Meetup RSVP'er
==============

This script will automatically RSVP 'yes' to your upcomining events on 
http://www.meetup.com.

## Setup
1. You must edit `API_KEY` and `MEMBER_ID` in `meetup-rsvper.py` to reflect
   your personal details. Instructions can be found in `meetup-rsvper.py`.
2. Run the script with the `--set-groups` option. This is a onetime setup
   process where you specify which of your groups to auto RSVP for. You can
   rerun this option at any time, or manually edit the config file found at
   `CONFIG_FILENAME` (`groups.config` by default).

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
