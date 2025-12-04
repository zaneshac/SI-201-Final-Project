"""
Weather calculation functions

STRING-TO-INTEGER MAPPING:
Weather table uses cities_lookup, dates_lookup, and forecasts_lookup tables.
All string values mapped to integers - no duplicate strings stored.
"""
import sqlite3
from typing import List, Tuple


def calculate_temp_variability_by_city(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """
    Calculate temperature difference between high and low per city.

    STRING-TO-INTEGER MAPPING:
    JOINs weather table with cities_lookup table to get city names.
    """
    c = conn.cursor()
    q = """
    SELECT c.city_name, AVG(w.temperature_high) as avg_high, AVG(w.temperature_low) as avg_low, COUNT(*) as cnt
    FROM weather w
    INNER JOIN cities_lookup c ON w.city_id = c.id
    WHERE w.city_id IS NOT NULL
    GROUP BY c.city_name
    """
    c.execute(q)
    results = []
    for row in c.fetchall():
        if row["avg_high"] is None or row["avg_low"] is None:
            continue
        variability = row["avg_high"] - row["avg_low"]
        results.append((row["city_name"], variability, row["cnt"]))
    return results
