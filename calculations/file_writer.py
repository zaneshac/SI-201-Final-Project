"""
File writer for calculation results
"""
import sqlite3
from calculations.pokemon_calculations import calculate_avg_base_exp_by_type, calculate_pokemon_with_stats_join
from calculations.spotify_calculations import calculate_avg_popularity_per_artist
from calculations.weather_calculations import calculate_temp_variability_by_city
from calculations.movies_calculations import calculate_runtime_rating_correlation


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
