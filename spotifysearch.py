import requests
import os
import time
from dotenv import load_dotenv
load_dotenv()
s = requests.Session()
market = os.getenv('SPOTIFY_MARKET')
expiry = 0

headers = {
	'Sec-Fetch-Mode': 'cors',
	'Origin': 'https://open.spotify.com',
	'Accept-Language': 'en',
	'Accept': 'application/json',
	'Referer': 'https://open.spotify.com/search/',
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
	'Spotify-App-Version': '1568993648',
	'App-Platform': 'WebPlayer',
	'DNT': '1',
}
def fetchToken():
	_headers = {
		'authority': 'open.spotify.com',
		'dnt': '1',
		'upgrade-insecure-requests': '1',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
		'sec-fetch-mode': 'navigate',
		'sec-fetch-user': '?1',
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		'sec-fetch-site': 'none',
		'accept-encoding': 'gzip, deflate, br',
	}

	response = s.get('https://open.spotify.com/browse', headers=_headers)
	_headers = {
		'Sec-Fetch-Mode': 'cors',
		'DNT': '1',
		'Accept-Language': 'vi',
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
		'Accept': 'application/json',
		'Referer': 'https://open.spotify.com/browse/featured',
		'Spotify-App-Version': '1570840119',
		'App-Platform': 'WebPlayer',
	}

	params = (
		('reason', 'transport'),
		('productType', 'web_player'),
	)

	response = s.get('https://open.spotify.com/access_token', headers=_headers, params=params).json()
	expiry = response['accessTokenExpirationTimestampMs']
	global headers
	headers['Authorization'] =  F"Bearer {response['accessToken']}"
def findSong(title, artist=''):
	if expiry<=time.time():
		fetchToken()
	params = [
		('type', 'track'),
		('decorate_restrictions', 'false'),
		('best_match', 'true'),
		('include_external', 'audio'),
		('limit', '50'),
		('userless', 'true'),
		('market', market),
	]
	if len(artist)>0:
		params.append(('q', F'{title} artist:{artist}'))
	else:
		params.append(('q', F'{title}'))
	response = s.get('https://api.spotify.com/v1/search', headers=headers, params=params)
	d = response.json()
	try:
		return (d['tracks']['items'][0]['name'],d['tracks']['items'][0]['artists'][0]['name'])
	except:
		return None

def findAlbum(title, artist=''):
	if expiry<=time.time():
		fetchToken()
	params = [
		('type', 'album'),
		('decorate_restrictions', 'false'),
		('best_match', 'true'),
		('include_external', 'audio'),
		('limit', '50'),
		('userless', 'true'),
		('market', market),
	]
	if len(artist)>0:
		params.append(('q', F'{title} artist:{artist}'))
	else:
		params.append(('q', F'{title}'))
	response = s.get('https://api.spotify.com/v1/search', headers=headers, params=params)
	d = response.json()
	try:
		return (d['albums']['items'][0]['name'],d['albums']['items'][0]['artists'][0]['name'])
	except:
		return None
if __name__ == "__main__":
	print(findSong("Grand Escape",""))
	print(findSong("Grand Escape","RADWIMPS"))
	print(findAlbum("Weathering With You"))
