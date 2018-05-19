import requests
from bs4 import BeautifulSoup, element
import time
import json
import pandas as pd

import pdb

from genius_db import *


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
    soup = BeautifulSoup(r.text, 'html5lib')

    # Assumption: all songs have this class
    header = soup.find('div', class_='header_with_cover_art')

    # Assumption: The first <h1> is the song title
    title = header.find('h1').text.strip()

    # TODO: There may be multiple artists
    # Assumption: The first <h2> is the artist
    artist_tag = header.find('h2')
    artist = artist_tag.text.strip()
    artist_url = artist_tag.a.get('href')

    # Assumption: All lyrics are in a <div class="lyrics">
    lyrics_tag = soup.find('div', class_='lyrics')

    lyrics = []
    bar = ''
    # Assumption: All lyrics are inside a <p>
    if lyrics_tag.p:
        # Do not create a new item in lyrics for italicized text:
        for tag in lyrics_tag.p.children:
            if type(tag) is element.NavigableString:
                bar += tag
            elif tag.name != 'br':
                bar += tag.get_text(strip=True)
            else:
                lyrics.append(bar.strip())
                bar = ''
    else:
        return None

    # lyrics = [lyric for lyric in lyrics_tag.stripped_strings]

    song = {
        'url': url,
        'title': title,
        'artist': artist,
        'artist_url': artist_url,
        'lyrics': json.dumps(lyrics)
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

    album = song.get('album')
    if album:
        album_id = album.get('id')
        album_title = album.get('name')
        album_artist_id = album.get('artist').get('id') if album.get('artist') else None
        album_href = album.get('url')
    else:
        album_id, album_title, album_artist_id, album_href = None, None, None, None

    prod_artists = song.get('producer_artists')
    if prod_artists:
        producers = [
            { 'producer_id': p.get('id'),
              'title': p.get('name'),
              'href': p.get('url')
             } for p in prod_artists]
    else:
        producers = None

    feat_artists = song.get('featured_artists')
    if feat_artists:
        featuring = [
            { 'artist_id': f.get('id'),
              'artist': f.get('name'),
              'href': f.get('url')
             } for f in feat_artists]
        featured_artist_ids = [x.get('id') for x in feat_artists]
    else:
        featuring, featured_artist_ids = None, None

    language = [x['value'] for x in song.get('tracking_data') if x['key'] == 'Lyrics Language'][0]
    lyrics_created_at = [x['value'] for x in song.get('tracking_data') if x['key'] == 'created_at'][0]

    data = {
        'album_id': album_id,
        'album_title': album_title,
        'album_artist_id': album_artist_id,
        'album_href': album_href,
        'produced_by': json.dumps(producers),
        'featuring': json.dumps(featuring),
        'release_date': song.get('release_date'),
        'published': song.get('published'),
        'recording_location': song.get('recording_location'),
        'title_with_featured': song.get('title_with_featured'),
        'lyrics_language': language,
        'lyrics_created_at': lyrics_created_at,
        'lyrics_updated_at': song.get('lyrics_updated_at'),
        'lyrics_state': song.get('lyrics_state'),
        'tags': json.dumps(get_song_tags(song)),
        'featured_artist_ids': json.dumps(featured_artist_ids)
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
        # next_page = ''
        for song in result['response']['songs']:
            lyric = scrape_song(song['url'])
            # If a song has no lyrics, skip it
            if not lyric:
                continue
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
# TODO: make sure this can handle temporary internet disconnects
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


def scrape_artist(id):
    engine = db_connect()
    songs = scrape_artist_songs(2197)


def scrape_album():
    pass


def to_df(songs):
    df = pd.DataFrame(songs)
    df = df.set_index('song_id')
    return df
# songs = api_artist_songs(2197)
# # titles = [s['title'] for s in songs]
# song_urls = [s['url'] for s in songs]
# lyrics = []
# for url in song_urls:
#     print('Scraping ' +  url)
#     lyrics.append(scrape_song(url))


def scrape_future():
    songs = scrape_artist_songs(2197)
    df = pd.DataFrame(songs)
    df = df.set_index('song_id')
    return df
    # engine = db_connect()
    # # TODO: How to handle pre-existing songs in the DB?
    # df.to_sql('songs_v3', engine, if_exists='append')
    # df.to_csv('data/future_sample.csv')
