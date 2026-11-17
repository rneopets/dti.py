from __future__ import annotations

import httpx
import pytest

from dti.errors import BrokenAssetImage
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


@pytest.mark.asyncio()
async def test_fetch_binary_data_raises_on_error_status() -> None:
    # regression: a 404/5xx used to be returned as-is, and the error page would only
    # blow up much later (e.g. PIL failing to parse HTML) - now it raises
    # BrokenAssetImage at the source, with the status in the message.
    client = HTTPClient()
    try:
        for status_code in (404, 502):
            response = httpx.Response(
                status_code,
                request=httpx.Request("GET", "https://example.com/asset.png"),
            )
            with pytest.raises(BrokenAssetImage, match=str(status_code)):
                await _fetch_binary_data(client, response)

        # a successful fetch still returns the raw bytes
        ok = httpx.Response(
            200,
            content=b"\x89PNG fake bytes",
            request=httpx.Request("GET", "https://example.com/asset.png"),
        )
        assert await _fetch_binary_data(client, ok) == b"\x89PNG fake bytes"
    finally:
        await client.aclose()


async def _fetch_binary_data(client: HTTPClient, response: httpx.Response) -> bytes:
    # the real method does its own request; this seam lets us inject a canned
    # response while exercising the exact status-checking logic.
    client._client.get = _FakeGet(response)  # type: ignore[method-assign]
    return await client._fetch_binary_data("https://example.com/asset.png")


class _FakeGet:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    async def __call__(self, *_args: object, **_kwargs: object) -> httpx.Response:
        return self.response
