# Spotify Festival Playlist Generator

## Description
Automates the creation of festival playlists using the Spotify API.
You can choose between different festivals (currently: Wacken and Partysan).
For each festival, the performing bands are loaded and the top 5 songs of each band (according to Spotify) are added to a playlist.

## Features
- Load festival lineups from CSV/Online Crawling files
- Fetch top tracks for each artist
- Create and update Spotify playlists
- Export playlist data to various formats

## Project Structure

- scr/
  - spotify_festival_playlist_generator.py  
    Main script: Generates and updates festival playlists on Spotify.
  - lineup_fetcher.py  
    Fetches festival lineups from online sources.
- lib/
  - common/
    - artist_utils.py  
      Helper functions for finding artist IDs and fetching top tracks.
    - export_utils.py  
      Functions to export playlist data to various formats.
    - lineup_loader.py  
      Loads and processes festival lineups from CSV files.
    - logger.py  
      Initializes and configures logging for the project.
    - playlist_manager.py  
      Manages creation, updating, and deletion of Spotify playlists.
    - spotify_client.py  
      Provides functions to connect and interact with the Spotify API.
    - utils.py  
      General utility functions used across the project.
  - domain/
    - metal_in_sachsen.py  
      Festival-specific logic for "Metal in Sachsen".
    - partysan.py  
      Festival-specific logic for "Partysan".
    - wacken.py  
      Festival-specific logic for "Wacken".
- conf/
  - config.py  
    Configuration settings for the project.
- logs/
  - spotify_festival.log  
    Log file for Spotify-related events.
- res/
  - lineups/
  - playlists/
- README.md  
  Project description and instructions.
- pyproject.toml  
  Project metadata and dependencies.
- LICENSE  
  License information.

## Installation

- Python >= 3.10 required
- Install dependencies via pip:
  `pip install .`

## Usage

```bash
# Show help
python scr/lineup_fetcher.py -h

# Example usage
python scr/lineup_fetcher.py --festival partysan wacken --year 2026 --export --generate_playlist --delete_old_playlists
