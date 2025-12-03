# Project Restructuring Documentation

## Overview
The project has been restructured from a single large file (`final_proj.py`) into a modular architecture with organized folders and separate files for better maintainability and code organization.

## New Project Structure

```
SI-201-Final-Project/
│
├── main.py                          # New main entry point (replaces final_proj.py)
├── final_proj.py                    # Original file (kept for reference)
│
├── config/                          # Configuration and API keys
│   ├── __init__.py
│   └── api_keys.py                 # All API keys and base URLs
│
├── database/                        # Database operations
│   ├── __init__.py
│   └── db_helper.py                # Connection and table creation
│
├── data_collection/                 # API data collection modules
│   ├── __init__.py
│   ├── pokemon_api.py              # PokeAPI functions (Zanesha)
│   ├── spotify_api.py              # Spotify API functions (Kevin)
│   ├── weather_api.py              # Weather.gov API functions (Ariana)
│   └── omdb_api.py                 # OMDb API functions (Ariana)
│
├── calculations/                    # Data analysis functions
│   ├── __init__.py
│   ├── pokemon_calculations.py     # Pokemon calculations & JOIN query
│   ├── spotify_calculations.py     # Spotify calculations
│   ├── weather_calculations.py     # Weather calculations
│   ├── movies_calculations.py      # Movies calculations
│   └── file_writer.py              # Write calculations to file
│
├── visualizations/                  # Data visualization functions
│   ├── __init__.py
│   ├── pokemon_viz.py              # Pokemon bar chart
│   ├── spotify_viz.py              # Spotify horizontal bar chart
│   ├── weather_viz.py              # Weather line plot
│   └── movies_viz.py               # Movies scatter plot
│
├── si201_project.db                 # SQLite database
├── calculations_output.txt          # Output file
├── *.png                            # Generated visualizations
│
└── Documentation files
    ├── FINAL_PROJECT_REPORT.md
    ├── FINAL_STATUS_REPORT.md
    ├── REQUIREMENTS_AUDIT.md
    └── RESTRUCTURE_README.md        # This file
```

## Benefits of Modular Structure

### 1. **Better Organization**
   - Each API has its own dedicated file
   - Easy to locate specific functionality
   - Clear separation of concerns

### 2. **Improved Maintainability**
   - Changes to one API don't affect others
   - Easier to debug specific components
   - Simpler to add new features

### 3. **Code Reusability**
   - Functions can be imported independently
   - Calculations and visualizations can be used separately
   - Database helpers are centralized

### 4. **Team Collaboration**
   - Each team member's work is clearly separated
   - Easier to work on different parts simultaneously
   - Clearer code ownership and attribution

### 5. **Testing & Debugging**
   - Can test individual modules independently
   - Easier to isolate and fix bugs
   - Simpler to verify specific functionality

## How to Run the Project

### Using the New Modular Structure:
```bash
# Activate virtual environment
source venv/bin/activate

# Run the main script
python3 main.py
```

### Using the Original File (still works):
```bash
# Activate virtual environment
source venv/bin/activate

# Run the original script
python3 final_proj.py
```

**Both methods produce the same results!** The modular structure is just better organized.

## File Details

### Configuration (`config/`)
- **api_keys.py**: Contains all API keys, base URLs, and database path
  - Environment variable support with fallback defaults
  - Centralized configuration management

### Database (`database/`)
- **db_helper.py**: Database connection and table creation
  - `create_connection()`: Creates SQLite connection with Row factory
  - `create_tables()`: Creates all 5 required tables (pokemon, pokemon_stats, tracks, weather, movies)

### Data Collection (`data_collection/`)
Each file contains API-specific fetch functions with 25-item limit:

- **pokemon_api.py**: Fetches Pokemon data from PokeAPI
  - `fetch_pokemon_up_to_limit()`: Gets Pokemon and stats (max 25 per run)

- **spotify_api.py**: Fetches track data from Spotify
  - `fetch_tracks_for_artist_list()`: Gets tracks for artists (max 25 per run)

- **weather_api.py**: Fetches weather forecasts from Weather.gov
  - `fetch_weather_for_cities()`: Gets weather for cities (max 25 per run)
  - `CITY_COORDS`: Dictionary of 20 cities with coordinates

- **omdb_api.py**: Fetches movie data from OMDb
  - `fetch_movies_by_title_list()`: Gets movie details (max 25 per run)

### Calculations (`calculations/`)
Each file contains calculation functions using SQL SELECT statements:

- **pokemon_calculations.py**:
  - `calculate_avg_base_exp_by_type()`: Average base experience per type
  - `calculate_pokemon_with_stats_join()`: **INTEGER JOIN query** (required)

- **spotify_calculations.py**:
  - `calculate_avg_popularity_per_artist()`: Average popularity per artist

- **weather_calculations.py**:
  - `calculate_temp_variability_by_city()`: Temperature difference per city

- **movies_calculations.py**:
  - `calculate_runtime_rating_correlation()`: Runtime vs rating correlation

- **file_writer.py**:
  - `write_calculations_to_file()`: Writes all calculations to text file

### Visualizations (`visualizations/`)
Each file contains visualization functions that save PNG files:

- **pokemon_viz.py**: Bar chart of Pokemon base experience by type
- **spotify_viz.py**: Horizontal bar chart of track popularity
- **weather_viz.py**: Line plot of temperatures by city
- **movies_viz.py**: Scatter plot of runtime vs rating

## Migration Notes

### What Changed:
1. ✅ All functionality preserved
2. ✅ Same database structure
3. ✅ Same calculations and visualizations
4. ✅ Same 25-item limit per run
5. ✅ Same output files generated

### What's New:
1. 🆕 Organized folder structure
2. 🆕 Modular imports
3. 🆕 Separate files for each component
4. 🆕 Centralized configuration
5. 🆕 Main entry point (`main.py`)

### What's Kept:
1. ✅ `final_proj.py` - Original file (still works)
2. ✅ `si201_project.db` - Database (unchanged)
3. ✅ All output files (calculations_output.txt, *.png)
4. ✅ All documentation (reports, audits)

## Testing Results

The restructured code was tested and **all functionality works correctly**:
- ✅ All modules import successfully
- ✅ Database connection and table creation working
- ✅ All 4 APIs fetch data correctly (25-item limit enforced)
- ✅ All calculations execute properly
- ✅ All visualizations generate PNG files
- ✅ Output file created successfully

## Grading Requirements

**All SI 201 requirements are still satisfied:**
- ✅ 4 APIs (PokeAPI, Spotify, Weather.gov, OMDb)
- ✅ 100+ rows per API
- ✅ INTEGER JOIN between pokemon tables
- ✅ 25-item per run limit
- ✅ No duplicate data
- ✅ Calculations from database
- ✅ JOIN query implemented
- ✅ File output with calculations
- ✅ 4 visualizations (1 bonus)

**The modular structure does not affect any grading criteria - it only improves code organization!**

## For Graders/Instructors

You can run either:
1. **`python3 main.py`** - New modular version (recommended)
2. **`python3 final_proj.py`** - Original version (still works)

Both produce identical results and satisfy all project requirements.

---

**Restructured on:** December 3, 2024
**Team:** Zanesha Chowdhury, Ariana Namei, Kevin Zang
**Purpose:** Improve code organization and maintainability
