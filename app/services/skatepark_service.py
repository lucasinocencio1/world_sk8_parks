import asyncio

from app.services.geocoding_service import GeocodingService
from app.services.overpass_service import OverpassService


def _build_display_address(tags: dict) -> str | None:
    """
    Builds a readable address from OSM addr:* tags.
    Returns None if no address tags are present.
    """
    if not tags:
        return None
    # addr:full is often present as a complete string
    full = tags.get("addr:full") or tags.get("address")
    if full and full.strip():
        return full.strip()
    # Build from individual fields
    street = tags.get("addr:street", "").strip()
    housenumber = tags.get("addr:housenumber", "").strip()
    unit = tags.get("addr:unit", "").strip()
    city = (
        tags.get("addr:city")
        or tags.get("addr:town")
        or tags.get("addr:village")
        or tags.get("addr:municipality")
        or ""
    ).strip()
    postcode = tags.get("addr:postcode", "").strip()
    country = tags.get("addr:country", "").strip()

    parts = []
    if street:
        line = f"{street}"
        if housenumber:
            line += f" {housenumber}"
        if unit:
            line += f", {unit}"
        parts.append(line)
    elif housenumber:
        parts.append(housenumber)
    if city:
        parts.append(city)
    if postcode:
        parts.append(postcode)
    if country:
        parts.append(country)

    if not parts:
        return None
    return ", ".join(parts)


class SkateparksService:
    """
    Orchestrates geocoding + Overpass queries. Returns all skate parks in the radius.
    """

    def __init__(self, geocoding: GeocodingService, overpass: OverpassService):
        self._geocoding = geocoding
        self._overpass = overpass

    async def find_by_city_and_radius(
        self, city: str, radius_m: int, *, resolve_address: bool = False
    ) -> dict:
        """
        Returns all skate parks near a city within the given radius.
        If resolve_address is True, fills address via reverse geocoding when OSM has none.
        """
        # Run sync geocoding in thread pool to avoid blocking the event loop
        lat, lon, center_address = await asyncio.to_thread(
            self._geocoding.geocode_city, city
        )

        # Query with multiple tags in parallel to get all skate parks in the region
        base_payload = {
            "city": city.lower().strip(),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "radius_m": radius_m,
        }
        queries = [
            (
                self._overpass.build_query_around(lat, lon, radius_m),
                {**base_payload, "tag": "leisure=pitch;sport=skateboard"},
            ),
            (
                self._overpass.build_query_around_leisure(lat, lon, radius_m, "skate_park"),
                {**base_payload, "tag": "leisure=skate_park"},
            ),
            (
                self._overpass.build_query_around_leisure(lat, lon, radius_m, "skatepark"),
                {**base_payload, "tag": "leisure=skatepark"},
            ),
        ]

        results = await asyncio.gather(
            *[self._overpass.query(query=q, cache_payload=payload) for q, payload in queries]
        )

        # Merge all elements and remove duplicates (same type+id)
        seen = set()
        all_elements = []
        for data in results:
            for el in data.get("elements", []):
                key = (el.get("type"), el.get("id"))
                if key not in seen:
                    seen.add(key)
                    all_elements.append(el)

        geojson = self._overpass.osm_elements_to_geojson(all_elements)

        # Only include skate parks that have a name in OSM (skip unnamed)
        features = geojson.get("features", [])
        skateparks = []
        for f in features:
            props = f.get("properties", {})
            tags = props.get("tags", {}) or {}
            name = (props.get("name") or "").strip()
            if not name:
                continue
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])  # [lon, lat]
            display_address = _build_display_address(tags)
            skateparks.append({
                "name": name,
                "lat": round(coords[1], 6),
                "lon": round(coords[0], 6),
                "address": display_address,
            })

        # Optionally resolve missing addresses via reverse geocoding (Nominatim: 1 req/sec)
        if resolve_address:
            for item in skateparks:
                if item["address"] is not None:
                    continue
                addr, from_cache = await asyncio.to_thread(
                    self._geocoding.reverse_geocode,
                    item["lat"],
                    item["lon"],
                )
                if addr:
                    item["address"] = addr
                if not from_cache:
                    await asyncio.sleep(1.1)  # respect Nominatim 1 request per second

        return {
            "skateparks": skateparks,
            "metadata": {
                "city": city,
                "address": center_address,
                "center": {"lat": lat, "lon": lon},
                "radius_m": radius_m,
                "total": len(skateparks),
            },
        }
