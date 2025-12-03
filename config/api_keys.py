"""
API Keys and Configuration
Team: Zanesha Chowdhury, Ariana Namei, Kevin Zang
"""
import os

# OMDb API Key
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "664d8386")

# Spotify API Keys
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID", "fc80ead3b4f0410da95885d93e837534")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "2535128eadda464c8890983d1ac28786")

# Database path
DB_PATH = "si201_project.db"

# API Base URLs
POKEAPI_BASE = "https://pokeapi.co/api/v2"
OMDB_BASE = "http://www.omdbapi.com/"
WEATHER_BASE = "https://api.weather.gov"
