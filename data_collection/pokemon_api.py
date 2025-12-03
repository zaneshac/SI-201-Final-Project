"""
PokeAPI data collection module
Author: Zanesha Chowdhury
"""
import requests
import sqlite3
import time
from config.api_keys import POKEAPI_BASE


def already_exists(conn: sqlite3.Connection, table: str, where_clause: str, params=()) -> bool:
    """Check if a record already exists in the database."""
    c = conn.cursor()
    q = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
    c.execute(q, params)
    return c.fetchone() is not None


def fetch_pokemon_up_to_limit(conn: sqlite3.Connection, target_new: int = 25, max_id: int = 151):
    """
    Fetch Pokemon data from PokeAPI (limited to 25 new entries per run).

    Args:
        conn: Database connection
        target_new: Maximum number of new Pokemon to insert (default 25)
        max_id: Maximum Pokemon ID to fetch (default 151 for Gen 1)
    """
    inserted = 0
    c = conn.cursor()
    for pid in range(1, max_id + 1):
        if inserted >= target_new:
            break
        if already_exists(conn, "pokemon", "id = ?", (pid,)):
            continue
        url = f"{POKEAPI_BASE}/pokemon/{pid}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            name = data.get("name")
            base_experience = data.get("base_experience")
            height = data.get("height")
            weight = data.get("weight")
            types = data.get("types", [])
            primary_type = types[0]["type"]["name"] if types else None

            c.execute("""
                INSERT OR IGNORE INTO pokemon (id, name, base_experience, height, weight, primary_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pid, name, base_experience, height, weight, primary_type))

            stats_map = {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])}
            hp = stats_map.get("hp")
            attack = stats_map.get("attack")
            defense = stats_map.get("defense")
            speed = stats_map.get("speed")

            c.execute("""
                INSERT OR IGNORE INTO pokemon_stats (pokemon_id, hp, attack, defense, speed)
                VALUES (?, ?, ?, ?, ?)
            """, (pid, hp, attack, defense, speed))

            conn.commit()
            inserted += 1
            print(f"[PokeAPI] Inserted {pid} {name} ({inserted}/{target_new})")
            time.sleep(0.15)
        except Exception as e:
            print("Error:", e)
    print(f"[PokeAPI] Finished run: inserted {inserted} new rows.")
