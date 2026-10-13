from __future__ import annotations

import pytest

from dti.enums import AppearanceLayerKnownGlitch, PetPose, try_enum


def test_try_enum_known_value() -> None:
    assert (
        try_enum(AppearanceLayerKnownGlitch, "OFFICIAL_SWF_IS_INCORRECT")
        is AppearanceLayerKnownGlitch.OFFICIAL_SWF_IS_INCORRECT
    )


def test_try_enum_unknown_value_plain_enum() -> None:
    # regression: a plain enum raises ValueError for an unknown value, which the old
    # `except TypeError` never caught - so a brand-new glitch type from DTI crashed
    # every appearance parse instead of falling back to the raw string.
    assert try_enum(AppearanceLayerKnownGlitch, "TOTALLY_NEW_GLITCH") == (
        "TOTALLY_NEW_GLITCH"
    )


def test_try_enum_unknown_value_dti_enum() -> None:
    # regression: _DTIEnum overrides _missing_ with a name lookup, which raises
    # KeyError for an unknown value - also not caught by the old `except TypeError`.
    assert try_enum(PetPose, "SOME_NEW_POSE") == "SOME_NEW_POSE"


def test_try_enum_none() -> None:
    assert try_enum(AppearanceLayerKnownGlitch, None) is None


@pytest.mark.parametrize(
    ("cls", "value"),
    [
        (AppearanceLayerKnownGlitch, 12345),
        (PetPose, "NOT_A_POSE"),
    ],
)
def test_try_enum_garbage_falls_back(cls: type, value: object) -> None:
    assert try_enum(cls, value) is value
