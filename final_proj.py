# Collaborator Names: (Zanesha Chowdhury - 10440553), (Ariana Namei - ), (Kevin Zang - 72328773 )
# Used ChatGPT for syntax, debugging, and pointing out errors. 
# Zanesha wrote functions for PokéAPI
# Ariana wrote functions for OMDB, Weather API
# Kevin wrote functions for Spotipy

import os
import sqlite3
import requests
import time
from typing import List, Optional, Tuple
import math
import spotipy


# Visualization
import matplotlib.pyplot as plt

# Spotify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

DB_PATH = "si201_project.db"

# API keys (set as environment variables)
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "664d8386")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID", "fc80ead3b4f0410da95885d93e837534")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "2535128eadda464c8890983d1ac28786")

# ----------------- Spotify client ------------------------
spotify_client = None
if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
    spotify_client = spotipy.Spotify(auth_manager=auth_manager)
else:
    print("Spotify credentials not set. Skipping Spotify fetch.")

# ----------- Database schema & helper functions -------------
def create_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn: sqlite3.Connection):
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

def already_exists(conn: sqlite3.Connection, table: str, where_clause: str, params=()) -> bool:
    c = conn.cursor()
    q = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
    c.execute(q, params)
    return c.fetchone() is not None

# ----------------- PokeAPI functions ------------------------
POKEAPI_BASE = "https://pokeapi.co/api/v2"

def fetch_pokemon_up_to_limit(conn: sqlite3.Connection, target_new: int = 25, max_id: int = 151):
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

# ----------------- Spotify functions ------------------------
def fetch_tracks_for_artist_list(conn: sqlite3.Connection, artist_list: List[str], max_new: int = 25):
    if spotify_client is None:
        print("Spotify client not initialized. Skipping track fetch.")
        return

    c = conn.cursor()
    inserted = 0

    for artist_name in artist_list:
        if inserted >= max_new:
            break
        try:
            results = spotify_client.search(q=f"artist:{artist_name}", type="track", limit=10)
            tracks = results.get("tracks", {}).get("items", [])
            for track in tracks:
                if inserted >= max_new:
                    break
                title = track["name"]
                artist_names = ", ".join([a["name"] for a in track["artists"]])
                popularity = track.get("popularity") or 0

                try:
                    c.execute("""
                        INSERT OR IGNORE INTO tracks (title, artist, popularity)
                        VALUES (?, ?, ?)
                    """, (title, artist_names, popularity))
                    if c.rowcount:
                        conn.commit()
                        inserted += 1
                        print(f"[Spotify] Inserted track: {title} - {artist_names} ({inserted}/{max_new})")
                except Exception as e:
                    print("DB insert error (tracks):", e)
        except Exception as e:
            print("Spotify API error:", e)
        time.sleep(0.2)
    print(f"[Spotify] Finished run: inserted {inserted} new tracks.")

# ---------------- Weather.gov functions -------------------
CITY_COORDS = {
    # Original 5 cities
    "Ann Arbor, MI": (42.2808, -83.7430),
    "Detroit, MI": (42.3314, -83.0458),
    "Chicago, IL": (41.8781, -87.6298),
    "New York, NY": (40.7128, -74.0060),
    "Los Angeles, CA": (34.0522, -118.2437),
    # Added 15 more cities to reach 100+ forecasts (20 cities * ~9 forecasts = 180+ rows)
    "San Francisco, CA": (37.7749, -122.4194),
    "Seattle, WA": (47.6062, -122.3321),
    "Boston, MA": (42.3601, -71.0589),
    "Philadelphia, PA": (39.9526, -75.1652),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Houston, TX": (29.7604, -95.3698),
    "Miami, FL": (25.7617, -80.1918),
    "Atlanta, GA": (33.7490, -84.3880),
    "Denver, CO": (39.7392, -104.9903),
    "Portland, OR": (45.5152, -122.6784),
    "Minneapolis, MN": (44.9778, -93.2650),
    "Austin, TX": (30.2672, -97.7431),
    "San Diego, CA": (32.7157, -117.1611),
    "Dallas, TX": (32.7767, -96.7970),
    "Las Vegas, NV": (36.1699, -115.1398),
}

def fetch_weather_for_cities(conn: sqlite3.Connection, cities: List[str], max_new_per_run: int = 25):
    base = "https://api.weather.gov"
    headers = {"User-Agent": "SI201-Project (student@example.edu)"}
    inserted = 0
    c = conn.cursor()

    for city in cities:
        if inserted >= max_new_per_run:
            break
        if city not in CITY_COORDS:
            continue
        lat, lon = CITY_COORDS[city]
        try:
            points_url = f"{base}/points/{lat},{lon}"
            r = requests.get(points_url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            points = r.json()
            grid = points.get("properties", {}).get("gridId")
            grid_x = points.get("properties", {}).get("gridX")
            grid_y = points.get("properties", {}).get("gridY")
            if not (grid and grid_x is not None and grid_y is not None):
                continue
            forecast_url = f"{base}/gridpoints/{grid}/{grid_x},{grid_y}/forecast"
            fr = requests.get(forecast_url, headers=headers, timeout=10)
            if fr.status_code != 200:
                continue
            periods = fr.json().get("properties", {}).get("periods", [])
            for p in periods:
                if inserted >= max_new_per_run:
                    break
                date = p.get("startTime", "").split("T")[0]
                temp = p.get("temperature")
                short_forecast = p.get("shortForecast")
                wind_speed = p.get("windSpeed", None)
                temperature_high = temp
                temperature_low = temp
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO weather (city, date, temperature_high, temperature_low, wind_speed, short_forecast)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (city, date, temperature_high, temperature_low, wind_speed, short_forecast))
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
    if not OMDB_API_KEY:
        print("OMDB_API_KEY not set. Skipping OMDb fetch.")
        return
    inserted = 0
    c = conn.cursor()
    for title in title_list:
        if inserted >= max_new:
            break
        params = {"t": title, "apikey": OMDB_API_KEY}
        try:
            resp = requests.get(OMDB_BASE, params=params, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            if data.get("Response") == "False":
                continue
            imdb_id = data.get("imdbID")
            if not imdb_id or already_exists(conn, "movies", "imdb_id = ?", (imdb_id,)):
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
            c.execute("""
                INSERT OR IGNORE INTO movies (imdb_id, title, year, genre, runtime, imdb_rating, box_office)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (imdb_id, title_ret, year, genre, runtime, imdb_rating, box_office))
            conn.commit()
            inserted += 1
            print(f"[OMDb] Inserted {title_ret} ({inserted}/{max_new})")
            time.sleep(0.2)
        except Exception as e:
            print("OMDb error:", e)
    print(f"[OMDb] Finished run: inserted {inserted} new movies.")

# ----------------- Calculations ------------------------
def calculate_avg_base_exp_by_type(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
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

def calculate_avg_popularity_per_artist(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
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

def calculate_temp_variability_by_city(conn: sqlite3.Connection) -> List[Tuple[str, float, int]]:
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

# ----------------- JOIN Query (REQUIRED for project) ------------------------
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

# ----------------- Write calculations to file (REQUIRED for project) ------------------------
def write_calculations_to_file(conn: sqlite3.Connection, filename: str = "calculations_output.txt"):
    """
    Writes all calculated data to a text file.
    Required by SI 201 project grading rubric (10 points).
    """
    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SI 201 FINAL PROJECT - CALCULATED DATA RESULTS\n")
        f.write("=" * 80 + "\n\n")

        # Pokemon calculations
        f.write("1. POKEMON: Average Base Experience by Type\n")
        f.write("-" * 80 + "\n")
        pokemon_data = calculate_avg_base_exp_by_type(conn)
        f.write(f"{'Type':<15} {'Avg Base Exp':<20} {'Count':<10}\n")
        f.write("-" * 80 + "\n")
        for ptype, avg_exp, count in pokemon_data:
            f.write(f"{ptype:<15} {avg_exp:<20.2f} {count:<10}\n")
        f.write("\n")

        # Spotify calculations
        f.write("2. SPOTIFY: Average Track Popularity per Artist\n")
        f.write("-" * 80 + "\n")
        spotify_data = calculate_avg_popularity_per_artist(conn)
        f.write(f"{'Artist':<40} {'Avg Popularity':<20} {'Count':<10}\n")
        f.write("-" * 80 + "\n")
        for artist, avg_pop, count in spotify_data:
            f.write(f"{artist:<40} {avg_pop:<20.2f} {count:<10}\n")
        f.write("\n")

        # Weather calculations
        f.write("3. WEATHER: Temperature Variability by City\n")
        f.write("-" * 80 + "\n")
        weather_data = calculate_temp_variability_by_city(conn)
        f.write(f"{'City':<25} {'Temp Variability':<20} {'Count':<10}\n")
        f.write("-" * 80 + "\n")
        for city, variability, count in weather_data:
            f.write(f"{city:<25} {variability:<20.2f} {count:<10}\n")
        f.write("\n")

        # Movies correlation
        f.write("4. MOVIES: Runtime vs IMDb Rating Correlation\n")
        f.write("-" * 80 + "\n")
        correlation = calculate_runtime_rating_correlation(conn)
        if correlation is not None:
            f.write(f"Correlation Coefficient: {correlation:.6f}\n")
            if abs(correlation) < 0.3:
                f.write("Interpretation: Weak correlation\n")
            elif abs(correlation) < 0.7:
                f.write("Interpretation: Moderate correlation\n")
            else:
                f.write("Interpretation: Strong correlation\n")
        else:
            f.write("Correlation: Not enough data\n")
        f.write("\n")

        # JOIN query results
        f.write("5. POKEMON JOIN QUERY: Top 10 Pokemon by Total Stats\n")
        f.write("-" * 80 + "\n")
        join_data = calculate_pokemon_with_stats_join(conn)
        f.write(f"{'ID':<5} {'Name':<15} {'Type':<10} {'HP':<5} {'Atk':<5} {'Def':<5} {'Spd':<5} {'Total':<8}\n")
        f.write("-" * 80 + "\n")
        for pid, name, ptype, base_exp, hp, attack, defense, speed, total in join_data[:10]:
            f.write(f"{pid:<5} {name:<15} {ptype:<10} {hp:<5} {attack:<5} {defense:<5} {speed:<5} {total:<8}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("End of calculations\n")
        f.write("=" * 80 + "\n")

    print(f"✓ Saved calculations to: {filename}")

# ----------------- Visualizations ------------------------
def visualize_avg_base_exp_by_type(conn: sqlite3.Connection, top_n: int = 12):
    data = calculate_avg_base_exp_by_type(conn)
    if not data:
        return
    types = [d[0] for d in data][:top_n]
    avg_be = [d[1] for d in data][:top_n]

    plt.figure(figsize=(10, 6))
    plt.bar(types, avg_be, color='steelblue', edgecolor='navy', linewidth=1.2)
    plt.title("Average Base Experience by Pokémon Primary Type", fontsize=14, fontweight='bold')
    plt.xlabel("Type", fontsize=12)
    plt.ylabel("Average Base Experience", fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig("pokemon_base_exp_by_type.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved visualization: pokemon_base_exp_by_type.png")

def visualize_avg_popularity_per_artist(conn: sqlite3.Connection, top_n: int = 12):
    data = calculate_avg_popularity_per_artist(conn)
    if not data:
        return
    artists = [d[0] for d in data][:top_n]
    avg_pop = [d[1] for d in data][:top_n]

    plt.figure(figsize=(10, 8))
    y_pos = range(len(artists))
    plt.barh(y_pos, avg_pop, color='coral', edgecolor='darkred', linewidth=1.2)
    plt.yticks(y_pos, artists, fontsize=10)
    plt.xlabel("Average Track Popularity", fontsize=12)
    plt.title("Average Spotify Track Popularity per Artist", fontsize=14, fontweight='bold')
    plt.grid(axis='x', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig("spotify_popularity_by_artist.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved visualization: spotify_popularity_by_artist.png")

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
        return
    cities = [r["city"] for r in rows]
    highs = [r["avg_high"] for r in rows]
    lows = [r["avg_low"] for r in rows]

    x = range(len(cities))
    plt.figure(figsize=(12, 6))
    plt.plot(x, highs, marker="o", label="Avg High", color='orangered', linewidth=2.5, markersize=8)
    plt.plot(x, lows, marker="s", label="Avg Low", color='dodgerblue', linewidth=2.5, markersize=8)
    plt.xticks(x, cities, rotation=45, ha='right')
    plt.ylabel("Temperature (°F)", fontsize=12)
    plt.title("Average High and Low Temperatures by City", fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig("weather_temperature_by_city.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved visualization: weather_temperature_by_city.png")

def visualize_runtime_vs_rating(conn: sqlite3.Connection):
    c = conn.cursor()
    q = """
    SELECT runtime, imdb_rating FROM movies
    WHERE runtime IS NOT NULL AND imdb_rating IS NOT NULL
    """
    c.execute(q)
    rows = c.fetchall()
    if not rows:
        return
    runtimes = [r["runtime"] for r in rows]
    ratings = [r["imdb_rating"] for r in rows]

    plt.figure(figsize=(10, 7))
    plt.scatter(runtimes, ratings, alpha=0.7, s=150, color='mediumseagreen', edgecolors='darkgreen', linewidths=2)
    plt.xlabel("Runtime (minutes)", fontsize=12)
    plt.ylabel("IMDb Rating", fontsize=12)
    plt.title("Movie Runtime vs. IMDb Rating", fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig("movies_runtime_vs_rating.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Saved visualization: movies_runtime_vs_rating.png")

# ----------------- Main example run ------------------------
def example_run():
    conn = create_connection()
    create_tables(conn)

    # Pokémon
    fetch_pokemon_up_to_limit(conn, target_new=25, max_id=151)

    # Spotify tracks - Expanded to 20 artists to ensure 100+ tracks
    artist_list = [
        # Original 10
        "Taylor Swift", "Adele", "Drake", "Beyonce", "Ed Sheeran",
        "Billie Eilish", "The Beatles", "Kanye West", "Kendrick Lamar", "Rihanna",
        # Added 10 more popular artists
        "Ariana Grande", "Justin Bieber", "Post Malone", "The Weeknd", "Bruno Mars",
        "Coldplay", "Eminem", "Lady Gaga", "Dua Lipa", "Harry Styles"
    ]
    fetch_tracks_for_artist_list(conn, artist_list, max_new=25)

    # Weather
    cities = list(CITY_COORDS.keys())
    fetch_weather_for_cities(conn, cities, max_new_per_run=25)

    # OMDb movies - Expanded list to reach 100+ for BONUS credit (30 points)
    title_list = [
        # Top rated classics
        "The Shawshank Redemption", "The Godfather", "The Dark Knight", "Pulp Fiction",
        "Forrest Gump", "Fight Club", "Inception", "Interstellar", "The Matrix",
        "Goodfellas", "The Silence of the Lambs", "Saving Private Ryan", "Schindler's List",
        # Action & Adventure
        "The Lord of the Rings: The Return of the King", "Gladiator", "The Departed",
        "The Prestige", "The Lion King", "Back to the Future", "Terminator 2",
        "Die Hard", "Raiders of the Lost Ark", "Mad Max: Fury Road", "Blade Runner",
        # Sci-Fi & Fantasy
        "Star Wars", "The Empire Strikes Back", "Return of the Jedi", "Avatar",
        "E.T. the Extra-Terrestrial", "Jurassic Park", "The Terminator",
        "Aliens", "The Thing", "Arrival", "Dune", "Her",
        # Drama
        "The Green Mile", "Good Will Hunting", "A Beautiful Mind", "Shawshank Redemption",
        "12 Angry Men", "Casablanca", "It's a Wonderful Life", "The Sixth Sense",
        "American Beauty", "Requiem for a Dream", "The Pianist", "Whiplash",
        # Thrillers & Mystery
        "Se7en", "Shutter Island", "Gone Girl", "Zodiac", "Memento",
        "The Usual Suspects", "Prisoners", "No Country for Old Men", "There Will Be Blood",
        # Comedy
        "The Big Lebowski", "Groundhog Day", "Superbad", "The Hangover",
        "Ferris Bueller's Day Off", "Anchorman", "Step Brothers", "Tropic Thunder",
        # Horror
        "The Shining", "Get Out", "A Quiet Place", "The Conjuring", "Hereditary",
        "It", "The Exorcist", "Psycho", "Alien", "Jaws",
        # Recent Blockbusters
        "Avengers: Endgame", "Joker", "Parasite", "1917", "Oppenheimer",
        "Everything Everywhere All at Once", "Top Gun: Maverick", "Spider-Man: No Way Home",
        "The Batman", "Black Panther", "Wonder Woman", "Deadpool",
        # More classics
        "The Godfather Part II", "One Flew Over the Cuckoo's Nest", "Citizen Kane",
        "Vertigo", "Apocalypse Now", "Taxi Driver", "Raging Bull", "The Graduate",
        "Chinatown", "2001: A Space Odyssey", "Clockwork Orange", "Full Metal Jacket",
        # Animated
        "Toy Story", "Finding Nemo", "Spirited Away", "WALL-E", "Up", "Inside Out",
        "Coco", "The Incredibles", "Ratatouille", "Shrek", "How to Train Your Dragon",
        # War & Historical
        "Dunkirk", "Hacksaw Ridge", "Braveheart", "Black Hawk Down", "Platoon",
        "Full Metal Jacket", "Inglourious Basterds", "Paths of Glory",
        # Crime & Gangster
        "The Irishman", "Casino", "Once Upon a Time in America", "Scarface",
        "Heat", "Reservoir Dogs", "Snatch", "Lock Stock and Two Smoking Barrels"
    ]
    fetch_movies_by_title_list(conn, title_list, max_new=25)

    # Calculations
    print("\n" + "=" * 80)
    print("CALCULATIONS")
    print("=" * 80)
    print("\n--- Pokémon ---")
    print("Avg base exp by type:", calculate_avg_base_exp_by_type(conn))
    print("\n--- Spotify ---")
    print("Avg track popularity per artist:", calculate_avg_popularity_per_artist(conn))
    print("\n--- Weather ---")
    print("Temperature variability by city:", calculate_temp_variability_by_city(conn))
    print("\n--- Movies ---")
    print("Runtime vs IMDb rating correlation:", calculate_runtime_rating_correlation(conn))
    print("\n--- Pokemon JOIN Query (Top 5) ---")
    join_results = calculate_pokemon_with_stats_join(conn)
    for pid, name, ptype, base_exp, hp, attack, defense, speed, total in join_results[:5]:
        print(f"  {name} ({ptype}): HP={hp}, Atk={attack}, Def={defense}, Spd={speed}, Total={total}")

    # Write calculations to file (REQUIRED)
    print("\n" + "=" * 80)
    print("WRITING CALCULATIONS TO FILE")
    print("=" * 80)
    write_calculations_to_file(conn)

    # Visualizations
    print("\n" + "=" * 80)
    print("CREATING VISUALIZATIONS")
    print("=" * 80)
    visualize_avg_base_exp_by_type(conn)
    visualize_avg_popularity_per_artist(conn)
    visualize_temp_high_low_by_city(conn)
    visualize_runtime_vs_rating(conn)

    print("\n" + "=" * 80)
    print("ALL TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    conn.close()

if __name__ == "__main__":
    example_run()
