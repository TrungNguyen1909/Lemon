import discord
from enum import Enum, auto
from queue import Queue
from random import shuffle
import re
import asyncio
import deez
client = discord.Client()
async def sendLyrics(client,text):
	#print(text)
	asyncio.run_coroutine_threadsafe(client.LM.edit(content = text),client.loop)
def stream_ended():
	print("Stream ended")
	asyncio.run_coroutine_threadsafe(client.voiceclient.disconnect(),client.loop)
	if client.LM:
		asyncio.run_coroutine_threadsafe(client.LM.unpin(),client.loop)
@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))
@client.event
async def on_message(message):
	if message.author == client.user:
		return
	if message.content.startswith('d!leave'):
		await client.voiceclient.disconnect()
		if client.LM:
			await client.LM.unpin()
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
		track = track[0]
		trackid = track['id']
		title = track['title']
		artist = track['artist']['name']
		album = track['album']['title']
		cover = track['album']['cover_medium']
		info = discord.Embed()
		info.title = title
		info.add_field(name = "Artist",value = artist)
		info.add_field(name = "Album",value = album)
		info.set_image(url = cover)
		await message.channel.send(embed = info)
		lyrics = deez.getlyrics(title, album, artist)
		chan = message.author.voice.channel
		if lyrics['has_lrc']:
			client.LM = await message.channel.send("{} - {}".format(title,artist))
			await client.LM.pin()
			stream = deez.streamTrack(trackid,readCallback = sendLyrics,lyrics = lyrics['lrc'],client = client)
		else:
			stream = deez.streamTrack(trackid)
		if chan is not None:
			client.voiceclient = await chan.connect()
			client.voiceclient.play(discord.PCMAudio(stream),after=stream_ended)
client.run('***REMOVED***')