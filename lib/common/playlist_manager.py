"""Handles playlist lookup, creation, and idempotent track updates.

All logging is done via the project-wide logger. Functions are designed to be
safe to call repeatedly; they only add truly new tracks.

Note:
    Spotify's Web API does not expose playlist folders. The project simulates
    grouping by prefixing playlist titles (e.g., "Festify · partysan_2026").
"""

import re
from datetime import date
from tqdm import tqdm
import logging
from typing import Iterable, Optional, Set, Dict, Any
from spotipy import Spotify
from lib.common.utils import slug
from lib.common.artist_utils import get_artist_id, get_top_tracks
from lib.common.export_utils import export_playlist
from lib.common.spotify_client import create_spotify_client


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

def set_playlist_description(spotify_client, user_id, playlist_id, description):
    """
    Setzt die Beschreibung einer Playlist bei Spotify.

    :param spotify_client: Authentifizierter Spotipy-Client
    :param user_id: Spotify User-ID
    :param playlist_id: ID der Playlist
    :param description: Beschreibungstext
    """
    spotify_client.user_playlist_change_details(user=user_id, playlist_id=playlist_id, description=description)

def generate_festival_playlist(
    sp_client,
    user_id,
    lineup,
    festival_name,
    year,
    top_n=3,
    export_dir="res/playlists",
    quiet=False
):
    """
    Creates or updates a festival playlist on Spotify and exports track data.

    Args:
        sp_client: Authenticated Spotipy client.
        user_id: Spotify user ID.
        lineup: Iterable of artist names.
        festival_name: Name of the festival.
        year: Year of the festival.
        top_n: Number of top tracks per artist to add.
        export_dir: Directory to export playlist data.
        quiet: If True, suppresses info logging.

    Returns:
        Tuple of (playlist title, number of new tracks added).
    """

    fest_slug = slug(festival_name)
    playlist_title = f"Festify · {festival_name.replace('_', ' ').strip().title()} {year}"
    playlist_description = (
        f"This is an automatically generated playlist for {festival_name.strip().title()} - {year} "
        f"as of {date.today().isoformat()}. It is updated sporadically."
    )

    logger = logging.getLogger(__name__)
    if not quiet:
        logger.info(f"Target playlist name resolved: {playlist_title}")

    # Ensure playlist exists or create it
    playlist = ensure_playlist(
        sp_client=sp_client,
        user_id=user_id,
        name=playlist_title,
        description=playlist_description
    )
    set_playlist_description(sp_client, user_id, playlist["id"], playlist_description)
    playlist_id = playlist["id"]
    existing_track_ids = get_playlist_track_ids(sp_client, playlist_id)

    new_track_ids = set()
    export_data = []

    # Process each artist in the lineup
    for artist in tqdm(lineup, desc=f"Processing {festival_name.strip().title()}", unit="artist", ncols=100, leave=True):
        artist_id = get_artist_id(sp_client=sp_client, name=artist)
        if not artist_id:
            continue
        top_tracks = get_top_tracks(sp_client=sp_client, artist_id=artist_id, limit=top_n)
        fresh_ids = [tid for tid in top_tracks if tid and tid not in existing_track_ids and tid not in new_track_ids]
        if fresh_ids:
            add_tracks(sp_client=sp_client, playlist_id=playlist_id, track_ids=fresh_ids)
            for tid in fresh_ids:
                tr = sp_client.track(tid)
                export_data.append({
                    "artist": artist,
                    "track_name": tr["name"],
                    "track_id": tid,
                    "spotify_url": tr["external_urls"]["spotify"],
                })
            new_track_ids.update(fresh_ids)

    # Export playlist data if new tracks were added
    if export_data:
        export_playlist(
            playlist_name=playlist_title,
            data=export_data,
            export_dir=export_dir,
            is_lineup=False,
            festival_slug=fest_slug,
            year=year,
        )

    if not quiet:
        logger.info(f"Done: {playlist_title} (+{len(new_track_ids)} new tracks)")
    return playlist_title, len(new_track_ids)


if __name__ == "__main__":

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
