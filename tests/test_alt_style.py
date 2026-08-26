from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

import pytest

from dti.enums import PetPose
from dti.http import HTTPClient
from dti.models import AltStyle

if TYPE_CHECKING:
    from dti.client import Client


def test_alt_style_model(
    client: Client,
    alt_style_data_species_31: list[dict[str, Any]],
) -> None:
    data = alt_style_data_species_31[0]
    alt_style = AltStyle(state=client._state, data=data)

    assert alt_style.id == 92370
    assert alt_style.species_id == 31
    assert alt_style.color_id == 44
    assert alt_style.body_id == 1170
    assert alt_style.adjective_name == "Aquatic Maraquan"
    assert alt_style.series_main_name == "Aquatic"
    assert alt_style.thumbnail_url == "https://images.neopets.com/items/035666cd.gif"


def test_alt_style_appearance(
    client: Client,
    alt_style_data_species_31: list[dict[str, Any]],
) -> None:
    data = alt_style_data_species_31[0]
    alt_style = AltStyle(state=client._state, data=data)

    appearance = alt_style.appearance
    assert appearance.pose == PetPose.UNKNOWN
    assert appearance.body_id == 1170
    assert appearance.is_glitched is False
    # real names resolved from the species/color cache seeded in conftest.py
    assert appearance.species.name == "Lupe"
    assert appearance.color.name == "Maraquan"

    assert len(alt_style.layers) == 1
    layer = alt_style.layers[0]
    assert layer.zone.id == 15
    assert layer.body_id == 1170
    assert layer.image_url == (
        "https://images.neopets.com/cp/bio/data/000/000/060/"
        "60189_e90d65ce95/60189.png?v=05d8742b2f"
    )


@pytest.mark.asyncio()
async def test_state_get_alt_style_caches(
    client: Client,
    alt_style_data_species_31: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    async def fake_fetch(
        self: HTTPClient,
        species_id: int,
    ) -> list[dict[str, Any]]:
        nonlocal calls
        calls += 1
        return alt_style_data_species_31

    monkeypatch.setattr(HTTPClient, "fetch_alt_styles_for_species", fake_fetch)
    client._state._alt_styles.pop(31, None)

    alt_style = await client._state.get_alt_style(species_id=31, alt_style_id=92370)
    assert alt_style is not None
    assert alt_style.id == 92370

    missing = await client._state.get_alt_style(species_id=31, alt_style_id=1)
    assert missing is None

    assert calls == 1  # second lookup reused the cached catalog, no re-fetch


@pytest.mark.asyncio()
async def test_fetch_neopet_alt_style(
    client: Client,
    alt_style_data_species_31: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_fetch(
        self: HTTPClient,
        species_id: int,
    ) -> list[dict[str, Any]]:
        return alt_style_data_species_31

    monkeypatch.setattr(HTTPClient, "fetch_alt_styles_for_species", fake_fetch)
    client._state._alt_styles.pop(31, None)

    neopet = await client.fetch_neopet_alt_style(
        species_id=31,
        alt_style_id=92370,
        name="test_pet",
    )

    assert neopet.alt_style is not None
    assert neopet.alt_style.id == 92370
    assert neopet.species.name == "Lupe"
    assert neopet.pose == PetPose.UNKNOWN
    assert "style=92370" in neopet.image_url


@pytest.mark.asyncio()
async def test_neopet_render_includes_style_param(
    client: Client,
    alt_style_data_species_31: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # regression test: Neopet.render() used to build its image request via
    # PetAppearance.read()/image_url() without ever passing the active alt style,
    # even though Neopet.image_url (the property) did it correctly - meaning the
    # actual rendered PNG silently dropped the style while other code paths worked.
    async def fake_fetch(
        self: HTTPClient,
        species_id: int,
    ) -> list[dict[str, Any]]:
        return alt_style_data_species_31

    monkeypatch.setattr(HTTPClient, "fetch_alt_styles_for_species", fake_fetch)
    client._state._alt_styles.pop(31, None)

    neopet = await client.fetch_neopet_alt_style(
        species_id=31,
        alt_style_id=92370,
        name="test_pet",
    )

    captured_urls: list[str] = []

    async def fake_fetch_binary_data(self: HTTPClient, url: str) -> bytes:
        captured_urls.append(url)
        return b""

    monkeypatch.setattr(HTTPClient, "_fetch_binary_data", fake_fetch_binary_data)

    await neopet.render(io.BytesIO())

    assert captured_urls
    assert "style=92370" in captured_urls[0]
