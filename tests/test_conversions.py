"""Tests for Hassio Units conversion policy."""

from __future__ import annotations

import pytest

from custom_components.hassio_units.conversions import (
    convert_state_value,
    default_enabled_categories,
    resolve_conversion,
)

TARGETS = {
    "power": "W",
    "energy": "kWh",
    "temperature": "°C",
    "electric_current": "A",
    "distance": "m",
    "energy_distance": "kWh/100km",
}


@pytest.mark.parametrize(
    ("value", "unit", "device_class", "target_overrides", "expected"),
    [
        ("1", "kW", "power", {}, 1000),
        ("3600000", "J", "energy", {}, 1),
        ("1000", "Wh", "energy", {}, 1),
        ("32", "°F", "temperature", {}, 0),
        ("1000", "mA", "current", {}, 1),
        ("1", "km", "distance", {}, 1000),
        ("1", "kWh", "energy", {"energy": "J"}, 3600000),
        ("1000", "Wh/km", "energy_distance", {}, 100),
    ],
)
def test_convert_state_value(
    value: str,
    unit: str,
    device_class: str,
    target_overrides: dict[str, str],
    expected: float,
) -> None:
    """Convert common Home Assistant sensor units."""
    targets = TARGETS | target_overrides

    converted = convert_state_value(
        value,
        unit,
        device_class,
        default_enabled_categories(),
        targets,
    )

    assert converted is not None
    assert converted[0] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("value", "unit", "device_class"),
    [
        ("1", "Beaufort", "wind_speed"),
        ("1", "mi/kWh", "energy_distance"),
        ("1", "km/kWh", "energy_distance"),
        ("not-a-number", "kW", "power"),
        ("1", "watts-ish", "power"),
        ("1", "mm", None),
    ],
)
def test_unsupported_cases(value: str, unit: str, device_class: str | None) -> None:
    """Skip unsupported, nonlinear, inverse, nonnumeric, and ambiguous states."""
    assert (
        convert_state_value(
            value,
            unit,
            device_class,
            default_enabled_categories(),
            TARGETS,
        )
        is None
    )


def test_invalid_yaml_target_skips_category() -> None:
    """Skip a category when YAML selects a target unsupported by that category."""
    assert (
        resolve_conversion(
            "kW",
            "power",
            default_enabled_categories(),
            {"power": "kWh"},
        )
        is None
    )
