import os
if 'PORT' in os.environ:
	fd =  open("/app/.heroku/python/lib/python3.7/site-packages/discord/gateway.py","r")
	lines = fd.readlines()
	fd.close()
	lines[686] = "            interval = (data['heartbeat_interval'] / 1000.0)*0.75\n"
	fd = open("/app/.heroku/python/lib/python3.7/site-packages/discord/gateway.py","w")
	for line in lines:
		fd.write(line)
	fd.close()
	fd = open("/app/.heroku/python/lib/python3.7/site-packages/discord/opus.py","r")
	lines = fd.readlines()
	fd.close()
	lines[109] = "        _lib = libopus_loader('libopus.so.0')\n"
	fd = open("/app/.heroku/python/lib/python3.7/site-packages/discord/opus.py","w")
	for line in lines:
		fd.write(line)
	fd.close()
import bot

