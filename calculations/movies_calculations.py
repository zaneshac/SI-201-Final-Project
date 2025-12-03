"""
Movies calculation functions
"""
import sqlite3
import math
from typing import Optional


def calculate_runtime_rating_correlation(conn: sqlite3.Connection) -> Optional[float]:
    """Calculate correlation coefficient between movie runtime and IMDb rating."""
    c = conn.cursor()
    q = """
    SELECT runtime, imdb_rating FROM movies
    WHERE runtime IS NOT NULL AND imdb_rating IS NOT NULL
    """
    c.execute(q)
    rows = c.fetchall()
    if len(rows) < 2:
        return None
    runtimes = [r["runtime"] for r in rows]
    ratings = [r["imdb_rating"] for r in rows]
    n = len(runtimes)
    mean_x = sum(runtimes) / n
    mean_y = sum(ratings) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(runtimes, ratings))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in runtimes))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ratings))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)
