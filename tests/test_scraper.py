"""Tests unitaires pour le module scraper."""

import unittest
from lxml import html
from metaloscrap.scraper import parse_release_line, Release


class TestScraper(unittest.TestCase):

    def test_parse_release_with_country_and_listen_link(self):
        html_str = (
            '<p>- <a class="groupe" href="https://www.metalorgie.com/groupe/Amon-Amarth">Amon Amarth</a> '
            '- The Allfather Awakens (Death Melo, Suède) '
            '<a href="https://www.metalorgie.com/sortie/10519/amon-amarth-the-allfather-awakens"><span>🎧</span></a></p>'
        )
        p = html.fromstring(html_str)
        release = parse_release_line(p)

        self.assertIsNotNone(release)
        self.assertEqual(release.artist, "Amon Amarth")
        self.assertEqual(release.album, "The Allfather Awakens")
        self.assertEqual(release.genres, ["Death Melo"])
        self.assertEqual(release.country, "Suède")
        self.assertEqual(
            release.listen_url,
            "https://www.metalorgie.com/sortie/10519/amon-amarth-the-allfather-awakens"
        )

    def test_parse_release_multiple_genres_and_us(self):
        html_str = (
            '<p>- Dééfait - Dééfait (Noise Rock / Psyche, France) '
            '<a href="https://www.metalorgie.com/sortie/10534/deefait-deefait"><span>🎧</span></a></p>'
        )
        p = html.fromstring(html_str)
        release = parse_release_line(p)

        self.assertIsNotNone(release)
        self.assertEqual(release.artist, "Dééfait")
        self.assertEqual(release.album, "Dééfait")
        self.assertEqual(release.genres, ["Noise Rock", "Psyche"])
        self.assertEqual(release.country, "France")

    def test_parse_release_without_country(self):
        html_str = (
            '<p>- Enterré Vivant - Kurogoku (Black Metal) '
            '<a href="https://www.metalorgie.com/sortie/10544/enterre-vivant-kurogoku"><span>🎧</span></a></p>'
        )
        p = html.fromstring(html_str)
        release = parse_release_line(p)

        self.assertIsNotNone(release)
        self.assertEqual(release.artist, "Enterré Vivant")
        self.assertEqual(release.album, "Kurogoku")
        self.assertEqual(release.genres, ["Black Metal"])
        self.assertIsNone(release.country)

    def test_parse_release_direct_spotify_link(self):
        html_str = (
            '<p>- Calus - The Evolution Of Social Exclusion (Stoner / Sludge, US) '
            '<a href="https://open.spotify.com/album/6QDdlwpiEGyhJnP2tIZw62"><span>🎧</span></a></p>'
        )
        p = html.fromstring(html_str)
        release = parse_release_line(p)

        self.assertIsNotNone(release)
        self.assertEqual(release.artist, "Calus")
        self.assertEqual(release.genres, ["Stoner", "Sludge"])
        self.assertEqual(release.listen_url, "https://open.spotify.com/album/6QDdlwpiEGyhJnP2tIZw62")

    def test_ignore_separator_lines(self):
        p1 = html.fromstring("<p>----</p>")
        p2 = html.fromstring("<p>Vous écoutez quoi cette semaine ?</p>")
        self.assertIsNone(parse_release_line(p1))
        self.assertIsNone(parse_release_line(p2))


if __name__ == "__main__":
    unittest.main()
