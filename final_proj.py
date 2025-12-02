# Collaborator Names: (Zanesha Chowdhury - 10440553), (Ariana Namei - ), (Kevin Zang - )
# Used ChatGPT for syntax, debugging, and pointing out errors. 
# Zanesha wrote functions for PokéAPI
# Ariana wrote functions for Word Cloud API
# Kevin wrote functions for Ksoft Lyrics API and Jikan API

import os
import sqlite3
import requests
import time
from typing import List, Optional, Dict, Any, Tuple
import math

# Visualization
import matplotlib.pyplot as plt

DB_PATH = "si201_project.db"

# API keys (set as environment variables)
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "664d8386")  # e.g., "your_omdb_key"
KSOFT_API_KEY = os.getenv("KSOFT_API_KEY", "")  # e.g., "your_ksoft_key"

# ----------- Database schema & helper functions -------------


def create_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection):
    """
    Create the tables described in the project plan.
    - pokemon and pokemon_stats share an integer key (pokemon.id -> pokemon_stats.pokemon_id)
    - songs, weather, movies tables
    """
    c = conn.cursor()

    # Pokemon primary table
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS pokemon (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        base_experience INTEGER,
        height INTEGER,
        weight INTEGER,
        primary_type TEXT
    )
    """
    )

    # Pokemon stats referencing pokemon.id
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS pokemon_stats (
        pokemon_id INTEGER PRIMARY KEY,
        hp INTEGER,
        attack INTEGER,
        defense INTEGER,
        speed INTEGER,
        FOREIGN KEY(pokemon_id) REFERENCES pokemon(id)
    )
    """
    )

    # Songs table (lyrics)
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS songs (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        artist TEXT,
        lyrics_text TEXT,
        word_count INTEGER,
        UNIQUE(title, artist)
    )
    """
    )

    # Weather table
    c.execute(
        """
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
    """
    )

    # Movies table
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS movies (
        imdb_id TEXT PRIMARY KEY,
        title TEXT,
        year INTEGER,
        genre TEXT,
        runtime INTEGER,
        imdb_rating REAL,
        box_office TEXT
    )
    """
    )

    conn.commit()


# ------------- Helper: limit new inserts per run ----------------

def rows_count(conn: sqlite3.Connection, table: str) -> int:
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table}")
    return c.fetchone()[0]


def already_exists(conn: sqlite3.Connection, table: str, where_clause: str, params=()) -> bool:
    c = conn.cursor()
    q = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
    c.execute(q, params)
    return c.fetchone() is not None


# ----------------- PokeAPI functions ------------------------

POKEAPI_BASE = "https://pokeapi.co/api/v2"


def fetch_pokemon_batch(conn: sqlite3.Connection, start_id: int, end_id: int):
    """
    Fetch Pokemon by numeric ID range inclusive and insert into DB.
    Use this to fetch small batches (<= 25) per run.
    Example: fetch_pokemon_batch(conn, 1, 25)
    """
    c = conn.cursor()
    for pid in range(start_id, end_id + 1):
        # Check if this pokemon id already in DB
        if already_exists(conn, "pokemon", "id = ?", (pid,)):
            continue
        url = f"{POKEAPI_BASE}/pokemon/{pid}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"pokemon {pid} fetch failed: {resp.status_code}")
                continue
            data = resp.json()
            name = data.get("name")
            base_experience = data.get("base_experience")
            height = data.get("height")
            weight = data.get("weight")
            types = data.get("types", [])
            primary_type = types[0]["type"]["name"] if types else None

            # insert into pokemon
            c.execute(
                """
                INSERT OR IGNORE INTO pokemon (id, name, base_experience, height, weight, primary_type)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pid, name, base_experience, height, weight, primary_type),
            )

            # Stats: find hp, attack, defense, speed
            stats_map = {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])}
            hp = stats_map.get("hp")
            attack = stats_map.get("attack")
            defense = stats_map.get("defense")
            speed = stats_map.get("speed")

            c.execute(
                """
                INSERT OR IGNORE INTO pokemon_stats (pokemon_id, hp, attack, defense, speed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pid, hp, attack, defense, speed),
            )

            conn.commit()
            print(f"Inserted pokemon {pid} - {name}")
            time.sleep(0.2)  # small delay to be polite
        except Exception as e:
            print(f"Error fetching pokemon {pid}: {e}")


def fetch_pokemon_up_to_limit(conn: sqlite3.Connection, target_new: int = 25, max_id: int = 151):
    """
    Fetch up to `target_new` new Pokemon. We will scan IDs from 1..max_id and insert up to target_new.
    Use multiple runs to get to >=100 rows.
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

            c.execute(
                """
                INSERT OR IGNORE INTO pokemon (id, name, base_experience, height, weight, primary_type)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pid, name, base_experience, height, weight, primary_type),
            )

            stats_map = {s["stat"]["name"]: s["base_stat"] for s in data.get("stats", [])}
            hp = stats_map.get("hp")
            attack = stats_map.get("attack")
            defense = stats_map.get("defense")
            speed = stats_map.get("speed")

            c.execute(
                """
                INSERT OR IGNORE INTO pokemon_stats (pokemon_id, hp, attack, defense, speed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pid, hp, attack, defense, speed),
            )

            conn.commit()
            inserted += 1
            print(f"[PokeAPI] Inserted {pid} {name} ({inserted}/{target_new})")
            time.sleep(0.15)
        except Exception as e:
            print("Error:", e)
    print(f"[PokeAPI] Finished run: inserted {inserted} new rows.")


# ----------------- KSoft Lyrics functions ------------------------
# NOTE: KSoft requires an API key. The actual endpoint and parameters might vary;
# adapt as needed per the KSoft docs.

KSOFT_BASE = "https://api.ksoft.si"

def fetch_lyrics_for_artist_list(conn: sqlite3.Connection, artist_list: List[str], max_new: int = 25):
    """
    Fetch lyrics for songs by artists in `artist_list`. Insert up to `max_new` new songs.
    This is a simple approach: iterate artists and request a search for their songs.
    Some artists may have many songs; adapt logic if endpoint supports paging.
    """
    if not KSOFT_API_KEY:
        print("KSOFT_API_KEY not set. Skipping lyrics fetch.")
        return

    headers = {"Authorization": f"Bearer {KSOFT_API_KEY}"}
    inserted = 0
    c = conn.cursor()

    for artist in artist_list:
        if inserted >= max_new:
            break
        # Example search endpoint: /lyrics/search?q=artist%20name  (check docs)
        params = {"q": artist, "limit": 5}  # small limit per artist
        try:
            resp = requests.get(f"{KSOFT_BASE}/v1/lyrics/search", headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"KSoft search failed for {artist}: {resp.status_code}")
                continue
            data = resp.json()
            results = data.get("data", []) if isinstance(data, dict) else data
            for item in results:
                if inserted >= max_new:
                    break
                title = item.get("title") or item.get("song")
                artist_name = item.get("artist") or artist
                lyrics_text = item.get("lyrics") or item.get("text") or ""
                word_count = len(lyrics_text.split()) if lyrics_text else 0

                try:
                    c.execute(
                        """
                        INSERT OR IGNORE INTO songs (title, artist, lyrics_text, word_count)
                        VALUES (?, ?, ?, ?)
                        """,
                        (title, artist_name, lyrics_text, word_count),
                    )
                    if c.rowcount:
                        inserted += 1
                        conn.commit()
                        print(f"[KSoft] Inserted song: {title} - {artist_name} ({inserted}/{max_new})")
                except Exception as e:
                    print("DB insert error (songs):", e)
            time.sleep(0.2)
        except Exception as e:
            print("KSoft API error:", e)

    print(f"[KSoft] Finished run: inserted {inserted} new songs.")


# ---------------- Weather.gov functions -------------------
# We'll use a simple approach: for a given city we map to a lat/lon (hardcoded small set)
# then call the NWS gridpoints API to get daily forecasts.
# For more cities, extend the CITY_COORDS map or use a geocoding API.

CITY_COORDS = {
    "Ann Arbor, MI": (42.2808, -83.7430),
    "Detroit, MI": (42.3314, -83.0458),
    "Chicago, IL": (41.8781, -87.6298),
    "New York, NY": (40.7128, -74.0060),
    "Los Angeles, CA": (34.0522, -118.2437),
}


def fetch_weather_for_cities(conn: sqlite3.Connection, cities: List[str], max_new_per_run: int = 25):
    """
    Fetch simple forecast items for supplied cities. Insert up to max_new_per_run rows overall.
    Uses the NWS API: /points/{lat},{lon} -> gridpoints -> forecast
    """
    base = "https://api.weather.gov"
    headers = {"User-Agent": "SI201-Project (student@example.edu)"}  # replace contact info if needed

    inserted = 0
    c = conn.cursor()

    for city in cities:
        if inserted >= max_new_per_run:
            break
        if city not in CITY_COORDS:
            print(f"No coordinates for {city}; skipping.")
            continue
        lat, lon = CITY_COORDS[city]
        try:
            # Get gridpoint info
            points_url = f"{base}/points/{lat},{lon}"
            r = requests.get(points_url, headers=headers, timeout=10)
            if r.status_code != 200:
                print(f"Points request failed for {city}: {r.status_code}")
                continue
            points = r.json()
            grid = points.get("properties", {}).get("gridId")
            grid_x = points.get("properties", {}).get("gridX")
            grid_y = points.get("properties", {}).get("gridY")
            if not (grid and grid_x is not None and grid_y is not None):
                print(f"Grid info missing for {city}")
                continue
            forecast_url = f"{base}/gridpoints/{grid}/{grid_x},{grid_y}/forecast"
            fr = requests.get(forecast_url, headers=headers, timeout=10)
            if fr.status_code != 200:
                print(f"Forecast request failed for {city}: {fr.status_code}")
                continue
            forecast = fr.json()
            periods = forecast.get("properties", {}).get("periods", [])
            # Insert each period (daily / night) as separate rows; to reach 100 rows across cities.
            for p in periods:
                if inserted >= max_new_per_run:
                    break
                date = p.get("startTime", "").split("T")[0]
                temp = p.get("temperature")  # this is the temp for period
                short_forecast = p.get("shortForecast")
                wind_speed = p.get("windSpeed", None)

                # We don't always have high/low mapping in period; store temp in both fields
                temperature_high = temp
                temperature_low = temp

                # Unique constraint city+date avoids duplicates
                try:
                    c.execute(
                        """
                        INSERT OR IGNORE INTO weather (city, date, temperature_high, temperature_low, wind_speed, short_forecast)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (city, date, temperature_high, temperature_low, wind_speed, short_forecast),
                    )
                    if c.rowcount:
                        conn.commit()
                        inserted += 1
                        print(f"[Weather] Inserted {city} {date} ({inserted}/{max_new_per_run})")
                except Exception as e:
                    print("DB error (weather)", e)
            time.sleep(0.25)
        except Exception as e:
            print("Weather API error:", e)
    print(f"[Weather] Finished run: inserted {inserted} new rows.")


# ----------------- OMDb functions ------------------------

OMDB_BASE = "http://www.omdbapi.com/"


def fetch_movies_by_title_list(conn: sqlite3.Connection, title_list: List[str], max_new: int = 25):
    """
    For each title in title_list, query OMDb for details and insert into movies table.
    Requires OMDB_API_KEY set in environment.
    """
    if not OMDB_API_KEY:
        print("OMDB_API_KEY not set. Skipping OMDb fetch.")
        return

    inserted = 0
    c = conn.cursor()
    for title in title_list:
        if inserted >= max_new:
            break
        # First check if we already have this title
        # For uniqueness use title+year would be ideal, but we used imdb_id as pk
        params = {"t": title, "apikey": OMDB_API_KEY}
        try:
            resp = requests.get(OMDB_BASE, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"OMDb fetch failed for {title}: {resp.status_code}")
                continue
            data = resp.json()
            if data.get("Response") == "False":
                print(f"OMDb no data for {title}: {data.get('Error')}")
                continue

            imdb_id = data.get("imdbID")
            if not imdb_id:
                continue
            # Check existing by imdb_id
            if already_exists(conn, "movies", "imdb_id = ?", (imdb_id,)):
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

            c.execute(
                """
                INSERT OR IGNORE INTO movies (imdb_id, title, year, genre, runtime, imdb_rating, box_office)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (imdb_id, title_ret, year, genre, runtime, imdb_rating, box_office),
            )
            conn.commit()
            inserted += 1
            print(f"[OMDb] Inserted {title_ret} ({inserted}/{max_new})")
            time.sleep(0.2)
        except Exception as e:
            print("OMDb error:", e)
    print(f"[OMDb] Finished run: inserted {inserted} new movies.")


# ----------------- Calculations ------------------------

def calculate_avg_base_exp_by_type(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """
    Returns list of tuples: (type, avg_base_exp, count)
    """
    c = conn.cursor()
    q = """
    SELECT primary_type, AVG(base_experience) AS avg_be, COUNT(*) as cnt
    FROM pokemon
    WHERE primary_type IS NOT NULL
    GROUP BY primary_type
    ORDER BY avg_be DESC
    """
    c.execute(q)
    results = [(row["primary_type"], row["avg_be"], row["cnt"]) for row in c.fetchall()]
    return results


def calculate_avg_lyrics_wordcount_per_artist(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """
    Returns (artist, avg_word_count, count_of_songs)
    """
    c = conn.cursor()
    q = """
    SELECT artist, AVG(word_count) as avg_wc, COUNT(*) as cnt
    FROM songs
    WHERE artist IS NOT NULL
    GROUP BY artist
    ORDER BY avg_wc DESC
    """
    c.execute(q)
    results = [(row["artist"], row["avg_wc"], row["cnt"]) for row in c.fetchall()]
    return results


def calculate_temp_variability_by_city(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
    """
    For each city: compute average(high) - average(low). Return (city, variability, count)
    """
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


def calculate_runtime_rating_correlation(conn: sqlite3.Connection) -> Optional[float]:
    """
    Compute Pearson correlation coefficient between runtime and imdb_rating for movies that have both.
    Return r or None if insufficient data.
    """
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
    # compute Pearson r
    n = len(runtimes)
    mean_x = sum(runtimes) / n
    mean_y = sum(ratings) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(runtimes, ratings))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in runtimes))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ratings))
    if den_x == 0 or den_y == 0:
        return None
    r = num / (den_x * den_y)
    return r


# ----------------- Visualizations ------------------------

def visualize_avg_base_exp_by_type(conn: sqlite3.Connection, top_n: int = 12):
    data = calculate_avg_base_exp_by_type(conn)
    if not data:
        print("No data to plot for Pokemon.")
        return
    types = [d[0] for d in data][:top_n]
    avg_be = [d[1] for d in data][:top_n]
    counts = [d[2] for d in data][:top_n]

    plt.figure(figsize=(10, 6))
    plt.bar(types, avg_be)
    plt.title("Average Base Experience by Pokémon Primary Type")
    plt.xlabel("Type")
    plt.ylabel("Average Base Experience")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def visualize_temp_high_low_by_city(conn: sqlite3.Connection):
    c = conn.cursor()
    q = """
    SELECT city, AVG(temperature_high) as avg_high, AVG(temperature_low) as avg_low
    FROM weather
    GROUP BY city
    """
    c.execute(q)
    rows = c.fetchall()
    if not rows:
        print("No weather data to plot.")
        return
    cities = [r["city"] for r in rows]
    highs = [r["avg_high"] for r in rows]
    lows = [r["avg_low"] for r in rows]

    x = range(len(cities))
    plt.figure(figsize=(10, 6))
    plt.plot(x, highs, marker="o", label="Avg High")
    plt.plot(x, lows, marker="o", label="Avg Low")
    plt.xticks(x, cities, rotation=45)
    plt.ylabel("Temperature")
    plt.title("Average High and Low Temperatures by City")
    plt.legend()
    plt.tight_layout()
    plt.show()


def visualize_runtime_vs_rating(conn: sqlite3.Connection):
    c = conn.cursor()
    q = """
    SELECT runtime, imdb_rating, title FROM movies
    WHERE runtime IS NOT NULL AND imdb_rating IS NOT NULL
    """
    c.execute(q)
    rows = c.fetchall()
    if not rows:
        print("No movie data to plot.")
        return
    runtimes = [r["runtime"] for r in rows]
    ratings = [r["imdb_rating"] for r in rows]
    titles = [r["title"] for r in rows]

    plt.figure(figsize=(8, 6))
    plt.scatter(runtimes, ratings)
    plt.xlabel("Runtime (minutes)")
    plt.ylabel("IMDb Rating")
    plt.title("Movie Runtime vs. IMDb Rating")
    plt.tight_layout()
    plt.show()


def visualize_avg_lyrics_wordcount(conn: sqlite3.Connection, top_n: int = 12):
    data = calculate_avg_lyrics_wordcount_per_artist(conn)
    if not data:
        print("No lyrics data to plot.")
        return
    artists = [d[0] for d in data][:top_n]
    avg_wc = [d[1] for d in data][:top_n]

    plt.figure(figsize=(10, 6))
    y_pos = range(len(artists))
    plt.barh(y_pos, avg_wc)
    plt.yticks(y_pos, artists)
    plt.xlabel("Average Word Count")
    plt.title("Average Lyrics Word Count per Artist")
    plt.tight_layout()
    plt.show()


# ----------------- Example main / run routine ------------------------

def example_run():
    """
    Example sequence to initialize DB and run a few fetch/compute/visualize steps.
    Modify the lists and parameters as your team decides.
    """
    conn = create_connection()
    create_tables(conn)

    # === POKEMON ===
    # Insert up to 25 new pokemons from the first 151
    print("Fetching Pokemon (up to 25 new)...")
    fetch_pokemon_up_to_limit(conn, target_new=25, max_id=151)

    # === KSOFT LYRICS ===
    # Supply a short list of artists to query. Repeat runs to gather more songs.
    artist_list = [
        "Taylor Swift", "Adele", "Drake", "Beyonce", "Ed Sheeran", "Billie Eilish",
        "The Beatles", "Kanye West", "Kendrick Lamar", "Rihanna"
    ]
    print("Fetching lyrics (up to 25 new)...")
    fetch_lyrics_for_artist_list(conn, artist_list, max_new=25)

    # === WEATHER ===
    cities = list(CITY_COORDS.keys())
    print("Fetching weather (up to 25 new)...")
    fetch_weather_for_cities(conn, cities, max_new_per_run=25)

    # === OMDb ===
    title_list = [
        "The Shawshank Redemption", "The Dark Knight", "Inception", "Pulp Fiction",
        "The Godfather", "Forrest Gump", "Fight Club", "Interstellar"
    ]
    print("Fetching movies (up to 25 new)...")
    fetch_movies_by_title_list(conn, title_list, max_new=25)

    # === Calculations & Visualizations (example) ===
    print("\n--- Calculations ---")
    print("Pokemon avg base exp by type:", calculate_avg_base_exp_by_type(conn)[:8])
    print("Top lyric averages:", calculate_avg_lyrics_wordcount_per_artist(conn)[:8])
    print("Temp variability by city:", calculate_temp_variability_by_city(conn))
    r = calculate_runtime_rating_correlation(conn)
    print("Runtime vs rating correlation:", r)

    # Visualize (call those you want)
    visualize_avg_base_exp_by_type(conn)
    visualize_temp_high_low_by_city(conn)
    visualize_runtime_vs_rating(conn)
    visualize_avg_lyrics_wordcount(conn)

    conn.close()


if __name__ == "__main__":
    example_run()