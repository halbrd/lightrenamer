import argparse
import json
import requests
import os
from glob import glob
import re

CREDENTIALS_FILE = 'lightrenamer-credentials.json'

api = lambda path: 'https://api.thetvdb.com/' + path
std_headers = {'Content-Type': 'application/json'}

def get_auth_jwt(args):

    def login(apikey):
        return json.loads(requests.post(api('login'),
                        headers={'Content-Type': 'application/json'},
                        json={'apikey': apikey}).text)['token']

    # read credentials
    if not os.path.isfile(CREDENTIALS_FILE):
        credentials = {}
    else:
        with open(CREDENTIALS_FILE, 'r') as f:
            credentials = json.load(f)

    # ensure we have an API key
    if args.apikey is None and not 'apikey' in credentials:
        raise ValueError('API key must be supplied with --apikey or stored in credentials file')

    # if api key is supplied as argument, use that
    if 'apikey' in args:
        credentials['apikey'] = args.apikey

    if not 'jwt' in credentials:
        credentials['jwt'] = login(args.apikey)

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
            if re.fullmatch('[Ss]?\d?\d[Eex]\d\d', term):
                episode_index_index = i
        if episode_index_index is None:
            raise ValueError('no valid season/episode index found')

        show_name = ' '.join(file[:episode_index_index])
        episode_index = file[episode_index_index]

        if not show_name in organized_files:
            organized_files[show_name] = {}
        organized_files[show_name][episode_index] = file_name

    return organized_files



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apikey', help='thetvdb api token (only needed the first time)')
    parser.add_argument('pattern', help='regexp to match files to rename')
    args = parser.parse_args()

    std_headers['jwt'] = get_auth_jwt(args)

    files = glob('*' + args.pattern + '*')

    print(process_files(files))
