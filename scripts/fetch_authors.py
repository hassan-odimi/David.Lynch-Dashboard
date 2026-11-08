"""Find a freely licensed Wikipedia photo of each frequent author and save it to site/data/authors.json.

No key is needed:
    python3 scripts/fetch_authors.py
Only free images (pilicense=free) are used. The photographer and licence come from Wikimedia Commons,
and the Books tab credits them under each photo.
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Authors with two or more books in site/data/books.json, mapped to their English Wikipedia page.
# Fondation Cartier is an institution, so it gets no photo.
PAGES = {
    'Barry Gifford': 'Barry Gifford',
    'Werner Spies': 'Werner Spies',
    'Charles Bukowski': 'Charles Bukowski',
    'Dennis Hopper': 'Dennis Hopper',
    'Isabella Rossellini': 'Isabella Rossellini',
    'Raymond Chandler': 'Raymond Chandler',
    'Peter Ettedgui': 'Peter Ettedgui',
    'Duginske': 'Mark Duginske',
}
OUT = Path(__file__).resolve().parent.parent / 'site' / 'data' / 'authors.json'
AGENT = {'User-Agent': 'lynch-collection-site/1.0 (static study site; author photo lookup)'}


def get(host, **params):
    query = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'formatversion': 2, **params})
    request = urllib.request.Request(f'https://{host}/w/api.php?{query}', headers=AGENT)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            time.sleep(int(error.headers.get('Retry-After') or 30))


def plain(html):
    return re.sub(r'<[^>]+>', '', html or '').strip()


def main():
    # Two batched requests: page images from Wikipedia, then credits from Commons.
    found = get('en.wikipedia.org', titles='|'.join(PAGES.values()), prop='pageimages', piprop='thumbnail|name',
                pithumbsize=400, pilicense='free', redirects=1)['query']
    renamed = {item['from']: item['to'] for item in found.get('redirects', []) + found.get('normalized', [])}
    pages = {page['title']: page for page in found['pages'] if 'thumbnail' in page}
    files = ['File:' + page['pageimage'] for page in pages.values()]
    credits = {}
    if files:
        for info in get('commons.wikimedia.org', titles='|'.join(files), prop='imageinfo', iiprop='extmetadata')['query']['pages']:
            credits[info['title']] = info.get('imageinfo', [{}])[0].get('extmetadata', {})
    authors = {}
    for author, title in PAGES.items():
        page = pages.get(renamed.get(title, title))
        if not page:
            print(author, 'no free photo')
            continue
        name = 'File:' + page['pageimage'].replace('_', ' ')
        meta = credits.get(name, {})
        authors[author] = {
            'src': page['thumbnail']['source'].split('?')[0],
            'page': 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(page['title'].replace(' ', '_')),
            'file': 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(name.replace(' ', '_')),
            'artist': plain(meta.get('Artist', {}).get('value')) or 'Unknown photographer',
            'licence': plain(meta.get('LicenseShortName', {}).get('value')) or 'see file page',
        }
        print(author, authors[author]['licence'])
    OUT.write_text(json.dumps(authors, indent=2, ensure_ascii=False) + '\n')
    print(f'{len(authors)} photos saved to {OUT}')


if __name__ == '__main__':
    main()
