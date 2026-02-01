import hashlib
import json
from typing import Any, Dict, List

from app.core.cache import TTLCache
from app.core.config import settings
from app.core.client import build_async_client


class OverpassService:
    """
    Handles all interactions with the Overpass API.
    """

    def __init__(self, cache: TTLCache):
        self._cache = cache

    def _cache_key(self, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return "overpass:" + hashlib.sha256(raw).hexdigest()

    def build_query_around(self, lat: float, lon: float, radius_m: int) -> str:
        """
        Builds an Overpass query: leisure=pitch + sport=skateboard (main OSM tag).
        """
        return (
            f"[out:json][timeout:25];"
            f'nwr["leisure"="pitch"]["sport"="skateboard"](around:{radius_m},{lat},{lon});'
            f"out center;"
        )

    def build_query_around_leisure(self, lat: float, lon: float, radius_m: int, leisure_value: str) -> str:
        """
        Builds an Overpass query for leisure=<value> (e.g. skate_park, skatepark).
        """
        return (
            f"[out:json][timeout:25];"
            f'nwr["leisure"="{leisure_value}"](around:{radius_m},{lat},{lon});'
            f"out center;"
        )

    async def query(self, query: str, cache_payload: dict) -> dict:
        """
        Executes an Overpass query with caching.
        """
        cache_key = self._cache_key(cache_payload)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        async with build_async_client(settings.OVERPASS_TIMEOUT_SECONDS) as client:
            response = await client.post(settings.OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            data = response.json()

        # Overpass can return 200 with "remark" (runtime error) or "error" in body
        if data.get("remark"):
            raise RuntimeError(f"Overpass remark: {data['remark']}")
        if data.get("error"):
            raise RuntimeError(f"Overpass error: {data['error']}")

        self._cache.set(
            cache_key,
            data,
            ttl_seconds=settings.OVERPASS_CACHE_TTL_SECONDS
        )

        return data

    def osm_elements_to_geojson(self, elements: List[Dict[str, Any]]) -> dict:
        """
        Converts OSM elements into GeoJSON FeatureCollection.
        """
        features = []

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name")

            if el["type"] == "node":
                lat = el.get("lat")
                lon = el.get("lon")
            else:
                center = el.get("center") or {}
                lat = center.get("lat")
                lon = center.get("lon")

            if lat is None or lon is None:
                continue

            features.append({
                "type": "Feature",
                "id": f'{el["type"]}/{el["id"]}',
                "properties": {
                    "name": name,
                    "osm_type": el["type"],
                    "osm_id": el["id"],
                    "tags": tags
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)]
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }
