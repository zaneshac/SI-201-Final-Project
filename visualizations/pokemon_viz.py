"""
Pokemon visualization functions
"""
import sqlite3
import matplotlib.pyplot as plt
from calculations.pokemon_calculations import calculate_avg_base_exp_by_type


def visualize_avg_base_exp_by_type(conn: sqlite3.Connection, top_n: int = 12):
    """Create bar chart of average base experience by Pokemon type."""
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
