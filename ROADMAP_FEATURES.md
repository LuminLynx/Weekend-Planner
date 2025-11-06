# Weekend Planner - Roadmap Features Guide

This document describes the implementation and usage of all features from the Weekend Planner roadmap.

## ✅ All Features Implemented

All 4 roadmap features have been fully implemented and tested:

1. ✅ User Personalization
2. ✅ Weather Awareness
3. ✅ Travel Distance & Carbon Estimate
4. ✅ Itinerary Sharing

---

## 1️⃣ User Personalization

**Status:** ✅ Complete

### Overview
The planner adapts to user preferences and past choices through a persistent profile system.

### Features
- **Profile Storage**: `~/.weekend_profile.json` or in-memory
- **Fields**:
  - `home_city`: User's home location
  - `preferred_currency`: Preferred currency for pricing
  - `max_distance_km`: Maximum travel distance preference
  - `preferred_cuisines`: List of preferred cuisine types

### API Endpoints

#### Get User Preferences
```bash
curl http://localhost:8000/user/preferences
```

**Response:**
```json
{
  "home_city": "Berlin",
  "preferred_currency": "EUR",
  "max_distance_km": 2000.0,
  "preferred_cuisines": []
}
```

#### Update User Preferences
```bash
curl -X POST http://localhost:8000/user/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "home_city": "Paris",
    "preferred_cuisines": ["French", "Italian"],
    "max_distance_km": 1500
  }'
```

### Scoring Integration
User preferences affect the scoring algorithm:
- **+0.05 bonus**: Event in home city
- **+0.05 bonus**: Dining matches preferred cuisines

### Code Example
```python
from app.utils.profile import get_profile_manager

# Get profile manager
profile_mgr = get_profile_manager()

# Update preferences
profile = profile_mgr.update(
    home_city="London",
    preferred_cuisines=["Japanese", "Thai"]
)

# Load preferences
loaded = profile_mgr.load()
print(loaded.to_dict())
```

### Test Coverage
- 8 tests in `app/tests/test_profile.py`
- Tests cover: defaults, custom values, serialization, persistence, updates

---

## 2️⃣ Weather Awareness

**Status:** ✅ Complete

### Overview
Enriches itineraries with live or forecasted weather using the Open-Meteo API (no API key required).

### Features
- **Free API**: Open-Meteo (no authentication needed)
- **Data Points**: 
  - Weather description (Clear, Rainy, Snowy, etc.)
  - Current temperature
  - Min/max temperature
- **Caching**: 2-hour TTL to minimize API calls
- **Graceful Fallback**: Returns `null` if API unavailable

### API Response
Weather data is included in all itinerary responses:

```json
{
  "event_title": "Indie Concert",
  "weather": {
    "desc": "Clear",
    "temp_c": 18.5,
    "temp_min": 15.0,
    "temp_max": 22.0
  }
}
```

### Debug Endpoint
```bash
curl "http://localhost:8000/plan/debug?date=2025-11-20&budget=30" | jq '.itineraries[0].weather'
```

### Configuration
Set in `app/config/settings.example.yaml`:
```yaml
apis:
  weather:
    provider: "open-meteo"
    base_url: "https://api.open-meteo.com/v1/forecast"
    timeout_seconds: 10
    cache_ttl_seconds: 7200  # 2 hours
```

### Code Example
```python
from app.connectors.weather import get_weather, get_weather_by_city

# By coordinates
weather = await get_weather(lat=38.709, lng=-9.133)

# By city name
weather = await get_weather_by_city("Lisbon")

# Returns: {"desc": "Clear", "temp_c": 18.5, "temp_min": 15, "temp_max": 22}
```

### Test Coverage
- 8 tests in `app/tests/test_weather.py`
- Tests cover: weather code mapping, city coordinates, error handling

---

## 3️⃣ Travel Distance & Carbon Estimate

**Status:** ✅ Complete

### Overview
Calculates trip distance and carbon footprint between home city and event location.

### Features
- **Distance Calculation**: Haversine formula for accurate great-circle distance
- **Transport Mode Estimation**:
  - `air`: > 1000 km
  - `rail`: 300-1000 km
  - `car`: 100-300 km
- **CO₂ Factors** (kg per km per person):
  - Air: 0.15
  - Rail: 0.04
  - Car: 0.12
  - Bus: 0.06

### API Response
Travel data is included in all itinerary responses:

```json
{
  "event_title": "Indie Concert",
  "travel": {
    "distance_km": 1453.8,
    "transport_mode": "air",
    "co2_kg_pp": 218.07
  }
}
```

### Scoring Integration
Travel affects the scoring algorithm:
- **Distance penalty**: -0.01 per 500km (max -0.10)
- **CO₂ penalty**: -0.01 per 10kg (max -0.10)

### Examples

#### Short distance (rail)
```
Paris → Amsterdam
- Distance: 430 km
- Mode: rail
- CO₂: 17.2 kg/person
```

#### Long distance (air)
```
Paris → Lisbon
- Distance: 1454 km
- Mode: air
- CO₂: 218 kg/person
```

### Code Example
```python
from app.connectors.travel import get_travel_info

info = get_travel_info("Berlin", "Lisbon")
print(info)
# {'distance_km': 2312.9, 'transport_mode': 'air', 'co2_kg_pp': 346.94}
```

### Test Coverage
- 19 tests in `app/tests/test_travel.py`
- Tests cover: distance calculation, CO₂ estimation, transport mode selection

---

## 4️⃣ Itinerary Sharing

**Status:** ✅ Complete

### Overview
Allows sharing planned weekends via unique links with static HTML snapshots.

### Features
- **UUID-based Links**: Each plan gets a unique identifier
- **Persistent Storage**: Plans saved in `.cache/shared/{uuid}.json`
- **HTML Rendering**: Beautiful, static HTML views
- **Metadata**: Tracks creation time and plan details
- **XSS Protection**: All user content is HTML-escaped

### API Endpoints

#### Create Shareable Link
```bash
curl -X POST "http://localhost:8000/share?date=2025-11-20&budget=30&with_dining=true"
```

**Response:**
```json
{
  "plan_id": "803bd55a-5d39-46a6-9970-36d0ae949a51",
  "share_url": "/share/803bd55a-5d39-46a6-9970-36d0ae949a51"
}
```

#### View Shared Plan
```bash
curl "http://localhost:8000/share/803bd55a-5d39-46a6-9970-36d0ae949a51"
```

Returns a fully styled HTML page with:
- Event details
- Pricing information
- Weather forecast
- Travel distance and CO₂
- Dining recommendations
- Scoring rationale

### HTML Preview

The generated HTML includes:
- Responsive design
- Clean, modern styling
- All itinerary details
- Weather and travel information
- Carbon footprint display
- Back link to create new plans

### Code Example
```python
from app.utils.share import get_share_manager, generate_html_view

# Get share manager
share_mgr = get_share_manager()

# Save a plan
plan_data = {"itineraries": [...]}
plan_id = share_mgr.save_plan(plan_data)

# Retrieve plan
retrieved = share_mgr.get_plan(plan_id)

# Generate HTML
html = generate_html_view(retrieved, plan_id)

# List all plans
plans = share_mgr.list_plans()

# Delete a plan
share_mgr.delete_plan(plan_id)
```

### Test Coverage
- 11 tests in `app/tests/test_share.py`
- Tests cover: save, retrieve, list, delete, HTML generation, persistence

---

## Scoring Integration Summary

All new features are integrated into the scoring algorithm in `app/ranking/scorer.py`:

### Scoring Factors

| Factor | Impact | Range |
|--------|--------|-------|
| Budget match | Heavy penalty if over-budget | -0.8 to +0.2 |
| Home city match | Bonus for local events | +0.05 |
| Cuisine match | Bonus for preferred cuisines | +0.05 |
| Distance | Penalty for long trips | 0 to -0.10 |
| CO₂ emissions | Penalty for high emissions | 0 to -0.10 |
| Price drop probability | Bonus for likely drops | +0.15 |
| Bookability | Bonus for bookable items | +0.10 |

### Example Scoring Comparison

**Scenario 1: Nearby event, matching preferences**
```
Home city: Paris
Event city: Paris
Cuisine: French (matches preference)
Distance: 0 km
CO₂: 0 kg

Score: 0.91 (high - local, preferred cuisine)
```

**Scenario 2: Far event, high emissions**
```
Home city: Paris
Event city: Lisbon
Cuisine: Portuguese (no match)
Distance: 1454 km
CO₂: 218 kg

Score: 0.61 (lower - distance and CO₂ penalties)
```

---

## Configuration

All features are configurable in `app/config/settings.example.yaml`:

```yaml
# User profile defaults
user_profile:
  home_city: "Berlin"
  preferred_currency: "EUR"
  max_distance_km: 2000
  preferred_cuisines: []

apis:
  # Weather API (Open-Meteo)
  weather:
    provider: "open-meteo"
    base_url: "https://api.open-meteo.com/v1/forecast"
    timeout_seconds: 10
    cache_ttl_seconds: 7200  # 2 hours
```

---

## Testing

### Run All Tests
```bash
pytest -v
# 69 tests pass, including:
# - 8 profile tests
# - 8 weather tests
# - 19 travel tests
# - 11 share tests
# - 5 scorer tests (with new features)
```

### Manual Testing

See `/tmp/test_roadmap_features.py` for a comprehensive manual test that verifies:
- Profile management
- Weather fetching
- Distance/CO₂ calculation
- Plan sharing
- Scoring integration

---

## Live Demo

The app is deployed on GitHub Pages:

**🚀 [Launch Weekend Planner](https://luminlynx.github.io/Weekend-Planner/app.html)**

All features are available in the live deployment:
- User preferences persist in browser storage
- Weather data is fetched in real-time
- Travel calculations work automatically
- Share links generate unique URLs

---

## Summary

✅ **All roadmap features implemented and tested**

| Feature | Files | Tests | Status |
|---------|-------|-------|--------|
| User Personalization | `profile.py`, `server.py` | 8 | ✅ Complete |
| Weather Awareness | `weather.py` | 8 | ✅ Complete |
| Travel & Carbon | `travel.py`, `scorer.py` | 19 | ✅ Complete |
| Itinerary Sharing | `share.py`, `server.py` | 11 | ✅ Complete |

**Total:** 69 tests passing, 0 failures
