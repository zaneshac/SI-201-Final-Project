"""
Weather visualization functions
"""
import sqlite3
import matplotlib.pyplot as plt


def visualize_temp_high_low_by_city(conn: sqlite3.Connection):
    """Create line plot of average high and low temperatures by city."""
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
