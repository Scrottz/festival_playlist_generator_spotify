"""Loads festival lineups from CSV or JSON files."""

import os
import csv
import json
import logging
from pathlib import Path


def load_lineup_from_csv(file_path: str) -> list[str]:
    """
    Loads artist names from a CSV file that contains a column 'artist'.

    :param file_path: Relative or absolute path to the CSV file.
    :return: List of artist names.
    """
    logger = logging.getLogger(__name__)
    abs_path = Path(file_path).resolve()

    if not abs_path.exists():
        logger.error(f"Lineup file not found: {abs_path}")
        raise FileNotFoundError(f"Lineup file not found: {abs_path}")

    with abs_path.open(encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        if "artist" not in reader.fieldnames:
            logger.error("CSV must contain an 'artist' column header.")
            raise ValueError("CSV must contain an 'artist' column header.")

        artists = [row["artist"].strip() for row in reader if row.get("artist")]
        logger.info(f"Loaded {len(artists)} artists from CSV → {abs_path}")
        return artists


def load_lineup_from_json(file_path: str) -> list[str]:
    """
    Loads artist names from a JSON file containing either:
        [{"artist": "Name"}, ...] or ["Name", "Other Name", ...]

    :param file_path: Relative or absolute path to the JSON file.
    :return: List of artist names.
    """
    logger = logging.getLogger(__name__)
    abs_path = Path(file_path).resolve()

    if not abs_path.exists():
        logger.error(f"Lineup JSON not found: {abs_path}")
        raise FileNotFoundError(f"Lineup JSON not found: {abs_path}")

    with abs_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        if all(isinstance(entry, dict) and "artist" in entry for entry in data):
            artists = [entry["artist"].strip() for entry in data if entry.get("artist")]
        elif all(isinstance(entry, str) for entry in data):
            artists = [entry.strip() for entry in data if entry]
        else:
            logger.error("JSON must be a list of dicts with 'artist' or list of strings.")
            raise ValueError("Invalid JSON structure for lineup.")
    else:
        logger.error("JSON must contain a list at the root level.")
        raise ValueError("Invalid JSON format.")

    logger.info(f"Loaded {len(artists)} artists from JSON → {abs_path}")
    return artists

def fetch_lineup(file_path: str) -> List[str]:
    """
    Loads a festival lineup from a CSV or JSON file.

    Args:
        file_path (str): Path to the lineup file.

    Returns:
        List[str]: List of artist names.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
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
