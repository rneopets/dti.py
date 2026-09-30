from __future__ import annotations

import httpx
import pytest

from dti.http import HTTPClient


@pytest.mark.asyncio()
async def test_http_client_retries_without_proxy() -> None:
    client = HTTPClient(retries=7)
    try:
        pool = client._client._transport._pool  # type: ignore[attr-defined]
        assert pool._retries == 7
    finally:
        await client.aclose()


@pytest.mark.asyncio()
async def test_http_client_retries_with_proxy() -> None:
    # regression: with a proxy set, retries were silently dropped - first because
    # passing `proxy=` to AsyncClient mounts a separate proxy transport that shadows
    # the custom one, then because httpx's AsyncHTTPTransport proxy branch doesn't
    # forward retries to the pool it builds.
    client = HTTPClient(proxy="http://user:pass@localhost:8030", retries=7)
    try:
        transport = client._client._transport
        pool = transport._pool  # type: ignore[attr-defined]
        assert pool._retries == 7

        # the API endpoint must route through our transport, not a shadowing proxy
        # mount created by AsyncClient itself.
        api_url = httpx.URL(f"{HTTPClient.API_BASE}/graphql")
        assert client._client._transport_for_url(api_url) is transport
    finally:
        await client.aclose()
