#!/usr/bin/python

"""
Description::

Simple utility to grab and apply a Django trac ticket.
It could in theory be used for any trac installation.

Usage:: trac_patch.py [ticket_num]

  -h, --help     show this help message and exit
  -r, --reverse  Reverse the patch
  -g, --git      Make a git branch
  -a, --ask      Confirm ticket and patch name

Examples::

    #Apply patch 6378
    trac_patch.py 6378

    #Reverse patch 6378
    trac_patch.py 6378 -r

    #Create a git branch and apply patch
    trac_patch.py 6378 -g

    #Confirm patch filename and ticket filename
    trac_patch.py 6378 -a

"""


import os
import sys
import urllib2
import BeautifulSoup
import commands
from optparse import OptionParser

django_src = '/Users/ericholscher/Code/Python/django-trunk/'
trac_url = 'http://code.djangoproject.com'
ticket_url = 'http://code.djangoproject.com/ticket/%s'

parser = OptionParser(usage='%prog [ticket_num]')
parser.add_option("-r", "--reverse", action="store_true", dest="reverse",
                  default=False, help="Reverse the patch")
parser.add_option("-g", "--git", action="store_true", dest="git",
                  default=False, help="Make a git branch")
parser.add_option("-a", "--ask", action="store_true", dest="ask",
                  default=False, help="Confirm ticket and patch name")
(options, args) = parser.parse_args()

ask_ticket_confirmation = options.ask
ask_patch_confirmation = options.ask
git_integration = options.git

if options.reverse:
    print "Reversing patch"
    reverse_string = '--reverse'
else:
    print "Patching file"
    reverse_string = ''

if len(args) != 1:
    print "Please provide a ticket number"
    sys.exit()
ticket_num = args[0]

request = urllib2.urlopen(ticket_url % ticket_num)
soup = BeautifulSoup.BeautifulSoup(request.read())
title = soup.find('title').find(text=True)

if ask_ticket_confirmation:
    print "Accessing ticket %s, Proceed with patching?" % title
    confirm = raw_input("yes/no: ")
    if confirm != "yes" and confirm != "y":
        print "exiting now"
        sys.exit()

links = soup.findAll('a', title="View attachment")
latest_patch_url = links[-1]['href']

if ask_patch_confirmation:
    print "Which patch would you like to apply?"
    for num,link in enumerate(links):
        print "%s) %s" % (num, link.find(text=True))
    patch_num = int(raw_input('>'))
    latest_patch_url = links[patch_num]['href']

patch_req = urllib2.urlopen(trac_url + latest_patch_url)
patch_soup = BeautifulSoup.BeautifulSoup(patch_req)
download_link = patch_soup.find('a', text="Original Format").previous['href']
patch = urllib2.urlopen(trac_url + download_link)
patch_string = patch.read()

patch_filename = '/tmp/%s' % download_link.split('/')[-1].split('?')[0]
p_file = open(patch_filename, 'w')
p_file.write(patch_string)
p_file.close()

if django_src:
    os.chdir(django_src)

if git_integration:
    branch_name = patch_filename.split('.')[0].split('/')[-1]
    print "Making git branch named %s" % branch_name
    commands.getoutput('git checkout -b %s' % branch_name)

cmd = 'patch -p0 %s < %s' % (reverse_string, patch_filename)
print cmd
output = commands.getoutput(cmd)
print output
