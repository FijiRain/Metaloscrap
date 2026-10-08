"""Module de filtrage des sorties musicales selon les genres préférés."""

import json
import unicodedata
from typing import List, Tuple
from metaloscrap.scraper import Release


def _normalize(text: str) -> str:
    """Normalise une chaîne : minuscules, suppression des accents et espaces superflus."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return without_accents.lower().strip()


def matches_genre(release: Release, target_genres: List[str]) -> List[str]:
    """
    Vérifie si une sortie correspond à au moins un genre cible.
    Retourne la liste des genres cibles correspondants.
    """
    matched: List[str] = []
    normalized_raw = _normalize(release.raw_genres)
    normalized_tokens = [_normalize(g) for g in release.genres]

    for target in target_genres:
        norm_target = _normalize(target)
        if not norm_target:
            continue

        # 1. Correspondance exacte ou partielle avec un des tokens de genre
        # Ex: "noise rock" dans ["noise rock", "psyche"]
        # Ex: "noise" dans "noise rock"
        if any(norm_target in token for token in normalized_tokens):
            if target not in matched:
                matched.append(target)
            continue

        # 2. Correspondance globale dans la chaîne brute des genres
        if norm_target in normalized_raw:
            if target not in matched:
                matched.append(target)

    return matched


def filter_releases(
    releases: List[Release],
    target_genres: List[str]
) -> List[Tuple[Release, List[str]]]:
    """
    Filtre une liste de sorties selon les genres cibles.
    Retourne une liste de tuples (Release, matched_genres).
    """
    results: List[Tuple[Release, List[str]]] = []
    for rel in releases:
        matched = matches_genre(rel, target_genres)
        if matched:
            results.append((rel, matched))
    return results


def load_genres_config(config_path: str = "genres.json") -> List[str]:
    """Charge la liste des genres cibles depuis un fichier JSON."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [str(item).strip() for item in data if str(item).strip()]
    raise ValueError("Le fichier genres.json doit contenir une liste de chaînes.")
