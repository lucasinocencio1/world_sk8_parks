Worlds_skate_parks API

FastAPI backend that returns skate parks for a given city. Uses OpenStreetMap (Overpass) for data, Nominatim for geocoding, and optional reverse geocoding for addresses.

Stack: Python 3.10+, FastAPI, httpx, geopy, pydantic-settings. Config via env (see `app/core/config.py`).

Cache: In-memory TTL cache for geocoding and Overpass results (see `app/core/cache.py`). Reduces calls to Nominatim and Overpass; TTLs are configurable. Designed so you can swap to Redis later without changing callers.

How to Run:

```bash
make server
```

Creates `.venv` if missing, installs deps, starts the API at `http://127.0.0.1:8000`.

- Docs: `http://127.0.0.1:8000/docs`
- Health: `GET /health`
- Skate parks: `GET /skateparks/by-city?city=Lisbon` (optional: `resolve_address=true` for reverse-geocoded addresses)

## Makefile

| Target   | Description                    |
|----------|--------------------------------|
| `make`   | Show help                      |
| `make setup`  | Create `.venv` if needed  |
| `make install` | Install dependencies     |
| `make server`  | Run the API (setup + install + uvicorn) |
