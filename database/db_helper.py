"""
Database helper functions for connection and table creation
"""
import sqlite3
from config.api_keys import DB_PATH


def create_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create a database connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection):
    """Create all required database tables."""
    c = conn.cursor()

    # Pokémon tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS pokemon (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        base_experience INTEGER,
        height INTEGER,
        weight INTEGER,
        primary_type TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS pokemon_stats (
        pokemon_id INTEGER PRIMARY KEY,
        hp INTEGER,
        attack INTEGER,
        defense INTEGER,
        speed INTEGER,
        FOREIGN KEY(pokemon_id) REFERENCES pokemon(id)
    )
    """)

    # Spotify tracks table
    c.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        track_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT,
        popularity INTEGER,
        UNIQUE(title, artist)
    )
    """)

    # Weather table
    c.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        date TEXT,
        temperature_high REAL,
        temperature_low REAL,
        wind_speed REAL,
        short_forecast TEXT,
        UNIQUE(city, date)
    )
    """)

    # Movies table
    c.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        imdb_id TEXT PRIMARY KEY,
        title TEXT,
        year INTEGER,
        genre TEXT,
        runtime INTEGER,
        imdb_rating REAL,
        box_office TEXT
    )
    """)

    conn.commit()
