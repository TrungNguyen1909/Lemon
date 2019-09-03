import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
load_dotenv()
gsession = requests.session()
gsession.headers = {
		'authority': 'www.google.com',
		'dnt': '1',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		'referer': 'https://www.google.com/',
		'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}
gsession.get('https://www.google.com/')
region = os.getenv('GOOGLE_REGION')
def findSong(title, artist='',validator = None):
	
	resp = None
	if artist is not None:
		resp  = gsession.get('https://www.google.com/search',params = {'q':'{} - {} site:deezer.com'.format(artist,title),'gl':region})
	else:
		resp  = gsession.get('https://www.google.com/search',params = {'q':'{} site:deezer.com'.format(title),'gl':region})
	soup = BeautifulSoup(resp.text,'lxml')
	name_links = []
	for nl in soup.find_all('div', class_='r'):
		name_links.append((nl.find_all('div',class_='ellip')[0].text,nl.find_all('a')[0]['href']))
	for n, l in name_links:
		print(f'{n}\n{l}')
		print('---------')
		if validator:
			if validator(l):
				return l
		elif 'track' in l:
			return l
	return None
def findAlbum(title, artist='',validator = None):
	resp = None
	if artist is not None:
		resp  = gsession.get('https://www.google.com.vn/search',params = {'q':'{} - {} site:deezer.com'.format(artist,title),'gl':region})
	else:
		resp  = gsession.get('https://www.google.com/search',params = {'q':'{} site:deezer.com'.format(title),'gl':region})
	soup = BeautifulSoup(resp.text,'lxml')
	name_links = []
	for nl in soup.find_all('div', class_='r'):
		name_links.append((nl.find_all('div',class_='ellip')[0].text,nl.find_all('a')[0]['href']))
	for n, l in name_links:
		print(f'{n}\n{l}')
		print('---------')
		if validator:
			if validator(l):
				return l
		elif 'album' in l:
			return l
	return None
if __name__ == "__main__":
	print(findSong("Counting star","One Republic"))
	print(findAlbum("Weathering with you","RADWIMPS"))
