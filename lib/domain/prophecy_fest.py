import requests
import re
import logging

def fetch_lineup(url: str = "https://fest.prophecy.de/programme/") -> list[str]:
    """
    Scrapes the Prophecy Fest lineup page.

    :param url: URL of the Prophecy Fest lineup page.
    :return: List of artist names (strings).
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching Prophecy Fest lineup from {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []

    html = response.text
    pattern = r'<div class="et_pb_text_inner">\s*<h3>\s*(.*?)\s*</h3>\s*</div>'
    artists = [a.strip() for a in re.findall(pattern, html, re.IGNORECASE | re.DOTALL) if a.strip()]

    # Remove entries with line breaks (multiple bands or info text)
    artists = [a for a in artists if "\n" not in a]

    # Remove last entry if it contains "PROPHECY FEST" (info text)
    if artists and "PROPHECY FEST" in artists[-1].upper():
        artists.pop()

    artists = sorted(set(artists))
    logger.info(f"Fetched {len(artists)} artists from Prophecy Fest page.")
    return artists

if __name__ == "__main__":
    bands = fetch_lineup()
    print(f"Found {len(bands)} bands:")
    for b in bands:
        print(f" - {b}")
