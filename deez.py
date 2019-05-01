CHUNK_SIZE = 2048
import io
import os
import requests
from math import floor
from random import random
import re
from hashlib import md5
from Crypto.Cipher import AES,Blowfish,blockalgo
from time import sleep
import json
import binascii
import pyaudio
import subprocess
import asyncio
import fcntl
from queue import Queue
import datetime
import threading
from urllib.parse import quote_plus
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
session.cookies['arl']='***REMOVED***'
def getApiCid():
	return floor(1e9 * random())
def initDeezerApi():
	param = unofficialApiQueries.copy()
	param.update({'method':'deezer.getUserData','cid':getApiCid()})
	response = session.post(unofficialApiUrl,params=param)
	response=response.json()
	if response:
		print('Successfully initiated Deezer API. Checkform: "' + response['results']['checkForm'] + '"');
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
		if counter % 3 == 0 and len(chunk)==CHUNK_SIZE:
			cipher = Blowfish.new(getBlowfishKey(trackInfos),Blowfish.MODE_CBC,bytes(range(8)))
			decrypted= cipher.decrypt(decrypted)
		counter += 1
		yield decrypted
	return
def downloadTrack(trackInfos,trackQualityId):
	trackDownloadUrl = getTrackDownloadUrl(trackInfos, trackQualityId)	
	return decryptTrack(trackInfos,session.get(trackDownloadUrl,headers=httpHeaders,stream=True).iter_content(chunk_size=2048))
	
def downloadSingleTrack(trackid):
	print(F"Starting download for trackid {trackid}")
	if(False):
		pass
	else:
		trackInfo = getTrackInfo(trackid)
		return downloadTrack(trackInfo, selectedMusicQuality['id'])
def download(deezerUrl):
	print(F"Starting download from url {deezerUrl}")
	deezerUrlParts = getDeezerUrlParts(deezerUrl)
	assert(deezerUrlParts['type']=='track')
	return downloadSingleTrack(deezerUrlParts['id'])

def search(track,artist = None):
	if not artist:
		return requests.get('https://api.deezer.com/search?q=track:"{}"'.format(quote_plus(track))).json()['data']
	else:
		return requests.get('https://api.deezer.com/search?q=track:"{}"artist:"{}"'.format(quote_plus(track),quote_plus(artist))).json()['data']
		
def getlyrics(track,album,artist):
	USER_TOKEN = '***REMOVED***'
	headers = {
		'$Host': 'apic-desktop.musixmatch.com',
		'$Connection': 'close',
		'$User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Musixmatch/0.21.27 Chrome/66.0.3359.181 Electron/3.1.3 Safari/537.36',
		'$Accept': '*/*',
		'$Accept-Encoding': 'gzip, deflate',
	}

	params = (
		('format', 'json'),
		('q_track', track),
		('q_artist', artist),
		('q_album', album),
		('user_language', 'en'),
		('tags', 'nowplaying'),
		('namespace', 'lyrics_synched'),
		('f_subtitle_length_max_deviation', '1'),
		('subtitle_format', 'mxm'),
		('app_id', 'web-desktop-app-v1.0'),
		('usertoken', USER_TOKEN),	
	)
	result = {}
	result['error']=False
	try:
		response = requests.get('https://apic-desktop.musixmatch.com/ws/1.1/macro.subtitles.get', headers=headers, params=params, verify=False)
		d = json.loads(response.text)
		lyrics = d['message']['body']['macro_calls']['track.lyrics.get']['message']['body']['lyrics']['lyrics_body']
		#print(lyrics)
		result['txt'] = lyrics
		result['has_lrc'] = False
		try:
			synced_lyrics = d['message']['body']['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']['subtitle_body']
			sd = json.loads(synced_lyrics)
			
			result['lrc']=sd
			result['has_lrc']=True
		except:
			pass
		finally:
			return result
	except:
		result['error']=True
		return result
class FFMpeg:
	def __init__(self,callback = None,lyrics = None,client = None):
		self.proc = subprocess.Popen(['/usr/local/bin/ffmpeg','-nostdin','-f','mp3','-i','-','-analyzeduration','0','-loglevel','0','-f','s16le','-ac','2','-ar','48000','pipe:1'],stdin = subprocess.PIPE,stdout = subprocess.PIPE,stderr = subprocess.DEVNULL)
		self.stdin = self.proc.stdin
		self.stdout = self.proc.stdout
		self.stderr = self.proc.stderr
		self.time = datetime.time()
		self.callback = callback
		self.lyrics = lyrics
		self.client = client
		self.oflag = fcntl.fcntl(self.stdout.fileno(), fcntl.F_GETFL)
		self.lock = threading.Lock()
		'''
		fcntl.fcntl(
				self.stdout.fileno(),
				fcntl.F_SETFL,
				fcntl.fcntl(self.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
			)
		'''
	def callbackLyrics(self):
		self.lock.acquire()
		line = self.lyrics[0]
		t = line['time']
		#F"[{line['time']['minutes']:02}:{line['time']['seconds']:02}.{line['time']['hundredths']:02}]"
		while self.time >= datetime.time(minute =t['minutes'],second = t['seconds'],microsecond=t['hundredths']*(10000)):
			#print(line['text'])
			if self.callback:
				asyncio.run(self.callback(client = self.client, text = line['text']))
			del self.lyrics[0]
			line = self.lyrics[0]
			t = line['time']
		self.lock.release()
	def __del__(self):
		self.proc.terminate()
	def read(self,size=3840):
		data =  self.proc.stdout.read(size)
		self.time = (datetime.datetime.combine(datetime.date(1,1,1),self.time) + datetime.timedelta(milliseconds=20)).time()
		if self.lyrics:
			threading._start_new_thread(self.callbackLyrics,())
		#print(self.time.strftime("%M:%S"))
		return data #+ bytearray([0]*(size-len(data)))
	def write(self,data):
		r = self.proc.stdin.write(data)
		self.proc.stdin.flush()
		return r
	def alive(self):
		return self.proc.poll() is not None
	def close(self):
		self.proc.stdin.close()
def stream(ffmpeg,trackid):
	for chunk in downloadSingleTrack(trackid):
		ffmpeg.write(chunk)
	ffmpeg.close()
def streamTrack(trackid,readCallback=None,lyrics=None,client =None):
	ffmpeg = FFMpeg(callback=readCallback,lyrics =lyrics,client = client)
	threading._start_new_thread(stream,(ffmpeg,trackid))
	return ffmpeg
async def sendLyrics(client,text):
	print(text)
if __name__ =="__main__":
	initDeezerApi()
	p = pyaudio.PyAudio()
	astream = p.open(format=p.get_format_from_width(2),
												channels=2,
												rate=48000,
												output=True)
	track = "Faded"
	artist = "Alan Walker"
	track = search(track,artist)
	#print(track)
	track = track[0]
	trackid = track['id']
	title = track['title']
	artist = track['artist']['name']
	album = track['album']['title']
	cover = track['album']['cover_medium']
	lyrics = getlyrics(title, album, artist)
	if lyrics['has_lrc']:
		s = streamTrack(trackid,readCallback = sendLyrics,lyrics = lyrics['lrc'],client = None)
	else:
		s = streamTrack(trackid)
	while True:
		c = s.read()
		if c  and len(c)>0:
			astream.write(c)
		else:
			break
		


