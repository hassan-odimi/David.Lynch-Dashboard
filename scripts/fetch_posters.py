"""Find each film's TMDB poster path and save them to site/data/posters.json.

Run it yourself with your own TMDB API key; the key is never written anywhere:
    TMDB_API_KEY=... python scripts/fetch_posters.py
The site loads the posters from TMDB's image server and credits TMDB on the Films tab.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# IMDb ids match FILMS in site/app.js. Ronnie Rocket was never made, so it has no poster.
IMDB_IDS = ['tt0074486', 'tt0080678', 'tt0087182', 'tt0090756', 'tt0098936', 'tt0100935', 'tt0105665',
            'tt0116922', 'tt0166896', 'tt0166924', 'tt0460829', 'tt4093826']
# TMDB files Twin Peaks: The Return as season 3 of Twin Peaks, so it borrows that season's poster.
SEASONS = {'tt4093826': ('tt0098936', 3)}
OUT = Path(__file__).resolve().parent.parent / 'site' / 'data' / 'posters.json'


def get(path, key, **params):
    query = urllib.parse.urlencode({'api_key': key, **params})
    with urllib.request.urlopen(f'https://api.themoviedb.org/3/{path}?{query}', timeout=20) as response:
        return json.load(response)


def poster_path(imdb_id, key):
    if imdb_id in SEASONS:
        series, season = SEASONS[imdb_id]
        show = get(f'find/{series}', key, external_source='imdb_id')['tv_results'][0]['id']
        return get(f'tv/{show}/season/{season}', key).get('poster_path')
    found = get(f'find/{imdb_id}', key, external_source='imdb_id')
    for result in found.get('movie_results', []) + found.get('tv_results', []):
        if result.get('poster_path'):
            return result['poster_path']
    return None


def main():
    key = os.environ.get('TMDB_API_KEY')
    if not key:
        sys.exit('Set TMDB_API_KEY first.')
    posters = {}
    for imdb_id in IMDB_IDS:
        path = poster_path(imdb_id, key)
        if path:
            posters[imdb_id] = path
        print(imdb_id, path or 'no poster')
    OUT.write_text(json.dumps(posters, indent=2) + '\n')
    print(f'{len(posters)} posters saved to {OUT}')


if __name__ == '__main__':
    main()
