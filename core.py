#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
campfire2me v0.1
Matt Behrens <askedrelic@gmail.com> http://asktherelic.com

Script to scrape Cater2Me's website for today's lunch menu and post to Campfire.
Quite a hack. Will probably break.
"""

import mechanize
import cookielib
from pyquery import PyQuery as pq
import re
import os
import requests
import datetime
from requests.auth import HTTPBasicAuth

campfire_newline = '&#xA;'

try:
    username        = os.environ['USERNAME']
    password        = os.environ['PASSWORD']
    room_id         = os.environ['CAMPFIRE_ROOM']
    campfire_auth   = os.environ['CAMPFIRE_AUTH']
    campfire_domain = os.environ['CAMPFIRE_DOMAIN']
except KeyError, e:
    raise SystemExit('missing environment setting: %s' % e)

# hack for Heroku's terrible scheduler API: 
# only run this script on specific days of the week
# eg; 1,3 or 1 3
dow_list = os.environ.get('DOW_LIST')
if dow_list:
    today = str(datetime.datetime.now().isoweekday())
    if today not in dow_list:
        raise SystemExit('today is not in dow list')

br = mechanize.Browser()
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)
br.set_handle_equiv(True)
br.open('http://cater2.me/login/')
br.select_form(nr=0)
br['username'] = username
br['pwd'] = password
resp = br.submit()
d = pq(resp.read())

image = d('#tabs_vnd-1 img')
if image:
    image_src = "http://www.cater2.me" + image.attr.src
    payload = '{"message":{"body":"%s"}}' %  image_src
    url = 'https://%s.campfirenow.com/room/%s/speak.json' % (campfire_domain, room_id)
    headers = {'content-type': 'application/json'}
    auth = HTTPBasicAuth(campfire_auth, 'X')
    try:
        requests.post(url, data=payload, headers=headers, auth=auth)
    except Exception, e:
        print e

content = ''
text = d('#tabs_vnd-1')
original_text = text.text()
prefix = re.sub('Menu.*', '', original_text)
content += prefix
#try to remove outer html tags?
body = pq(text.children('div').html())

#kill links
body.children('div').children().children('a').remove()
body.children('h3').remove()
body = body.html().strip().strip('\n').strip('\t')
good_body = body.replace('<u/>','').replace(u'<br/>','').replace('<b>','').replace('</b>',campfire_newline).replace('</span>',campfire_newline).replace('<div>','').replace('</div>','').strip()
good_body = re.sub('<span.*?>','',good_body)
good_body = re.sub('Items have been.*\n*','',good_body, re.DOTALL|re.MULTILINE)

content += campfire_newline
content += campfire_newline
content += good_body

#fix unicode content
content = content.encode('ascii', 'ignore')
# print content

payload = '<message><type>PasteMessage</type><body>%s</body></message>' % content
url = 'https://%s.campfirenow.com/room/%s/speak.xml' % (campfire_domain, room_id)
headers = {'content-type': 'application/xml'}
auth = HTTPBasicAuth(campfire_auth, 'X')
try:
    requests.post(url, data=payload, headers=headers, auth=auth)
except Exception, e:
    print e

print 'done. happy eating!'
