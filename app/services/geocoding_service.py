import hashlib
import json
from geopy.geocoders import Nominatim

from app.core.cache import TTLCache
from app.core.config import settings


class GeocodingService:
    """
    Responsible for converting city names into coordinates.
    """

    def __init__(self, cache: TTLCache):
        self._cache = cache

    def _cache_key(self, city: str) -> str:
        payload = {"city": city.lower().strip()}
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return "geocode:" + hashlib.sha256(raw).hexdigest()

    def geocode_city(self, city: str) -> tuple[float, float, str]:
        """
        Converts a city name to (latitude, longitude, full_address).
        """
        city = city.strip()
        if not city:
            raise ValueError("city cannot be empty")

        cache_key = self._cache_key(city)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        geolocator = Nominatim(
            user_agent=settings.NOMINATIM_USER_AGENT,
            timeout=settings.NOMINATIM_TIMEOUT_SECONDS
        )

        location = geolocator.geocode(city, addressdetails=True)
        if location is None:
            raise ValueError(f"could not find location: {city}")

        result = (
            float(location.latitude),
            float(location.longitude),
            str(location.address)
        )

        self._cache.set(
            cache_key,
            result,
            ttl_seconds=settings.GEOCODE_CACHE_TTL_SECONDS
        )

        return result

    def _reverse_cache_key(self, lat: float, lon: float) -> str:
        payload = {"lat": round(lat, 5), "lon": round(lon, 5)}
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        return "reverse:" + hashlib.sha256(raw).hexdigest()

    def reverse_geocode(self, lat: float, lon: float) -> tuple[str | None, bool]:
        """
        Converts (lat, lon) to a readable address via Nominatim.
        Returns (address or None, from_cache). Successful results are cached.
        """
        cache_key = self._reverse_cache_key(lat, lon)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return (cached, True)

        geolocator = Nominatim(
            user_agent=settings.NOMINATIM_USER_AGENT,
            timeout=settings.NOMINATIM_TIMEOUT_SECONDS,
        )
        location = geolocator.reverse(f"{lat}, {lon}")
        if location is None:
            return (None, False)

        result = str(location.address)
        self._cache.set(
            cache_key,
            result,
            ttl_seconds=settings.GEOCODE_CACHE_TTL_SECONDS,
        )
        return (result, False)
