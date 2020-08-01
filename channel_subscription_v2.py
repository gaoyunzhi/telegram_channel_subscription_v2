#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import time
from telegram.ext import Updater, MessageHandler, Filters
import threading
import export_to_telegraph
from telegram_util import splitCommand, log_on_fail, autoDestroy, matchKey
import plain_db
import webgram

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)
tele = Updater(credential['token'], use_context=True)
export_to_telegraph.token = credential['telegraph_token']
debug_group = tele.bot.get_chat(420074357)

existing = plain_db.loadKeyOnlyDB('existing')
with open('subscription') as f:
    db = yaml.load(f, Loader=yaml.FullLoader)
def saveDB():
    for chat_id in list(db.keys()):
        if not isinstance(chat_id, int):
            continue
        try:
            r = tele.bot.send_message(chat_id, 'test')
            r.delete()
        except:
            del db[chat_id]
    with open('db', 'w') as f:
        f.write(yaml.dump(db, sort_keys=True, indent=2, allow_unicode=True))

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

def getMessage(text, toTelegraph=True):
    result = ''
    for item in text:
        if item.name in set(['br']):
            result += '\n'
            continue
        if item.name == 'i':
            if item.text:
                result += '<i>' + item.text + '</i>'
            continue
        if 'telegra' in result and str(item).startswith('原文'):
            return result
        if item.name == 'a':
            if 'rel' in item:
                del item['rel']
            if toTelegraph and 'telegra' not in result:
                telegraph_url = export_to_telegraph.export(item['href'])
                if telegraph_url:
                    item['href'] = telegraph_url
                    if 'http' in item.text:
                        item.contents[0].replaceWith(telegraph_url)
        result += str(item)
    return result

def getMatches(index):
    for chat_id in db:
        if not isinstance(chat_id, int):
            continue
        if matchKey(index, db[chat_id]):
            yield chat_id

@log_on_fail(debug_group)
def loopImp():
    for channel in db['pool']:
        for post in webgram.getPosts(channel)[1:]:
            maintext = post.getMaintext()
            if not existing.add(maintext):
                continue
            matches = list(getMatches(post.getIndex()))
            if not matches:
                continue
            message = getMessage(post.text, channel != 'twitter_subscriptions')
            for chat_id in matches:
                try:
                    tele.bot.send_message(chat_id, message, parse_mode='HTML')
                except Exception as e:
                    debug_group.send_message(str(chat_id) + ' ' + str(e))
                    debug_group.send_message(message, parse_mode='HTML')
                time.sleep(5)

def loop():
    loopImp()
    threading.Timer(3600, loop).start()

if __name__ == '__main__':
    threading.Timer(1, loop).start()
    tele.dispatcher.add_handler(MessageHandler(Filters.command, manage))
    tele.dispatcher.add_handler(MessageHandler(Filters.private & (~Filters.command), start))
    tele.start_polling()
    tele.idle()