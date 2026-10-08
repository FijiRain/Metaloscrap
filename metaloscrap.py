#!/usr/bin/env python3
"""Point d'entrée principal de Metaloscrap.

Exécute le scraping de Metalorgie, filtre les albums et alimente Spotify.
"""

import argparse
import datetime
import os
import sys
from dotenv import load_dotenv

from metaloscrap.scraper import fetch_latest_weekly_post
from metaloscrap.filter import filter_releases, load_genres_config
from metaloscrap.spotify import SpotifyClient
from metaloscrap.reporter import AddedAlbum, MissingAlbum, RunReport


def build_playlist_name() -> str:
    """Génère le nom horodaté de la playlist hebdomadaire."""
    today = datetime.date.today()
    week_num = today.isocalendar().week
    year = today.year
    return f"Metaloscrap - Semaine {week_num:02d} ({year})"


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Metaloscrap : Scraping de Metalorgie et alimentation de playlist Spotify."
    )
    parser.add_argument(
        "--config",
        default="genres.json",
        help="Chemin vers le fichier de configuration des genres (défaut: genres.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exécute le scraping et le filtrage sans interagir avec l'API Spotify.",
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Rend la playlist Spotify publique (privée par défaut).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recrée la playlist même si une playlist avec ce nom existe déjà.",
    )

    args = parser.parse_args()

    # 1. Chargement des genres
    if not os.path.exists(args.config):
        print(f"❌ Erreur : Fichier de configuration '{args.config}' introuvable.", file=sys.stderr)
        return 1

    try:
        target_genres = load_genres_config(args.config)
    except Exception as e:
        print(f"❌ Erreur lors du chargement de {args.config} : {e}", file=sys.stderr)
        return 1

    print(f"🎵 Genres surveillés ({len(target_genres)}) : {', '.join(target_genres)}")

    # 2. Scraping de Metalorgie
    print("🌐 Récupération des dernières actualités sur Metalorgie...")
    try:
        post = fetch_latest_weekly_post()
    except Exception as e:
        print(f"❌ Erreur lors du scraping de Metalorgie : {e}", file=sys.stderr)
        return 1

    if not post:
        print("⚠️ Aucun post 'Sorties de la semaine' trouvé dans les actualités récentes.")
        return 0

    print(f"📰 Post trouvé : '{post.title}' ({post.url})")
    print(f"📦 Total de sorties détectées : {len(post.releases)}")

    # 3. Filtrage des genres
    matched_releases = filter_releases(post.releases, target_genres)
    print(f"🎯 Sorties correspondant à vos genres : {len(matched_releases)}")

    for rel, matched in matched_releases:
        print(f"   • {rel.artist} - {rel.album} [{', '.join(matched)}] (Pays: {rel.country or 'N/A'})")

    playlist_name = build_playlist_name()

    # 4. Mode Dry-Run
    if args.dry_run:
        print(f"\n🔍 [DRY-RUN] Simulation terminée avec succès.")
        print(f"   Nom de playlist prévu : '{playlist_name}'")
        print(f"   {len(matched_releases)} albums auraient été recherchés sur Spotify.")
        return 0

    if not matched_releases:
        print("ℹ️ Aucun album correspondant à vos genres cette semaine. Fin du traitement.")
        return 0

    # 5. Connexion Spotify
    try:
        spotify = SpotifyClient()
    except ValueError as e:
        print(f"❌ Erreur de configuration Spotify : {e}", file=sys.stderr)
        return 1

    # Vérification de l'existence de la playlist
    print(f"\n🔍 Recherche de la playlist '{playlist_name}' sur Spotify...")
    existing = spotify.find_playlist_by_name(playlist_name)
    if existing and not args.force:
        print(f"ℹ️ La playlist '{playlist_name}' existe déjà ({existing['external_urls']['spotify']}).")
        print("   Exécution interrompue pour éviter les doublons (utilisez --force pour outrepasser).")
        report = RunReport(
            post_title=post.title,
            post_url=post.url,
            playlist_name=playlist_name,
            playlist_url=existing["external_urls"]["spotify"],
            target_genres=target_genres,
            total_scraped=len(post.releases),
            already_existed=True,
        )
        report.write_github_summary()
        return 0

    # 6. Recherche et collecte des pistes de chaque album
    added_albums = []
    missing_albums = []
    all_track_uris = []

    print("\n🎧 Résolution des albums sur Spotify...")
    for rel, matched in matched_releases:
        album_id = None

        # Tentative d'extraction si lien direct Spotify
        if rel.listen_url and "spotify.com" in rel.listen_url:
            album_id = SpotifyClient.extract_album_id_from_url(rel.listen_url)

        album_data = None
        if album_id:
            # Récupération directe des infos
            try:
                album_tracks = spotify.get_album_tracks(album_id)
                if album_tracks:
                    all_track_uris.extend(album_tracks)
                    added_albums.append(
                        AddedAlbum(
                            release=rel,
                            matched_genres=matched,
                            spotify_album_id=album_id,
                            spotify_url=f"https://open.spotify.com/album/{album_id}",
                            track_count=len(album_tracks),
                        )
                    )
                    print(f"   ✅ [Lien direct] {rel.artist} - {rel.album} ({len(album_tracks)} titres)")
                    continue
            except Exception:
                pass

        # Recherche via l'API Spotify
        try:
            album_data = spotify.search_album(rel.artist, rel.album)
        except Exception as e:
            print(f"   ⚠️ Erreur recherche pour {rel.artist} - {rel.album} : {e}")

        if album_data:
            alb_id = album_data["id"]
            spotify_url = album_data["external_urls"]["spotify"]
            tracks = spotify.get_album_tracks(alb_id)
            all_track_uris.extend(tracks)
            added_albums.append(
                AddedAlbum(
                    release=rel,
                    matched_genres=matched,
                    spotify_album_id=alb_id,
                    spotify_url=spotify_url,
                    track_count=len(tracks),
                )
            )
            print(f"   ✅ [Trouvé] {rel.artist} - {rel.album} ({len(tracks)} titres) -> {spotify_url}")
        else:
            missing_albums.append(
                MissingAlbum(
                    release=rel,
                    matched_genres=matched,
                    listen_url=rel.listen_url,
                )
            )
            print(f"   ⚠️ [Introuvable] {rel.artist} - {rel.album} (Lien : {rel.listen_url or 'N/A'})")

    if not all_track_uris:
        print("⚠️ Aucun morceau trouvé sur Spotify pour les albums retenus.")
        return 0

    # 7. Création de la playlist et injection des pistes
    description = (
        f"Sélection hebdomadaire automatique Metalorgie ({post.title}) "
        f"pour les genres : {', '.join(target_genres)}."
    )
    print(f"\n📝 Création de la playlist '{playlist_name}'...")
    new_playlist = spotify.create_playlist(
        name=playlist_name,
        description=description,
        public=args.public,
    )
    playlist_id = new_playlist["id"]
    playlist_url = new_playlist["external_urls"]["spotify"]

    print(f"🚀 Ajout de {len(all_track_uris)} pistes à la playlist...")
    added_count = spotify.add_tracks_to_playlist(playlist_id, all_track_uris)
    print(f"🎉 Succès ! {added_count} titres ajoutés à la playlist : {playlist_url}")

    # 8. Génération du rapport
    report = RunReport(
        post_title=post.title,
        post_url=post.url,
        playlist_name=playlist_name,
        playlist_url=playlist_url,
        target_genres=target_genres,
        total_scraped=len(post.releases),
        added_albums=added_albums,
        missing_albums=missing_albums,
        already_existed=False,
    )

    report.write_github_summary()
    print("\n" + report.to_markdown())

    return 0


if __name__ == "__main__":
    sys.exit(main())
