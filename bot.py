import discord
from queue import Queue
from random import shuffle
import re
import asyncio
import deez
client = discord.Client()
gq = {}

def sendLyrics(text):
	#print(text)
	if len(text) == 0:
		text = client.placeholder
	asyncio.run_coroutine_threadsafe(client.LM.edit(content = '```'+text+'```'),client.loop)
def stream_ended(leave=False):
	if client.looping:
		if client.np:
			client.queue.put(client.np)
			client.np = None
	print("Stream ended")
	asyncio.run_coroutine_threadsafe(client.voiceclient.disconnect(),client.loop)
	if hasattr(client,"LM"):
		asyncio.run_coroutine_threadsafe(client.LM.unpin(),client.loop)
	if not client.queue.empty() and not leave:
		asyncio.run_coroutine_threadsafe(processTrack(),client.loop)
	else:
		client.playing = False
		if hasattr(client,'placeholder'):
			client.placeholder = None
		if hasattr(client,"LM"):
			asyncio.run_coroutine_threadsafe(client.LM.channel.send('Queue ended'),client.loop)
		asyncio.run_coroutine_threadsafe(client.change_presence(activity=discord.Activity()),client.loop)
async def processTrack():
	if not client.queue or client.queue.qsize()==0:
		await message.channel.send("Empty music queue")
		return
	print("Processing track on top of the queue")
	track = client.queue.get()
	client.np = track	
	trackid = track['id']
	title = track['title']
	artist = track['artist']['name']
	album = track['album']['title']
	cover = track['album']['cover_medium']
	duration = track['duration']
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
	#act = discord.Activity(details = "Playing {} by {}".format(title,artist),small_image_url=track['album']['cover_small'],large_image_url=track['album']['cover_medium'],type=discord.ActivityType.playing)
	act = discord.Game(name="{} by {}".format(title,artist))
	await client.change_presence(activity=act)
	lyrics = deez.getlyrics(title, album, artist,duration)
	chan = track['voice']
	if not lyrics['error'] and lyrics['has_lrc']:
		client.LM = await track['channel'].send("```Now playing\n{} - {}\n```".format(title,artist))
		try:
			await client.LM.pin()
		except:
			pass
		stream = deez.streamTrack(trackid,readCallback = sendLyrics,lyrics = lyrics['lrc'],after = stream_ended)
	else:
		stream = deez.streamTrack(trackid,after = stream_ended)
	if chan is not None:
		client.playing = True
		client.voiceclient = await chan.connect()
		client.placeholder = "{} - {}".format(title,artist)
		client.voiceclient.play(discord.PCMAudio(stream),after=None)
@client.event
async def on_ready():
	client.queue = Queue()
	client.looping = False
	client.playing = False
	client.np = None
	client.placeholder = None
	print('We have logged in as {0.user}'.format(client))
	await client.change_presence(activity=discord.Activity())
@client.event
async def on_message(message):
	if message.author.bot:
		return	
	if message.content.startswith('d!leave'):
		stream_ended(leave=True)
		await message.channel.send("Left voice channel and skipped song")
	if message.content.startswith('d!loop'):
		client.looping =not client.looping
		if client.looping:
			await message.channel.send("Looping enabled")
		else:
			await message.channel.send("Looping disabled")

	if message.content.startswith('d!skip'):
		stream_ended()
	if message.content.startswith('d!stop'):
		stream_ended(leave = True)
		while not client.queue.empty():
			client.queue.get()
		await message.channel.send("Stopped playing music and destroyed queue.")
	if message.content.startswith('d!pause'):
		if hasattr(client,"voiceclient"):
			client.voiceclient.pause()
	if message.content.startswith('d!resume'):
		if hasattr(client,"voiceclient"):
			client.voiceclient.resume()
		else:
			processTrack()
	if message.content.startswith('d!queue'):
		if len(client.queue.queue)==0:
			await message.channel.send("Empty music queue")
			return
		embed = discord.Embed()
		embed.title = "Music Queue"
		i = 1
		for item in client.queue.queue:
			embed.add_field(name = "{}.".format(i),value = "{} - {}".format(i,item['title'],item['artist']['name']),inline=False)
			i += 1
		await message.channel.send(content=None,embed=embed)
	if message.content.startswith('d!play'):
		deez.initDeezerApi()
		content = message.content[len('d!play'):]
		data = None
		if '-' in content:
			track = content.split('-')[0]
			artist = content[len(track)+1::]
		else:
			track,artist = content,None
			if len(track.strip()) == 0:
				if not client.playing:
					processTrack()
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
