"""
Spotify calculation functions

STRING-TO-INTEGER MAPPING:
All calculations JOIN with artists_lookup table to retrieve artist names.
Main tracks table stores only artist_id integers.
"""
import sqlite3
from typing import List, Tuple


def calculate_avg_popularity_per_artist(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """
    Calculate average track popularity per artist.

    STRING-TO-INTEGER MAPPING:
    JOINs tracks table with artists_lookup table to get artist names.
    """
    c = conn.cursor()
    q = """
    SELECT a.artist_name, AVG(t.popularity) as avg_pop, COUNT(*) as cnt
    FROM tracks t
    INNER JOIN artists_lookup a ON t.artist_id = a.id
    WHERE t.artist_id IS NOT NULL
    GROUP BY a.artist_name
    ORDER BY avg_pop DESC
    """
    c.execute(q)
    return [(row["artist_name"], row["avg_pop"], row["cnt"]) for row in c.fetchall()]
