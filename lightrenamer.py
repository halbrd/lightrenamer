#!/usr/bin/env python3

# TODO: clean up code
# TODO: explicitly specify show id
# TODO: explicitly specify episode index format
# TODO: explicitly specify output file name format
# TODO: save api key in common location (XDG_CONFIG_HOME or %APPDATA%)
# TODO: match everything when pattern parameter isn't provided

import argparse
import json
import requests
import os
from glob import glob
import re
from pathlib import Path

CREDENTIALS_FILE = os.getenv('XDG_CONFIG_HOME', os.environ['HOME'] + '/.config') + '/lightrenamer/credentials.json'
CREDENTIALS_FILE = Path(CREDENTIALS_FILE)
EPISODE_INDEX_PATTERN = '[Ss]?(\d?\d)[EeXx](\d\d)'

api = lambda path: 'https://api.thetvdb.com' + path
std_headers = {'Content-Type': 'application/json'}

def get_auth_jwt(apikey):

    def login(apikey):
        return requests.post(api('/login'),
                             headers={'Content-Type': 'application/json'},
                             json={'apikey': apikey}).json()['token']

    # read credentials
    if not CREDENTIALS_FILE.is_file():
        credentials = {}
    else:
        with CREDENTIALS_FILE.open('r') as f:
            credentials = json.load(f)

    # ensure we have an API key
    if apikey is None and not 'apikey' in credentials:
        raise ValueError('API key must be supplied with --apikey or stored in credentials file')

    # if api key is supplied as argument, use that
    if apikey is not None:
        credentials['apikey'] = apikey

        CREDENTIALS_FILE.parents[0].mkdir(parents=True, exist_ok=True)
        with CREDENTIALS_FILE.open('w') as f:
            json.dump(credentials, f)

    return login(credentials['apikey'])

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

    try:
        return next(episode for episode in episodes if episode[season_key] == int(season_no) and episode[episode_key] == int(episode_no))
    except StopIteration:
        raise ValueError(f'one or more episodes don\'t have DVD ordering; try using --aired-order')

def clean_string(string, replacement='', colon_replacement='-'):
	illegals = '<>:"/\\|?*'
	return ''.join(c for c in string.replace(':', colon_replacement) if c not in illegals)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apikey', help='thetvdb api token (only needed the first time)')
    parser.add_argument('--aired-order', action='store_true', help='use the aired order of episodes instead of the dvd order')
    parser.add_argument('pattern', nargs='?', help='regexp to match files to rename')
    args = parser.parse_args()

    std_headers['Authorization'] = f'Bearer {get_auth_jwt(args.apikey)}'

    files = glob('*' + args.pattern + '*') if args.pattern else []

    sorted_files = process_files(files)

    rename_tasks = []
    for show_name in sorted(sorted_files.keys()):
        episodes = sorted_files[show_name]

        show = get_show_from_name(show_name)
        show_id = show['id']
        clean_show_name = clean_string(show['seriesName'])

        show_episodes = get_episodes(show_id)

        for episode_index in sorted(episodes.keys()):
            file_name = episodes[episode_index]

            extension = file_name.split('.')[-1]
            match = re.match(EPISODE_INDEX_PATTERN, episode_index)
            season, episode = int(match.group(1)), int(match.group(2))

            episode_data = get_episode_by_index(show_episodes, season, episode, args.aired_order)
            clean_episode_name = clean_string(episode_data["episodeName"])
            result_filename = f'{clean_show_name} S{str(season).zfill(2)}E{str(episode).zfill(2)} - {clean_episode_name}.{extension}'
            result_filename = result_filename.replace(':', '-').replace('/',  '-')

            rename_tasks.append((file_name, result_filename))

    rename_tasks = list(filter(lambda task: task[0] != task[1], rename_tasks))

    for original, new in rename_tasks:
        print('Old: ' + original)
        print('New: ' + new)
        print()

    if input('Continue? (y/n) ').lower() == 'y':
        for original, new in rename_tasks:
            os.rename(original, new)
