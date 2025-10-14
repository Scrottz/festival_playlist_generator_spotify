"""Helper functions for artist lookup and top track retrieval."""

from spotipy import Spotify

def get_artist_id(sp_client: Spotify, name: str) -> str | None:
    """Searches Spotify for an artist by name and returns the ID."""
    result = sp_client.search(q=f"artist:{name}", type="artist", limit=1)
    items = result.get("artists", {}).get("items", [])
    return items[0]["id"] if items else None

def get_top_tracks(sp_client: Spotify, artist_id: str, limit: int = 5) -> list[str]:
    """Returns the IDs of the top tracks for a given artist."""
    tracks = sp_client.artist_top_tracks(artist_id).get("tracks", [])
    return [t["id"] for t in tracks[:limit]]
