"""Tests unitaires pour le module Spotify."""

import unittest
from metaloscrap.spotify import SpotifyClient


class TestSpotifyClient(unittest.TestCase):

    def test_extract_album_id_standard_url(self):
        url = "https://open.spotify.com/album/4IClZdiTbhIIf4hxBoGph2"
        alb_id = SpotifyClient.extract_album_id_from_url(url)
        self.assertEqual(alb_id, "4IClZdiTbhIIf4hxBoGph2")

    def test_extract_album_id_international_url_with_query(self):
        url = "https://open.spotify.com/intl-fr/album/6QDdlwpiEGyhJnP2tIZw62?nd=1&dlsi=a3ccad8e943e4eb3"
        alb_id = SpotifyClient.extract_album_id_from_url(url)
        self.assertEqual(alb_id, "6QDdlwpiEGyhJnP2tIZw62")

    def test_extract_album_id_non_spotify_url(self):
        url = "https://thecrawlingband.bandcamp.com/album/what-we-leave-behind"
        alb_id = SpotifyClient.extract_album_id_from_url(url)
        self.assertIsNone(alb_id)

    def test_missing_credentials_raises_value_error(self):
        with self.assertRaises(ValueError):
            SpotifyClient(client_id="", client_secret="", refresh_token="")


if __name__ == "__main__":
    unittest.main()
