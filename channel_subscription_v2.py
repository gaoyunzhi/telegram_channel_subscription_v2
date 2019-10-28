#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
import requests
import traceback as tb
import json
import threading
import export_to_telegraph
from bs4 import BeautifulSoup

START_MESSAGE = ('''
Subscribe messages from public channels. 

add - /add channel_link add channel to subscription pool. Channel must have public name. Automatically subscribe this channel if messge is send in a group or channel.
list - /list: list all channels.
keys - /show_keys: show subscription keywords
edit - /keys keywords: give a new set of keywords, in json format
''')

reload(sys)
sys.setdefaultencoding('utf-8')

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f)

export_to_telegraph.token = CREDENTIALS.get('telegraph')

LONG_TEXT_LIMIT = 300

def appendMessageLog(message):
    with open('message_log.txt', 'a') as f:
        f.write(message) 

hashs = set()
