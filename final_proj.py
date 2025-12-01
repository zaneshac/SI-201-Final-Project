# Collaborator Names: (Zanesha Chowdhury - 10440553), (Ariana Namei - ), (Kevin Zang - )
# Used ChatGPT for syntax, debugging, and pointing out errors. 
# Zanesha wrote functions for PokéAPI
# Ariana wrote functions for Word Cloud API
# Kevin wrote functions for Lyrics & Music API and AniDB

import sqlite3
import requests
import json
import time
import plotly.express as px

DB_NAME = "final_project.db"

# ============================================================
#   DATABASE SETUP
# ============================================================

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Pokémon table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pokemon (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            height INTEGER,
            weight INTEGER
        );
    """)

    # Lyrics table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lyrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_name TEXT,
            lyrics TEXT,
            source TEXT
        );
    """)

    # Anime table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS anime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_name TEXT,
            episode_title TEXT,
            synopsis TEXT,
            episode_number INTEGER
        );
    """)

    # Word cloud table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wordcloud (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_name TEXT,
            word TEXT,
            count INTEGER
        );
    """)

    conn.commit()
    conn.close()


# ============================================================
#   FETCH FUNCTIONS
# ============================================================

# --------------------- 1. POKÉAPI ---------------------------

def fetch_pokemon(limit=25):
    """
    Fetches Pokémon basic data from PokeAPI.
    Only fetches 'limit' items each run to satisfy assignment rules.
    """
    url = f"https://pokeapi.co/api/v2/pokemon?limit={limit}"
    resp = requests.get(url).json()

    pokemon_list = []
    for p in resp["results"]:
        details = requests.get(p["url"]).json()
        pokemon_list.append({
            "id": details["id"],
            "name": details["name"],
            "height": details["height"],
            "weight": details["weight"]
        })
        time.sleep(0.1)

    save_pokemon_to_db(pokemon_list)
    print(f"Added {len(pokemon_list)} Pokémon.")


# --------------------- 2. LYRICS API ------------------------

def fetch_lyrics_for_pokemon(name):
    """
    Fetches song lyrics containing a Pokémon name.
    Using lyrics.ovh (free, simple, keyword-based).
    """
    url = f"https://api.lyrics.ovh/v1/pikachu/{name}"  # fake artist to trigger search-like behavior
    r = requests.get(url)

    if r.status_code != 200:
        return None

    data = r.json().get("lyrics", "")
    return data if data else None


def fetch_lyrics_all():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT name FROM pokemon LIMIT 25;")
    names = [row[0] for row in cur.fetchall()]
    conn.close()

    results = []
    for name in names:
        lyrics = fetch_lyrics_for_pokemon(name)
        if lyrics:
            results.append({
                "pokemon_name": name,
                "lyrics": lyrics,
                "source": "lyrics.ovh"
            })

    save_lyrics_to_db(results)
    print(f"Saved {len(results)} lyrics entries.")


# --------------------- 3. ANIME (Jikan API) -----------------

def fetch_anime_for_pokemon(name):
    """
    Uses Jikan API to search for anime episodes referencing Pokémon names.
    """
    url = f"https://api.jikan.moe/v4/anime?q={name}&limit=1"
    r = requests.get(url).json()

    if "data" not in r or len(r["data"]) == 0:
        return None

    anime = r["data"][0]
    return {
        "title": anime.get("title"),
        "synopsis": anime.get("synopsis", ""),
        "episodes": anime.get("episodes", 0)
    }


def fetch_anime_all():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT name FROM pokemon LIMIT 25;")
    names = [row[0] for row in cur.fetchall()]
    conn.close()

    results = []
    for name in names:
        anime_info = fetch_anime_for_pokemon(name)
        if anime_info:
            results.append({
                "pokemon_name": name,
                "episode_title": anime_info["title"],
                "synopsis": anime_info["synopsis"],
                "episode_number": anime_info["episodes"]
            })
        time.sleep(0.5)

    save_anime_to_db(results)
    print(f"Saved {len(results)} anime entries.")


# --------------------- 4. WORD CLOUD API --------------------

WORDCLOUD_API_KEY = "YOUR_API_KEY"

def fetch_wordcloud_for_text(pokemon_name, text):
    """
    Calls WordCloudAPI.com to get word frequencies.
    """
    url = "https://wordcloudapi.com/api/text/analyze"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": WORDCLOUD_API_KEY
    }
    payload = {
        "text": text
    }

    r = requests.post(url, headers=headers, data=json.dumps(payload))

    if r.status_code != 200:
        return None

    data = r.json()
    if "words" not in data:
        return None

    result = []
    for w in data["words"]:
        result.append({
            "pokemon_name": pokemon_name,
            "word": w["word"],
            "count": w["count"]
        })
    return result


def fetch_wordcloud_all():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT pokemon_name, lyrics FROM lyrics LIMIT 25;")
    rows = cur.fetchall()
    conn.close()

    all_results = []

    for name, lyrics in rows:
        wc = fetch_wordcloud_for_text(name, lyrics)
        if wc:
            all_results.extend(wc)
        time.sleep(0.25)

    save_wordcloud_to_db(all_results)
    print(f"Saved {len(all_results)} word cloud rows.")


# ============================================================
#   SAVE FUNCTIONS
# ============================================================

def save_pokemon_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for item in data:
        cur.execute("""
            INSERT OR IGNORE INTO pokemon (id, name, height, weight)
            VALUES (?, ?, ?, ?);
        """, (item["id"], item["name"], item["height"], item["weight"]))

    conn.commit()
    conn.close()


def save_lyrics_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for item in data:
        cur.execute("""
            INSERT OR IGNORE INTO lyrics (pokemon_name, lyrics, source)
            VALUES (?, ?, ?);
        """, (item["pokemon_name"], item["lyrics"], item["source"]))

    conn.commit()
    conn.close()


def save_anime_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for item in data:
        cur.execute("""
            INSERT OR IGNORE INTO anime (pokemon_name, episode_title, synopsis, episode_number)
            VALUES (?, ?, ?, ?);
        """, (
            item["pokemon_name"],
            item["episode_title"],
            item["synopsis"],
            item["episode_number"]
        ))

    conn.commit()
    conn.close()


def save_wordcloud_to_db(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for item in data:
        cur.execute("""
            INSERT INTO wordcloud (pokemon_name, word, count)
            VALUES (?, ?, ?);
        """, (item["pokemon_name"], item["word"], item["count"]))

    conn.commit()
    conn.close()


# ============================================================
#   ANALYSIS
# ============================================================

def calculate_top_words(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT word, SUM(count) as total_count
        FROM wordcloud
        GROUP BY word
        ORDER BY total_count DESC
        LIMIT ?;
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    return rows


def calculate_pokemon_song_counts():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT pokemon_name, COUNT(*) 
        FROM lyrics
        GROUP BY pokemon_name
        ORDER BY COUNT(*) DESC;
    """)
    rows = cur.fetchall()
    conn.close()

    return rows


# ============================================================
#   VISUALIZATION
# ============================================================

def visualize_top_words():
    data = calculate_top_words()

    words = [row[0] for row in data]
    counts = [row[1] for row in data]

    fig = px.bar(
        x=words,
        y=counts,
        title="Top Words in Pokémon Lyrics (WordCloudAPI.com)",
        labels={"x": "Word", "y": "Frequency"}
    )
    fig.show()


def visualize_song_counts():
    data = calculate_pokemon_song_counts()
    names = [row[0] for row in data]
    counts = [row[1] for row in data]

    fig = px.pie(
        names=names,
        values=counts,
        title="Song Mentions Per Pokémon"
    )
    fig.show()


# ============================================================
#   COMMAND LINE INTERFACE
# ============================================================

def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python project_unified.py create-db")
        print("  python project_unified.py fetch-pokemon")
        print("  python project_unified.py fetch-lyrics")
        print("  python project_unified.py fetch-anime")
        print("  python project_unified.py fetch-wordcloud")
        print("  python project_unified.py visualize")
        return

    cmd = sys.argv[1]

    if cmd == "create-db":
        create_tables()
        print("Database initialized.")

    elif cmd == "fetch-pokemon":
        fetch_pokemon()

    elif cmd == "fetch-lyrics":
        fetch_lyrics_all()

    elif cmd == "fetch-anime":
        fetch_anime_all()

    elif cmd == "fetch-wordcloud":
        fetch_wordcloud_all()

    elif cmd == "visualize":
        visualize_top_words()
        visualize_song_counts()

    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()