#!/usr/bin/env python3
CHUNK_SIZE = 3840

import io
import os
import signal
import requests
from math import floor
from random import random
import re
from hashlib import md5
from Crypto.Cipher import AES,Blowfish,blockalgo
from time import sleep
import json
import binascii
import subprocess
import asyncio
import fcntl
from queue import Queue
import datetime
import threading
from collections import deque
import urllib3
from lyrics import *
urllib3.disable_warnings()
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()
httpHeaders = {
		'user-agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
		'cache-control':   'max-age=0',
		'accept-language': 'en-US,en;q=0.9,en-US;q=0.8,en;q=0.7',
		'accept-charset':  'utf-8,ISO-8859-1;q=0.8,*;q=0.7',
		'content-type':    'text/plain;charset=UTF-8'
	};
unofficialApiUrl = 'https://www.deezer.com/ajax/gw-light.php';
ajaxActionUrl = 'https://www.deezer.com/ajax/action.php';

unofficialApiQueries = {
	'api_version': '1.0',
	'api_token':   '',
	'input':       3
};
musicQualities = {
	'MP3_128':  {
		'id':             1,
		'name':           'MP3 - 128 kbps',
		'aproxMaxSizeMb': '100'
	},
	'MP3_256':  {
		'id':   5,
		'name': 'MP3 - 256 kbps'
	},
	'MP3_320':  {
		'id':             3,
		'name':           'MP3 - 320 kbps',
		'aproxMaxSizeMb': '200'
	},
	'FLAC':     {
		'id':             9,
		'name':           'FLAC - 1411 kbps',
		'aproxMaxSizeMb': '700'
	},
	'MP3_MISC': {
		'id':   0,
		'name': 'User uploaded song'
	}
};

selectedMusicQuality = musicQualities['MP3_128'];
session = requests.Session()
session.headers = httpHeaders
session.cookies['arl']=os.getenv('DEEZER_ARL')
def getApiCid():
	return floor(1e9 * random())
def initDeezerApi():
	param = unofficialApiQueries.copy()
	param.update({'method':'deezer.getUserData','cid':getApiCid()})
	response = session.post(unofficialApiUrl,params=param)
	response=response.json()
	if response:
		#print('Successfully initiated Deezer API. Checkform: "' + response['results']['checkForm'] + '"');
		unofficialApiQueries['api_token'] = response['results']['checkForm'];
def getDeezerUrlParts(deezerUrl):
	urlParts = re.split(r'\/(\w+)\/(\d+)',deezerUrl);

	return {
		'type': urlParts[1],
		'id':   urlParts[2]
	};
def getSongFileName(trackInfos, trackQuality):
	step1 = '¤'.join([trackInfos['MD5_ORIGIN'], str(trackQuality), trackInfos['SNG_ID'], trackInfos['MEDIA_VERSION']])
	step2 = md5(step1.encode('cp1252')).hexdigest() + '¤' + step1 + '¤'
	while len(step2) % 16 > 0:
		 step2+=' '
	return binascii.hexlify(AES.new(b'jo6aey6haid2Teih', AES.MODE_ECB).encrypt(step2.encode('cp1252')))
def getBlowfishKey(trackInfos) :
		SECRET = 'g4el58wc0zvf9na1'

		idMd5 = md5(trackInfos['SNG_ID'].encode('cp1252')).hexdigest()
		bfKey = ''

		for i in range(16):
			bfKey += chr(ord(idMd5[i]) ^ ord(idMd5[i + 16]) ^ ord(SECRET[i]));

		return bfKey;


def getTrackInfo(trackid):
	param = unofficialApiQueries.copy()
	param.update({'method':'deezer.pageTrack','cid':getApiCid()})
	data = {'SNG_ID':trackid}
	resp = session.post(unofficialApiUrl,params=param,data=json.dumps(data))
	resp= resp.json()
	if resp:
		trackInfo = resp['results']['DATA']
		return trackInfo
def getTrackDownloadUrl(trackInfos, trackQuality):
	cdn = trackInfos['MD5_ORIGIN'][0];

	return 'https://e-cdns-proxy-' + cdn + '.dzcdn.net/mobile/1/' + getSongFileName(trackInfos, trackQuality).decode('utf-8')
def decryptTrack(trackInfos,trackBuffer):
	counter = 0
	cipher = Blowfish.new(getBlowfishKey(trackInfos),Blowfish.MODE_CBC,bytes(range(8)))
	for chunk in trackBuffer:
		decrypted = chunk
		if counter % 3 == 0 and len(chunk)==2048:
			cipher = Blowfish.new(getBlowfishKey(trackInfos),Blowfish.MODE_CBC,bytes(range(8)))
			decrypted= cipher.decrypt(decrypted)
		counter += 1
		yield decrypted
	return
def downloadTrack(trackInfos,trackQualityId):
	trackDownloadUrl = getTrackDownloadUrl(trackInfos, trackQualityId)
	return decryptTrack(trackInfos,session.get(trackDownloadUrl,headers=httpHeaders,stream=True).iter_content(chunk_size=2048))
	
def downloadSingleTrack(trackid):
	initDeezerApi()
	#print(F"Starting download for trackid {trackid}")
	if(False):
		pass
	else:
		trackInfo = getTrackInfo(trackid)
		return downloadTrack(trackInfo, selectedMusicQuality['id'])
def download(deezerUrl):
	#print(F"Starting download from url {deezerUrl}")
	deezerUrlParts = getDeezerUrlParts(deezerUrl)
	assert(deezerUrlParts['type']=='track')
	return downloadSingleTrack(deezerUrlParts['id'])

def search(track,artist = None):
	if not artist:
		res = requests.get('https://api.deezer.com/search?q="{}"'.format(quote_plus(track))).json()['data']
	else:
		res = requests.get('https://api.deezer.com/search?q=track:"{}"artist:"{}"'.format(quote_plus(track),quote_plus(artist))).json()['data']
	
	res.sort(key=lambda x:x['rank'],reverse=True)
	return res
		
def searchTrackFromID(trackid):
	return requests.get('https://api.deezer.com/track/{}'.format(trackid)).json()
def searchAlbumFromID(albumid):
	return requests.get('https://api.deezer.com/album/{}'.format(albumid)).json()
def searchAlbum(album,artist = None):
	if not artist:
			res = requests.get('https://api.deezer.com/search/album?q=album:"{}"'.format(quote_plus(album))).json()['data']
	else:
		res =  requests.get('https://api.deezer.com/search/album?q=album:"{}"artist:"{}"'.format(quote_plus(album),quote_plus(artist))).json()['data']
	res.sort(key=lambda x:x['rank'],reverse=True)
	return res
def getAlbumTracks(albumid):
	return requests.get("https://api.deezer.com/album/{}/tracks".format(albumid)).json()['data']

class FFMpeg:
	def __init__(self,client = None,callback = None,lyrics = None,after = None):
		self.proc = subprocess.Popen(['ffmpeg','-nostdin','-f','mp3','-i','-','-analyzeduration','0','-loglevel','0','-f','s16le','-ac','2','-ar','48000','pipe:1'],stdin = subprocess.PIPE,stdout = subprocess.PIPE,stderr = subprocess.DEVNULL)
		self.stdin = self.proc.stdin
		self.stdout = self.proc.stdout
		self.stderr = self.proc.stderr
		self.callback = callback
		self.lyrics = lyrics
		self.after = after
		self.oflag = fcntl.fcntl(self.stdout.fileno(), fcntl.F_GETFL)
		self.lock = threading.Lock()
		self.end = threading.Event()
		self.new_time = threading.Event()
		self.buffering_done = False
		self.client = client
		self.cidx = 0
		self.chunks = []
		self.buf = b''
		self.prevLine = ''
		threading._start_new_thread(self.callbackLyrics,())
		threading._start_new_thread(self.poll,())
		threading._start_new_thread(self._cleanup,())
		'''
		fcntl.fcntl(
				self.stdout.fileno(),
				fcntl.F_SETFL,
				fcntl.fcntl(self.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
			)
		'''
	def time(self):
		return 0.02*self.cidx
	def callbackLyrics(self):
		if not self.lyrics or len(self.lyrics) == 0:
			return
		while True:
			if self.end.is_set():
				return
			self.new_time.wait()
			self.new_time.clear()
			if self.end.is_set():
				return
			if len(self.lyrics) == 0:
				return
			for line in reversed(self.lyrics):
				t = line['time']
				if self.time() >= t['total']:
					#print(line['text'])
					if self.callback and self.prevLine!=line:
						threading._start_new_thread(self.callback,(),{'client':self.client,'line':line})
					self.prevLine = line
					break
	def __del__(self):
		self.stop()
	def read(self,size=3840):
		while len(self.chunks)<= self.cidx and not self.buffering_done:
			sleep(0.5)
		if self.buffering_done and self.cidx >= len(self.chunks):
			if not self.end.is_set():
				self.end.set()
				self.new_time.set()
				if self.after:
					asyncio.create_task(self.after(client = self.client))
			return b''
		
		data = self.chunks[self.cidx]
		self.cidx += 1
		if len(data)< 3840:
			self.end.set()
		if self.lyrics:
			self.new_time.set()
		if len(data)< 3840:
			if self.after:
				asyncio.create_task(self.after(client = self.client))
		return data #+ bytearray([0]*(size-len(data)))
	def write(self,data):
		if not self.proc:
			self.end.set()
			return None
		try:
			r = self.proc.stdin.write(data)
			self.proc.stdin.flush()
		except BrokenPipeError:
			return None
		return r
	def alive(self):
		return self.proc.poll() is not None
	def close(self):
		if self.proc:
			self.proc.stdin.close()
	def stop(self):
		self.end.set()
	def append(self,data):
		self.buf += data
		if len(self.buf) >= CHUNK_SIZE:
			self.chunks.append(self.buf[:CHUNK_SIZE])
			self.buf = self.buf[CHUNK_SIZE:]
	def clearBuf(self):
		if len(self.buf) > 0:
			self.chunks.append(self.buf)
			self.buf = b''
		self.buffering_done = True
	def poll(self):
		while True:
			try:
				data = self.proc.stdout.read(CHUNK_SIZE)
				self.append(data)
			except AttributeError:
				self.clearBuf()
				return
	def seek(self,second):
		self.cidx = int(second/0.02)
	def _cleanup(self):
		#print("Waiting for stream.")
		self.end.wait()
		#print("Stream ended. House-keeping.")
		self.new_time.set()
		threading._start_new_thread(self.kill,())
	def cleanup(self,*args,**kwargs):
		#print("Stream cleanup requested. Ending stream.")
		self.end.set()
	def kill(self):
		if not self.proc:
			return
		self.proc.kill()
		#print("Killing ffmpeg")
		self.proc = None
		#print("ffmpeg killed")
def stream(ffmpeg,trackid):
	for chunk in downloadSingleTrack(trackid):
		if not ffmpeg.write(chunk):
			break
	ffmpeg.close()
def streamTrack(trackid,client = None,readCallback=None,lyrics=None,after = None):
	ffmpeg = FFMpeg(client = client,callback=readCallback,lyrics =lyrics,after=after)
	threading._start_new_thread(stream,(ffmpeg,trackid))
	return ffmpeg

is_playing = threading.Event()
def waitKey(scr):
	while True:
		c = scr.get_wch()
		if c in ('p','P',' '):
			if is_playing.is_set():
				is_playing.clear()
			else:
				is_playing.set()
def main(scr):
	import curses
	curses.noecho()
	scr.clear()
	placeholder = ''
	def sendLyrics(line,**kwargs):
		#print(text)
		text = line['text']
		if len(text) == 0:
			text = placeholder
		elif 'en_text' in line:
			et = line['en_text']
			if len(et) == 0:
				et = placeholder
			else:
				text += '\n\n'+et+'\n'
		scr.move(1,0)
		scr.clrtoeol()
		scr.addstr(1,0,text)
		scr.refresh()
	import pyaudio
	initDeezerApi()
	p = pyaudio.PyAudio()
	astream = p.open(format=p.get_format_from_width(2),
												channels=2,
												rate=48000,
												output=True)
	import sys
	track = sys.argv[1]
	artist = sys.argv[2] if len(sys.argv)>2 else None
	track = search(track,artist)
	#print(track)
	track = track[0]
	trackid = track['id']
	title = track['title']
	artist = track['artist']['name']
	album = track['album']['title']
	cover = track['album']['cover_medium']
	duration = track['duration']
	#placeholder = F"{title} - {artist}"
	scr.addstr(F"{title} - {artist}")
	scr.refresh()
	lyrics = getlyrics(title, album, artist,duration)
	if 'has_lrc' in lyrics and lyrics['has_lrc']:
		s = streamTrack(trackid,readCallback = sendLyrics,lyrics = lyrics['lrc'],client = None)
	else:
		s = streamTrack(trackid)
	is_playing.set()
	threading._start_new_thread(waitKey,(scr,))
	while True:
		is_playing.wait()
		c = s.read()
		if c  and len(c)>0:
			astream.write(c)
		else:
			break
if __name__ == "__main__":
	import curses
	curses.wrapper(main)

