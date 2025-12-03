"""
Weather calculation functions
"""
import sqlite3
from typing import List, Tuple


def calculate_temp_variability_by_city(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """Calculate temperature variability (difference between high and low) per city."""
    c = conn.cursor()
    q = """
    SELECT city, AVG(temperature_high) as avg_high, AVG(temperature_low) as avg_low, COUNT(*) as cnt
    FROM weather
    WHERE city IS NOT NULL
    GROUP BY city
    """
    c.execute(q)
    results = []
    for row in c.fetchall():
        if row["avg_high"] is None or row["avg_low"] is None:
            continue
        variability = row["avg_high"] - row["avg_low"]
        results.append((row["city"], variability, row["cnt"]))
    return results
