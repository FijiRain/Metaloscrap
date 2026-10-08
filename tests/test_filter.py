"""Tests unitaires pour le module de filtrage des genres."""

import unittest
from metaloscrap.scraper import Release
from metaloscrap.filter import matches_genre, filter_releases


class TestFilter(unittest.TestCase):

    def setUp(self):
        self.r1 = Release(
            artist="Dééfait",
            album="Dééfait",
            raw_genres="Noise Rock / Psyche",
            genres=["Noise Rock", "Psyche"],
            country="France"
        )
        self.r2 = Release(
            artist="The Dillinger Escape Plan",
            album="Calculating Infinity",
            raw_genres="Mathcore / Hardcore",
            genres=["Mathcore", "Hardcore"],
            country="US"
        )
        self.r3 = Release(
            artist="Amon Amarth",
            album="The Allfather Awakens",
            raw_genres="Death Melo",
            genres=["Death Melo"],
            country="Suède"
        )
        self.r4 = Release(
            artist="Swans",
            album="The Beggar",
            raw_genres="Experimental Rock / Post-Punk",
            genres=["Experimental Rock", "Post-Punk"],
            country="US"
        )

    def test_matches_exact_or_substring(self):
        targets = ["Noise", "mathcore", "screamo"]
        self.assertEqual(matches_genre(self.r1, targets), ["Noise"])
        self.assertEqual(matches_genre(self.r2, targets), ["mathcore"])
        self.assertEqual(matches_genre(self.r3, targets), [])

    def test_case_and_accent_insensitivity(self):
        targets = ["experimental"]
        self.assertEqual(matches_genre(self.r4, targets), ["experimental"])

    def test_filter_releases_list(self):
        targets = ["Noise", "Noise Rock", "mathcore", "experimental", "screamo"]
        releases = [self.r1, self.r2, self.r3, self.r4]
        filtered = filter_releases(releases, targets)

        # r1 (Noise, Noise Rock), r2 (mathcore), r4 (experimental) should match
        matched_artists = [rel.artist for rel, _ in filtered]
        self.assertIn("Dééfait", matched_artists)
        self.assertIn("The Dillinger Escape Plan", matched_artists)
        self.assertIn("Swans", matched_artists)
        self.assertNotIn("Amon Amarth", matched_artists)


if __name__ == "__main__":
    unittest.main()
