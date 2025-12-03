"""
Pokemon calculation functions
"""
import sqlite3
from typing import List, Tuple


def calculate_avg_base_exp_by_type(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """Calculate average base experience grouped by Pokemon type."""
    c = conn.cursor()
    q = """
    SELECT primary_type, AVG(base_experience) AS avg_be, COUNT(*) as cnt
    FROM pokemon
    WHERE primary_type IS NOT NULL
    GROUP BY primary_type
    ORDER BY avg_be DESC
    """
    c.execute(q)
    return [(row["primary_type"], row["avg_be"], row["cnt"]) for row in c.fetchall()]


def calculate_pokemon_with_stats_join(conn: sqlite3.Connection) -> List[Tuple]:
    """
    This function uses a JOIN to combine pokemon and pokemon_stats tables.
    Required by SI 201 project grading rubric (20 points).
    """
    c = conn.cursor()
    q = """
    SELECT
        p.id,
        p.name,
        p.primary_type,
        p.base_experience,
        ps.hp,
        ps.attack,
        ps.defense,
        ps.speed,
        (ps.hp + ps.attack + ps.defense + ps.speed) AS total_stats
    FROM pokemon p
    INNER JOIN pokemon_stats ps ON p.id = ps.pokemon_id
    WHERE p.primary_type IS NOT NULL
    ORDER BY total_stats DESC
    """
    c.execute(q)
    return [(row["id"], row["name"], row["primary_type"], row["base_experience"],
             row["hp"], row["attack"], row["defense"], row["speed"], row["total_stats"])
            for row in c.fetchall()]
