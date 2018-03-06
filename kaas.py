#!/usr/bin/env python3

import requests

import functools
import logging
import os
import sys


class Kaas:
    """A Kodi Artist Artwork Scraper."""

    API_KEY = 1
    ARTWORK_FILE = 'artist.jpg'

    def __init__(self, library_root):
        self._root_dir = library_root
        self._http = requests.Session()
        self._logger = self._configure_logging(logging.INFO)
        self._artist_dir = functools.partial(os.path.join, self._root_dir)
        self._api_search = 'http://www.theaudiodb.com/api/v1/json/{}/search.php'.format(
            Kaas.API_KEY,
        )

    def _configure_logging(self, level):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
        )

        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(level)
        logger.addHandler(handler)

        return logger

    def scrape(self):
        artists = [
            node for node in os.listdir(self._root_dir)
            if os.path.isdir(self._artist_dir(node))
        ]

        for artist in artists:
            if Kaas.ARTWORK_FILE in os.listdir(self._artist_dir(artist)):
                self._logger.info(
                    '\'%s\' already has artwork: skipping.',
                    artist
                )
                continue

            self._logger.info('Searching \'%s\'', artist)
            matches = self._http.get(
                self._api_search,
                params={'s': artist}
            ).json()['artists']

            if not matches:
                self._logger.warn('No match for \'%s\': skipping.', artist)
                continue
            elif len(matches) != 1:
                self._logger.warn(
                    '%d matches for \'%s\': skipping.',
                    len(matches),
                    artist
                )
                continue
            elif not matches[0]['strArtistThumb']:
                self._logger.warn('No artwork for \'%s\': skipping.', artist)
                continue
            else:
                self._logger.debug(' Fetching %s', matches[0]['strArtistThumb'])
                image_data = self._http.get(
                    matches[0]['strArtistThumb']
                ).content

                image_file = self._artist_dir(artist, Kaas.ARTWORK_FILE)
                self._logger.debug(' Writing %s', image_file)
                with open(image_file, 'wb') as f:
                    f.write(image_data)


if __name__ == '__main__':
    kaas = Kaas(sys.argv[1])
    kaas.scrape()
