"""
Weather.gov API data collection module
Author: Ariana Namei

STRING-TO-INTEGER MAPPING:
- City names mapped to integers using cities_lookup table
- Dates mapped to integers using dates_lookup table
- Forecast descriptions mapped to integers using forecasts_lookup table
This eliminates ALL duplicate strings in weather data.
"""
import requests
import sqlite3
import time
from typing import List
from config.api_keys import WEATHER_BASE
from database.db_helper import get_or_create_lookup_id


# City coordinates for weather data collection
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
    """
    Fetch weather data from Weather.gov API (limited to 25 new entries per run).

    STRING-TO-INTEGER MAPPING:
    - City names: "Ann Arbor, MI" -> city_id=1 (stored in cities_lookup)
    - Dates: "2025-12-03" -> date_id=1 (stored in dates_lookup)
    - Forecasts: "Sunny" -> forecast_id=1 (stored in forecasts_lookup)
    All duplicate strings eliminated - same value reuses same ID.

    Args:
        conn: Database connection
        cities: List of city names to fetch weather for
        max_new_per_run: Maximum number of new weather records to insert (default 25)
    """
    headers = {"User-Agent": "SI201-Project (student@example.edu)"}
    inserted = 0
    c = conn.cursor()

    for city in cities:
        if inserted >= max_new_per_run:
            break
        if city not in CITY_COORDS:
            continue
        lat, lon = CITY_COORDS[city]

        # Convert city string to integer ID using lookup table
        city_id = get_or_create_lookup_id(conn, 'cities_lookup', 'city_name', city)

        try:
            points_url = f"{WEATHER_BASE}/points/{lat},{lon}"
            r = requests.get(points_url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            points = r.json()
            grid = points.get("properties", {}).get("gridId")
            grid_x = points.get("properties", {}).get("gridX")
            grid_y = points.get("properties", {}).get("gridY")
            if not (grid and grid_x is not None and grid_y is not None):
                continue
            forecast_url = f"{WEATHER_BASE}/gridpoints/{grid}/{grid_x},{grid_y}/forecast"
            fr = requests.get(forecast_url, headers=headers, timeout=10)
            if fr.status_code != 200:
                continue
            periods = fr.json().get("properties", {}).get("periods", [])
            for p in periods:
                if inserted >= max_new_per_run:
                    break
                date_str = p.get("startTime", "").split("T")[0]
                temp = p.get("temperature")
                short_forecast_str = p.get("shortForecast")
                wind_speed = p.get("windSpeed", None)
                temperature_high = temp
                temperature_low = temp

                # Convert date and forecast strings to integer IDs using lookup tables
                date_id = get_or_create_lookup_id(conn, 'dates_lookup', 'date_value', date_str)
                forecast_id = get_or_create_lookup_id(conn, 'forecasts_lookup', 'forecast_description', short_forecast_str)

                try:
                    c.execute("""
                        INSERT OR IGNORE INTO weather (city_id, date_id, temperature_high, temperature_low, wind_speed, forecast_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (city_id, date_id, temperature_high, temperature_low, wind_speed, forecast_id))
                    if c.rowcount:
                        conn.commit()
                        inserted += 1
                        print(f"[Weather] Inserted {city} (city_id={city_id}) date_id={date_id} forecast_id={forecast_id} ({inserted}/{max_new_per_run})")
                except Exception as e:
                    print("DB error (weather)", e)
            time.sleep(0.25)
        except Exception as e:
            print("Weather API error:", e)
    print(f"[Weather] Finished run: inserted {inserted} new rows.")
