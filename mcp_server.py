"""
Skateparks MCP server – exposes skate park search as a tool for LLM/assistant use.

How to run:
  python mcp_server.py              # stdio + HTTP (both)
  python mcp_server.py --stdio     # stdio only (e.g. for Cursor)
  python mcp_server.py --http      # HTTP only on port 8010

HTTP (streamable-http): use from another terminal with an MCP client or
  curl -X POST http://127.0.0.1:8010/mcp/ -H "Content-Type: application/json" -d '...'
"""

import argparse
import json
import threading

from fastmcp import FastMCP

from app.core.cache import TTLCache
from app.core.config import settings
from app.services.geocoding_service import GeocodingService
from app.services.overpass_service import OverpassService
from app.services.skatepark_service import SkateparksService

# Same service setup as the API
_cache = TTLCache()
_geocoding = GeocodingService(_cache)
_overpass = OverpassService(_cache)
_skateparks = SkateparksService(_geocoding, _overpass)

mcp = FastMCP("Skateparks Server")


@mcp.resource("skateparks://info")
def get_server_info() -> str:
    """
    Information about the skateparks MCP server.

    Returns capabilities, data sources, and usage.
    """
    return """
    Skateparks MCP Server

    Capabilities:
    - List skate parks for any city worldwide (named parks only, from OpenStreetMap)
    - Geocoding via Nominatim; skate park data via Overpass API
    - Optional address resolution per park (slower)

    Data sources:
    - OpenStreetMap (Overpass API) – leisure=pitch+sport=skateboard, leisure=skate_park, leisure=skatepark
    - Nominatim – geocoding and reverse geocoding

    Usage:
    Use the get_skateparks tool with a city name to get skate parks in that city (within 50 km of center).
    """


@mcp.prompt()
def analyze_skateparks(location: str) -> str:
    """
    Generate a prompt for analyzing skate parks in a city.

    Args:
        location: City name to analyze (e.g. "Lisbon", "Barcelona").
    """
    return f"""
    Please analyze skate parks in {location} and provide:

    1. How many skate parks were found and where they are (names and areas).
    2. Which ones have an address and which are best for visiting.
    3. A short summary for someone planning a skate session in {location}.

    Use the get_skateparks tool to get the data, then give a clear, useful summary.
    """


@mcp.tool()
async def get_skateparks(city_name: str, resolve_address: bool = False) -> str:
    """
    Get skate parks for a city by name.

    Returns skate parks from OpenStreetMap within 50 km of the city center.
    Only parks with a name in OSM are included. Result is JSON plus a short
    text summary for LLM context.

    Args:
        city_name: City name (e.g. "Lisbon", "Barcelona", "São Paulo").
        resolve_address: If True, resolve address per park via reverse geocoding (slower).

    Returns:
        JSON response and summary text.
    """
    try:
        result = await _skateparks.find_by_city_and_radius(
            city=city_name.strip(),
            radius_m=settings.CITY_RADIUS_M,
            resolve_address=resolve_address,
        )
    except ValueError as e:
        return json.dumps({"error": str(e), "skateparks": [], "metadata": {}})
    except Exception as e:
        return json.dumps({"error": f"Service error: {e}", "skateparks": [], "metadata": {}})

    # JSON for machines
    out = json.dumps(result, ensure_ascii=False, indent=2)

    # Short summary for LLM
    meta = result.get("metadata", {})
    parks = result.get("skateparks", [])
    total = meta.get("total", 0)
    city = meta.get("city", city_name)
    center = meta.get("address") or meta.get("center", {})

    summary = f"\nSummary: {total} skate park(s) found for {city}. Center: {center}. Full JSON above."
    return out + summary


MCP_HTTP_HOST = "127.0.0.1"
MCP_HTTP_PORT = 8010  # distinct from API (8000)


def _run_http() -> None:
    mcp.run(
        transport="streamable-http",
        host=MCP_HTTP_HOST,
        port=MCP_HTTP_PORT,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skateparks MCP server")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stdio", action="store_true", help="Run stdio transport only")
    group.add_argument("--http", action="store_true", help="Run HTTP transport only on port 8010")
    args = parser.parse_args()

    if args.stdio:
        mcp.run()
    elif args.http:
        mcp.run(
            transport="streamable-http",
            host=MCP_HTTP_HOST,
            port=MCP_HTTP_PORT,
        )
    else:
        # Both: HTTP in background thread, stdio in main
        t = threading.Thread(target=_run_http, daemon=True)
        t.start()
        mcp.run()
