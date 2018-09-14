import argparse
import json
import requests
import os
from glob import glob
import re
from pprint import pprint   # TODO: remove

CREDENTIALS_FILE = 'lightrenamer-credentials.json'
EPISODE_INDEX_PATTERN = '[Ss]?(\d?\d)[EeXx](\d\d)'

api = lambda path: 'https://api.thetvdb.com' + path
std_headers = {'Content-Type': 'application/json'}

def get_auth_jwt(apikey):

    def login(apikey):
        return requests.post(api('/login'),
                             headers={'Content-Type': 'application/json'},
                             json={'apikey': apikey}).json()['token']

    # read credentials
    if not os.path.isfile(CREDENTIALS_FILE):
        credentials = {}
    else:
        with open(CREDENTIALS_FILE, 'r') as f:
            credentials = json.load(f)

    # ensure we have an API key
    if apikey is None and not 'apikey' in credentials:
        raise ValueError('API key must be supplied with --apikey or stored in credentials file')

    # if api key is supplied as argument, use that
    if apikey is not None:
        credentials['apikey'] = apikey

    if not 'jwt' in credentials:
        credentials['jwt'] = login(apikey)

    # write updated credentials to file
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(credentials, f)

    return credentials['jwt'] 

def process_files(files):
    organized_files = {}

    for file_name in files:
        file = file_name
        file = file.replace('.', ' ').split()

        # get index of term that contains episode index
        episode_index_index = None
        for i, term in enumerate(file):
            if re.fullmatch(EPISODE_INDEX_PATTERN, term):
                episode_index_index = i
        if episode_index_index is None:
            raise ValueError(f'no valid season/episode index found in \'{file_name}\'')

        show_name = ' '.join(file[:episode_index_index])
        episode_index = file[episode_index_index]

        if not show_name in organized_files:
            organized_files[show_name] = {}
        organized_files[show_name][episode_index] = file_name

    return organized_files

def get_show_from_name(search_term):
    return requests.get(api('/search/series'),
                        headers=std_headers,
                        params={'name': search_term}).json()['data'][0]

def get_episodes(show_id):
    episodes = requests.get(api(f'/series/{show_id}/episodes'),
                            headers=std_headers,
                            params={'id': show_id}).json()

    total_pages = episodes['links']['last']

    data = episodes['data']

    for i in range(total_pages):
        episodes = requests.get(api(f'/series/{show_id}/episodes'),
                                headers=std_headers,
                                params={'id': show_id, 'page': i + 1}).json()

        data += episodes['data']

    return data

def get_episode_by_index(episodes, season_no, episode_no, aired_order=False):
    ordering_type = 'aired' if aired_order else 'dvd'
    season_key = ordering_type + 'Season'
    episode_key = ordering_type + 'EpisodeNumber'

    return next(episode for episode in episodes if episode[season_key] == season_no and episode[episode_key] == episode_no)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apikey', help='thetvdb api token (only needed the first time)')
    parser.add_argument('pattern', nargs='?', help='regexp to match files to rename')
    args = parser.parse_args()

    std_headers['Authorization'] = f'Bearer {get_auth_jwt(args.apikey)}'

    files = glob('*' + args.pattern + '*') if args.pattern else []

    sorted_files = process_files(files)

    rename_tasks = []
    for show_name, episodes in sorted_files.items():
        show = get_show_from_name(show_name)
        show_id = show['id']
        clean_show_name = show['seriesName']

        show_episodes = get_episodes(show_id)

        for episode_index, file_name in episodes.items():
            match = re.match(EPISODE_INDEX_PATTERN, episode_index)
            season, episode = int(match.group(1)), int(match.group(2))
            print(season, episode)

            episode_data = get_episode_by_index(show_episodes, season, episode)
            filename = f'{clean_show_name} S{str(season).zfill(2)}E{str(episode).zfill(2)} - {episode_data["episodeName"]}'
            print(filename)

