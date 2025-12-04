"""
OMDb API data collection module
Author: Ariana Namei

STRING-TO-INTEGER MAPPING:
- Movie genres mapped to integers using genres_lookup table
- Box office values mapped to integers using box_office_lookup table
This eliminates ALL duplicate strings in movie data.
Note: Movies may have multiple genres (e.g., "Action, Drama"), we store the full string
as a single lookup entry to maintain the original genre combination.
"""
import requests
import sqlite3
import time
from typing import List
from config.api_keys import OMDB_BASE, OMDB_API_KEY
from database.db_helper import get_or_create_lookup_id


def already_exists(conn: sqlite3.Connection, table: str, where_clause: str, params=()) -> bool:
    """Check if a record already exists in the database."""
    c = conn.cursor()
    q = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
    c.execute(q, params)
    return c.fetchone() is not None


def fetch_movies_by_title_list(conn: sqlite3.Connection, title_list: List[str], max_new: int = 25):
    """
    Fetch movie data from OMDb API (limited to 25 new entries per run).

    STRING-TO-INTEGER MAPPING:
    - Movie genres: "Action, Sci-Fi" -> genre_id=1 (stored in genres_lookup)
    - Box office: "$50.0M" -> box_office_id=1 (stored in box_office_lookup)
    Same value reuses the same ID (no duplicates).

    Args:
        conn: Database connection
        title_list: List of movie titles to fetch
        max_new: Maximum number of new movies to insert (default 25)
    """
    if not OMDB_API_KEY:
        print("OMDB_API_KEY not set. Skipping OMDb fetch.")
        return
    inserted = 0
    c = conn.cursor()
    for title in title_list:
        if inserted >= max_new:
            break
        params = {"t": title, "apikey": OMDB_API_KEY}
        try:
            resp = requests.get(OMDB_BASE, params=params, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            if data.get("Response") == "False":
                continue
            imdb_id = data.get("imdbID")
            if not imdb_id or already_exists(conn, "movies", "imdb_id = ?", (imdb_id,)):
                continue
            title_ret = data.get("Title")
            year = None
            try:
                year = int(data.get("Year", "").split("–")[0]) if data.get("Year") else None
            except:
                year = None
            genre_str = data.get("Genre")
            box_office_str = data.get("BoxOffice")

            # Convert genre and box_office strings to integer IDs using lookup tables
            genre_id = get_or_create_lookup_id(conn, 'genres_lookup', 'genre_name', genre_str)
            box_office_id = get_or_create_lookup_id(conn, 'box_office_lookup', 'box_office_value', box_office_str)

            runtime = None
            rt = data.get("Runtime")
            try:
                runtime = int(rt.replace(" min", "")) if rt and "min" in rt else None
            except:
                runtime = None
            imdb_rating = None
            try:
                imdb_rating = float(data.get("imdbRating")) if data.get("imdbRating") and data.get("imdbRating") != "N/A" else None
            except:
                imdb_rating = None

            c.execute("""
                INSERT OR IGNORE INTO movies (imdb_id, title, year, genre_id, runtime, imdb_rating, box_office_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (imdb_id, title_ret, year, genre_id, runtime, imdb_rating, box_office_id))
            conn.commit()
            inserted += 1
            print(f"[OMDb] Inserted {title_ret} (genre_id={genre_id}, box_office_id={box_office_id}) ({inserted}/{max_new})")
            time.sleep(0.2)
        except Exception as e:
            print("OMDb error:", e)
    print(f"[OMDb] Finished run: inserted {inserted} new movies.")
