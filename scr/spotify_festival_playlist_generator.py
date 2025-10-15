"""
Lineup Fetcher (Festify Auto-Scraper Edition)

Automatically fetches or creates a festival lineup.
If no local lineup file exists, it uses the domain scraper
(e.g., lib/domain/partysan.py) to populate res/lineups/{festival}/{year}/.

Config-driven constants:
    DEFAULT_TOP_N, DATA_DIR, PLAYLIST_DIR, LOG_DIR

Supports:
    --quiet   → suppress console logs, keep progress bar
    --export  → export normalized lineup
    --generate_playlist → trigger Spotify playlist generator
    --delete_old_playlists → löscht alle alten Festify-Playlists vor dem Neuaufbau
"""

import argparse
import importlib
import logging
import os
import sys
from typing import List

from conf.config import DEFAULT_TOP_N, DATA_DIR, LOG_DIR
from lib.common.logger import setup_logger
from lib.common.lineup_loader import fetch_lineup
from lib.common.export_utils import export_playlist
from lib.common.spotify_client import get_spotify_client_and_user_id
from lib.common.playlist_manager import delete_playlists_by_prefix, generate_festival_playlist
from lib.common.utils import schema_name, slug, find_lineup_path

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-fetch, scrape, and normalize festival lineup data.")
    parser.add_argument("--festival", required=True, nargs='+', help="Festival key(s), z.B. partysan wacken.")
    parser.add_argument("--year", required=True, help="Festival year (z.B. 2026).")
    parser.add_argument("--export", action="store_true", help="Export normalized lineup to res/lineups/.")
    parser.add_argument("--generate_playlist", action="store_true",
                        help="Trigger Spotify playlist generation after fetching lineup.")
    parser.add_argument("--log_level", default="INFO", help="Logging level (default: INFO).")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress all console logs (keep progress bar visible).")
    parser.add_argument("--delete_old_playlists", action="store_true",
                        help="Löscht alle alten Festify-Playlists vor dem Neuaufbau.")
    args = parser.parse_args()

    setup_logger(level=args.log_level, log_dir=LOG_DIR, quiet=args.quiet)
    logger = logging.getLogger(__name__)

    sp_client = None
    user_id = None
    if args.generate_playlist or args.delete_old_playlists:
        sp_client, user_id = get_spotify_client_and_user_id()

    if args.delete_old_playlists and sp_client and user_id:
        removed = delete_playlists_by_prefix(sp_client, user_id, "Festify")
        logger.info(f"Entfernt {removed} alte Festify-Playlists.")

    for festival in args.festival:
        lineup_path = find_lineup_path(festival=festival, year=args.year)

        logger.info(f"Using lineup file: {lineup_path}")

        lineup = fetch_lineup(file_path=lineup_path)
        if not lineup or lineup == ["(empty lineup placeholder)"]:
            logger.warning("No valid artists found (placeholder or empty lineup in use).")

        playlist_title = f"Festify · {schema_name(festival_key=festival, year_val=args.year)}"
        logger.info(f"Detected festival='{festival}', year='{args.year}' → Playlist name: '{playlist_title}'")
        logger.info(f"Artists loaded: {len(lineup)}")

        if args.export:
            export_playlist(
                playlist_name=playlist_title,
                data=[{"artist": name} for name in lineup],
                export_dir=DATA_DIR,
                is_lineup=True,
                festival_slug=slug(text=festival),
                year=args.year,
            )
            logger.info(f"Exported normalized lineup for {festival} {args.year}.")

        if args.generate_playlist and sp_client and user_id:
            playlist_title, new_tracks = generate_festival_playlist(
                sp_client=sp_client,
                user_id=user_id,
                lineup=lineup,
                festival_name=festival,
                year=args.year,
                top_n=DEFAULT_TOP_N,
                export_dir=DATA_DIR,
                quiet=args.quiet
            )
            logger.info(f"Generated playlist '{playlist_title}' with {new_tracks} new tracks.")

            if args.quiet:
                sys.argv.append("--quiet")

if __name__ == "__main__":
    main()
