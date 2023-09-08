import time

import click
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@click.group()
def nts():
    pass


def standardize(artist, track):
    # TODO: Standardize artist and track names
    return artist, track


def get_all_tracks_on_page(driver, url, artist=None, span_selector='search-result-play_track_artist',
                           artist_selector='search-result-play__track__artist',
                           track_selector='search-result-play__track__title'):
    # Find all html elements like this
    # <div><span class="search-result-play__track__artist text-bold text-uppercase">EarthGang, Young Thug feat. Young Thug</span><br class="visible-phone"><span class="search-result-play__track__title nts-font-secondary">Young Thug (2)</span></div>
    # and extract the track and artist names
    # artist: EarthGang, Young Thug
    # track: Young Thug (2)
    # Return string with all tracks and artists like so:
    # EarthGang, Young Thug - Young Thug (2)
    # ...
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, span_selector)))
    artists_and_tracks = set()
    # Iterate through all divs with class search-result-play__track as child
    for element in driver.find_elements(By.CLASS_NAME, span_selector):
        # Append artist and track to list
        track_artist = element.find_element(By.CLASS_NAME, artist_selector).text.lower()
        track = element.find_element(By.CLASS_NAME, track_selector).text.lower()
        # Strip artist and track, standardize feature formatting, and append to list
        track_artist, track = standardize(track_artist, track)
        # Skip if the artist is not the one we are looking for and is not featured on the song
        if artist and not artist in track_artist and 'feat.' not in artist and not (
                'feat.' in track and artist in track):  # TODO: improve filtering
            continue

        artists_and_tracks.add((track_artist, track))
    return artists_and_tracks


@nts.command()
@click.option('--artist', '-a', help='Artist name')
def get_artist(artist):
    """Get artist info"""
    click.echo('Getting all songs by artist {}'.format(artist))
    artist = artist.lower()
    # Format url like https://www.nts.live/find?q=young%20thug&type=track
    url = 'https://www.nts.live/find?q={}&type=track'.format(artist.replace(' ', '%20'))
    click.echo('URL: {}'.format(url))
    # Get page
    driver = webdriver.Chrome()

    artists_and_tracks = get_all_tracks_on_page(driver, url, artist)
    artists_and_tracks_strings = ['{} - {}'.format(artist, track) for artist, track in artists_and_tracks]
    artists_and_tracks_string = '\n'.join(artists_and_tracks_strings)
    click.echo('Artists and tracks:\n\n{}'.format(artists_and_tracks_string))

    pyperclip.copy(artists_and_tracks_string)

    return artists_and_tracks_string


@nts.command()
@click.option('--url', '-u', help='URL of episode (e.g. https://www.nts.live/shows/umru/episodes/umru-19th-july-2023)')
def get_episode(url):
    driver = webdriver.Chrome()
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'track__detail')))

    # <div><a class="nts-app nts-link" href="/artists/37665-dj-jayhood" data-track="event" data-category="Navigation" data-target="GoTo-Artist" data-origin="from: tracklist"><span class="track__artist">DJ Jayhood</span></a><span class="track__artist track__artist--mobile" style="display: none;">DJ Jayhood</span>&nbsp;<img src="/img/go-to.svg" alt="" style="height: 0.75em; width: 0.75em; position: relative; top: -0.1em; margin-left: 1px;"><br><span class="track__title">Ass On The Floor</span></div>
    artists_and_tracks = get_all_tracks_on_page(driver, url, artist=None, span_selector='track__detail',
                                                artist_selector='track__artist', track_selector='track__title')
    artists_and_tracks_strings = ['{} - {}'.format(artist, track) for artist, track in artists_and_tracks]
    artists_and_tracks_string = '\n'.join(artists_and_tracks_strings)
    click.echo('Artists and tracks:\n\n{}'.format(artists_and_tracks_string))

    pyperclip.copy(artists_and_tracks_string)

    return artists_and_tracks_string

@nts.command()
@click.option('--url', '-u', help='URL')
def get_show(url):
    # Wait until tracklist elements show up. For each one, open link in new url, then run get_all_tracks_on_page on it
    # Example element:
    #  <a class="nts-grid-v2-item__extra nts-app nts-link" href="/shows/umru/episodes/umru-19th-july-2023" data-track="event" data-origin="showTracklistLink" data-target="/shows/umru/episodes/umru-19th-july-2023">Tracklist</a>
    driver = webdriver.Chrome()
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'nts-grid-v2-item__extra')))
    page_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for some time to allow content to load (you can adjust this)
        time.sleep(2)

        # Get the new page height after scrolling
        new_page_height = driver.execute_script("return document.body.scrollHeight")

        # Check if the page height has remained the same (no more content to load)
        if new_page_height == page_height:
            break

        # Update the page height
        page_height = new_page_height

    artist_and_tracks_set = set()
    episodes = [episode.get_attribute('href') for episode in driver.find_elements(By.CLASS_NAME, 'nts-grid-v2-item__extra')]
    for url in episodes:
        artist_and_tracks_set.update(get_all_tracks_on_page(driver, url, artist=None, span_selector='track__detail', artist_selector='track__artist', track_selector='track__title'))

    artists_and_tracks_strings = ['{} - {}'.format(artist, track) for artist, track in artist_and_tracks_set]
    artists_and_tracks_string = '\n'.join(artists_and_tracks_strings)

    click.echo('Artists and tracks:\n\n{}'.format(artists_and_tracks_string))

    pyperclip.copy(artists_and_tracks_string)

    return artists_and_tracks_string




if __name__ == '__main__':
    nts()
