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
import re
import sys
from typing import List

from conf.config import DEFAULT_TOP_N, DATA_DIR, LOG_DIR
from lib.common.logger import setup_logger
from lib.common.lineup_loader import load_lineup_from_csv, load_lineup_from_json
from lib.common.export_utils import export_playlist
from lib.common.playlist_manager import delete_playlists_by_prefix
from scr.spotify_festival_playlist_generator import _slug, _schema_name

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _find_lineup_path(festival: str, year: str) -> str | None:
    base_dir = os.path.join(DATA_DIR, festival.lower(), str(year))
    csv_path = os.path.join(base_dir, f"{festival.lower()}_{year}.csv")
    json_path = os.path.join(base_dir, f"{festival.lower()}_{year}.json")

    if os.path.exists(csv_path):
        return csv_path
    if os.path.exists(json_path):
        return json_path

    if os.path.isdir(base_dir):
        for f in os.listdir(base_dir):
            if f.lower().endswith((".csv", ".json")):
                return os.path.join(base_dir, f)
    return None

def _auto_fetch_from_scraper(festival: str, year: str) -> str:
    logger = logging.getLogger(__name__)
    module_name = f"lib.domain.{festival.lower()}"
    base_dir = os.path.join(DATA_DIR, festival.lower(), str(year))
    os.makedirs(base_dir, exist_ok=True)
    output_path = os.path.join(base_dir, f"{festival.lower()}_{year}.csv")

    try:
        scraper = importlib.import_module(module_name)
        if not hasattr(scraper, "fetch_lineup"):
            raise AttributeError(f"Module {module_name} has no fetch_lineup() function.")
        lineup = scraper.fetch_lineup()
        if not lineup:
            logger.warning(f"Scraper for {festival} returned no data.")
            lineup = ["(empty lineup placeholder)"]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("artist\n")
            for artist in lineup:
                f.write(f"{artist}\n")
        logger.info(f"Fetched lineup via scraper and wrote to {output_path}")
        return output_path
    except ImportError:
        logger.warning(f"No scraper found for {festival} (lib/domain/{festival}.py). Creating placeholder.")
    except Exception as e:
        logger.error(f"Failed to auto-fetch lineup for {festival} {year}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("artist\n(empty lineup placeholder)\n")
    return output_path

def fetch_lineup(file_path: str) -> List[str]:
    logger = logging.getLogger(__name__)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Lineup file not found: {file_path}")

    if file_path.lower().endswith(".csv"):
        logger.info(f"Loading lineup from CSV: {file_path}")
        return load_lineup_from_csv(file_path=file_path)
    elif file_path.lower().endswith(".json"):
        logger.info(f"Loading lineup from JSON: {file_path}")
        return load_lineup_from_json(file_path=file_path)
    else:
        raise ValueError(f"Unsupported lineup format: {os.path.splitext(file_path)[1]}")

def generate_festify_name(festival: str, year: str) -> str:
    return f"Festify · {_schema_name(festival_key=festival, year_val=year)}"

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

    # Spotify-Authentifizierung (hier ggf. anpassen)
    sp_client = None
    user_id = None
    if args.generate_playlist or args.delete_old_playlists:
        from scr.spotify_festival_playlist_generator import get_spotify_client_and_user_id
        sp_client, user_id = get_spotify_client_and_user_id()

    if args.delete_old_playlists and sp_client and user_id:
        removed = delete_playlists_by_prefix(sp_client, user_id, "Festify")
        logger.info(f"Entfernt {removed} alte Festify-Playlists.")

    for festival in args.festival:
        lineup_path = _find_lineup_path(festival=festival, year=args.year)
        if not lineup_path:
            logger.warning(f"No lineup file found locally for {festival} {args.year}. Attempting scraper...")
            lineup_path = _auto_fetch_from_scraper(festival=festival, year=args.year)

        logger.info(f"Using lineup file: {lineup_path}")

        lineup = fetch_lineup(file_path=lineup_path)
        if not lineup or lineup == ["(empty lineup placeholder)"]:
            logger.warning("No valid artists found (placeholder or empty lineup in use).")

        playlist_title = generate_festify_name(festival=festival, year=args.year)
        logger.info(f"Detected festival='{festival}', year='{args.year}' → Playlist name: '{playlist_title}'")
        logger.info(f"Artists loaded: {len(lineup)}")

        if args.export:
            export_playlist(
                playlist_name=playlist_title,
                data=[{"artist": name} for name in lineup],
                export_dir=DATA_DIR,
                is_lineup=True,
                festival_slug=_slug(festival),
                year=args.year,
            )
            logger.info(f"Exported normalized lineup for {festival} {args.year}.")

        if args.generate_playlist:
            from scr.spotify_festival_playlist_generator import main as generate_playlist_main
            logger.info("Triggering Spotify playlist generation via Festify workflow...")

            sys.argv = [
                "spotify_festival_playlist_generator.py",
                "--lineup", str(lineup_path),
                "--festival", festival,
                "--top_n", str(DEFAULT_TOP_N),
                "--log_level", args.log_level,
            ]
            if args.quiet:
                sys.argv.append("--quiet")
            generate_playlist_main()

if __name__ == "__main__":
    main()
