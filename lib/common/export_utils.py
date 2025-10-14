"""Utility functions for exporting playlist or lineup data to CSV and JSON files.

Exports ensure consistent naming and structure:
    - Normalized filenames derived from playlist_name (e.g. "Festify · partysan_2026" → "festify_partysan_2026").
    - Data written to res/playlists/{festival}/{year}/ directories.
    - Supports both CSV and JSON outputs for easy inspection and archival.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, List, Dict


def _sanitize_name(name: str) -> str:
    """Normalize a playlist or festival name into a safe lowercase filename."""
    safe = (
        name.replace("·", "_")
        .replace("·", "_")
        .replace(" ", "_")
        .replace("·", "_")
        .replace("Festify", "festify")
        .replace(".", "_")
        .replace("-", "_")
    )
    return "".join(c for c in safe if c.isalnum() or c == "_").strip("_").lower()


def _ensure_directory(base_dir: str, festival_slug: str, year: str) -> Path:
    """Ensure export directory exists and return its path."""
    path = Path(base_dir) / festival_slug / str(year)
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_playlist(
    playlist_name: str,
    data: List[Dict[str, Any]],
    export_dir: str,
    is_lineup: bool,
    festival_slug: str,
    year: str
) -> None:
    """Export playlist or lineup data to CSV and JSON.

    Parameters
    ----------
    playlist_name : str
        The playlist title (e.g. "Festify · partysan_2026").
    data : List[Dict[str, Any]]
        The rows to export.
    export_dir : str
        Base output directory (e.g. "res/playlists").
    is_lineup : bool
        Whether this is a lineup (True) or a playlist export (False).
    festival_slug : str
        Festival identifier.
    year : str
        Festival year.
    """
    logger = logging.getLogger(__name__)
    export_path = _ensure_directory(base_dir=export_dir, festival_slug=festival_slug, year=year)
    filename = _sanitize_name(playlist_name)
    csv_path = export_path / f"{filename}.csv"
    json_path = export_path / f"{filename}.json"

    # Write CSV
    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Exported CSV: {csv_path}")
    except Exception as e:
        logger.error(f"Failed to export CSV ({csv_path}): {e}")

    # Write JSON
    try:
        with open(json_path, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported JSON: {json_path}")
    except Exception as e:
        logger.error(f"Failed to export JSON ({json_path}): {e}")
