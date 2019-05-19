import requests
from bs4 import BeautifulSoup
def findSong(title, artist='',validator = None):
	resp  = requests.get('https://google.com/search',params = {'q':'{} - {} site:deezer.com/track'.format(title,artist)})
	soup = BeautifulSoup(resp.text,'lxml')
	name_link = soup.find_all('h3', class_='r')
	link = soup.find_all('cite')
	for n_link, l in zip(name_link,link):
		print(f'{n_link.text}\n{l.text}')
		print('---------')
		if validator:
			if validator(l.text):
				return l.text
		else:
			return l.text
	return None
def findAlbum(title, artist='',validator = None):
	resp  = requests.get('https://google.com/search',params = {'q':'{} - {} site:deezer.com/album'.format(title,artist)})
	soup = BeautifulSoup(resp.text,'lxml')
	name_link = soup.find_all('h3', class_='r')
	link = soup.find_all('cite')
	for n_link, l in zip(name_link,link):
		print(f'{n_link.text}\n{l.text}')
		print('---------')
		if validator:
			if validator(l.text):
				return l.text
		else:
			return l.text
	return None
if __name__ == "__main__":
	findSong("Ice cream cake"," Red velvet")
