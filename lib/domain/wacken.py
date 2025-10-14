"""
Fetches the official Wacken Open Air lineup from the 2026 JSON feed.

This module loads the JSON file that powers the Wacken lineup page and extracts
all band names from it. It is used as the data foundation for playlist generation
in the festival_playlist_generator_spotify project.

Example:
    >>> python3 -m lib.domain.wacken
"""

import requests, json
from lib.common.logger import setup_logger, get_logger

# Initialize logger early
setup_logger(level="INFO", log_dir="logs")
logger = get_logger(__name__)

def fetch_wacken_lineup() -> list[str]:
    """
    Fetches and parses the official Wacken lineup JSON.

    :returns: List of band names.
    :rtype: list[str]
    :raises requests.exceptions.RequestException: If the JSON could not be fetched.
    """
    url = "https://www.wacken.com/fileadmin/Json/bandlist-concert.json"
    logger.info(f"Fetching Wacken lineup from {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Wacken lineup: {e}")
        return []

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return []

    bands = [entry["title"].strip() for entry in data if "title" in entry]
    logger.info(f"Successfully parsed {len(bands)} bands from Wacken JSON")

    # Optional preview
    if bands:
        preview = "\n".join(f" - {band}" for band in bands[:10])
        logger.info(f"Sample bands:\n{preview}")

    return bands


if __name__ == "__main__":
    bands = fetch_wacken_lineup()
    print(f"\nFound {len(bands)} bands:\n")
    for band in bands:
        print(f" - {band}")
