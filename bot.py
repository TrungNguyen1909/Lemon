import discord
from queue import Queue
from collections import deque
from random import shuffle
import re
import asyncio
import deez
import google
import os
from dotenv import load_dotenv
cl = discord.Client()
gq = {}
class mServer():
	def __init__(self):
		self.queue = deque()
		self.looping = False
		self.playing = False
		self.np = None
		self.placeholder = None
def sendLyrics(client,line):
	#print(text)
	text = line['text']
	if len(text) == 0:
		text = client.placeholder
	elif 'en_text' in line:
		et = line['en_text']
		if len(et) == 0:
			et = client.placeholder
		else:
			text += '\n\n'+et+'\n'
	asyncio.run_coroutine_threadsafe(client.LM.edit(content = '```'+text+'```'),cl.loop)
def stream_ended(client,skip = False,leave=False):
	if client.looping:
		if client.np and not skip:
			client.queue.append(client.np)
			client.np = None
	print("Stream ended.")
	if hasattr(client, 'voiceclient'):
		asyncio.run_coroutine_threadsafe(client.voiceclient.disconnect(),cl.loop)
	if hasattr(client,"LM"):
		asyncio.run_coroutine_threadsafe(client.LM.unpin(),cl.loop)
	if len(client.queue) and not leave:
		asyncio.run_coroutine_threadsafe(processTrack(client),cl.loop)
	else:
		client.playing = False
		client.np = None
		if hasattr(client,'placeholder'):
			client.placeholder = None
		if hasattr(client,"LM") and len(client.queue)==0:
			asyncio.run_coroutine_threadsafe(client.LM.channel.send('Queue ended'),cl.loop)
		asyncio.run_coroutine_threadsafe(cl.change_presence(activity=discord.Activity()),cl.loop)
async def printTrack(client,track,mContent = None):
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
	info.set_image(url = cover)
	await track['channel'].send(content = mContent,embed = info)
async def processTrack(client):
	if not client.queue or len(client.queue)==0:
		#await message.channel.send("Empty music queue")
		return
	print("Processing track on top of the queue")
	track = client.queue.popleft()
	client.np = track	
	trackid = track['id']
	title = track['title']
	artist = track['artist']['name']
	album = track['album']['title']
	cover = track['album']['cover_medium']
	duration = track['duration']
	await printTrack(client, track,mContent = "Now playing:")
	#act = discord.Activity(details = "Playing {} by {}".format(title,artist),small_image_url=track['album']['cover_medium'],large_image_url=track['album']['cover_medium'],type=discord.ActivityType.playing)
	act = discord.Game(name="{} by {}".format(title,artist))
	await cl.change_presence(activity=act)
	lyrics = deez.getlyrics(title, album, artist,duration)
	chan = track['voice']
	if not lyrics['error'] and lyrics['has_lrc']:
		client.LM = await track['channel'].send("```Now playing\n{} - {}\n```".format(title,artist))
		try:
			await client.LM.pin()
		except:
			pass
		stream = deez.streamTrack(trackid,client=client,readCallback = sendLyrics,lyrics = lyrics['lrc'],after = stream_ended)
	else:
		stream = deez.streamTrack(trackid,client=client,after = stream_ended)
	if chan is not None:
		client.playing = True
		client.voiceclient = await chan.connect()
		client.placeholder = "{} - {}".format(title,artist)
		client.voiceclient.play(discord.PCMAudio(stream),after=stream.cleanup)
def processAlbum(client,album):
	albumid = album['id']
	title = album['title']
	artist = album['artist']['name']
	cover = album['cover_medium']
	info = discord.Embed()
	info.title = title
	info.add_field(name = "Artist",value = artist)
	info.set_image(url = cover)
	tracklist = deez.getAlbumTracks(albumid)
	l = ''
	for track in tracklist:
		l += track['title']+'\n'
	info.add_field(name="Tracks",value=l)
	return (info,tracklist)
@cl.event
async def on_ready():
	print('We have logged in as {0.user}'.format(cl))
	await cl.change_presence(activity=discord.Activity())
@cl.event
async def on_message(message):
	if message.author.bot:
		return
	if message.guild.id not in gq:
		gq[message.guild.id] = mServer()
	client = gq[message.guild.id]
	if message.content.startswith('d!help'):
		embed = discord.Embed()
		embed.title = "Help"
		embed.add_field(name = "`d!help`", value="Show this help message",inline=False)
		embed.add_field(name = "`d!play song_name [- artist]`", value="Play/Queue a song.`",inline=False)
		embed.add_field(name = "`d!np`", value="Show the song that's currently being played.",inline=False)
		embed.add_field(name = "`d!info song_name [- artist]`", value="Show a song's information.",inline=False)
		embed.add_field(name = "`d!album album_name [- artist] [-shuffle]`", value="Play/Queue an album.",inline=False)
		embed.add_field(name = "`d!queue`", value="Show current music queue",inline=False)
		embed.add_field(name = "`d!shuffle`", value="Shuffle the whole queue",inline=False)
		embed.add_field(name = "`d!skip [noloop|norepeat|nr]`", value="Skip the current song, specify `noloop|norepeat|nr` if you don't want it to loop again.",inline=False)
		embed.add_field(name = "`d!pause`", value="Pause the current song",inline=False)
		embed.add_field(name = "`d!resume`", value="Resume the paused song or resume a left queue",inline=False)
		embed.add_field(name = "`d!leave`", value="Skip the current song and leaves the current voice channel.",inline=False)
		embed.add_field(name = "`d!stop`", value="Stop the music session, destroy the whole queue",inline=False)
		await message.channel.send(embed = embed)
		return
	if message.content.startswith('d!leave'):
		stream_ended(client,leave=True)
		await message.channel.send("Left voice channel and skipped song")
		return 
	if message.content.startswith('d!loop'):
		client.looping = not client.looping
		if client.looping:
			await message.channel.send("Looping enabled")
		else:
			await message.channel.send("Looping disabled")
		return
	if message.content.startswith('d!skip'):
		if 'noloop' in message.content or 'nr' in message.content or 'norepeat' in message.content:
			stream_ended(client,skip=True)
		else:
			stream_ended(client)
		return
	if message.content.startswith('d!stop'):
		stream_ended(client,leave = True)
		client.queue = deque()
		await message.channel.send("Stopped playing music and destroyed queue.")
		return
	if message.content.startswith('d!pause'):
		if hasattr(client,"voiceclient"):
			client.voiceclient.pause()
		return
	if message.content.startswith('d!resume'):
		if hasattr(client,"voiceclient"):
			client.voiceclient.resume()
		else:
			if not client.queue or len(client.queue)==0:
				await message.channel.send("Empty music queue")
				return
			await processTrack(client)
		return
	if message.content.startswith('d!queue'):
		if len(client.queue)==0:
			await message.channel.send("Empty music queue")
			return
		embed = discord.Embed()
		embed.title = "Music Queue"
		i = 1
		for item in client.queue:
			embed.add_field(name = "{}.".format(i),value = "{} - {}".format(item['title'],item['artist']['name']),inline=False)
			i += 1
		await message.channel.send(content=None,embed=embed)
		return
	if message.content.startswith('d!shuffle'):
		if len(client.queue)==0:
			await message.channel.send("Empty music queue")
			return
		l = list(client.queue)
		shuffle(l)
		client.queue = deque(l)
		embed = discord.Embed()
		embed.title = "Music Queue"
		i = 1
		for item in client.queue:
			embed.add_field(name = "{}.".format(i),value = "{} - {}".format(item['title'],item['artist']['name']),inline=False)
			i += 1
		await message.channel.send(content=None,embed=embed)
		return
	if message.content.startswith('d!album'):
		if not message.author.voice or not message.author.voice.channel:
			await message.channel.send("You must be in a voice channel to play music")
			return
		deez.initDeezerApi()
		content = message.content[len('d!album'):]
		shuff = False
		if '-shuffle' in content:
			shuff = True
			content = content.replace('-shuffle','')
		data = None
		if '-' in content:
			album = content.split('-')[0]
			artist = content[len(album)+1::]
		else:
			album,artist = content,None
			if len(album.strip()) == 0:
				return
		albums = deez.searchAlbum(album,artist)
		if len(albums) == 0:
			try:
				res = google.findAlbum(album,artist)
				if res:
					albumid = deez.getDeezerUrlParts(res)['id']
					album = deez.searchAlbumFromID(albumid)
					if not album:
						raise ValueError
				else:
					raise ValueError
			
			except ValueError:
				await message.channel.send("Sorry, I can't find that track.")
				return
		else:
			album = albums[0]
		albuminfo = processAlbum(client, album)
		await message.channel.send(content="Album:",embed = albuminfo[0])
		trackList = albuminfo[1]
		if shuff:
			shuffle(trackList)
		for track in trackList:
			track['channel'] = message.channel
			track['voice'] = message.author.voice.channel
			track['album'] = album
			client.queue.append(track)
		if not client.playing:
			await processTrack(client)
		return
	if message.content.startswith('d!info-album'):
		deez.initDeezerApi()
		content = message.content[len('d!info-album'):]
		data = None
		if '-' in content:
			album = content.split('-')[0]
			artist = content[len(album)+1::]
		else:
			album,artist = content,None
			if len(album.strip()) == 0:
				if not client.playing:
					await processTrack(client)
		albums = deez.searchAlbum(album,artist)
		if len(albums) == 0:
			try:
				res = google.findAlbum(album,artist)
				if res:
					albumid = deez.getDeezerUrlParts(res)['id']
					album = deez.searchAlbumFromID(albumid)
					if not album:
						raise ValueError
				else:
					raise ValueError
			
			except ValueError:
				await message.channel.send("Sorry, I can't find that track.")
				return
		else:
			album = albums[0]
		albuminfo = processAlbum(client, album)
		await message.channel.send(content="May this be the album you requested?",embed = albuminfo[0])
		return
	if message.content.startswith('d!play'):
		if not message.author.voice or not message.author.voice.channel:
			await message.channel.send("You must be in a voice channel to play music")
			return 
		deez.initDeezerApi()
		content = message.content[len('d!play'):]
		data = None
		if '-' in content:
			title = content.split('-')[0]
			artist = content[len(title)+1::]
		else:
			title,artist = content,None
			if len(title.strip()) == 0:
				return
		track = deez.search(title,artist)
		#print(track)
		if len(track) == 0:
			try:
				res = google.findSong(title,artist)
				if res:
					trackid = deez.getDeezerUrlParts(res)['id']
					track = deez.searchTrackFromID(trackid)
					if not track:
						raise ValueError
				else:
					raise ValueError
			
			except ValueError:
				await message.channel.send("Sorry, I can't find that track.")
				return
		else:
			track = track[0]
		track['channel'] = message.channel
		track['voice'] = message.author.voice.channel
		client.queue.append(track)
		if not client.playing:
			await processTrack(client)
		else:
			await printTrack(client, track,mContent = "Added to Queue")
		return
	if message.content.startswith("d!np"):
		if client.np:
			await printTrack(client,client.np,mContent = "Now playing:")
		else:
			await message.channel.send("I'm currently not playing any song.")
	if message.content.startswith('d!info'):
		deez.initDeezerApi()
		content = message.content[len('d!info'):]
		data = None
		if '-' in content:
			title = content.split('-')[0]
			artist = content[len(title)+1::]
		else:
			title,artist = content,None
			if len(title.strip()) == 0:
				return
		track = deez.search(title,artist)
		#print(track)
		if len(track) == 0:
			try:
				res = google.findSong(title,artist)
				if res:
					trackid = deez.getDeezerUrlParts(res)['id']
					track = deez.searchTrackFromID(trackid)
					if not track:
						raise ValueError
				else:
					raise ValueError
			
			except ValueError:
				await message.channel.send("Sorry, I can't find that track.")
				return
		else:
			track = track[0]
			track['channel'] = message.channel
			await printTrack(client, track, mContent = "May this be the song you requested?")
		return
load_dotenv()
cl.run(os.getenv('BOT_TOKEN'))
