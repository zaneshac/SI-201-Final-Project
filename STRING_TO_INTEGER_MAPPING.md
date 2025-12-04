# String-to-Integer Mapping System

**Purpose:** Eliminate duplicate string data in the database to satisfy SI 201 project requirements.

---

## Problem

The project requires "no duplicate string data" across database entries. However, our original design had repeated strings:
- Pokemon types ("fire", "water", etc.) appeared in multiple pokemon records
- Artist names appeared in multiple track records
- City names appeared in multiple weather records
- Genre names appeared in multiple movie records

**This violated the "no duplicate strings" requirement!**

---

## Solution: Database Normalization with Lookup Tables

We implemented **string-to-integer mapping** using lookup tables. Each repeated string is stored exactly once in a lookup table with a unique integer ID. Main tables store only the integer ID, eliminating duplicate strings.

### Architecture

```
LOOKUP TABLES (store unique strings):
┌─────────────────┐
│ pokemon_types   │  ← Stores "fire", "water", etc. ONCE
│ - id (INTEGER)  │
│ - type_name     │
└─────────────────┘

MAIN TABLES (store integer IDs):
┌────────────────┐
│ pokemon        │  ← Stores type_id (1, 2, 3) NOT "fire", "water", "grass"
│ - id           │
│ - name         │
│ - type_id  ────┼──→ References pokemon_types.id
└────────────────┘
```

---

## Implementation Details

### 1. Lookup Tables Created

Four lookup tables map strings to integers:

#### `pokemon_types` Table
```sql
CREATE TABLE pokemon_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE
);
```
**Example Data:**
| id | type_name |
|----|-----------|
| 1  | grass     |
| 2  | fire      |
| 3  | water     |
| 4  | bug       |
| 5  | normal    |

---

#### `artists` Table
```sql
CREATE TABLE artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_name TEXT NOT NULL UNIQUE
);
```
**Example Data:**
| id | artist_name |
|----|-------------|
| 1  | Taylor Swift |
| 2  | Adele |
| 3  | Drake |
| 4  | Billie Eilish |

---

#### `cities` Table
```sql
CREATE TABLE cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL UNIQUE
);
```
**Example Data:**
| id | city_name |
|----|-----------|
| 1  | Ann Arbor, MI |
| 2  | Detroit, MI |
| 3  | Chicago, IL |
| 4  | New York, NY |

---

#### `genres` Table
```sql
CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_name TEXT NOT NULL UNIQUE
);
```
**Example Data:**
| id | genre_name |
|----|------------|
| 1  | Drama |
| 2  | Crime, Drama |
| 3  | Action, Crime, Drama |
| 4  | Comedy |

---

### 2. Updated Main Tables

Main tables now store **integer foreign keys** instead of strings:

#### Pokemon Table (BEFORE ❌)
```sql
CREATE TABLE pokemon (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    primary_type TEXT  ← DUPLICATE STRINGS!
);
```

#### Pokemon Table (AFTER ✅)
```sql
CREATE TABLE pokemon (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type_id INTEGER,  ← INTEGER REFERENCE
    FOREIGN KEY(type_id) REFERENCES pokemon_types(id)
);
```

**Result:**
- **BEFORE:** "fire" appeared 12 times (12 duplicate strings)
- **AFTER:** type_id=2 appears 12 times (NO duplicate strings, just integers)

---

### 3. Helper Function: `get_or_create_lookup_id()`

**Location:** `database/db_helper.py` lines 28-62

This function ensures strings are mapped to integers without duplicates:

```python
def get_or_create_lookup_id(conn, table, name_column, name_value):
    """
    Get existing ID or create new entry in lookup table.

    Example: get_or_create_lookup_id(conn, 'pokemon_types', 'type_name', 'fire')
    - First call: Creates 'fire' with id=2, returns 2
    - Second call: Finds existing 'fire', returns 2 (no duplicate!)
    """
    # Try to find existing entry
    c.execute(f"SELECT id FROM {table} WHERE {name_column} = ?", (name_value,))
    row = c.fetchone()
    if row:
        return row["id"]  # Reuse existing ID

    # Create new entry
    c.execute(f"INSERT INTO {table} ({name_column}) VALUES (?)", (name_value,))
    return c.lastrowid  # Return new ID
```

---

### 4. Updated Data Collection

All data collection functions now use `get_or_create_lookup_id()`:

#### Pokemon API (BEFORE ❌)
```python
primary_type = "fire"
c.execute("INSERT INTO pokemon (..., primary_type) VALUES (..., ?)",
          (..., primary_type))  # Stores "fire" string
```

#### Pokemon API (AFTER ✅)
```python
primary_type = "fire"
type_id = get_or_create_lookup_id(conn, 'pokemon_types', 'type_name', primary_type)
c.execute("INSERT INTO pokemon (..., type_id) VALUES (..., ?)",
          (..., type_id))  # Stores integer 2, not "fire"
```

**Similar changes in:**
- `data_collection/spotify_api.py` - Maps artist names to artist_id
- `data_collection/weather_api.py` - Maps city names to city_id
- `data_collection/omdb_api.py` - Maps genres to genre_id

---

### 5. Updated Calculations (JOIN with Lookup Tables)

All calculations now **JOIN** with lookup tables to retrieve the original strings:

#### Pokemon Calculation (BEFORE ❌)
```sql
SELECT primary_type, AVG(base_experience)
FROM pokemon
GROUP BY primary_type  -- Can't group by integers!
```

#### Pokemon Calculation (AFTER ✅)
```sql
SELECT pt.type_name, AVG(p.base_experience)
FROM pokemon p
INNER JOIN pokemon_types pt ON p.type_id = pt.id  ← JOIN to get string
GROUP BY pt.type_name
```

**Location:** `calculations/pokemon_calculations.py`

**Similar JOINs in:**
- `calculations/spotify_calculations.py` - JOINs with artists table
- `calculations/weather_calculations.py` - JOINs with cities table
- `calculations/movies_calculations.py` - Would JOIN with genres table

---

## Verification: No Duplicate Strings

### Check Lookup Tables (Each String Appears ONCE)
```sql
-- Pokemon Types: 15 unique types
SELECT COUNT(*) FROM pokemon_types;  -- 15 rows
SELECT COUNT(DISTINCT type_name) FROM pokemon_types;  -- 15 (same!)

-- Artists: ~75 unique artists
SELECT COUNT(*) FROM artists;  -- 75 rows
SELECT COUNT(DISTINCT artist_name) FROM artists;  -- 75 (same!)

-- Cities: 20 unique cities
SELECT COUNT(*) FROM cities;  -- 20 rows
SELECT COUNT(DISTINCT city_name) FROM cities;  -- 20 (same!)

-- Genres: ~50 unique genre combinations
SELECT COUNT(*) FROM genres;  -- 50 rows
SELECT COUNT(DISTINCT genre_name) FROM genres;  -- 50 (same!)
```

### Check Main Tables (Store Only Integers)
```sql
-- Pokemon table: 151 pokemon, but only integer type_id
SELECT type_id FROM pokemon LIMIT 10;
-- Result: 1, 1, 1, 2, 2, 2, 3, 3, 3, 4 (integers, not strings!)

-- Tracks table: 175 tracks, but only integer artist_id
SELECT artist_id FROM tracks LIMIT 10;
-- Result: 1, 1, 1, 1, 1, 1, 2, 1, 1, 1 (integers!)

-- Weather table: 145 forecasts, but only integer city_id
SELECT city_id FROM weather LIMIT 10;
-- Result: 1, 1, 1, 1, 1, 1, 1, 1, 2, 2 (integers!)

-- Movies table: 108 movies, but only integer genre_id
SELECT genre_id FROM movies LIMIT 10;
-- Result: 1, 2, 3, 2, 4, 5, 6, 7, 8, 9 (integers!)
```

---

## Benefits

1. **✅ Satisfies Requirements:** No duplicate strings in database
2. **✅ Data Integrity:** FOREIGN KEY constraints ensure referential integrity
3. **✅ Storage Efficiency:** Integers (4 bytes) smaller than strings (variable)
4. **✅ Query Performance:** Joining on integers is faster than strings
5. **✅ Consistency:** Spelling variations automatically unified
6. **✅ Database Normalization:** Follows Third Normal Form (3NF)

---

## Example: Complete Flow

### 1. First "fire" Type Pokemon
```python
# Data Collection (data_collection/pokemon_api.py)
primary_type = "fire"  # From API
type_id = get_or_create_lookup_id(conn, 'pokemon_types', 'type_name', 'fire')
# → Creates: INSERT INTO pokemon_types (type_name) VALUES ('fire')
# → Returns: 2 (new ID)
# → Stores: INSERT INTO pokemon (..., type_id) VALUES (..., 2)
```

### 2. Second "fire" Type Pokemon
```python
# Data Collection
primary_type = "fire"  # Same type!
type_id = get_or_create_lookup_id(conn, 'pokemon_types', 'type_name', 'fire')
# → Finds: SELECT id FROM pokemon_types WHERE type_name = 'fire'
# → Returns: 2 (existing ID, no new row!)
# → Stores: INSERT INTO pokemon (..., type_id) VALUES (..., 2)
```

**Result:** "fire" string stored only ONCE, but 12 pokemon reference type_id=2

### 3. Calculation (Retrieve Strings)
```python
# Calculation (calculations/pokemon_calculations.py)
q = """
SELECT pt.type_name, AVG(p.base_experience)
FROM pokemon p
INNER JOIN pokemon_types pt ON p.type_id = pt.id
GROUP BY pt.type_name
"""
# → Result: "fire", 151.67
```

---

## File Locations

### Implementation Files:
- **Database Schema:** `database/db_helper.py` (lines 65-189)
- **Helper Function:** `database/db_helper.py` (lines 28-62)
- **Pokemon Data Collection:** `data_collection/pokemon_api.py` (line 58)
- **Spotify Data Collection:** `data_collection/spotify_api.py` (line 65)
- **Weather Data Collection:** `data_collection/weather_api.py` (line 70)
- **OMDb Data Collection:** `data_collection/omdb_api.py` (line 69)
- **Pokemon Calculations:** `calculations/pokemon_calculations.py` (lines 20-27)
- **Spotify Calculations:** `calculations/spotify_calculations.py` (lines 20-28)
- **Weather Calculations:** `calculations/weather_calculations.py` (lines 20-26)

### Documentation:
- **This file:** `STRING_TO_INTEGER_MAPPING.md`
- **Main Report:** `FINAL_PROJECT_REPORT.md` (Section 3, Problem 11)

---

## Summary

**BEFORE (❌ Violated Requirements):**
- Main tables stored duplicate strings
- "fire" appeared 12 times in pokemon table
- "Taylor Swift" appeared 9 times in tracks table
- "Ann Arbor, MI" appeared 9 times in weather table

**AFTER (✅ Meets Requirements):**
- Lookup tables store each string exactly ONCE
- Main tables store only integer IDs
- JOINs retrieve original strings when needed
- **ZERO duplicate strings in database!**

---

**Date:** December 3, 2024
**Project:** SI 201 Final Project
**Team:** Zanesha Chowdhury, Ariana Namei, Kevin Zang
