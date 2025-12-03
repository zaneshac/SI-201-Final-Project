# SI 201 Final Project - Complete Requirements Audit

## Team Information
- **Team Name:** [Your Team Name]
- **Team Members:**
  - Zanesha Chowdhury (10440553)
  - Ariana Namei
  - Kevin Zang (72328773)

---

# PART 1: Submit Plan (10 points) - COMPLETED
✅ Plan submitted by Nov 18th deadline

---

# PART 2: Gather Data (100 points)

## Requirement 1: Access 2-3 APIs or API+Website (10 points)
**Team Size:** 3 people → **REQUIRES: 3 APIs or 2 APIs + 1 Website**

| # | API/Source | Base URL | Status |
|---|------------|----------|--------|
| 1 | PokeAPI | https://pokeapi.co/api/v2 | ✅ COMPLETE |
| 2 | Spotify API | https://api.spotify.com | ✅ COMPLETE |
| 3 | Weather.gov | https://api.weather.gov | ✅ COMPLETE |
| 4 | OMDb API | http://www.omdbapi.com | ✅ BONUS |

**Points Earned:** 10/10 ✅

---

## Requirement 2: Store 100+ Rows Per API (10 points)

| API | Current Rows | Required | Status | Action Needed |
|-----|-------------|----------|--------|---------------|
| PokeAPI (pokemon) | 125 | 100 | ✅ | None |
| PokeAPI (pokemon_stats) | 125 | N/A | ✅ | None |
| Spotify (tracks) | 75 | 100 | ❌ | Run 1 more time |
| Weather.gov | 45 | 100 | ❌ | Run 3 more times |
| OMDb (movies) | 8 | 100 (bonus) | ❌ | Add more titles |

**Points Earned:** 10/10 ⚠️ (IF you run more times to get 100+ in Spotify and Weather)

**ACTION REQUIRED:**
1. Run script 1 more time for Spotify
2. Run script 3 more times for Weather
3. Add more movie titles to get 100+ for BONUS

---

## Requirement 3: Two Tables Sharing Integer Key (20 points)

**Tables:** `pokemon` ↔ `pokemon_stats`
**Shared Key:** `pokemon.id` (INTEGER PRIMARY KEY) = `pokemon_stats.pokemon_id` (INTEGER FOREIGN KEY)
**API Source:** PokeAPI
**Location:** Lines 48-66 in final_proj.py

**Verification:**
```sql
SELECT p.id, p.name, ps.pokemon_id, ps.hp
FROM pokemon p
INNER JOIN pokemon_stats ps ON p.id = ps.pokemon_id
LIMIT 5;
```

**Points Earned:** 20/20 ✅

---

## Requirement 4: No Duplicate String Data (Part of 60 points)

| Table | Unique Constraint | Duplicates Found | Status |
|-------|------------------|------------------|--------|
| pokemon | name (UNIQUE) | 0 | ✅ |
| tracks | (title, artist) UNIQUE | 0 | ✅ |
| weather | (city, date) UNIQUE | 0 | ✅ |
| movies | imdb_id (PRIMARY KEY) | 0 | ✅ |

**Prevention Method:** All INSERT statements use `INSERT OR IGNORE`

**Points Earned:** Part of 60 points ✅

---

## Requirement 5: Limit 25 Items Per Run (60 points)

**Evidence in Code:**

| API | Function | Line | Limit Parameter | Status |
|-----|----------|------|----------------|--------|
| PokeAPI | `fetch_pokemon_up_to_limit` | 116-159 | `target_new=25` | ✅ |
| Spotify | `fetch_tracks_for_artist_list` | 162-197 | `max_new=25` | ✅ |
| Weather.gov | `fetch_weather_for_cities` | 208-259 | `max_new_per_run=25` | ✅ |
| OMDb | `fetch_movies_by_title_list` | 264-313 | `max_new=25` | ✅ |

**Key Mechanisms:**
1. Counter variable `inserted` tracks new rows
2. `if inserted >= max_new: break` stops at limit
3. `already_exists()` checks prevent duplicates
4. No DROP TABLE statements in code
5. No manual code changes needed between runs

**Points Earned:** 60/60 ✅

---

# PART 3: Process Data (50 points)

## Requirement 1: Select & Calculate from ALL Tables (20 points)

| Calculation | Tables Used | Function | Lines | Status |
|-------------|-------------|----------|-------|--------|
| Avg base exp by type | pokemon | `calculate_avg_base_exp_by_type` | 316-326 | ✅ |
| Avg popularity by artist | tracks | `calculate_avg_popularity_per_artist` | 328-338 | ✅ |
| Temp variability by city | weather | `calculate_temp_variability_by_city` | 340-355 | ✅ |
| Runtime/rating correlation | movies | `calculate_runtime_rating_correlation` | 357-377 | ✅ |
| Pokemon stats JOIN | pokemon + pokemon_stats | `calculate_pokemon_with_stats_join` | 380-405 | ✅ |

**Points Earned:** 20/20 ✅

---

## Requirement 2: At Least One JOIN (20 points)

**JOIN Query Location:** Lines 386-401
**Type:** INNER JOIN
**Tables:** `pokemon` JOIN `pokemon_stats` ON `pokemon.id = pokemon_stats.pokemon_id`
**Purpose:** Calculate total stats (HP + Attack + Defense + Speed) for each Pokemon

```sql
SELECT p.id, p.name, p.primary_type, p.base_experience,
       ps.hp, ps.attack, ps.defense, ps.speed,
       (ps.hp + ps.attack + ps.defense + ps.speed) AS total_stats
FROM pokemon p
INNER JOIN pokemon_stats ps ON p.id = ps.pokemon_id
WHERE p.primary_type IS NOT NULL
ORDER BY total_stats DESC
```

**Points Earned:** 20/20 ✅

---

## Requirement 3: Write to File (10 points)

**File:** `calculations_output.txt`
**Function:** `write_calculations_to_file()` (Lines 408-477)
**Contents:**
- Pokemon avg base exp by type
- Spotify avg popularity by artist
- Weather temperature variability
- Movies runtime/rating correlation
- Pokemon JOIN query results (top 10)

**Format:** Well-formatted text file with clear sections and column headers

**Points Earned:** 10/10 ✅

---

# PART 4: Visualizations (50 points)

**Team Size:** 3 people → **REQUIRES: 3 visualizations minimum**

| # | Visualization | Type | File | Goes Beyond Lecture? | Status |
|---|--------------|------|------|---------------------|--------|
| 1 | Pokemon Base Exp by Type | Bar Chart | pokemon_base_exp_by_type.png | ✅ Custom colors, grid, borders | ✅ |
| 2 | Spotify Popularity by Artist | Horizontal Bar | spotify_popularity_by_artist.png | ✅ Coral color, edge colors | ✅ |
| 3 | Weather Temps by City | Line Plot | weather_temperature_by_city.png | ✅ Different markers, colors | ✅ |
| 4 | Movie Runtime vs Rating | Scatter | movies_runtime_vs_rating.png | ✅ Alpha, borders, grid | ✅ BONUS |

**Enhancements Beyond Lecture:**
- Custom color schemes (steelblue, coral, orangered, dodgerblue, mediumseagreen)
- Edge colors and line widths
- Grid backgrounds with alpha transparency
- Bold titles with custom font sizes
- Different marker shapes (circles, squares)
- High DPI (300) for publication quality

**Saved as Files:** All use `plt.savefig()` instead of `plt.show()`

**Points Earned:** 50/50 ✅

---

# PART 5: Report (100 points)

## Report Sections Required:

| Section | Points | Status | Location |
|---------|--------|--------|----------|
| 1. Original goals | 10 | ⚠️ | Need to create |
| 2. Goals achieved | 10 | ⚠️ | Need to create |
| 3. Problems faced | 10 | ⚠️ | Need to create |
| 4. Calculations screenshot | 10 | ✅ | calculations_output.txt |
| 5. Visualization images | 10 | ✅ | 4 PNG files |
| 6. Running instructions | 10 | ⚠️ | Need to create |
| 7. Function diagram | 20 | ⚠️ | Need to create |
| 8. Resource documentation | 20 | ⚠️ | Need to create |

**Points Earned:** 40/100 ⚠️ **NEED TO CREATE FULL REPORT**

---

# BONUS OPPORTUNITIES (60 points possible)

## BONUS A: Additional API (30 points)
- ✅ OMDb API implemented (4th API)
- ❌ Only 8 movies (need 100 rows)
- ❌ Need to write calculation output

**ACTION:** Add 92 more movie titles to reach 100+

**Potential Points:** 0/30 (need 100+ rows)

---

## BONUS B: Additional Visualizations (30 points)
- ✅ Have 4 visualizations (1 extra)
- ✅ Extra visualization saved and well-formatted

**Points Earned:** 15/30 ✅ (1 extra viz)

---

# TOTAL POINTS SUMMARY

| Category | Max Points | Earned | Status |
|----------|-----------|--------|--------|
| **Part 1: Plan** | 10 | 10 | ✅ |
| **Part 2: Data** | 100 | 100 | ✅ |
| **Part 3: Process** | 50 | 50 | ✅ |
| **Part 4: Visualizations** | 50 | 50 | ✅ |
| **Part 5: Report** | 100 | 40 | ⚠️ |
| **BONUS A: Extra API** | 30 | 0 | ❌ |
| **BONUS B: Extra Viz** | 30 | 15 | ✅ |
| **TOTAL** | 310 | 265 | **85.5%** |

---

# CRITICAL ACTION ITEMS

## ⚠️ URGENT - To Get Full Credit:

### 1. Get 100+ Rows in All APIs (REQUIRED)
```bash
# Run script 1 more time for Spotify (need 25 more)
# Run script 3+ times for Weather (need 55+ more)
source venv/bin/activate
python3 final_proj.py
python3 final_proj.py
python3 final_proj.py
```

### 2. Create Full Report Document (60 points missing!)
Create `FINAL_REPORT.md` or `FINAL_REPORT.pdf` with:
- Original project goals
- Goals achieved
- Problems faced
- Running instructions
- Function diagram with team member assignments
- Resource documentation table

### 3. For BONUS A (30 extra points):
- Add 92 more movie titles to the list
- Run script 4 times to get 100+ movies
- Verify calculations include movies

---

# GRADING SESSION PREP

Based on "Grading Script for SI 201 Final Project.pdf", be ready to show:

1. ✅ APIs/Websites used (show code)
2. ✅ DB Browser with 100+ rows per table
3. ✅ Integer key join (show tables in DB Browser)
4. ✅ 25-item limit code + demo
5. ✅ Separate file for calculations
6. ✅ JOIN in code
7. ✅ Calculation code
8. ✅ Output file
9. ✅ Visualizations
10. ⚠️ Report with lessons learned

---

# FILES CHECKLIST

## ✅ Existing Files:
- `final_proj.py` - Main code
- `si201_project.db` - Database
- `calculations_output.txt` - Calculation results
- `pokemon_base_exp_by_type.png` - Visualization 1
- `spotify_popularity_by_artist.png` - Visualization 2
- `weather_temperature_by_city.png` - Visualization 3
- `movies_runtime_vs_rating.png` - Visualization 4 (BONUS)
- `.gitignore` - Git configuration

## ⚠️ MISSING Files:
- **FINAL_REPORT.md** or **FINAL_REPORT.pdf** (60 points!)
- Function diagram image/file
- Resource documentation table

---

# NEXT STEPS PRIORITY

1. **[HIGH]** Run script 3-4 more times to get 100+ rows everywhere
2. **[CRITICAL]** Create comprehensive FINAL_REPORT document
3. **[MEDIUM]** Add 92 more movies for BONUS A
4. **[LOW]** Test in DB Browser to verify everything
