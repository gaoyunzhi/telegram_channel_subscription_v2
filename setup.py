import os
import sys

MAIN_FILE = 'channel_subscription_v2'

def kill():
	os.system("ps aux | grep ython | grep " + MAIN_FILE + " | awk '{print $2}' | xargs kill -9")

def setup():
	kill()
	if 'kill' in sys.argv:
		return

	RUN_COMMAND = 'nohup python3 '+ MAIN_FILE + '.py &'

	if 'debug' in sys.argv:
		os.system(RUN_COMMAND[6:-2])
	else:
		os.system(RUN_COMMAND)

if __name__ == '__main__':
	setup()