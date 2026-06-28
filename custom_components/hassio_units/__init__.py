"""Hassio Units integration."""

from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENABLED_CATEGORIES,
    CONF_EXCLUDE_ENTITIES,
    CONF_INCLUDE_ENTITIES,
    CONF_TARGETS,
    DOMAIN,
    PLATFORMS,
)
from .conversions import SPEC_BY_CATEGORY


def _validate_targets(targets: dict[str, str]) -> dict[str, str]:
    """Validate configured target units."""
    for category, target_unit in targets.items():
        if not SPEC_BY_CATEGORY[category].supports_target(target_unit):
            raise vol.Invalid(f"{target_unit} is not valid for {category}")
    return targets


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default="Hassio Units"): cv.string,
                vol.Optional(CONF_TARGETS, default={}): vol.All(
                    {vol.In(sorted(SPEC_BY_CATEGORY)): cv.string},
                    _validate_targets,
                ),
                vol.Optional(CONF_INCLUDE_ENTITIES, default=[]): cv.entity_ids,
                vol.Optional(CONF_EXCLUDE_ENTITIES, default=[]): cv.entity_ids,
                vol.Optional(CONF_ENABLED_CATEGORIES): vol.All(
                    cv.ensure_list, [vol.In(sorted(SPEC_BY_CATEGORY))]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Hassio Units from YAML."""
    if DOMAIN not in config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=config[DOMAIN],
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hassio Units from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Hassio Units config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        manager = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if manager is not None:
            manager.async_stop()
    return unloaded
