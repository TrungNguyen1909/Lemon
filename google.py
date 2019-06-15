import requests
from bs4 import BeautifulSoup
def findSong(title, artist='',validator = None):
	session = requests.session()
	session.headers = {
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
			'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
		}
	resp = None
	if artist is not None:
		resp  = session.get('https://www.google.com/search',params = {'q':'{} - {} site:deezer.com'.format(title,artist)})
	else:
		resp  = session.get('https://www.google.com/search',params = {'q':'{} site:deezer.com'.format(title)})
	soup = BeautifulSoup(resp.text,'lxml')
	name_link = soup.find_all('h3', class_='LC20lb')
	link = soup.find_all('cite')
	for n_link, l in zip(name_link,link):
		print(f'{n_link.text}\n{l.text}')
		print('---------')
		if validator:
			if validator(l.text):
				return l.text
		elif 'track' in l.text:
			return l.text
	return None
def findAlbum(title, artist='',validator = None):
	session = requests.session()
	session.headers = {
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
			'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
		}
	resp = None
	if artist is not None:
		resp  = session.get('https://www.google.com/search',params = {'q':'{} - {} site:deezer.com'.format(title,artist)})
	else:
		resp  = session.get('https://www.google.com/search',params = {'q':'{} site:deezer.com'.format(title)})
	soup = BeautifulSoup(resp.text,'lxml')
	name_link = soup.find_all('h3', class_='LC20lb')
	link = soup.find_all('cite')
	for n_link, l in zip(name_link,link):
		print(f'{n_link.text}\n{l.text}')
		print('---------')
		if validator:
			if validator(l.text):
				return l.text
		elif 'album' in l.text:
			return l.text
	return None
if __name__ == "__main__":
	findSong("Ice cream cake"," Red velvet")
