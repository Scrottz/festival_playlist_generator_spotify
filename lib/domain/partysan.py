"""Scraper for Party.San Open Air lineup using BeautifulSoup."""

import requests
from bs4 import BeautifulSoup
import logging


def fetch_lineup(url: str = "https://www.party-san.de/bands-2026") -> list[str]:
    """
    Scrapes the current Party.San lineup page.

    :param url: URL of the Party.San lineup page.
    :return: List of artist names (strings).
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching Party.San lineup from {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Each band name is inside <div class="card-body"><h3><a>NAME</a></h3></div>
    band_links = soup.select("div.card-body h3 a")

    lineup = []
    for link in band_links:
        name = link.get_text(strip=True)
        if name and len(name) > 1:
            lineup.append(name)

    # Fallback if nothing found (site structure changed)
    if not lineup:
        logger.warning("No bands found with primary selector, trying fallback.")
        fallback_links = soup.find_all("a", href=True)
        for a in fallback_links:
            if "/banddetail/" in a["href"]:
                text = a.get_text(strip=True)
                if text and len(text) > 1:
                    lineup.append(text)

    lineup = sorted(set(lineup))
    logger.info(f"Fetched {len(lineup)} artists from Party.San page.")
    return lineup


if __name__ == "__main__":
    # For quick manual test
    bands = fetch_lineup()
    print(f"Found {len(bands)} bands:")
    for b in bands:
        print(f" - {b}")
