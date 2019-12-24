import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
USER_TOKEN = os.getenv('MXM_TOKEN')
def getlyrics(track,album,artist,duration = None,albumartist = None):
	if albumartist is None:
		albumartist = artist
	params = [
		('format', 'json'),
		('q_track', track),
		('q_artists', artist),
		('q_artist', albumartist),
		('q_album', album),
		('user_language', 'en'),
		('tags', 'playing'),
		('namespace', 'lyrics_synched'),
		('f_subtitle_length_max_deviation', '1'),
		('subtitle_format', 'mxm'),
		('app_id', 'mac-ios-v2.0'),
		('part','lyrics_crowd,subtitle_translated,lyrics_translated'),
		('selected_language','en'),
		('usertoken', USER_TOKEN),	
	]
	if duration:
		params.append(('q_duration', duration))
		params.append(('f_subtitle_length', duration))
	result = {}
	result['error']=False
	try:
		response = requests.get('https://apic.musixmatch.com/ws/1.1/macro.subtitles.get', params=params, verify=False)
		#print(response.text)
		d = json.loads(response.text)
		result['txt'] = ''
		result['has_lrc'] = False
		try:
			result['txt'] = lyrics = d['message']['body']['macro_calls']['track.lyrics.get']['message']['body']['lyrics']['lyrics_body']
		except:
			pass
		try:
			result['lang'] = d['message']['body']['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']['subtitle_language']
			synced_lyrics = d['message']['body']['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']['subtitle_body']
			sd = json.loads(synced_lyrics)
			result['lrc']=sd
			result['has_lrc']=True
		except:
			result['lang'] = ''
			pass
		finally:
			if result['lang'] == 'en':
				return result
			try:
				subtitle_translated = json.loads(d['message']['body']['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']['subtitle_translated']['subtitle_body'])
				translated = []
				for line in subtitle_translated:
					try:
						line['en_text'] = line['text']				
					except:
						line['en_text'] = ''
					finally:
						line['text'] = line['original']	
						translated.append(line)
				result['lrc'] = translated
				result['has_lrc']=True
				result['has_trans'] = True
				return result
			except Exception as e:
				print(e)
				return result
			finally:
				return result
	except:
		result['error']=True
		return result
		
if __name__ == "__main__":
	result = getlyrics("Just the Way You Are", "Doo-Wops & Hooligans", artist = "Bruno Mars",duration=3*60+40)
	print(result)

