import discord
from queue import Queue
from collections import deque
from random import shuffle
import re
import asyncio
import deez
import google
import spotifysearch
import os
import datetime
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
async def printTrack(client,track,mContent = None, withCover = True):
	trackid = track['id']
	title = track['title']
	artist = track['artist']['name']
	album = track['album']['title']
	cover = track['album']['cover_big']
	duration = track['duration']
	copyright = deez.getTrackInfo(trackid)['COPYRIGHT']
	info = discord.Embed()
	info.title = title
	info.add_field(name = "Artist",value = artist)
	if len(album) > 0:
		info.add_field(name = "Album",value = album)
	if len(copyright) > 0:
		info.add_field(name = "Copyright",value = copyright)
	if withCover:
		info.set_image(url = cover)
	await track['channel'].send(content = mContent,embed = info)
def songValidator(url):
	try:
		urlparts = deez.getDeezerUrlParts(url)
		trackid = urlparts['id']
		if urlparts['type'] != 'track':
			return False
		track = deez.searchTrackFromID(trackid)
		return track['preview'] !='' and len(track['available_countries'])>0
	except:
		return False

def ed(word1, word2):
	word2 = word2.lower()
	word1 = word1.lower()
	matrix = [[0 for x in range(len(word2) + 1)] for x in range(len(word1) + 1)]

	for x in range(len(word1) + 1):
		matrix[x][0] = x
	for y in range(len(word2) + 1):
		matrix[0][y] = y

	for x in range(1, len(word1) + 1):
		for y in range(1, len(word2) + 1):
			if word1[x - 1] == word2[y - 1]:
				matrix[x][y] = min(
					matrix[x - 1][y] + 1,
					matrix[x - 1][y - 1],
					matrix[x][y - 1] + 1
				)
			else:
				matrix[x][y] = min(
					matrix[x - 1][y] + 1,
					matrix[x - 1][y - 1] + 1,
					matrix[x][y - 1] + 1
				)

	return matrix[len(word1)][len(word2)]

def findTrack(title,artist):
	artist = artist if artist is not None else ''
	#Find on Spotify for name
	strack = spotifysearch.findSong(title,artist)
	if strack is not None:
		dtrack = deez.search(strack[0],strack[1])
		if len(dtrack)>0:
			return dtrack[0]
	gtrack = google.findSong(title,artist,songValidator)
	if gtrack is not None:
		gtrackid = deez.getDeezerUrlParts(gtrack)['id']
		gtrack = deez.searchTrackFromID(gtrackid)
	dtrack = deez.search(title,artist)
	if len(dtrack)>0:
		dtrack = dtrack[0]
	else:
		dtrack = None
	tracks = list(filter(lambda a:a is not None,[gtrack,dtrack]))
	if len(tracks)==1:
		return tracks[0]
	elif len(tracks)==0:
		return None
	return min(tracks,key=lambda x:ed(title+artist,x['title']+x['artist']['name'])*x['rank'])
def findAlbum(title,artist):
	artist = artist if artist is not None else ''
	galbum = google.findAlbum(title,artist)
	if galbum is not None:
		galbumid = deez.getDeezerUrlParts(galbum)['id']
		galbum = deez.searchAlbumFromID(galbumid)
	dalbum = deez.searchAlbum(title,artist)
	if len(dalbum)>0:
		dalbum = dalbum[0]
	else:
		dalbum = None
	albums = list(filter(lambda a:a is not None,[galbum,dalbum]))
	if len(albums)==1:
		return albums[0]
	elif len(albums)==0:
		return None
	return min(albums,key=lambda x:ed(title+artist,x['title']+x['artist']['name'])*x['rank'])
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
	cover = track['album']['cover_big']
	duration = track['duration']
	await printTrack(client, track,mContent = "Now playing:")
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
		act = discord.Activity(name="{} by {}".format(title,artist),type = discord.ActivityType.listening,start = datetime.datetime.utcnow())
		await cl.change_presence(activity=act)
		client.voiceclient.play(discord.PCMAudio(stream),after=stream.cleanup)
def processAlbum(client,album):
	albumid = album['id']
	title = album['title']
	artist = album['artist']['name']
	cover = album['cover_big']
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
		embed.add_field(name = "`d!play [song_name [- artist]]`", value="Play/Queue a song or resume the queue.`",inline=False)
		embed.add_field(name = "`d!np`", value="Show the song that's currently being played.",inline=False)
		embed.add_field(name = "`d!info song_name [- artist]`", value="Show a song's information.",inline=False)
		embed.add_field(name = "`d!album album_name [- artist] [-shuffle]`", value="Play/Queue an album.",inline=False)
		embed.add_field(name = "`d!queue`", value="Show current music queue",inline=False)
		embed.add_field(name = "`d!shuffle`", value="Shuffle the whole queue",inline=False)
		embed.add_field(name = "`d!skip [noloop|norepeat|nr]`", value="Skip the current song, specify `noloop|norepeat|nr` if you don't want it to loop again.",inline=False)
		embed.add_field(name = "`d!remove index`", value="Remove the song with given index from queue.",inline=False)
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
	if message.content.startswith('d!remove'):
		idx = message.content[len('d!remove')::]
		try:
			idx = int(idx)
			if idx<0:
				idx = len(client.queue) + idx + 1
			elif idx == 0:
				idx = 1
			del client.queue[idx-1]
			await message.channel.send(F"Song at index {idx} was removed from queue.")
		except:
			await message.channel.send("Invalid index.")
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
		album = findAlbum(album,artist)
		if not album:
			await message.channel.send("Sorry, I can't find that album.")
			return
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
				return
		album = findAlbum(album,artist)
		if not album:
			await message.channel.send("Sorry, I can't find that album.")
			return
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
				if client.playing or len(client.queue)==0:
					return
				else:
					await processTrack(client)
					return
		track = findTrack(title, artist)
		if not track:
			await message.channel.send("Sorry, I can't find that track.")
			return
		track['channel'] = message.channel
		track['voice'] = message.author.voice.channel
		client.queue.append(track)
		if not client.playing:
			await processTrack(client)
		else:
			await printTrack(client, track,mContent = "Added to Queue",withCover = False)
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
		track = findTrack(title, artist)
		if not track:
			await message.channel.send("Sorry, I can't find that track.")
			return
		else:
			track['channel'] = message.channel
			await printTrack(client, track, mContent = "May this be the song you requested?")
		return
load_dotenv()
cl.run(os.getenv('BOT_TOKEN'))
