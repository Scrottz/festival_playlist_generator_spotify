"""
Spotify Festival Playlist Generator

Creates or updates Spotify playlists for a given lineup.
Supports quiet mode (--quiet): hides all console logs, keeps progress bar visible.
"""

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path
from tqdm import tqdm
from contextlib import contextmanager

from lib.common.logger import setup_logger
from lib.common.spotify_client import create_spotify_client
from lib.common.playlist_manager import ensure_playlist, add_tracks, get_playlist_track_ids
from lib.common.artist_utils import get_artist_id, get_top_tracks
from lib.common.lineup_loader import load_lineup_from_csv
from lib.common.export_utils import export_playlist


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    """Return a lowercase, underscore-separated version of the given text."""
    s = re.sub(r"[^\w\s-]", "_", text.strip().lower())
    s = re.sub(r"\s+", "_", s)
    return re.sub(r"_+", "_", s).strip("_") or "unknown"

def _schema_name(festival_key: str, year_val: str | int) -> str:
    """Return 'festival_year' as canonical naming schema."""
    return f"{_slug(str(festival_key))}_{_slug(str(year_val))}"

def _resolve_lineup_path(lineup_arg: str) -> Path:
    """Resolve a lineup path argument safely."""
    path = Path(lineup_arg).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Lineup file not found: {path}")
    return path

@contextmanager
def silence_stream_logs():
    """Temporarily remove all console StreamHandlers (for clean tqdm output)."""
    root_logger = logging.getLogger()
    removed = []
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)
            removed.append(handler)
    try:
        yield
    finally:
        for handler in removed:
            root_logger.addHandler(handler)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or update festival playlists on Spotify.")
    parser.add_argument("--lineup", required=True, help="Path to the festival lineup (CSV).")
    parser.add_argument("--festival", help="Festival name (e.g., Partysan).")
    parser.add_argument("--playlist_name", help="Optional custom playlist name.")
    parser.add_argument("--top_n", type=int, default=3, help="Number of top tracks per artist.")
    parser.add_argument("--log_level", default="INFO", help="Logging level (default: INFO).")
    parser.add_argument("--quiet", action="store_true", help="Hide console logs but keep progress bar.")
    args = parser.parse_args()

    setup_logger(level=args.log_level, log_dir="logs", quiet=args.quiet)
    logger = logging.getLogger(__name__)

    if not args.quiet:
        logger.info("Starting Spotify Festival Playlist Generator.")

    sp = create_spotify_client()
    lineup_path = _resolve_lineup_path(args.lineup)
    lineup = load_lineup_from_csv(lineup_path)
    if not lineup:
        if not args.quiet:
            logger.error("No artists found in lineup file.")
        return

    fest_slug = _slug(args.festival) if args.festival else lineup_path.parent.parent.name
    year_match = re.search(r"(\d{4})", lineup_path.name)
    year_val = year_match.group(1) if year_match else lineup_path.parent.name
    schema = _schema_name(fest_slug, year_val)
    playlist_title = f"Festify · {schema}"

    if not args.quiet:
        logger.info(f"Target playlist name resolved: {playlist_title}")

    user_id = sp.current_user()["id"]
    playlist = ensure_playlist(
        sp_client=sp,
        user_id=user_id,
        name=playlist_title,
        description=f"Auto-generated playlist for {fest_slug} {year_val}. Top {args.top_n} tracks per artist."
    )
    playlist_id = playlist["id"]
    existing_track_ids = get_playlist_track_ids(sp, playlist_id)

    new_track_ids = set()
    export_data = []

    with silence_stream_logs():
        pbar = tqdm(iterable=lineup, desc="Processing artists", unit="artist", ncols=100, leave=True)
        for artist in pbar:
            pbar.set_description(f"Artist: {artist[:30]}")
            artist_id = get_artist_id(sp_client=sp, name=artist)
            if not artist_id:
                pbar.set_postfix_str("not found")
                continue
            top_tracks = get_top_tracks(sp_client=sp, artist_id=artist_id, limit=args.top_n)
            fresh_ids = [tid for tid in top_tracks if tid and tid not in existing_track_ids and tid not in new_track_ids]
            if not fresh_ids:
                pbar.set_postfix_str("no new tracks")
                continue
            add_tracks(sp_client=sp, playlist_id=playlist_id, track_ids=fresh_ids)
            new_track_ids.update(fresh_ids)
            for tid in fresh_ids:
                tr = sp.track(tid)
                export_data.append({
                    "artist": artist,
                    "track_name": tr["name"],
                    "track_id": tid,
                    "spotify_url": tr["external_urls"]["spotify"],
                })
            time.sleep(0.3)
        pbar.close()

    if export_data:
        export_playlist(
            playlist_name=playlist_title,
            data=export_data,
            export_dir="res/playlists",
            is_lineup=False,
            festival_slug=fest_slug,
            year=year_val,
        )

    print(f"\nDone: {playlist_title} (+{len(new_track_ids)} new tracks)")


if __name__ == "__main__":
    main()
