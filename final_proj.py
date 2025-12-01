# Collaborator Names: (Zanesha Chowdhury - 10440553), (Ariana Namei - ), (Kevin Zang - )
# Used ChatGPT for syntax, debugging, and pointing out errors. 
# Zanesha wrote functions for PokéAPI
# Ariana wrote functions for Word Cloud API
# Kevin wrote functions for Lyrics & Music API and AniDB

import sqlite3
from typing import Optional

DB_PATH = "project_data.db"

POKEMON_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    base_experience INTEGER,
    height INTEGER,
    weight INTEGER
);
"""

POKEMON_TYPES_SCHEMA = """
CREATE TABLE IF NOT EXISTS pokemon_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER,
    type_name TEXT,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id)
);
"""

LYRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS song_lyrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id TEXT,          -- external song id or url
    title TEXT,
    artist TEXT,
    matched_keyword TEXT,
    UNIQUE(song_id, matched_keyword)
);
"""

ANIME_SCHEMA = """
CREATE TABLE IF NOT EXISTS pokemon_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    title TEXT,
    aired DATE,
    episode_num INTEGER,
    series_title TEXT,
    UNIQUE(episode_id)
);
"""

WORD_COUNTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS word_counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER,
    word TEXT,
    count INTEGER,
    source TEXT,         -- 'wordcloudapi' or 'local'
    UNIQUE(pokemon_id, word, source),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon(id)
);
"""

def get_connection(db_path: Optional[str] = None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    return conn

def initialize_db(conn=None):
    close = False
    if conn is None:
        conn = get_connection()
        close = True
    cur = conn.cursor()
    cur.execute(POKEMON_TABLE_SCHEMA)
    cur.execute(POKEMON_TYPES_SCHEMA)
    cur.execute(LYRICS_SCHEMA)
    cur.execute(ANIME_SCHEMA)
    conn.commit()
    if close:
        conn.close()

"""
get_pokemon_data.py

Fetch Pokémon data from the public PokéAPI (https://pokeapi.co) and store it in the SQLite DB.
Respects a per-run limit (default 25).
Creates two tables: pokemon and pokemon_types (they share an integer key).
"""

import requests
import sqlite3
from db_utils import get_connection, initialize_db
from typing import List

POKEAPI_BASE = "https://pokeapi.co/api/v2"
DEFAULT_PER_RUN = 25

def fetch_pokemon_list(limit: int = 25, offset: int = 0) -> dict:
    url = f"{POKEAPI_BASE}/pokemon?limit={limit}&offset={offset}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_pokemon_detail(url: str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def get_existing_pokemon_ids(conn: sqlite3.Connection) -> set:
    cur = conn.cursor()
    cur.execute("SELECT id FROM pokemon;")
    rows = cur.fetchall()
    return set(r[0] for r in rows)

def store_pokemon_batch(max_items_per_run: int = DEFAULT_PER_RUN, db_path: str = None):
    conn = get_connection(db_path)
    initialize_db(conn)
    existing_ids = get_existing_pokemon_ids(conn)

    # calculate offset to use by counting how many pokemon are already in DB
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pokemon;")
    already = cur.fetchone()[0]
    offset = already

    # API supports limit+offset; we will fetch up to max_items_per_run
    data = fetch_pokemon_list(limit=max_items_per_run, offset=offset)
    results = data.get("results", [])

    inserted = 0
    for item in results:
        detail = fetch_pokemon_detail(item["url"])
        poke_id = detail["id"]
        if poke_id in existing_ids:
            continue
        name = detail["name"]
        base_exp = detail.get("base_experience")
        height = detail.get("height")
        weight = detail.get("weight")
        types = [t["type"]["name"] for t in detail.get("types", [])]

        try:
            cur.execute(
                "INSERT INTO pokemon (id, name, base_experience, height, weight) VALUES (?, ?, ?, ?, ?);",
                (poke_id, name, base_exp, height, weight),
            )
            for t in types:
                cur.execute(
                    "INSERT INTO pokemon_types (pokemon_id, type_name) VALUES (?, ?);",
                    (poke_id, t),
                )
            conn.commit()
            inserted += 1
            existing_ids.add(poke_id)
        except sqlite3.IntegrityError:
            # skip duplicates
            conn.rollback()
        if inserted >= max_items_per_run:
            break

    conn.close()
    print(f"Inserted {inserted} new Pokémon (attempted up to {max_items_per_run}).")

if __name__ == "__main__":
    # run as script: insert up to 25 new pokemon per run
    store_pokemon_batch()

"""
get_lyrics_data.py

Searches lyrics for Pokémon-related keywords using the KSoft.si Lyrics Search endpoint.
This script is optional (KSoft.si requires an API key). If the API key is not present,
the script will exit gracefully and explain how to enable it.

Behavior:
- Reads keywords from the current pokemon table (names).
- Searches lyrics per keyword, up to `max_items_per_run` total insertions per run.
- Stores metadata (song id/url, title, artist, matched_keyword) in song_lyrics table.
"""

import os
import requests
import sqlite3
from db_utils import get_connection, initialize_db

KSOFT_BASE = "https://api.ksoft.si/lyrics/search"
KSOFT_KEY_ENV = "KSOFT_API_KEY"
DEFAULT_PER_RUN = 25

def get_pokemon_keywords(conn: sqlite3.Connection, limit: int = 50) -> list:
    cur = conn.cursor()
    cur.execute("SELECT name FROM pokemon ORDER BY id LIMIT ?;", (limit,))
    return [r[0] for r in cur.fetchall()]

def count_existing_lyrics(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM song_lyrics;")
    return cur.fetchone()[0]

def search_lyrics_ksoft(keyword: str, api_key: str, page: int = 1) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"q": keyword, "limit": 10, "page": page}
    resp = requests.get(KSOFT_BASE, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def store_lyrics_from_keywords(max_items_per_run: int = DEFAULT_PER_RUN, db_path: str = None):
    api_key = os.environ.get(KSOFT_KEY_ENV)
    if not api_key:
        print(f"No KSoft.si API key found in env var {KSOFT_KEY_ENV}. Skipping lyrics collection.")
        print("If you have a key, export it: export KSOFT_API_KEY='your_key' and rerun this script.")
        return

    conn = get_connection(db_path)
    initialize_db(conn)
    cur = conn.cursor()
    keywords = get_pokemon_keywords(conn, limit=100)
    inserted = 0

    for kw in keywords:
        # try up to 2 pages per keyword to increase chance of matches, but stop if we reach max
        for p in range(1, 3):
            try:
                result = search_lyrics_ksoft(kw, api_key, page=p)
            except requests.HTTPError as e:
                print(f"HTTP error searching for {kw}: {e}")
                break
            items = result.get("data", [])
            for item in items:
                song_id = item.get("id") or item.get("url") or item.get("songId")
                title = item.get("title") or item.get("song")
                artist = item.get("artist") or item.get("artists")
                try:
                    cur.execute(
                        "INSERT INTO song_lyrics (song_id, title, artist, matched_keyword) VALUES (?, ?, ?, ?);",
                        (str(song_id), title, artist, kw),
                    )
                    conn.commit()
                    inserted += 1
                except sqlite3.IntegrityError:
                    conn.rollback()
                if inserted >= max_items_per_run:
                    conn.close()
                    print(f"Inserted {inserted} lyric rows (limit reached).")
                    return
            # break early if no items
            if not items:
                break
    conn.close()
    print(f"Inserted {inserted} lyric rows (done).")

if __name__ == "__main__":
    store_lyrics_from_keywords()

"""
get_anime_data.py

Uses the Jikan (MyAnimeList) v4 API to search for anime with "pokemon" and fetch episodes.
Stores episodes in pokemon_episodes table. Inserts up to max_items_per_run rows per run.

Jikan base: https://api.jikan.moe/v4
"""

import requests
import sqlite3
from db_utils import get_connection, initialize_db
from typing import List

JIKAN_BASE = "https://api.jikan.moe/v4"
DEFAULT_PER_RUN = 25

def search_anime(query: str = "pokemon", limit: int = 5) -> List[dict]:
    url = f"{JIKAN_BASE}/anime"
    params = {"q": query, "limit": limit}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])

def fetch_anime_episodes(anime_mal_id: int, page: int = 1) -> dict:
    url = f"{JIKAN_BASE}/anime/{anime_mal_id}/episodes"
    params = {"page": page}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def store_episodes_from_search(max_items_per_run: int = DEFAULT_PER_RUN, db_path: str = None):
    conn = get_connection(db_path)
    initialize_db(conn)
    cur = conn.cursor()

    anime_results = search_anime("pokemon", limit=5)
    inserted = 0

    for anime in anime_results:
        mal_id = anime.get("mal_id")
        title = anime.get("title")
        # fetch episode pages until we get enough or no more pages
        page = 1
        while True:
            resp = fetch_anime_episodes(mal_id, page=page)
            episodes = resp.get("data", [])
            if not episodes:
                break
            for ep in episodes:
                episode_id = ep.get("mal_id") or ep.get("url")
                ep_title = ep.get("title")
                aired = ep.get("aired", {}).get("string")  # sometimes returns string
                ep_num = ep.get("mal_id")  # best-effort episode identifier
                try:
                    cur.execute(
                        "INSERT INTO pokemon_episodes (episode_id, title, aired, episode_num, series_title) VALUES (?, ?, ?, ?, ?);",
                        (episode_id, ep_title, aired, ep_num, title),
                    )
                    conn.commit()
                    inserted += 1
                except sqlite3.IntegrityError:
                    conn.rollback()
                if inserted >= max_items_per_run:
                    conn.close()
                    print(f"Inserted {inserted} episodes (limit reached).")
                    return
            # if pagination info indicates no more pages, break
            pagination = resp.get("pagination", {})
            if not pagination.get("has_next_page"):
                break
            page += 1

    conn.close()
    print(f"Inserted {inserted} episodes (done).")

if __name__ == "__main__":
    store_episodes_from_search()

"""
analyze_and_visualize.py

Performs the required SQL joins and calculations, then creates Plotly visualizations.
- Calculates frequency of pokemon types in the pokemon_types table (counts).
- Calculates number of episodes fetched per series.
- (If lyrics data exists) counts of matched keywords by type (attempts to map pokemon name -> type).
"""

import sqlite3
import pandas as pd
import plotly.graph_objects as go
from db_utils import get_connection, initialize_db

DB_PATH = "project_data.db"

def load_type_counts(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT type_name, COUNT(DISTINCT pokemon_id) AS pokemon_count
    FROM pokemon_types
    GROUP BY type_name
    ORDER BY pokemon_count DESC;
    """
    return pd.read_sql_query(q, conn)

def load_episode_series_counts(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT series_title, COUNT(*) as episodes
    FROM pokemon_episodes
    GROUP BY series_title
    ORDER BY episodes DESC;
    """
    return pd.read_sql_query(q, conn)

def load_lyrics_keyword_counts(conn: sqlite3.Connection) -> pd.DataFrame:
    # Count matched_keyword occurrences in song_lyrics
    q = """
    SELECT matched_keyword as pokemon_name, COUNT(*) as matches
    FROM song_lyrics
    GROUP BY matched_keyword
    ORDER BY matches DESC;
    """
    return pd.read_sql_query(q, conn)

def map_pokemon_to_types(conn: sqlite3.Connection) -> pd.DataFrame:
    q = """
    SELECT p.name as pokemon_name, pt.type_name
    FROM pokemon p
    JOIN pokemon_types pt ON p.id = pt.pokemon_id;
    """
    return pd.read_sql_query(q, conn)

def plot_type_bar(df: pd.DataFrame, outfile: str = "type_counts.html"):
    fig = go.Figure([go.Bar(x=df['type_name'], y=df['pokemon_count'])])
    fig.update_layout(title="Number of Pokémon per Type", xaxis_title="Type", yaxis_title="Count of Pokémon")
    fig.write_html(outfile)
    print(f"Saved: {outfile}")

def plot_episode_pie(df: pd.DataFrame, outfile: str = "episode_distribution.html"):
    fig = go.Figure([go.Pie(labels=df['series_title'], values=df['episodes'], hole=0.3)])
    fig.update_layout(title="Episode Count per Series (fetched)")
    fig.write_html(outfile)
    print(f"Saved: {outfile}")

def plot_comparison_types_vs_lyrics(types_df: pd.DataFrame, lyrics_map_df: pd.DataFrame, outfile: str = "comparison.html", conn=None):
    # map lyric keyword -> types using pokemon->type mapping
    if lyrics_map_df.empty or types_df.empty:
        print("Not enough data to create comparison plot.")
        return

    # Build mapping pokemon_name -> list of types
    mapping = map_pokemon_to_types(conn)
    # Normalize names for joins
    mapping['pokemon_name_lower'] = mapping['pokemon_name'].str.lower()
    lyrics_map_df['pokemon_lower'] = lyrics_map_df['pokemon_name'].str.lower()

    # Join lyrics keywords to mapping to see which types have lyric hits
    merged = lyrics_map_df.merge(mapping, left_on='pokemon_lower', right_on='pokemon_name_lower', how='left')
    # Count matches per type
    type_lyrics = merged.groupby('type_name')['matches'].sum().reset_index()
    # bring in pokemon counts per type
    merged2 = types_df.merge(type_lyrics, left_on='type_name', right_on='type_name', how='left').fillna(0)

    fig = go.Figure(data=[
        go.Bar(name='Pokemon count', x=merged2['type_name'], y=merged2['pokemon_count']),
        go.Bar(name='Lyric matches', x=merged2['type_name'], y=merged2['matches'])
    ])
    fig.update_layout(barmode='group', title="Pokémon count vs Lyric matches by Type", xaxis_title="Type")
    fig.write_html(outfile)
    print(f"Saved: {outfile}")

def run_all_and_visualize(db_path=DB_PATH):
    conn = get_connection(db_path)
    initialize_db(conn)

    types_df = load_type_counts(conn)
    ep_df = load_episode_series_counts(conn)
    lyrics_df = load_lyrics_keyword_counts(conn)

    if not types_df.empty:
        plot_type_bar(types_df, outfile="type_counts.html")
    else:
        print("No pokemon type data to plot.")

    if not ep_df.empty:
        plot_episode_pie(ep_df, outfile="episode_distribution.html")
    else:
        print("No anime episode data to plot.")

    if not lyrics_df.empty and not types_df.empty:
        plot_comparison_types_vs_lyrics(types_df, lyrics_df, outfile="comparison.html", conn=conn)
    else:
        print("Not enough lyrics data or pokemon types to create comparison plot.")

    conn.close()

if __name__ == "__main__":
    run_all_and_visualize()

"""
get_wordcloud_data.py

For each pokemon in the DB:
- fetch species description from PokéAPI (text)
- either call Word Cloud API (via RapidAPI) to get word frequencies OR
  compute local word frequencies as fallback
- store results in word_counts table
- respects <=25 insertions per run (configurable)
"""

import os
import re
import sqlite3
import requests
from collections import Counter
from typing import Dict, List
from db_utils import get_connection, initialize_db

POKEAPI_SPECIES = "https://pokeapi.co/api/v2/pokemon-species/{}"
# RapidAPI config (optional)
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_WORDCLOUD_HOST", "Textvis-word-cloud.p.rapidapi.com")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")  # set this if you want to call the Word Cloud API
# Note: RapidAPI host string may vary; environment var allows you to supply the correct host if needed.

DEFAULT_MAX_INSERTS = 25
STOPWORDS = {
    # a small stopword set; extend as needed
    "the","and","a","an","of","in","to","is","it","for","on","with","that","this","as","by","from","are","was","be","its"
}

def get_pokemon_list(conn: sqlite3.Connection, limit: int = 200) -> List[Dict]:
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM pokemon ORDER BY id LIMIT ?;", (limit,))
    return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

def fetch_species_description(pokemon_name_or_id: str) -> str:
    """
    Use the species endpoint to get flavor_text_entries (english).
    """
    url = POKEAPI_SPECIES.format(pokemon_name_or_id)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    entries = data.get("flavor_text_entries", [])
    # prefer english entries; join them into a single text blob
    texts = []
    for e in entries:
        if e.get("language", {}).get("name") == "en":
            # remove newlines and weird characters
            txt = e.get("flavor_text", "").replace("\n", " ").replace("\f", " ").strip()
            texts.append(txt)
    return " ".join(texts)

def call_wordcloudapi_via_rapidapi(text: str) -> Dict[str, int]:
    """
    Attempt to call Word Cloud API via RapidAPI. Because RapidAPI endpoints and payloads might vary,
    we make this function resilient and expect that if credentials are missing or the endpoint
    doesn't return frequencies, we fall back to local processing.
    NOTE: Users must set RAPIDAPI_KEY (and optionally RAPIDAPI_WORDCLOUD_HOST) env vars to enable this.
    """
    if not RAPIDAPI_KEY:
        raise RuntimeError("RAPIDAPI_KEY not set")

    # Example RapidAPI endpoint structure used by many RapidAPI 'word cloud' listings:
    # This is a best-effort: many word-cloud RapidAPI endpoints accept JSON with "text" and return "words" list.
    url = f"https://{RAPIDAPI_HOST}/api/wordcloud"
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    payload = {"text": text}
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # try to find word counts in the response in common shapes:
    #  - data["words"] = [{"word":"x","count":5}, ...]
    #  - data["counts"] = {"x": 5, ...}
    if isinstance(data, dict):
        if "words" in data and isinstance(data["words"], list):
            return {w.get("word"): int(w.get("count", 0)) for w in data["words"] if w.get("word")}
        if "counts" in data and isinstance(data["counts"], dict):
            return {k: int(v) for k,v in data["counts"].items()}
        # sometimes the API returns nested object, try to search:
        for v in data.values():
            if isinstance(v, list):
                # take first plausible list of dicts
                for item in v:
                    if isinstance(item, dict) and "word" in item and "count" in item:
                        return {w.get("word"): int(w.get("count", 0)) for w in v}
    # if we get here, can't parse; raise to trigger fallback
    raise ValueError("Unexpected response shape from Word Cloud API")

def local_word_counts(text: str, top_n: int = 50) -> Dict[str, int]:
    # simple tokenizer, lower, remove non-alpha, filter stopwords, count
    words = re.findall(r"\b[a-zA-Z']{2,}\b", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    counts = Counter(filtered)
    most = dict(counts.most_common(top_n))
    return most

def store_word_counts(conn: sqlite3.Connection, pokemon_id: int, counts: Dict[str,int], source: str):
    cur = conn.cursor()
    inserted = 0
    for word, cnt in counts.items():
        try:
            cur.execute(
                "INSERT INTO word_counts (pokemon_id, word, count, source) VALUES (?, ?, ?, ?);",
                (pokemon_id, word, int(cnt), source)
            )
            inserted += 1
        except sqlite3.IntegrityError:
            conn.rollback()
    conn.commit()
    return inserted

def run(max_inserts_per_run: int = DEFAULT_MAX_INSERTS, db_path: str = None):
    conn = get_connection(db_path)
    initialize_db(conn)
    pokemon_list = get_pokemon_list(conn, limit=200)
    total_inserted = 0

    for p in pokemon_list:
        if total_inserted >= max_inserts_per_run:
            break
        pid = p["id"]
        pname = p["name"]
        # skip if we already have word_counts for this pokemon (avoid duplicates)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM word_counts WHERE pokemon_id = ?;", (pid,))
        if cur.fetchone()[0] > 0:
            continue

        try:
            text = fetch_species_description(pname)
        except Exception as e:
            print(f"Failed to fetch species for {pname}: {e}")
            continue

        if not text.strip():
            print(f"No species text for {pname}, skipping.")
            continue

        inserted_for_pokemon = 0
        # try remote API first if available
        if RAPIDAPI_KEY:
            try:
                counts = call_wordcloudapi_via_rapidapi(text)
                inserted_for_pokemon = store_word_counts(conn, pid, counts, source="wordcloudapi")
                print(f"[{pname}] inserted {inserted_for_pokemon} word counts from RapidAPI.")
            except Exception as e:
                print(f"RapidAPI call failed for {pname}: {e}. Falling back to local counts.")
                counts = local_word_counts(text)
                inserted_for_pokemon = store_word_counts(conn, pid, counts, source="local")
                print(f"[{pname}] inserted {inserted_for_pokemon} word counts (local).")
        else:
            counts = local_word_counts(text)
            inserted_for_pokemon = store_word_counts(conn, pid, counts, source="local")
            print(f"[{pname}] inserted {inserted_for_pokemon} word counts (local).")

        total_inserted += inserted_for_pokemon

    conn.close()
    print(f"Total word-count rows inserted this run: {total_inserted} (limit was {max_inserts_per_run}).")

if __name__ == "__main__":
    run()