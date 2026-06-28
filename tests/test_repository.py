"""Repository metadata tests."""

from __future__ import annotations

import json
from pathlib import Path


def test_manifest_metadata() -> None:
    """Validate key manifest metadata."""
    manifest = json.loads(
        Path("custom_components/hassio_units/manifest.json").read_text()
    )

    assert manifest["domain"] == "hassio_units"
    assert manifest["documentation"] == "https://github.com/tobias-/hassio_units/"
    assert manifest["issue_tracker"] == (
        "https://github.com/tobias-/hassio_units/issues"
    )
    assert manifest["codeowners"] == ["@tobias-"]
    assert manifest["config_flow"] is True
    assert manifest["version"]


def test_hacs_metadata() -> None:
    """Validate HACS metadata."""
    hacs = json.loads(Path("hacs.json").read_text())

    assert hacs["name"] == "Hassio Units"


def test_hacs_brand_asset() -> None:
    """Validate the HACS integration brand asset path."""
    icon = Path("custom_components/hassio_units/brand/icon.png")

    assert icon.is_file()
    assert icon.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
