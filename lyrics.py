import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
USER_TOKEN = os.getenv('MXM_TOKEN')
def getlyricsTranslation(track_id):
	params = (
			('commontrack_id',str(track_id)),
			('usertoken', USER_TOKEN),	
			('selected_language','en'),
			('format', 'json'),
			('user_language', 'en'),
			('tags', 'nowplaying'),
			('namespace', 'track_translation'),
			('f_subtitle_length_max_deviation', '1'),
			('subtitle_format', 'mxm'),
			('app_id', 'web-desktop-app-v1.0'),
			('translation_fields_set','minimal'),
			
		)
	apiurl = 'https://apic.musixmatch.com/ws/1.1/crowd.track.translations.get'
	response = requests.get(apiurl,params = params)
	d = json.loads(response.text)
	return d['message']['body']['translations_list']
def getlyrics(track,album,artist,duration = None):
	params = [
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
	]
	if duration:
		params.append(('q_duration', duration))
		params.append(('f_subtitle_length', duration))
	result = {}
	result['error']=False
	try:
		response = requests.get('https://apic-desktop.musixmatch.com/ws/1.1/macro.subtitles.get', params=params, verify=False)
		d = json.loads(response.text)
		lyrics = d['message']['body']['macro_calls']['track.lyrics.get']['message']['body']['lyrics']['lyrics_body']
		#print(lyrics)
		trackid = d['message']['body']['macro_calls']['matcher.track.get']['message']['body']['track']['commontrack_id']
		result['txt'] = lyrics
		result['has_lrc'] = False
		try:
			synced_lyrics = d['message']['body']['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']['subtitle_body']
			sd = json.loads(synced_lyrics)
			result['lang'] = d['message']['body']['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']['subtitle_language']
			result['lrc']=sd
			result['has_lrc']=True
		except:
			pass
		finally:
			if result['lang'] == 'en':
				return result
			try:
				trans = getlyricsTranslation(trackid)
				trans_map = {}
				for tran in trans:
					tran = tran['translation']
					trans_map[tran['subtitle_matched_line']] = tran['description']
				translated = []
				for line in result['lrc']:
					try:
						line['en_text'] = trans_map[line['text']]
					except:
						line['en_text'] = ''
					finally:
						translated.append(line)
				result['lrc'] = translated
				result['has_trans'] = True
				return result
			except:
				return result
			finally:
				return result
	except:
		result['error']=True
		return result
		
if __name__ == "__main__":
	getlyrics("The best thing i ever did", "The year of YES", artist = "TWICE")
	getlyricsTranslation(90555411)

