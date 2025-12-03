"""
OMDb API data collection module
Author: Ariana Namei
"""
import requests
import sqlite3
import time
from typing import List
from config.api_keys import OMDB_BASE, OMDB_API_KEY


def already_exists(conn: sqlite3.Connection, table: str, where_clause: str, params=()) -> bool:
    """Check if a record already exists in the database."""
    c = conn.cursor()
    q = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
    c.execute(q, params)
    return c.fetchone() is not None


def fetch_movies_by_title_list(conn: sqlite3.Connection, title_list: List[str], max_new: int = 25):
    """
    Fetch movie data from OMDb API (limited to 25 new entries per run).

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
            genre = data.get("Genre")
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
            box_office = data.get("BoxOffice")
            c.execute("""
                INSERT OR IGNORE INTO movies (imdb_id, title, year, genre, runtime, imdb_rating, box_office)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (imdb_id, title_ret, year, genre, runtime, imdb_rating, box_office))
            conn.commit()
            inserted += 1
            print(f"[OMDb] Inserted {title_ret} ({inserted}/{max_new})")
            time.sleep(0.2)
        except Exception as e:
            print("OMDb error:", e)
    print(f"[OMDb] Finished run: inserted {inserted} new movies.")
