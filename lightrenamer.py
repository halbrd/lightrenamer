import argparse
import json
import requests
import os

api = lambda path: 'https://api.thetvdb.com/' + path

CREDENTIALS_FILE = 'lightrenamer-credentials.json'

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



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apikey', help='thetvdb api token (only needed the first time)')
    args = parser.parse_args()

    jwt = get_auth_jwt(args)
    print(jwt)


