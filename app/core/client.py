import httpx


def build_async_client(timeout_seconds: int) -> httpx.AsyncClient:
    """
    Creates a reusable async HTTP client.
    """
    return httpx.AsyncClient(timeout=timeout_seconds)
