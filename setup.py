import os
import sys
import json

REQUIRED_KEYS = set(['bot_token'])

def setup(arg = ''):
	RUN_COMMAND = 'nohup python3 channel_subscription_v2.py &'

	with open('CREDENTIALS') as f:
		CREDENTIALS = json.load(f)

	for key in REQUIRED_KEYS:
		if key not in CREDENTIALS:
			print('ERROR: please fill the CREDENTIALS file in json format, required keys : ' + ', '.join(sorted(REQUIRED_KEYS)))
			return

	if arg != 'debug':
		r = os.system('sudo pip3 install -r requirements.txt')
		if r != 0:
			os.system('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
			os.system('sudo python3 get-pip.py')
			os.system('rm get-pip.py')
			os.system('sudo pip3 install -r requirements.txt')
		
	try:
		from telegram.ext import Updater, MessageHandler, Filters
	except:
		os.system('sudo pip3 install python-telegram-bot --upgrade') # need to use some experiement feature, e.g. message filtering
			
	# kill the old running bot if any. If you need two same bot running in one machine, use mannual command instead
	os.system("ps aux | grep ython | grep subscription_v3 | awk '{print $2}' | xargs kill -9")

	if arg.startswith('debug'):
		os.system(RUN_COMMAND[6:-2])
	else:
		os.system(RUN_COMMAND)

if __name__ == '__main__':
	if len(sys.argv) > 1:
		setup(sys.argv[1])
	else:
		setup('')