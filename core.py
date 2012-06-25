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
from requests.auth import HTTPBasicAuth

campfire_newline = '&#xA;'

if os.environ.has_key('USERNAME') and os.environ.has_key('PASSWORD'):
    username = os.environ['USERNAME']
    password = os.environ['PASSWORD']
    room_id = os.environ['ROOM_ID']
    campfire_auth = os.environ['CAMPFIRE_AUTH']
else:
    raise SystemExit('need cater2me username/password env variables set')

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
    url = 'https://seatme.campfirenow.com/room/%s/speak.json' % room_id
    headers = {'content-type': 'application/json'}
    auth = HTTPBasicAuth(campfire_auth, 'X')
    try:
        requests.post(url, data=payload, headers=headers, auth=auth)
    except Exception, e:
        pass

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

payload = '<message><type>PasteMessage</type><body>%s</body></message>' % content
url = 'https://seatme.campfirenow.com/room/%s/speak.xml' % room_id
headers = {'content-type': 'application/xml'}
auth = HTTPBasicAuth(campfire_auth, 'X')
try:
    requests.post(url, data=payload, headers=headers, auth=auth)
except Exception, e:
    pass    
