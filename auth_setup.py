#!/usr/bin/env python3
"""Script d'initialisation unique pour générer le SPOTIFY_REFRESH_TOKEN.

Ce script ouvre votre navigateur, vous connecte à votre compte Spotify,
et extrait le refresh_token nécessaire pour faire tourner Metaloscrap
en local et sur GitHub Actions sans interaction manuelle.
"""

import base64
import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from dotenv import load_dotenv

REDIRECT_URI = "http://127.0.0.1:8888/callback"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "playlist-modify-public playlist-modify-private playlist-read-private"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;padding:50px;'>"
                b"<h1 style='color:#1DB954;'>&#10004; Autorisation r&eacute;ussie !</h1>"
                b"<p>Metaloscrap a bien re&ccedil;u l'autorisation. Vous pouvez fermer cet onglet et revenir &agrave; votre terminal.</p>"
                b"</body></html>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>Erreur lors de l'autorisation Spotify.</h1>")

    def log_message(self, format, *args):
        # Silence HTTP logs
        return


def main():
    load_dotenv()

    print("=" * 65)
    print("🎸 Metaloscrap - Configuration de l'authentification Spotify")
    print("=" * 65)
    print("\nCe script va générer votre SPOTIFY_REFRESH_TOKEN permanent.\n")

    client_id = os.getenv("SPOTIFY_CLIENT_ID") or input("Entrez votre Spotify Client ID : ").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET") or input("Entrez votre Spotify Client Secret : ").strip()

    if not client_id or not client_secret:
        print("❌ Client ID et Client Secret sont obligatoires.", file=sys.stderr)
        return 1

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "show_dialog": "true",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("\n👉 IMPORTANT : Assurez-vous d'avoir ajouté l'URI de redirection suivante")
    print(f"   dans votre Spotify Developer Dashboard (Edit Settings > Redirect URIs) :")
    print(f"   \033[1;36m{REDIRECT_URI}\033[0m\n")

    server = HTTPServer(("127.0.0.1", 8888), OAuthCallbackHandler)
    print(f"🌐 Ouverture du navigateur pour autoriser Metaloscrap...")
    webbrowser.open(url)

    print("⏳ En attente de l'autorisation dans votre navigateur...")
    while OAuthCallbackHandler.auth_code is None:
        server.handle_request()

    code = OAuthCallbackHandler.auth_code
    print("✅ Code d'autorisation reçu ! Échange avec l'API Spotify...")

    # Échange du code contre le refresh token
    creds = f"{client_id}:{client_secret}"
    encoded_creds = base64.b64encode(creds.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_creds}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    resp = requests.post(TOKEN_URL, headers=headers, data=data, timeout=15)
    if resp.status_code != 200:
        print(f"❌ Erreur lors de l'obtention du token ({resp.status_code}) : {resp.text}", file=sys.stderr)
        return 1

    payload = resp.json()
    refresh_token = payload.get("refresh_token")

    if not refresh_token:
        print("❌ Aucun refresh_token retourné par Spotify.", file=sys.stderr)
        return 1

    print("\n" + "=" * 65)
    print("🎉 SUCCÈS ! Voici vos variables à conserver :")
    print("=" * 65)
    print(f"SPOTIFY_CLIENT_ID={client_id}")
    print(f"SPOTIFY_CLIENT_SECRET={client_secret}")
    print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")

    # Mise à jour ou création du fichier .env local
    env_path = ".env"
    env_content = (
        f"SPOTIFY_CLIENT_ID={client_id}\n"
        f"SPOTIFY_CLIENT_SECRET={client_secret}\n"
        f"SPOTIFY_REFRESH_TOKEN={refresh_token}\n"
    )
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    print(f"\n💾 Variables enregistrées localement dans '{env_path}'.")
    print("\n🔒 POUR GITHUB ACTIONS :")
    print("Rendez-vous sur votre dépôt GitHub :")
    print("Settings > Secrets and variables > Actions > New repository secret")
    print("Ajoutez les 3 secrets suivants :")
    print("  1. SPOTIFY_CLIENT_ID")
    print("  2. SPOTIFY_CLIENT_SECRET")
    print("  3. SPOTIFY_REFRESH_TOKEN")
    print("=" * 65 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
