"""
Database helper functions for connection and table creation

================================================================================
STRING-TO-INTEGER MAPPING SYSTEM
================================================================================
To satisfy the "no duplicate string data" requirement, we use LOOKUP TABLES
to map ALL repeated strings to unique integers.

TABLE NAMING CONVENTION:
========================
ALL LOOKUP TABLES end with "_lookup" suffix - these store unique strings ONCE
ALL DATA TABLES have simple names - these store only integer references

LOOKUP TABLES (7 total):
  - types_lookup        : Pokemon types ("fire", "water", etc.)
  - artists_lookup      : Spotify artist names
  - cities_lookup       : Weather city names
  - genres_lookup       : Movie genres
  - forecasts_lookup    : Weather forecast descriptions
  - dates_lookup        : Dates (eliminate duplicate date strings)
  - box_office_lookup   : Box office values (eliminate duplicate "$" strings)

DATA TABLES (5 total):
  - pokemon            : Pokemon data (references types_lookup)
  - pokemon_stats      : Pokemon stats (references pokemon)
  - tracks             : Spotify tracks (references artists_lookup)
  - weather            : Weather data (references cities_lookup, forecasts_lookup, dates_lookup)
  - movies             : Movie data (references genres_lookup, box_office_lookup)

All data tables store ONLY integers, no duplicate strings!
================================================================================
"""
import sqlite3
from config.api_keys import DB_PATH


def create_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create a database connection with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_or_create_lookup_id(conn: sqlite3.Connection, table: str, name_column: str, name_value: str) -> int:
    """
    Get existing ID or create new entry in lookup table.

    This function ensures we map strings to integers without duplicates.

    Args:
        conn: Database connection
        table: Lookup table name (e.g., 'types_lookup', 'artists_lookup')
        name_column: Column name for the string (e.g., 'type_name', 'artist_name')
        name_value: The string value to lookup/insert

    Returns:
        Integer ID for the string

    Example:
        type_id = get_or_create_lookup_id(conn, 'types_lookup', 'type_name', 'fire')
        # First call: Creates 'fire' with id=1, returns 1
        # Second call: Finds existing 'fire', returns 1 (no duplicate!)
    """
    if name_value is None:
        return None

    c = conn.cursor()

    # Try to find existing entry
    c.execute(f"SELECT id FROM {table} WHERE {name_column} = ?", (name_value,))
    row = c.fetchone()

    if row:
        return row["id"]

    # Create new entry
    c.execute(f"INSERT INTO {table} ({name_column}) VALUES (?)", (name_value,))
    conn.commit()
    return c.lastrowid


def create_tables(conn: sqlite3.Connection):
    """
    Create all required database tables.

    7 LOOKUP TABLES (store unique strings):
      - types_lookup, artists_lookup, cities_lookup, genres_lookup,
        forecasts_lookup, dates_lookup, box_office_lookup

    5 DATA TABLES (store only integers):
      - pokemon, pokemon_stats, tracks, weather, movies
    """
    c = conn.cursor()

    print("\n" + "="*80)
    print("CREATING DATABASE TABLES")
    print("="*80)

    # ==================== LOOKUP TABLES ====================
    # These tables store actual strings - each string appears EXACTLY ONCE

    print("\nCreating LOOKUP TABLES (store unique strings):")

    c.execute("""
    CREATE TABLE IF NOT EXISTS types_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL UNIQUE
    )
    """)
    print("  ✓ types_lookup - Pokemon types")

    c.execute("""
    CREATE TABLE IF NOT EXISTS artists_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_name TEXT NOT NULL UNIQUE
    )
    """)
    print("  ✓ artists_lookup - Spotify artists")

    c.execute("""
    CREATE TABLE IF NOT EXISTS cities_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT NOT NULL UNIQUE
    )
    """)
    print("  ✓ cities_lookup - Weather cities")

    c.execute("""
    CREATE TABLE IF NOT EXISTS genres_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        genre_name TEXT NOT NULL UNIQUE
    )
    """)
    print("  ✓ genres_lookup - Movie genres")

    c.execute("""
    CREATE TABLE IF NOT EXISTS forecasts_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forecast_description TEXT NOT NULL UNIQUE
    )
    """)
    print("  ✓ forecasts_lookup - Weather forecast descriptions")

    c.execute("""
    CREATE TABLE IF NOT EXISTS dates_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_value TEXT NOT NULL UNIQUE
    )
    """)
    print("  ✓ dates_lookup - Date strings")

    c.execute("""
    CREATE TABLE IF NOT EXISTS box_office_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        box_office_value TEXT NOT NULL UNIQUE
    )
    """)
    print("  ✓ box_office_lookup - Box office revenue strings")

    # ==================== DATA TABLES ====================
    # These tables store ONLY integers (IDs that reference lookup tables)

    print("\nCreating DATA TABLES (store only integer references):")

    c.execute("""
    CREATE TABLE IF NOT EXISTS pokemon (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        base_experience INTEGER,
        height INTEGER,
        weight INTEGER,
        type_id INTEGER,
        FOREIGN KEY(type_id) REFERENCES types_lookup(id)
    )
    """)
    print("  ✓ pokemon - References types_lookup via type_id")

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
    print("  ✓ pokemon_stats - All integer columns")

    c.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        track_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist_id INTEGER NOT NULL,
        popularity INTEGER,
        UNIQUE(title, artist_id),
        FOREIGN KEY(artist_id) REFERENCES artists_lookup(id)
    )
    """)
    print("  ✓ tracks - References artists_lookup via artist_id")

    c.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER NOT NULL,
        date_id INTEGER NOT NULL,
        temperature_high REAL,
        temperature_low REAL,
        wind_speed REAL,
        forecast_id INTEGER,
        UNIQUE(city_id, date_id),
        FOREIGN KEY(city_id) REFERENCES cities_lookup(id),
        FOREIGN KEY(date_id) REFERENCES dates_lookup(id),
        FOREIGN KEY(forecast_id) REFERENCES forecasts_lookup(id)
    )
    """)
    print("  ✓ weather - References cities_lookup, dates_lookup, forecasts_lookup")

    c.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        imdb_id TEXT PRIMARY KEY,
        title TEXT,
        year INTEGER,
        genre_id INTEGER,
        runtime INTEGER,
        imdb_rating REAL,
        box_office_id INTEGER,
        FOREIGN KEY(genre_id) REFERENCES genres_lookup(id),
        FOREIGN KEY(box_office_id) REFERENCES box_office_lookup(id)
    )
    """)
    print("  ✓ movies - References genres_lookup, box_office_lookup")

    conn.commit()

    print("\n" + "="*80)
    print("DATABASE SCHEMA COMPLETE")
    print("="*80)
    print("7 LOOKUP TABLES: Store unique strings (NO DUPLICATES)")
    print("5 DATA TABLES: Store only integer references")
    print("="*80 + "\n")
