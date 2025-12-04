"""
Spotify API data collection module
Author: Kevin Zang

STRING-TO-INTEGER MAPPING:
Artist names are mapped to integers using the artists_lookup table.
This eliminates duplicate artist name strings in the database.
"""
import sqlite3
import time
from typing import List
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config.api_keys import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET
from database.db_helper import get_or_create_lookup_id


# Initialize Spotify client
spotify_client = None
if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
    auth_manager = SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET
    )
    spotify_client = spotipy.Spotify(auth_manager=auth_manager)
else:
    print("Spotify credentials not set. Skipping Spotify fetch.")


def fetch_tracks_for_artist_list(conn: sqlite3.Connection, artist_list: List[str], max_new: int = 25):
    """
    Fetch Spotify tracks for a list of artists (limited to 25 new entries per run).

    STRING-TO-INTEGER MAPPING:
    Artist names are converted to integer IDs using artists_lookup table.
    Example: "Taylor Swift" -> 1, "Drake" -> 2 (first occurrence gets next ID)
    If same artist appears in multiple tracks, same ID is reused.

    Args:
        conn: Database connection
        artist_list: List of artist names to search for
        max_new: Maximum number of new tracks to insert (default 25)
    """
    if spotify_client is None:
        print("Spotify client not initialized. Skipping track fetch.")
        return

    c = conn.cursor()
    inserted = 0

    for artist_name in artist_list:
        if inserted >= max_new:
            break
        try:
            results = spotify_client.search(q=f"artist:{artist_name}", type="track", limit=10)
            tracks = results.get("tracks", {}).get("items", [])
            for track in tracks:
                if inserted >= max_new:
                    break
                title = track["name"]
                artist_names = ", ".join([a["name"] for a in track["artists"]])
                popularity = track.get("popularity") or 0

                # Convert artist string to integer ID using lookup table
                artist_id = get_or_create_lookup_id(conn, 'artists_lookup', 'artist_name', artist_names)

                try:
                    c.execute("""
                        INSERT OR IGNORE INTO tracks (title, artist_id, popularity)
                        VALUES (?, ?, ?)
                    """, (title, artist_id, popularity))
                    if c.rowcount:
                        conn.commit()
                        inserted += 1
                        print(f"[Spotify] Inserted track: {title} - {artist_names} (artist_id={artist_id}) ({inserted}/{max_new})")
                except Exception as e:
                    print("DB insert error (tracks):", e)
        except Exception as e:
            print("Spotify API error:", e)
        time.sleep(0.2)
    print(f"[Spotify] Finished run: inserted {inserted} new tracks.")
