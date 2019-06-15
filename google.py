import requests
from bs4 import BeautifulSoup
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
def findSong(title, artist='',validator = None):
	
	resp = None
	if artist is not None:
		resp  = gsession.get('https://www.google.com/search',params = {'q':'{} - {} site:deezer.com'.format(title,artist),'gl':'VN'})
	else:
		resp  = gsession.get('https://www.google.com/search',params = {'q':'{} site:deezer.com'.format(title),'gl':'VN'})
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
	resp = None
	if artist is not None:
		resp  = gsession.get('https://google.com.vn/search',params = {'q':'{} - {} site:deezer.com'.format(title,artist),'gl':'VN'})
	else:
		resp  = gsession.get('https://google.com.vn/search',params = {'q':'{} site:deezer.com'.format(title),'gl':'VN'})
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
	findSong("What is love")
