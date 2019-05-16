import requests
from bs4 import BeautifulSoup
def findSong(title, artist=''):
	resp  = requests.get('https://google.com/search',params = {'q':'{} - {} site:deezer.com/track'.format(title,artist)})
	soup = BeautifulSoup(resp.text,'lxml')
	name_link = soup.find_all('h3', class_='r')
	link = soup.find_all('cite')
	for n_link, l in zip(name_link,link):
		print(f'{n_link.text}\n{l.text}')
		print('---------')
		return l.text
	return None

if __name__ == "__main__":
	findSong("Ice cream cake"," Red velvet")
