"""
Spotify visualization functions
"""
import sqlite3
import matplotlib.pyplot as plt
from calculations.spotify_calculations import calculate_avg_popularity_per_artist


def visualize_avg_popularity_per_artist(conn: sqlite3.Connection, top_n: int = 12):
    """Create horizontal bar chart of average popularity per artist."""
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
