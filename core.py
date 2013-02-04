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
allergy_key = 'Allergen Key: *Vegetarian, **Vegan, (G) Gluten Safe, (D) Dairy Safe, (N) Nut Safe, (E) Egg Safe, (S) Soy Safe.'

try:
    username        = os.environ['USERNAME']
    password        = os.environ['PASSWORD']
    room_id         = os.environ['CAMPFIRE_ROOM']
    campfire_auth   = os.environ['CAMPFIRE_AUTH']
    campfire_domain = os.environ['CAMPFIRE_DOMAIN']
    company         = os.environ['COMPANY']
except KeyError, e:
    raise SystemExit('missing environment setting: %s' % e)

testing = os.environ.get('TESTING')

# hack for Heroku's terrible scheduler API:
# only run this script on specific days of the week
# eg; 1,3 or 1 3
dow_list = os.environ.get('DOW_LIST')
now = datetime.datetime.now().strftime("%Y,%m,%d")
if dow_list:
    today = str(datetime.datetime.now().isoweekday())
    if today not in dow_list:
        raise SystemExit('Today (%s) is not in dow list' % now)

output = {
    'image_src': '',
    'text': '',
}

# br = mechanize.Browser()
# cj = cookielib.LWPCookieJar()
# br.set_cookiejar(cj)
# br.set_handle_equiv(True)
# br.open('http://cater2.me/login/')
# br.select_form(nr=0)
# br['username'] = username
# br['pwd'] = password
# resp = br.submit()
# d = pq(resp.read())

# #get company name
# try:
#     script = [x.text for x in d('script') if x.text and 'json' in x.text][0]
#     matches = re.search(r'calendar\/(.*)\.json', script)
#     company = matches.groups()[0]
# except Exception,e:
#     raise e

#meh, ignore logging in

meal_json_url = 'http://cater2.me/VeriteCo-TimelineJS/calendar/%s.json' % company

cater_info = requests.get(meal_json_url).json()
meals = cater_info['timeline']['date']
try:
    today = filter(lambda x: now in x['startDate'], meals)[0]
except IndexError:
    raise SystemExit('There is no food scheduled for delivery today (%s)' % now)

output['image_src'] = "http://www.cater2.me" + today['asset']['media']
text = today['text']

output['text'] += "Today's Lunch:"
output['text'] += campfire_newline

# text = d('#tabs_vnd-1')
# original_text = text.text()
# prefix = re.sub('Menu.*', '', original_text)
# output['text'] += prefix
# #try to remove outer html tags?
# body = pq(text.children('div').html())

body = text
body = body.strip('\n').strip('\t')
body = re.sub('(<.?div>|<.?b>|<span.*?>|<.?br>)','',body)
body = body.strip('Mouse over items to see your allergens')
body = body.replace('&', 'and')
body = body.replace('</span>', campfire_newline)

# dedupe newlines, final cleanup
body = campfire_newline.join([x.strip() for x in body.split(campfire_newline) if x])
body += campfire_newline*2 + allergy_key

output['text'] += body

#fix unicode content; entree
output['text'] = output['text'].encode('utf-8')

if testing:
    print output['image_src']
    print output['text']
else:
    if output['image_src']:
        payload = '{"message":{"body":"%s"}}' %  output['image_src']
        url = 'https://%s.campfirenow.com/room/%s/speak.json' % (campfire_domain, room_id)
        headers = {'content-type': 'application/json'}
        auth = HTTPBasicAuth(campfire_auth, 'X')
        try:
            requests.post(url, data=payload, headers=headers, auth=auth)
        except Exception, e:
            print e

    payload = '<message><type>PasteMessage</type><body>%s</body></message>' % output['text']
    url = 'https://%s.campfirenow.com/room/%s/speak.xml' % (campfire_domain, room_id)
    headers = {'content-type': 'application/xml'}
    auth = HTTPBasicAuth(campfire_auth, 'X')
    try:
        requests.post(url, data=payload, headers=headers, auth=auth)
    except Exception, e:
        print e

print 'done. happy eating!'
