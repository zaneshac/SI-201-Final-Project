"""
Movies visualization functions
"""
import sqlite3
import matplotlib.pyplot as plt


def visualize_runtime_vs_rating(conn: sqlite3.Connection):
    """Create scatter plot of movie runtime vs IMDb rating."""
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
