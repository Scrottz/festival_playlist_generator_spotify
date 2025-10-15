"""Handles playlist lookup, creation, and idempotent track updates.

All logging is done via the project-wide logger. Functions are designed to be
safe to call repeatedly; they only add truly new tracks.

Note:
    Spotify's Web API does not expose playlist folders. The project simulates
    grouping by prefixing playlist titles (e.g., "Festify · partysan_2026").
"""

from typing import Iterable, Optional, Set, Dict, Any
import logging
from spotipy import Spotify


def find_playlist_by_name(sp_client: Spotify, user_id: str, name: str) -> Optional[Dict[str, Any]]:
    """Return the user's playlist dict if a playlist with `name` exists, else None."""
    logger = logging.getLogger(__name__)
    limit = 50
    offset = 0
    while True:
        page = sp_client.current_user_playlists(limit=limit, offset=offset)
        items = page.get("items", [])
        for pl in items:
            if pl.get("name") == name and pl.get("owner", {}).get("id") == user_id:
                logger.info(f"Found existing playlist: {name} ({pl.get('id')})")
                return pl
        if len(items) < limit:
            break
        offset += limit
    logger.info(f"No existing playlist named '{name}' found for user {user_id}.")
    return None


def create_playlist(sp_client: Spotify, user_id: str, name: str, description: str) -> Dict[str, Any]:
    """Create a new playlist with the given name and description."""
    logger = logging.getLogger(__name__)
    logger.info(f"Creating new playlist: {name}")
    return sp_client.user_playlist_create(user=user_id, name=name, public=False, description=description)


def get_playlist_track_ids(sp_client: Spotify, playlist_id: str) -> Set[str]:
    """Return a set of all track IDs currently in the playlist (handles pagination)."""
    logger = logging.getLogger(__name__)
    track_ids: Set[str] = set()
    limit = 100
    offset = 0
    while True:
        page = sp_client.playlist_items(playlist_id=playlist_id, limit=limit, offset=offset)
        items = page.get("items", [])
        for it in items:
            track = it.get("track") or {}
            tid = track.get("id")
            if tid:
                track_ids.add(tid)
        if len(items) < limit:
            break
        offset += limit
    logger.info(f"Collected {len(track_ids)} existing track IDs from playlist {playlist_id}.")
    return track_ids


def add_tracks(sp_client: Spotify, playlist_id: str, track_ids: Iterable[str]) -> None:
    """Add tracks in chunks of 100 (no-op if iterable is empty)."""
    batch = list(track_ids)
    if not batch:
        return
    logger = logging.getLogger(__name__)
    logger.info(f"Adding {len(batch)} new tracks to playlist {playlist_id}...")
    for i in range(0, len(batch), 100):
        chunk = batch[i:i + 100]
        sp_client.playlist_add_items(playlist_id=playlist_id, items=chunk)


def ensure_playlist(sp_client: Spotify, user_id: str, name: str, description: str) -> Dict[str, Any]:
    """Return an existing playlist by name or create a fresh one if missing."""
    existing = find_playlist_by_name(sp_client=sp_client, user_id=user_id, name=name)
    if existing:
        return existing
    return create_playlist(sp_client=sp_client, user_id=user_id, name=name, description=description)


def delete_playlists_by_prefix(sp_client: Spotify, user_id: str, prefix: str) -> int:
    """
    Entfernt alle Playlists des Nutzers, deren Name mit `prefix` beginnt.
    Gibt die Anzahl der entfernten Playlists zurück.
    """
    logger = logging.getLogger(__name__)
    removed = 0
    limit = 50
    offset = 0
    while True:
        page = sp_client.current_user_playlists(limit=limit, offset=offset)
        items = page.get("items", [])
        for pl in items:
            name = pl.get("name", "")
            pid = pl.get("id")
            owner = pl.get("owner", {}).get("id")
            if name.startswith(prefix) and owner == user_id:
                sp_client.current_user_unfollow_playlist(pid)
                logger.info(f"Entfernt Playlist: {name} ({pid})")
                removed += 1
        if len(items) < limit:
            break
        offset += limit
    logger.info(f"Entfernte insgesamt {removed} Playlists mit Prefix '{prefix}'.")
    return removed


if __name__ == "__main__":
    from lib.common.spotify_client import create_spotify_client

    sp = create_spotify_client()
    user_id = sp.current_user()["id"]
    prefix = "Festify ·"

    # Debug-Ausgabe: Zeige alle Playlists mit Name, Owner und ID
    print("Gefundene Playlists:")
    limit = 50
    offset = 0
    while True:
        page = sp.current_user_playlists(limit=limit, offset=offset)
        items = page.get("items", [])
        print(f"Offset: {offset}, Anzahl Playlists auf Seite: {len(items)}")  # <-- Hier einfügen
        for pl in items:
            name = pl.get("name", "")
            pid = pl.get("id")
            owner = pl.get("owner", {}).get("id")
            print(f"Name='{name}', Owner='{owner}', ID='{pid}'")
        if len(items) < limit:
            break
        offset += limit

    # Löschen der Playlists mit passendem Prefix
    deleted = delete_playlists_by_prefix(sp, user_id, prefix)
    print(f"Entfernte {deleted} Playlists mit Prefix '{prefix}'.")
