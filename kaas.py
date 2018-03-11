#!/usr/bin/env python3

"""
Scrape artist artwork from TheAudioDB
for Kodi to display with your music library.
"""

import argparse
import functools
import logging
import os

import requests


PROJECT_NAME = os.path.basename(os.path.dirname(os.path.abspath(__file__)))


class ScrapingError(Exception):
    """Encapsulate all semantic problems when fetching artwork."""
    pass


class KodiArtistArtworkScraper:
    """A Kodi Artist Artwork Scraper."""

    def __init__(self, library_root, api_key, artwork_file):
        self._library_dir = library_root
        self._artist_dir = functools.partial(os.path.join, library_root)
        self._artwork_file = artwork_file

        self._http = requests.Session()
        self._api_search = 'http://www.theaudiodb.com/api/v1/json/{}' \
                           '/search.php'.format(api_key)

    def scrape(self):
        """Find and download artist artwork."""
        artists = self._collect_artists()
        for artist in artists:
            try:
                image = self._fetch_artwork(artist)
            except ScrapingError as problem:
                logging.warning('%s: skipping.', problem)
            except requests.exceptions.RequestException as error:
                logging.error('%s: skipping.', error)
            else:
                self._save_image(artist, image)

    def _collect_artists(self):
        artist_dirs = [
            node for node in os.listdir(self._library_dir)
            if os.path.isdir(self._artist_dir(node))
            and not node.startswith('.')
        ]
        logging.debug(
            'Identified %d artists: %s',
            len(artist_dirs),
            artist_dirs
        )

        no_artwork = [
            artist for artist in artist_dirs
            if self._artwork_file not in os.listdir(self._artist_dir(artist))
        ]
        logging.info(
            'Skipping %d artists that already have artwork',
            len(artist_dirs)-len(no_artwork)
        )

        return no_artwork

    def _fetch_artwork(self, artist):
        logging.info('Looking up \'%s\'', artist)
        response = self._http.get(
            self._api_search,
            params={'s': artist},
        )
        response.raise_for_status()
        matches = response.json()['artists']

        if not matches:
            raise ScrapingError('No match for \'{}\''.format(artist))
        elif len(matches) != 1:
            raise ScrapingError(
                '{} matches for \'{}\''.format(len(matches), artist)
            )
        elif not matches[0]['strArtistThumb']:
            raise ScrapingError('No artwork for \'{}\''.format(artist))
        else:
            logging.debug(' Fetching %s', matches[0]['strArtistThumb'])
            return self._http.get(matches[0]['strArtistThumb']).content

    def _save_image(self, artist, data):
        image_file = self._artist_dir(artist, self._artwork_file)
        logging.debug(' Writing %s', image_file)

        with open(image_file, 'wb') as file:
            file.write(data)


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        'library_root',
        help='the directory containing your artist folders'
    )
    parser.add_argument(
        '--api-key',
        '-k',
        default='1',
        metavar='KEY',
        help='the key to use when accessing TheAudioDB\'s API'
             ' (default: %(default)s)')
    parser.add_argument(
        '--artwork-file',
        '-f',
        default='artist.jpg',
        metavar='IMG',
        help='the file name to save downloaded artwork under'
             ' (default: %(default)s)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        dest='verbosity',
        action='count',
        default=0,
        help='increase the log level with each use'
    )

    return parser.parse_args()


def _main():
    args = _parse_args()

    logging.basicConfig(
        level=max(logging.DEBUG, logging.WARNING - args.verbosity * 10),
        format='%(asctime)s:%(name)s:%(levelname)s:%(message)s',
    )
    logging.root.name = PROJECT_NAME

    KodiArtistArtworkScraper(
        args.library_root,
        args.api_key,
        args.artwork_file
    ).scrape()


if __name__ == '__main__':
    _main()
