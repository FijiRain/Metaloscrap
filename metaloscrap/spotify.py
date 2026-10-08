"""Client Spotify pour la recherche d'albums, l'extraction de pistes et la gestion des playlists."""

import base64
import os
import re
import time
from typing import Dict, List, Optional, Tuple
import requests


class SpotifyClient:
    """Client pour interagir avec l'API Web Spotify via OAuth 2.0 (Refresh Token)."""

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("SPOTIFY_REFRESH_TOKEN")

        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise ValueError(
                "Les identifiants Spotify sont manquants. "
                "Veuillez définir SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET et SPOTIFY_REFRESH_TOKEN."
            )

        self._access_token: Optional[str] = None
        self._token_expiry: float = 0
        self._user_id: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        """Retourne les headers HTTP d'autorisation avec token valide."""
        now = time.time()
        if not self._access_token or now >= (self._token_expiry - 60):
            self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _refresh_access_token(self) -> None:
        """Échange le refresh_token contre un nouvel access_token."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_creds = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        resp = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Échec du renouvellement du token Spotify ({resp.status_code}): {resp.text}"
            )

        payload = resp.json()
        self._access_token = payload["access_token"]
        # expires_in est généralement 3600 secondes
        self._token_expiry = time.time() + payload.get("expires_in", 3600)

    def get_current_user_id(self) -> str:
        """Récupère l'identifiant du compte Spotify de l'utilisateur."""
        if self._user_id:
            return self._user_id

        url = f"{self.API_BASE_URL}/me"
        resp = requests.get(url, headers=self._get_headers(), timeout=15)
        resp.raise_for_status()
        self._user_id = resp.json()["id"]
        return self._user_id

    @staticmethod
    def extract_album_id_from_url(url: Optional[str]) -> Optional[str]:
        """Extrait l'ID d'album Spotify depuis une URL de partage."""
        if not url:
            return None
        match = re.search(r"spotify\.com/(?:[a-zA-Z-]+/)?album/([a-zA-Z0-9]+)", url)
        if match:
            return match.group(1)
        return None

    def search_album(self, artist: str, album_title: str) -> Optional[Dict]:
        """
        Recherche un album sur Spotify par artiste et titre.
        Retourne les détails de l'album ou None.
        """
        headers = self._get_headers()
        # 1. Requête ciblée avec syntaxe avancée Spotify
        query = f"album:{album_title} artist:{artist}"
        url = f"{self.API_BASE_URL}/search"
        params = {"q": query, "type": "album", "limit": 5}

        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            items = resp.json().get("albums", {}).get("items", [])
            if items:
                return items[0]

        # 2. Requête large de secours en texte libre si échec
        broad_query = f"{artist} {album_title}"
        params = {"q": broad_query, "type": "album", "limit": 5}
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            items = resp.json().get("albums", {}).get("items", [])
            artist_lower = artist.lower()
            for alb in items:
                # Vérifier la présence d'au moins un artiste correspondant
                artists_names = [a["name"].lower() for a in alb.get("artists", [])]
                if any(artist_lower in a_name or a_name in artist_lower for a_name in artists_names):
                    return alb

        return None

    def get_album_tracks(self, album_id: str) -> List[str]:
        """Récupère l'intégralité des URIs des morceaux d'un album."""
        headers = self._get_headers()
        track_uris: List[str] = []
        url: Optional[str] = f"{self.API_BASE_URL}/albums/{album_id}/tracks?limit=50"

        while url:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2))
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                if item.get("uri"):
                    track_uris.append(item["uri"])
            url = data.get("next")

        return track_uris

    def find_playlist_by_name(self, name: str) -> Optional[Dict]:
        """Vérifie si une playlist portant ce nom exact existe déjà."""
        headers = self._get_headers()
        url: Optional[str] = f"{self.API_BASE_URL}/me/playlists?limit=50"

        while url:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for pl in data.get("items", []):
                if pl.get("name") == name:
                    return pl

            url = data.get("next")

        return None

    def create_playlist(
        self,
        name: str,
        description: str = "Généré automatiquement par Metaloscrap",
        public: bool = False
    ) -> Dict:
        """Crée une nouvelle playlist sur le compte de l'utilisateur."""
        user_id = self.get_current_user_id()
        headers = self._get_headers()
        url = f"{self.API_BASE_URL}/users/{user_id}/playlists"
        body = {
            "name": name,
            "description": description,
            "public": public,
        }

        resp = requests.post(url, headers=headers, json=body, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> int:
        """
        Ajoute une liste de morceaux à la playlist par blocs de 100 max.
        Retourne le nombre total de morceaux ajoutés.
        """
        if not track_uris:
            return 0

        headers = self._get_headers()
        url = f"{self.API_BASE_URL}/playlists/{playlist_id}/tracks"
        chunk_size = 100
        added_count = 0

        for i in range(0, len(track_uris), chunk_size):
            chunk = track_uris[i:i + chunk_size]
            body = {"uris": chunk}
            resp = requests.post(url, headers=headers, json=body, timeout=15)
            resp.raise_for_status()
            added_count += len(chunk)

        return added_count
