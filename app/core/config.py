from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.
    Values can be overridden using environment variables.
    """

    # Required identification for Nominatim (avoid being blocked)
    NOMINATIM_USER_AGENT: str = "skateparks_api/0.1 (contact: dev@yourdomain.com)"
    NOMINATIM_TIMEOUT_SECONDS: int = 10

    # Overpass API configuration
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT_SECONDS: int = 35

    # Radius used for "all skate parks in city" (no user choice)
    CITY_RADIUS_M: int = 50_000   # 50 km from city center

    # Cache TTLs
    GEOCODE_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 30   # 30 days
    OVERPASS_CACHE_TTL_SECONDS: int = 60 * 30            # 30 minutes

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Pagination limits (protects your API and the client)
    # DEFAULT_PAGE: int = 1
    # DEFAULT_LIMIT: int = 25
    # MAX_LIMIT: int = 100


settings = Settings()