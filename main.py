#!/usr/bin/env python3
"""
SI 201 Final Project - Main Entry Point
Team: Zanesha Chowdhury, Ariana Namei, Kevin Zang

This is the main script that runs the complete data collection pipeline
using modular components organized in separate folders.

Used ChatGPT for syntax, debugging, and pointing out errors.
Zanesha wrote functions for PokéAPI
Ariana wrote functions for OMDB, Weather API
Kevin wrote functions for Spotipy
"""

# Database imports
from database.db_helper import create_connection, create_tables

# Data collection imports
from data_collection.pokemon_api import fetch_pokemon_up_to_limit
from data_collection.spotify_api import fetch_tracks_for_artist_list
from data_collection.weather_api import fetch_weather_for_cities, CITY_COORDS
from data_collection.omdb_api import fetch_movies_by_title_list

# Calculation imports
from calculations.pokemon_calculations import calculate_avg_base_exp_by_type, calculate_pokemon_with_stats_join
from calculations.spotify_calculations import calculate_avg_popularity_per_artist
from calculations.weather_calculations import calculate_temp_variability_by_city
from calculations.movies_calculations import calculate_runtime_rating_correlation
from calculations.file_writer import write_calculations_to_file

# Visualization imports
from visualizations.pokemon_viz import visualize_avg_base_exp_by_type
from visualizations.spotify_viz import visualize_avg_popularity_per_artist
from visualizations.weather_viz import visualize_temp_high_low_by_city
from visualizations.movies_viz import visualize_runtime_vs_rating


def example_run():
    """Main execution function that runs all data collection, calculations, and visualizations."""
    # Initialize database
    conn = create_connection()
    create_tables(conn)

    # ==================== DATA COLLECTION ====================
    print("\n" + "=" * 80)
    print("STARTING DATA COLLECTION")
    print("=" * 80)

    # Pokémon data collection
    print("\n[1/4] Fetching Pokemon data...")
    fetch_pokemon_up_to_limit(conn, target_new=25, max_id=151)

    # Spotify tracks - Expanded to 20 artists to ensure 100+ tracks
    print("\n[2/4] Fetching Spotify tracks...")
    artist_list = [
        # Original 10
        "Taylor Swift", "Adele", "Drake", "Beyonce", "Ed Sheeran",
        "Billie Eilish", "The Beatles", "Kanye West", "Kendrick Lamar", "Rihanna",
        # Added 10 more popular artists
        "Ariana Grande", "Justin Bieber", "Post Malone", "The Weeknd", "Bruno Mars",
        "Coldplay", "Eminem", "Lady Gaga", "Dua Lipa", "Harry Styles"
    ]
    fetch_tracks_for_artist_list(conn, artist_list, max_new=25)

    # Weather data collection
    print("\n[3/4] Fetching weather data...")
    cities = list(CITY_COORDS.keys())
    fetch_weather_for_cities(conn, cities, max_new_per_run=25)

    # OMDb movies - Expanded list to reach 100+ for BONUS credit (30 points)
    print("\n[4/4] Fetching movie data...")
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

    # ==================== CALCULATIONS ====================
    print("\n" + "=" * 80)
    print("RUNNING CALCULATIONS")
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

    # ==================== VISUALIZATIONS ====================
    print("\n" + "=" * 80)
    print("CREATING VISUALIZATIONS")
    print("=" * 80)
    visualize_avg_base_exp_by_type(conn)
    visualize_avg_popularity_per_artist(conn)
    visualize_temp_high_low_by_city(conn)
    visualize_runtime_vs_rating(conn)

    # ==================== COMPLETION ====================
    print("\n" + "=" * 80)
    print("ALL TASKS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - calculations_output.txt")
    print("  - pokemon_base_exp_by_type.png")
    print("  - spotify_popularity_by_artist.png")
    print("  - weather_temperature_by_city.png")
    print("  - movies_runtime_vs_rating.png")
    print("\nDatabase: si201_project.db")
    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    example_run()
