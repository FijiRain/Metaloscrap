"""Module de reporting et d'export du résumé d'exécution en Markdown."""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from metaloscrap.scraper import Release


@dataclass
class AddedAlbum:
    release: Release
    matched_genres: List[str]
    spotify_album_id: str
    spotify_url: str
    track_count: int


@dataclass
class MissingAlbum:
    release: Release
    matched_genres: List[str]
    listen_url: Optional[str] = None


@dataclass
class RunReport:
    post_title: str
    post_url: str
    playlist_name: str
    playlist_url: Optional[str]
    target_genres: List[str]
    total_scraped: int
    added_albums: List[AddedAlbum] = field(default_factory=list)
    missing_albums: List[MissingAlbum] = field(default_factory=list)
    already_existed: bool = False

    def to_markdown(self) -> str:
        lines = []
        lines.append(f"# 🎸 Metaloscrap - Résumé d'exécution")
        lines.append(f"")
        lines.append(f"- **Source :** [{self.post_title}]({self.post_url})")
        lines.append(f"- **Playlist :** {f'[{self.playlist_name}]({self.playlist_url})' if self.playlist_url else self.playlist_name}")
        lines.append(f"- **Genres ciblés :** {', '.join(f'`{g}`' for g in self.target_genres)}")
        lines.append(f"- **Total sorties scrapées :** {self.total_scraped}")
        
        total_matched = len(self.added_albums) + len(self.missing_albums)
        lines.append(f"- **Sorties correspondantes :** {total_matched}")
        lines.append(f"")

        if self.already_existed:
            lines.append(f"> ℹ️ **Note :** La playlist `{self.playlist_name}` existait déjà sur Spotify. Aucune modification n'a été effectuée pour éviter les doublons.")
            lines.append(f"")
            return "\n".join(lines)

        total_tracks = sum(a.track_count for a in self.added_albums)
        lines.append(f"### ✅ Albums ajoutés à la playlist ({len(self.added_albums)} albums, {total_tracks} titres)")
        if self.added_albums:
            lines.append(f"| Artiste | Album | Genres | Titres | Spotify |")
            lines.append(f"| :--- | :--- | :--- | :---: | :---: |")
            for a in self.added_albums:
                genres_str = ", ".join(a.matched_genres)
                lines.append(
                    f"| **{a.release.artist}** | {a.release.album} | {genres_str} | {a.track_count} | [Écouter]({a.spotify_url}) |"
                )
        else:
            lines.append(f"_Aucun album n'a pu être ajouté._")
        lines.append(f"")

        lines.append(f"### ⚠️ Albums introuvables sur Spotify ({len(self.missing_albums)})")
        if self.missing_albums:
            lines.append(f"Ces albums correspondent à vos genres mais n'ont pas été trouvés sur Spotify (sorties Bandcamp ou labels underground) :")
            lines.append(f"")
            lines.append(f"| Artiste | Album | Genres déclarés | Lien alternatif |")
            lines.append(f"| :--- | :--- | :--- | :---: |")
            for m in self.missing_albums:
                alt_link = f"[Lien]({m.listen_url})" if m.listen_url else "—"
                lines.append(
                    f"| **{m.release.artist}** | {m.release.album} | {m.release.raw_genres} | {alt_link} |"
                )
        else:
            lines.append(f"_Tous les albums retenus ont été trouvés sur Spotify !_ 🎉")
        lines.append(f"")

        return "\n".join(lines)

    def write_github_summary(self) -> None:
        """Écrit le compte-rendu dans GITHUB_STEP_SUMMARY si la variable est présente."""
        summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(self.to_markdown() + "\n")
