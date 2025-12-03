"""
Spotify calculation functions
"""
import sqlite3
from typing import List, Tuple


def calculate_avg_popularity_per_artist(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """Calculate average track popularity per artist."""
    c = conn.cursor()
    q = """
    SELECT artist, AVG(popularity) as avg_pop, COUNT(*) as cnt
    FROM tracks
    WHERE artist IS NOT NULL
    GROUP BY artist
    ORDER BY avg_pop DESC
    """
    c.execute(q)
    return [(row["artist"], row["avg_pop"], row["cnt"]) for row in c.fetchall()]
