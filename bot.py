import discord
from queue import Queue
from random import shuffle
import re
import asyncio
import deez
client = discord.Client()
async def sendLyrics(client,text):
	#print(text)
	asyncio.run_coroutine_threadsafe(client.LM.edit(content = '```'+text+'```'),client.loop)
def stream_ended():
	print("Stream ended")
	asyncio.run_coroutine_threadsafe(client.voiceclient.disconnect(),client.loop)
	if client.LM:
		asyncio.run_coroutine_threadsafe(client.LM.unpin(),client.loop)
	if not client.queue.empty():
		asyncio.run_coroutine_threadsafe(processTrack(),client.loop)
	else:
		client.playing = False
		asyncio.run_coroutine_threadsafe(client.LM.channel.send('Queue ended'),client.loop)
async def processTrack():
	print("Processing track on top of the queue")
	track = client.queue.get()
	trackid = track['id']
	title = track['title']
	artist = track['artist']['name']
	album = track['album']['title']
	cover = track['album']['cover_medium']
	copyright = deez.getTrackInfo(trackid)['COPYRIGHT']
	info = discord.Embed()
	info.title = title
	info.add_field(name = "Artist",value = artist)
	if len(album) > 0:
		info.add_field(name = "Album",value = album)
	if len(copyright) > 0:
		info.add_field(name = "Copyright",value = copyright)
	info.add_field(name = "NOTICE", value = "Remember that the artists and studios put a lot of work into making music - purchase music to support them.")
	info.set_image(url = cover)
	await track['channel'].send(content = "Now playing:",embed = info)
	lyrics = deez.getlyrics(title, album, artist)
	chan = track['voice']
	if lyrics['has_lrc']:
		client.LM = await track['channel'].send("```Now playing\n{} - {}\n```".format(title,artist))
		await client.LM.pin()
		stream = deez.streamTrack(trackid,readCallback = sendLyrics,lyrics = lyrics['lrc'],client = client,after = stream_ended)
	else:
		stream = deez.streamTrack(trackid,client = client,after = stream_ended)
	if chan is not None:
		client.playing = True
		client.voiceclient = await chan.connect()
		client.voiceclient.play(discord.PCMAudio(stream),after=None)
@client.event
async def on_ready():
	client.queue = Queue()
	client.playing = False
	print('We have logged in as {0.user}'.format(client))
@client.event
async def on_message(message):
	if message.author == client.user:
		return	
	if message.content.startswith('d!leave'):
		await client.voiceclient.disconnect()
		if client.LM:
			await client.LM.unpin()
	if message.content.startswith('d!skip'):
		await client.voiceclient.disconnect()
		stream_ended()
	if message.content.startswith('d!play'):
		deez.initDeezerApi()
		content = message.content[len('d!play'):]
		data = None
		if '-' in content:
			track,artist = content.split('-')
		else:
			track,artist = content,None
		track = deez.search(track,artist)
		#print(track)
		if len(track) == 0:
			await message.channel.send("Sorry, currently I can't find that track.")
			return
		track = track[0]
		track['channel'] = message.channel
		if not message.author.voice or not message.author.voice.channel:
			await message.channel.send("You must be in a voice channel to play music")
			return 
		track['voice'] = message.author.voice.channel
		client.queue.put(track)
		if not client.playing:
			await processTrack()
		else:
			trackid = track['id']
			title = track['title']
			artist = track['artist']['name']
			album = track['album']['title']
			cover = track['album']['cover_medium']
			copyright = deez.getTrackInfo(trackid)['COPYRIGHT']
			info = discord.Embed()
			info.title = title
			info.add_field(name = "Artist",value = artist)
			if len(album) > 0:
				info.add_field(name = "Album",value = album)
			if len(copyright) > 0:
				info.add_field(name = "Copyright",value = copyright)
			info.add_field(name = "NOTICE", value = "Remember that the artists and studios put a lot of work into making music - purchase music to support them.")
			info.set_image(url = cover)
			await message.channel.send(content="Added to queue",embed = info)
client.run('***REMOVED***')