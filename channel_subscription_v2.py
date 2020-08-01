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
from telegram_util import splitCommand, log_on_fail, autoDestroyss
import plain_db

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(credential['token'], use_context=True)
export_to_telegraph.token = credential['telegraph_token']
debug_group = tele.bot.get_chat(420074357)

existing = plain_db.loadKeyOnlyDB('existing')
with open('db') as f:
    db = yaml.load(f, Loader=yaml.FullLoader)
def saveDB():
    with open('db', 'w') as f:
        f.write(yaml.dump(db, sort_keys=True, indent=2, allow_unicode=True))

INTERVAL = 3600

def listPool(msg):
    items = ['%d: [%s](t.me/%s)' % (index, content, content)
        for index, content in enumerate(db['pool'])]
    msg.reply_text('\n'.join(items), disable_web_page_preview=True, 
        parse_mode='Markdown')

def getKeysText(msg):
    return '/keys: ' + ' '.join(db.get(msg.chat_id, []))

def show(msg):
    autoDestroy(msg.reply_text(getKeysText(msg)))

def setKey(msg, content):
    db[msg.chat_id] = [item for item in content.split() if item]
    saveDB()
    autoDestroy(msg.reply_text('success ' + getKeysText(msg)))

@log_on_fail(debug_group)
def manage(update, context):
    msg = update.effective_message
    if not msg:
        return
    autoDestroy(msg)
    command, content = splitCommand(msg.text)
    if 'list' in command:
        return listPool(msg)
    if 'show' in command:
        return show(msg)
    if 'key' in command:
        return setKey(msg, content)

with open('help.md') as f:
    help_message = f.read()

def start(update, context):
    if update.message:
        update.message.reply_text(help_message)

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
    if (not isinstance(chat_id, int)) or (not db[chat_id]):
        return False
    for key in db[chat_id]:
        if key in str(author) or key in str(result):
            return True
    return False

def intersect(l1, l2):
    return set(l1).intersection(l2)

@log_on_fail(debug_group)
def loopImp():
    for item in db['pool']:
        post = webgram.getPosts('')
        for msg in soup.find_all('div', class_='tgme_widget_message_bubble'):
            text = msg.find('div', class_='tgme_widget_message_text')
            if (not text) or (not text.text):
                continue
            hash_value = hashlib.sha224(str(text.text).encode('utf-8')).hexdigest()
            if hash_value in hashes:
                continue
            author = msg.find('div', class_='tgme_widget_message_author')
            result = getParsedText(text)
            matches = [chat_id for chat_id in db if keyMatch(chat_id, str(author), result)]
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
    threading.Timer(3600, loop).start()

if __name__ == '__main__':
    threading.Timer(1, loop).start()
    tele.dispatcher.add_handler(MessageHandler(Filters.command, manage))
    tele.dispatcher.add_handler(MessageHandler(Filters.private & (~Filters.command), start))
    tele.start_polling()
    tele.idle()