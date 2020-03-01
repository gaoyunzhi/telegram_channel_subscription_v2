#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
import requests
import threading
import export_to_telegraph
from bs4 import BeautifulSoup
import hashlib
import telegram_util
from telegram_util import splitCommand, log_on_fail, autoDestroy, getDisplayUser

START_MESSAGE = ('''
Subscribe messages from public channels. 

add - /add channel_link add channel to subscription pool. Channel must have public name. Automatically subscribe this channel if messge is send in a group or channel.
list - /list: list all channels.
keys - /show_keys: show subscription keywords
edit - /keys keywords: give a new set of keywords, in json format
''')

with open('CREDENTIALS') as f:
    CREDENTIALS = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(CREDENTIALS['bot_token'], use_context=True)
export_to_telegraph.token = CREDENTIALS.get('telegraph')
debug_group = tele.bot.get_chat(-1001198682178)

INTERVAL = 3600
PAUSED = []

with open('hashes') as f:
    hashes = set(yaml.load(f, Loader=yaml.FullLoader))

def saveHashes(hash_value):
    with open('hashes', 'a') as f:
        f.write(hash_value + ': null\n')

with open('DB') as f:
    DB = yaml.load(f, Loader=yaml.FullLoader)

def saveDB():
    with open('DB', 'w') as f:
        f.write(yaml.dump(DB, sort_keys=True, indent=2))

def addKey(chat_id, key):
    DB[chat_id] = DB.get(chat_id, [])
    DB[chat_id].append(key)
    saveDB()

def listPool(msg):
    items = ['{}: [{}](t.me/{})'.format(index, content, content) \
        for index, content in enumerate(DB['pool'])]
    msg.reply_text('\n\n'.join(items), quote=False, disable_web_page_preview=True, 
        parse_mode='Markdown')

def add(msg, content):
    if not msg.from_user:
        return
    if msg.from_user.id not in CREDENTIALS.get('admins', []):
        tele.bot.send_message(chat_id=debug_group, text='suggestion: ' + content)
        msg.reply_text('Only admin can add, your suggestion is recorded.', quote=False)
        tele.bot.send_message(
            chat_id=debug_group, 
            text ='suggestion from ' + getDisplayUser(msg.from_user),
            parse_mode='Markdown',
            disable_web_page_preview=True) 
        return
    pieces = [x.strip() for x in content.split('/') if x.strip()]
    if len(pieces) == 0:
        return msg.reply_text('FAIL. can not find channel: ' + content, quote=False)
    name = pieces[-1]
    if name.startswith('@'):
        name = name[1:]
    if not name:
        return msg.reply_text('FAIL. can not find channel: ' + content, quote=False)
    if name in DB['pool']:
        return msg.reply_text('channel already in pool: ' + content, quote=False)
    DB['pool'].append(name)
    if msg.chat_id < 0:
        addKey(msg.chat_id, name) 
    msg.reply_text('success', quote=False)

def remove(msg, content):
    if not msg.from_user:
        return
    if msg.from_user.id not in CREDENTIALS.get('admins', []):
        return msg.reply_text('FAIL. Only admin can remove subscription', quote=False)
    try:
        del DB['pool'][int(content)]
        saveDB()
    except Exception as e:
        msg.reply_text(str(e), quote=False)

def getKeysText(msg):
    return '/keys: ' + str(DB.get(msg.chat_id))

def show(msg):
    autoDestroy(msg.reply_text(getKeysText(msg), quote=False))

def key(msg, content):
    try:
        DB[msg.chat_id] = yaml.load(content, Loader=yaml.FullLoader)
        saveDB()
        autoDestroy(msg.reply_text('success ' + getKeysText(msg), quote=False))
    except Exception as e:
        msg.reply_text(str(e), quote=False)

def unpause(chat_id):
    global PAUSED
    PAUSED.remove(chat_id)

@log_on_fail(debug_group)
def manage(update, context):
    msg = update.effective_message
    if not msg:
        return
    autoDestroy(msg)
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
    if 'pause' in command:
        global PAUSED
        PAUSED.append(msg.chat_id)
        threading.Timer(4 * 60 * 60, lambda: unpause(msg.chat_id)).start()
        autoDestroy(msg.reply_text('success', quote=False))
        return

def start(update, context):
    if update.message:
        update.message.reply_text(START_MESSAGE, quote=False)

tele.dispatcher.add_handler(MessageHandler(Filters.command, manage))
tele.dispatcher.add_handler(MessageHandler(Filters.private & (~Filters.command), start))

def getSoup(url):
    headers = {'Host':'telete.in',
        'Connection':'keep-alive',
        'Cache-Control':'max-age=0',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36',
        'Sec-Fetch-User':'?1',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Sec-Fetch-Site':'none',
        'Sec-Fetch-Mode':'navigate',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'en-US,en;q=0.9,zh;q=0.8,zh-CN;q=0.7'}
    r = requests.get(url, headers=headers)
    return BeautifulSoup(r.text, 'html.parser')

def getParsedText(text):
    result = ''
    for item in text:
        if item.name in set(['br']):
            result += '\n'
            continue
        if item.name == 'i':
            if item.text:
                result += '<i>' + item.text + '</i>'
            continue
        if item.name == 'a':
            telegraph_url = export_to_telegraph.export(item['href'])
            if telegraph_url:
                item['href'] = telegraph_url
                del item['rel']
                if 'http' in item.text:
                    item.contents[0].replaceWith(telegraph_url)
        if str(item).startswith('原文') and 'telegra' in result:
            return result
        result += str(item)
    return result

def keyMatch(chat_id, author, result):
    if (not isinstance(chat_id, int)) or (not DB[chat_id]):
        return False
    for key in DB[chat_id]:
        if key in str(author) or key in str(result):
            return True
    return False

def intersect(l1, l2):
    return set(l1).intersection(l2)

@log_on_fail(debug_group)
def loopImp():
    global hashes
    global DB
    for item in DB['pool']:
        soup = getSoup('https://telete.in/s/' + item)
        for msg in soup.find_all('div', class_='tgme_widget_message_bubble'):
            text = msg.find('div', class_='tgme_widget_message_text')
            if (not text) or (not text.text):
                continue
            hash_value = hashlib.sha224(str(text.text).encode('utf-8')).hexdigest()
            if hash_value in hashes:
                continue
            author = msg.find('div', class_='tgme_widget_message_author')
            result = getParsedText(text)
            matches = [chat_id for chat_id in DB if keyMatch(chat_id, str(author), result)]
            if intersect(matches, PAUSED):
                continue
            for chat_id in matches:
                try:
                    tele.bot.send_message(chat_id=chat_id, text=result, parse_mode='HTML')
                    time.sleep(1)
                except Exception as e:
                    print(chat_id)
                    print(e)                        
                    print(result)
            hashes.add(hash_value)
            saveHashes(hash_value)

def loop():
    loopImp()
    threading.Timer(INTERVAL, loop).start()

threading.Timer(1, loop).start()

tele.start_polling()
tele.idle()