import logging

import httpx
from fastapi import APIRouter, HTTPException, Query
from geopy.exc import GeocoderServiceError, GeocoderTimedOut

from app.core.cache import TTLCache
from app.core.config import settings
from app.services.geocoding_service import GeocodingService
from app.services.overpass_service import OverpassService
from app.services.skatepark_service import SkateparksService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skateparks", tags=["skateparks"])

# Simple shared in-memory cache for MVP
cache = TTLCache()

# Services
geocoding_service = GeocodingService(cache)
overpass_service = OverpassService(cache)
skateparks_service = SkateparksService(geocoding_service, overpass_service)


@router.get("/by-city")
async def get_skateparks_by_city(
    city: str = Query(..., description="City name"),
    resolve_address: bool = Query(
        True,
        description="Resolve address via reverse geocoding when OSM has none. First request may be slower (~1s per park); then cached.",
    ),
):
    try:
        return await skateparks_service.find_by_city_and_radius(
            city=city,
            radius_m=settings.CITY_RADIUS_M,
            resolve_address=resolve_address,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except (GeocoderTimedOut, GeocoderServiceError) as exc:
        logger.exception("Geocoding failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Geocoding service temporarily unavailable. Try again later.",
        )
    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as exc:
        logger.exception("Overpass request failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Search service temporarily unavailable. Try again later.",
        )
    except RuntimeError as exc:
        logger.exception("Overpass error in response: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Search service temporarily unavailable. Try again later.",
        )
    except Exception as exc:
        logger.exception("external service error: %s", exc)
        raise HTTPException(status_code=502, detail="external service error")