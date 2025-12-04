# Quick Reference Guide

**Don't worry about the structure! Here's a simple guide to find everything.**

---

## 🎯 Where Is Everything?

### To RUN the project:
```bash
python3 main.py
```
**That's it!** The main.py file handles everything.

---

## 📁 Folder Structure (Simple View)

```
Your Project/
│
├── main.py                    ← START HERE! Run this file
│
├── config/
│   └── api_keys.py           ← All API keys are here
│
├── database/
│   └── db_helper.py          ← Database tables & string-to-integer mapping
│
├── data_collection/          ← Each API has its own file
│   ├── pokemon_api.py        ← Zanesha's work
│   ├── spotify_api.py        ← Kevin's work
│   ├── weather_api.py        ← Ariana's work
│   └── omdb_api.py           ← Ariana's work
│
├── calculations/             ← Each calculation in separate file
│   ├── pokemon_calculations.py
│   ├── spotify_calculations.py
│   ├── weather_calculations.py
│   ├── movies_calculations.py
│   └── file_writer.py        ← Writes calculations_output.txt
│
├── visualizations/           ← Each chart in separate file
│   ├── pokemon_viz.py
│   ├── spotify_viz.py
│   ├── weather_viz.py
│   └── movies_viz.py
│
└── Documentation/
    ├── FINAL_PROJECT_REPORT.md          ← Complete report for submission
    ├── PROJECT_README.md                 ← How to run & setup
    ├── STRING_TO_INTEGER_MAPPING.md     ← String mapping explained
    └── QUICK_REFERENCE.md               ← This file!
```

---

## 🔍 Need to Find Something?

### "Where's the code that fetches Pokemon?"
→ `data_collection/pokemon_api.py`

### "Where's the code that fetches Spotify tracks?"
→ `data_collection/spotify_api.py`

### "Where's the code that fetches weather?"
→ `data_collection/weather_api.py`

### "Where's the code that fetches movies?"
→ `data_collection/omdb_api.py`

### "Where's the code that creates database tables?"
→ `database/db_helper.py`

### "Where are the API keys?"
→ `config/api_keys.py`

### "Where's the string-to-integer mapping code?"
→ `database/db_helper.py` (function: `get_or_create_lookup_id`)

### "Where's the calculation code?"
→ `calculations/` folder - each calculation in its own file

### "Where's the visualization code?"
→ `visualizations/` folder - each chart in its own file

### "Where's the main entry point?"
→ `main.py` (just run this!)

---

## 📊 String-to-Integer Mapping (Simple Explanation)

**Problem:** We had duplicate strings (like "fire" appearing 12 times)

**Solution:** 4 lookup tables that map strings to numbers

### How It Works:

1. **Lookup Tables** (store each string ONCE):
   - `pokemon_types`: fire=2, water=3, grass=1
   - `artists`: Taylor Swift=1, Drake=2
   - `cities`: Ann Arbor=1, Detroit=2
   - `genres`: Drama=1, Action=2

2. **Main Tables** (store only numbers):
   - `pokemon` table: stores type_id (1, 2, 3) not "fire", "water"
   - `tracks` table: stores artist_id not "Taylor Swift"
   - `weather` table: stores city_id not "Ann Arbor, MI"
   - `movies` table: stores genre_id not "Drama"

3. **When You Need the String Back:**
   - Use JOIN to get the name from lookup table
   - Example: `JOIN pokemon_types ON type_id = pokemon_types.id`

### Example:
```
First "fire" Pokemon:
  → Creates: pokemon_types: id=2, type_name="fire"
  → Stores in pokemon: type_id=2

Second "fire" Pokemon:
  → Finds existing: pokemon_types id=2
  → Stores in pokemon: type_id=2 (reuses same ID!)

Result: "fire" string stored only ONCE ✅
```

**Full details:** See `STRING_TO_INTEGER_MAPPING.md`

---

## 🚀 Common Tasks

### Run the project:
```bash
python3 main.py
```

### View database:
1. Open "DB Browser for SQLite" app
2. Open file: `si201_project.db`
3. Click "Browse Data" tab
4. See tables:
   - **Lookup tables:** pokemon_types, artists, cities, genres
   - **Main tables:** pokemon, tracks, weather, movies, pokemon_stats

### Check for duplicate strings:
```bash
sqlite3 si201_project.db

-- Check pokemon_types (should match)
SELECT COUNT(*) FROM pokemon_types;
SELECT COUNT(DISTINCT type_name) FROM pokemon_types;

-- Check artists (should match)
SELECT COUNT(*) FROM artists;
SELECT COUNT(DISTINCT artist_name) FROM artists;
```

### View calculations:
```bash
cat calculations_output.txt
```

### View visualizations:
Open the PNG files:
- pokemon_base_exp_by_type.png
- spotify_popularity_by_artist.png
- weather_temperature_by_city.png
- movies_runtime_vs_rating.png

---

## 💡 Key Files to Show Grader

### 1. String-to-Integer Mapping (Required!)

**Show in DB Browser:**
- Open `si201_project.db`
- Show lookup tables: `pokemon_types`, `artists`, `cities`, `genres`
- Show main tables: `pokemon`, `tracks`, `weather`, `movies`
- Point out: Main tables store only integer IDs, not strings

**Show in code:**
- `database/db_helper.py` - Lookup table creation (lines 87-113)
- `database/db_helper.py` - `get_or_create_lookup_id()` function (lines 28-62)

### 2. Example: Pokemon Type Mapping

**Show:**
```sql
-- Lookup table (strings stored ONCE)
SELECT * FROM pokemon_types;

-- Main table (stores integers)
SELECT id, name, type_id FROM pokemon LIMIT 10;

-- JOIN to get string back
SELECT p.id, p.name, pt.type_name
FROM pokemon p
JOIN pokemon_types pt ON p.type_id = pt.id
LIMIT 10;
```

### 3. INTEGER JOIN (Required!)

**Show in code:**
- `calculations/pokemon_calculations.py` - `calculate_pokemon_with_stats_join()` function

**Show query:**
```sql
SELECT p.id, p.name, pt.type_name, ps.hp, ps.attack
FROM pokemon p
INNER JOIN pokemon_stats ps ON p.id = ps.pokemon_id
INNER JOIN pokemon_types pt ON p.type_id = pt.id
ORDER BY (ps.hp + ps.attack + ps.defense + ps.speed) DESC
LIMIT 10;
```

**Result:** 3-way JOIN! (pokemon + pokemon_stats + pokemon_types)

---

## 📝 Documentation Files

1. **FINAL_PROJECT_REPORT.md** (41 KB)
   - Complete report with all 8 sections
   - Submit this for grading

2. **PROJECT_README.md** (15 KB)
   - How to run the project
   - Setup instructions
   - Troubleshooting

3. **STRING_TO_INTEGER_MAPPING.md** (9.9 KB)
   - Detailed explanation of string mapping
   - Show this to prove no duplicate strings

4. **QUICK_REFERENCE.md** (This file)
   - Quick lookup guide

---

## ✅ Checklist Before Submission

- [ ] Run `python3 main.py` successfully
- [ ] Check database has lookup tables
- [ ] Verify no duplicate strings in main tables
- [ ] Review `FINAL_PROJECT_REPORT.md`
- [ ] Test visualizations generated
- [ ] Verify calculations_output.txt created

---

## 🆘 Need Help?

### "I'm confused about the folder structure"
→ Don't worry! Just run `python3 main.py` and it works!
→ Read this file (QUICK_REFERENCE.md) for simple explanations

### "Where's the string-to-integer mapping explained?"
→ `STRING_TO_INTEGER_MAPPING.md` has full details
→ Short version: Lookup tables store strings once, main tables store integer IDs

### "How do I verify no duplicate strings?"
→ Open `si201_project.db` in DB Browser
→ Check lookup tables (pokemon_types, artists, cities, genres)
→ Check main tables only have integer columns (type_id, artist_id, etc.)

### "What files do I submit?"
→ Everything! The whole folder.
→ Most important: `FINAL_PROJECT_REPORT.md`, `si201_project.db`, all code files

---

**Remember:** The modular structure is just for organization. You don't need to understand every detail - just know where to find things using this guide!

**Last Updated:** December 3, 2024
