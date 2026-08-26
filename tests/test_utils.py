from __future__ import annotations

from dti.enums import PetPose
from dti.utils import outfit_image_url


def test_outfit_image_url() -> None:
    url = outfit_image_url(
        species=1,
        color=8,
        pose=PetPose.HAPPY_FEM,
        style=90030,
        item_ids=[74967, 37002, 71526],
    )
    assert (
        url == "https://impress.openneo.net/outfits/new.png?"
        "species=1&color=8&pose=HAPPY_FEM&style=90030&"
        "objects%5B%5D=74967&objects%5B%5D=37002&objects%5B%5D=71526"
    )


def test_outfit_image_url_alt_style_pose_unknown_is_rewritten() -> None:
    # regression test: the classic renderer rejects pose=UNKNOWN with an HTTP 400,
    # but alt style appearances are always built with pose=UNKNOWN since pose isn't
    # a meaningful concept for them - the URL builder needs to substitute a real pose.
    url = outfit_image_url(
        species=31,
        color=44,
        pose=PetPose.UNKNOWN,
        style=92370,
    )
    assert "pose=HAPPY_MASC" in url
    assert "pose=UNKNOWN" not in url


def test_outfit_image_url_pose_unknown_without_style_is_unchanged() -> None:
    # the pose=UNKNOWN rewrite is specific to alt styles - without a style, pose
    # should pass through untouched (this scenario just shouldn't come up in
    # practice, but the function shouldn't silently rewrite pose on its own).
    url = outfit_image_url(species=1, color=8, pose=PetPose.UNKNOWN)
    assert "pose=UNKNOWN" in url
