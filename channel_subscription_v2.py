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
debug_group = CREDENTIALS.get('debug_group') or -1001198682178

LONG_TEXT_LIMIT = 300
INTERVAL = 30 # debug, change to 3600

def appendMessageLog(message):
    with open('message_log.txt', 'a') as f:
        f.write(message) 

hashs = set()

try:
    with open('DB') as f:
        DB = yaml.load(f)
except:
    DB = {'pool': []}

def saveDB():
    with open('DB', 'w') as f:
        f.write(yaml.dumps(DB, sort_keys=True, indent=2))

def addKey(chat_id, key):
    DB[chat_id] = DB.get(chat_id, [])
    DB[chat_id].append(key)
    saveDB()

def splitCommand(text):
    pieces = text.split()
    if len(pieces) < 1:
        return '', ''
    command = pieces[0]
    return command.lower(), text[text.find(command) + len(command):].strip()

def listPool(msg):
    items = ['{}: [t.me/{}]({})'.format(index, content, content) \
        for index, content in enumerate(DB['pool'])]
    msg.reply_text('\n\n'.join(items), quote=False, disable_web_page_preview=True, 
        parse_mode='Markdown')

def add(msg, content):
    pieces = [x.strip() for x in content.split('/') if x.strip()]
    if len(pieces) == 0:
        return msg.reply_text('FAIL. can not find channel: ' + content, quote=False)
    if name.starwith('@'):
        name = name[1:]
    if not name:
        return msg.reply_text('FAIL. can not find channel: ' + content, quote=False)
    if name in DB['pool']:
        return msg.reply_text('channel already in pool: ' + content, quote=False)
    DB['pool'].append(name)
    addKey(msg.chat_id, name)
    msg.reply_text('success', quote=False)

def remove(msg, content):
    if msg.from_user_id not in CREDENTIALS.get('admins', []):
        return msg.reply_text('FAIL. Only admin can remove subscription', quote=False)
    try:
        del DB['pool'][int(content)]
        saveDB()
    except Exception as e:
        msg.reply_text(str(e), quote=False)

def show(msg):
    msg.reply_text('Subscription Keys' + str(DB.get(msg.chat_id)), quote=False)

def key(msg, content):
    try:
        DB[chat_id] = yaml.load(content)
        msg.reply_text('success', quote=False)
    except Exception as e:
        msg.reply_text(str(e), quote=False)

def manage(update, context):
    try:
        msg = update.effective_message
        if not msg:
            return
        command, content = splitCommand(msg.text)
        if ('add' in command) and content:
            return add(msg, content)
        if 'list' in command:
            return listPool(msg)
        if 'remove' in command:
            return remove(msg, content)
        if 'show' in command:
            return show(msg)
        if 'key' in command:
            return key(msg, content)
        msg.reply_text(START_MESSAGE, quote=False)
    except Exception as e:
        print(e)
        tb.print_exc()
        context.bot.send_message(chat_id=debug_group, text=str(e))


def start(update, context):
    if update.message:
        update.message.reply_text(START_MESSAGE, quote=False)

updater = Updater(CREDENTIALS['bot_token'], use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.command, manage))
dp.add_handler(MessageHandler(Filters.private & (~Filters.command), start))

def loopImp():
    pass 

def loop():
    try:
        loopImp()
    except Exception as e:
        print(e)
        tb.print_exc()
    threading.Timer(INTERVAL, loop).start()

loop()

updater.start_polling()
updater.idle()