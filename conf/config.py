"""Configuration constants for the Spotify Festival Playlist Generator."""

# Spotify OAuth settings
SPOTIFY_SCOPES = ["playlist-modify-public", "playlist-modify-private"]
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

# General project settings
DEFAULT_TOP_N = 5
DEFAULT_LOG_LEVEL = "INFO"
DATA_DIR = "res/lineups"
PLAYLIST_DIR = "res/playlists"
LOG_DIR = "logs"