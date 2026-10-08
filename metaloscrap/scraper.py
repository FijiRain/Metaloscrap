"""Module de scraping et de parsing des sorties d'albums depuis Metalorgie."""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import re
import requests
from lxml import html


@dataclass
class Release:
    artist: str
    album: str
    raw_genres: str
    genres: List[str]
    country: Optional[str] = None
    listen_url: Optional[str] = None
    source_text: str = ""

    def __repr__(self) -> str:
        return f"<Release: {self.artist} - {self.album} [{', '.join(self.genres)}]>"


@dataclass
class WeeklyPost:
    title: str
    url: str
    releases: List[Release]


KNOWN_COUNTRIES = {
    "us", "usa", "france", "suède", "suede", "royaume-uni", "uk", "allemagne",
    "canada", "australie", "finlande", "italie", "belgique", "pays-bas",
    "danemark", "norvège", "norvege", "espagne", "portugal", "suisse",
    "autriche", "chili", "brésil", "bresil", "japon", "colombie", "bulgarie",
    "islande", "pologne", "mexique", "irlande", "nouvelle-zélande", "nouvelle-zelande"
}


def _clean_text(text: str) -> str:
    """Nettoie les espaces multiples et caractères invisibles."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_release_line(p_element: html.HtmlElement) -> Optional[Release]:
    """Parse un élément <p> représentant une sortie d'album."""
    full_text = _clean_text(p_element.text_content())
    if not full_text or len(full_text) < 5:
        return None

    # Doit généralement commencer par un tiret ou puce
    if not re.match(r"^[-–—•*]\s*", full_text):
        return None

    # Exclure les séparateurs comme '----'
    clean_line = re.sub(r"^[-–—•*]+\s*", "", full_text).strip()
    if clean_line.startswith("-") or not clean_line:
        return None

    # Extraction du lien d'écoute (🎧)
    listen_url = None
    for a in p_element.xpath(".//a"):
        href = a.get("href")
        a_text = a.text_content()
        if "🎧" in a_text or (href and ("/sortie/" in href or "spotify.com" in href or "bandcamp.com" in href)):
            listen_url = href
            break

    # Retirer l'icône 🎧 pour le parsing du texte
    clean_line = clean_line.replace("🎧", "").strip()

    # Pattern attendu: "Artiste - Titre (Genres, Pays)" ou "Artiste - Titre (Genres)"
    # Ex: Amon Amarth - The Allfather Awakens (Death Melo, Suède)
    match = re.match(r"^(.*?)\s*[-–—]\s*(.*?)\s*\((.*?)\)$", clean_line)
    if not match:
        return None

    artist = _clean_text(match.group(1))
    album = _clean_text(match.group(2))
    inside_parens = _clean_text(match.group(3))

    if not artist or not album:
        return None

    # Séparation genres / pays
    # Dans Metalorgie : "(Stoner / Sludge, US)" ou "(Black Metal)"
    genres_part = inside_parens
    country = None

    if "," in inside_parens:
        parts = [p.strip() for p in inside_parens.rsplit(",", 1)]
        potential_country = parts[1].strip()
        # Si la partie après la dernière virgule ressemble à un pays
        if potential_country.lower() in KNOWN_COUNTRIES or len(potential_country) <= 3:
            country = potential_country
            genres_part = parts[0]
        else:
            genres_part = inside_parens

    # Découpage des genres séparés par des slashes ou virgules
    genre_tokens = [
        _clean_text(g)
        for g in re.split(r"[/,]", genres_part)
        if _clean_text(g)
    ]

    return Release(
        artist=artist,
        album=album,
        raw_genres=genres_part,
        genres=genre_tokens,
        country=country,
        listen_url=listen_url,
        source_text=full_text,
    )


def fetch_latest_weekly_post(
    base_url: str = "https://www.metalorgie.com/news",
    headers: Optional[dict] = None
) -> Optional[WeeklyPost]:
    """Récupère et parse le dernier article 'Sorties de la semaine' sur Metalorgie."""
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }

    response = requests.get(base_url, headers=headers, timeout=20)
    response.raise_for_status()

    tree = html.fromstring(response.content)
    news_items = tree.xpath('//li[contains(@class, "news__item")]')

    for item in news_items:
        text = item.text_content().lower()
        if "sorties de la semaine" in text:
            # Récupérer l'URL du post
            post_url = base_url
            for link in item.xpath('.//a[contains(@href, "/news/")]/@href'):
                if link.startswith("http"):
                    post_url = link
                else:
                    post_url = f"https://www.metalorgie.com{link}"
                break

            # Titre du post
            title_node = item.xpath('.//*[contains(@class, "news__item__title")]/text()')
            title = _clean_text(title_node[0]) if title_node else "Les sorties de la semaine"

            # Parser chaque paragraphe <p>
            releases: List[Release] = []
            for p in item.xpath(".//p"):
                release = parse_release_line(p)
                if release:
                    releases.append(release)

            if releases:
                return WeeklyPost(
                    title=title,
                    url=post_url,
                    releases=releases
                )

    return None
