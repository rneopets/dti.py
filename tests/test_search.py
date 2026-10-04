from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from dti.iterators import ItemSearch


class FakeHTTP:
    def __init__(self, total: int) -> None:
        self.total = total
        self.calls: list[dict[str, Any]] = []

    async def _query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(variables)
        start = variables["offset"]
        stop = min(start + variables["limit"], self.total)
        items = [
            {
                "id": str(i),
                "name": f"Item {i}",
                "description": "",
                "thumbnailUrl": "",
                "isNc": False,
                "isPb": False,
                "rarityIndex": "0",
            }
            for i in range(start, stop)
        ]
        return {"data": {"itemSearch": {"numTotalItems": self.total, "items": items}}}


def make_search(total: int, per_page: int = 30) -> tuple[ItemSearch, FakeHTTP]:
    http = FakeHTTP(total)
    state = SimpleNamespace(http=http)
    return ItemSearch(query="p", per_page=per_page, state=state), http  # type: ignore[arg-type]


@pytest.mark.asyncio()
async def test_item_search_paginates_offsets() -> None:
    search, http = make_search(total=75)

    items = await search.flatten()

    assert len(items) == 75
    assert [c["offset"] for c in http.calls] == [0, 30, 60]
    assert all(c["limit"] == 30 for c in http.calls)


@pytest.mark.asyncio()
async def test_item_search_exact_multiple_skips_empty_request() -> None:
    search, http = make_search(total=60)

    assert len(await search.flatten()) == 60
    assert [c["offset"] for c in http.calls] == [0, 30]


@pytest.mark.asyncio()
async def test_item_search_fetch_page_reports_total() -> None:
    search, http = make_search(total=75, per_page=10)
    assert search.total is None
    assert search.num_pages is None

    page = await search.fetch_page(2)

    assert [i.id for i in page] == list(range(20, 30))
    assert http.calls[0]["offset"] == 20
    assert search.total == 75
    assert search.num_pages == 8

    # fetching a page must not move the iterator
    assert search.offset == 0
    first = await search.next()
    assert first.id == 0


@pytest.mark.asyncio()
async def test_item_search_fetch_page_rejects_negative() -> None:
    search, _ = make_search(total=5)
    with pytest.raises(ValueError, match="non-negative"):
        await search.fetch_page(-1)
