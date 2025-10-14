"""Handles Spotify API authentication and client creation with persistent caching."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from conf.config import SPOTIFY_SCOPES, SPOTIFY_REDIRECT_URI
from lib.common.logger import setup_logger


# ---------------------------------------------------------------------------
# Load .env exactly once from the project root (two levels up from this file)
# ---------------------------------------------------------------------------
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)


def create_spotify_client(cache_path: str = ".cache-spotify") -> Spotify:
    """
    Creates and returns an authenticated Spotify client instance.

    :param cache_path: Path for the token cache file.
    :return: Authenticated spotipy.Spotify instance.
    """
    setup_logger(level="INFO")  # ensures consistent logging across modules
    logger = logging.getLogger(__name__)
    logger.info("Initializing Spotify client...")

    # Environment variables (already loaded by load_dotenv above)
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", SPOTIFY_REDIRECT_URI)

    if not all([client_id, client_secret, redirect_uri]):
        logger.error("Missing Spotify credentials or redirect URI. Check your environment variables.")
        raise EnvironmentError("Spotify credentials not configured properly.")

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=" ".join(SPOTIFY_SCOPES),
        cache_path=cache_path,
        open_browser=True,
    )

    sp = Spotify(auth_manager=auth_manager)
    user = sp.current_user()
    logger.info(f"Authenticated as: {user.get('display_name')} ({user.get('id')})")

    return sp


if __name__ == "__main__":
    # simple test run: shows your user info when executed directly
    sp = create_spotify_client()
    print(sp.current_user())
