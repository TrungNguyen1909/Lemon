import os
if 'PORT' in os.environ:
	fd = open("/app/.heroku/python/lib/python3.7/site-packages/discord/opus.py","r")
	content = fd.read()
	fd.close()
	content = content.replace("_lib = libopus_loader(ctypes.util.find_library('opus'))","_lib = libopus_loader('libopus.so.0')")
	fd = open("/app/.heroku/python/lib/python3.7/site-packages/discord/opus.py","w")
	fd.write(content)
	fd.close()
import bot

