import requests
from bs4 import BeautifulSoup
import time
import json
import pandas as pd


# Scrape song
def scrape_song(url):
    """
        Scrapes lyrics and some metadata from a Rap Genius lyrics page.

        Args:
            url (str): The URL of the page to scrape.

        Returns:
            dict representing a song object.
    """
    print('Scraping ' + url)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    # Assumption: all songs have this class
    header = soup.find('div', class_='header_with_cover_art')

    # Assumption: The first <h1> is the song title
    title = header.find('h1').text.strip()

    # TODO: There may be multiple artists
    # Assumption: The first <h2> is the artist
    artist_tag = header.find('h2')
    artist = artist_tag.text.strip()
    artist_url = artist_tag.a.get('href')

    # Assumption: All metadata is in divs with class="metadata_unit-*"
    # Assumption: All metadata info is contained in <a>
    metadata = []
    for md in header.find_all('div', class_='metadata_unit'):
        label = md.find('span', class_='metadata_unit-label')
        item = {}
        item[label.text] = []
        # print(label.text)
        info = md.find('span', class_='metadata_unit-info')
        for a in info.find_all('a'):
            # print(a.text.strip())
            # print(a.get('href'))
            item[label.text].append({
                'text': a.text.strip(),
                'href': a.get('href')
            })
        metadata.append(item)

    # Assumption: All lyrics are in a <div class="lyrics">
    lyrics_tag = soup.find('div', class_='lyrics')
    lyrics = [lyric for lyric in lyrics_tag.stripped_strings]

    song = {
        'url': url,
        'title': title,
        'artist': artist,
        'artist_url': artist_url,
        'metadata': metadata,
        'lyrics': lyrics
    }

    return song


def get_release_date(song_id):
    """
        Given a Genius song ID, returns the release date.

        Args:
            song_id (int or str): The song ID.
        Returns:
            The YYYY-MM-DD date as a str.
    """
    url = "https://genius.com/api/songs/{0}".format(song_id)
    r = requests.get(url)
    result = r.json()
    return result.get('response').get('song').get('release_date')


def get_song_tags(song):
    """
        Given a song object from https://genius.com/api/songs/, returns the tags.
        First attempts to get tags from the `tags` key, and if None, uses `tracking_data`.

        Args:
            song (dict): The `song` attribute from https://genius.com/api/songs/{id}.
        Returns:
            A list of tags.
    """
    if song.get('tags'):
        tags = [x['name'] for x in song.get('tags')]
    else:
        tags = [x['value'] for x in song.get('tracking_data') if x['key'] == 'Tag']
    return tags


def enrich_song_data(song_id):
    """
        Fetches additional data from the Genius API.

        Args:
            song_id (int or str): The Genius ID of the song.
        Returns:
            A dict of additional song data.
    """
    print('Fetching additional data...')
    url = "https://genius.com/api/songs/{0}".format(song_id)
    r = requests.get(url)
    # result = r.json()
    song = r.json().get('response').get('song')
    # tags = [x['value'] for x in song.get('tracking_data') if x['key'] == 'Tag']

    language = [x['value'] for x in song.get('tracking_data') if x['key'] == 'Lyrics Language'][0]
    featured_artist_ids = [x['id'] for x in song.get('featured_artists')]
    data = {
        'release_date': song.get('release_date'),
        'published': song.get('published'),
        'recording_location': song.get('recording_location'),
        'lyrics_language': language,
        'tags': get_song_tags(song),
        'featured_artist_ids': featured_artist_ids
    }

    return data


def scrape_artist_songs(artist_id):
    """
        Grabs all of an artist's songs from the Genius API, scrapes each song
        page for lyrics, then further enriches the scraped data with additonal
        information from the API.

        Args:
            artist_id (str or int): The Genius artist ID.
        Returns:
            A list of dicts of song data for all songs by the artist.
    """
    songs = []
    next_page = 1
    while isinstance(next_page, int):
        print('*******************')
        print("Downloading page {0}".format(next_page))
        print('*******************')
        url = "https://genius.com/api/artists/{0}/songs?page={1}&sort=title".format(artist_id, next_page)
        r = requests.get(url)
        result = r.json()
        next_page = result['response']['next_page']

        for song in result['response']['songs']:
            lyric = scrape_song(song['url'])
            # Get release date
            # song_id = song['api_path'].replace('/songs/', '')
            # song_id = song['id']
            primary_artist_id = song.get('primary_artist').get('id')

            lyric['song_id'] = song['id']
            lyric['primary_artist_id'] = primary_artist_id
            # lyric['release_date'] = get_release_date(song_id)
            extra_data = enrich_song_data(song['id'])
            lyric = {**lyric, **extra_data}

            songs.append(lyric)
        # time.sleep(1)
    return songs


# Rick Ross: 88
# Future: 2197
def api_artist_songs(artist_id):
    songs = []
    next_page = 1
    while isinstance(next_page, int):
        print("Downloading page {0}".format(next_page))
        url = "https://genius.com/api/artists/{0}/songs?page={1}&sort=title".format(artist_id, next_page)
        r = requests.get(url)
        # result = json.loads(page.text)
        result = r.json()
        next_page = result['response']['next_page']
        songs.extend(result['response']['songs'])
        time.sleep(1)
    return songs


def scrape_artist(url):
    pass


def scrape_album():
    pass


# songs = api_artist_songs(2197)
# # titles = [s['title'] for s in songs]
# song_urls = [s['url'] for s in songs]
# lyrics = []
# for url in song_urls:
#     print('Scraping ' +  url)
#     lyrics.append(scrape_song(url))

songs = scrape_artist_songs(2197)

df = pd.DataFrame(songs)
df.to_csv('future.csv')
