"""Config flow for Hassio Units."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ENABLED_CATEGORIES,
    CONF_EXCLUDE_ENTITIES,
    CONF_INCLUDE_ENTITIES,
    CONF_TARGETS,
    DOMAIN,
)


class HassioUnitsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hassio Units."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle setup from the UI."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "Hassio Units"),
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Optional(CONF_NAME, default="Hassio Units"): str}
            ),
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Import YAML configuration."""
        title = user_input.get(CONF_NAME, "Hassio Units")
        data = {
            CONF_TARGETS: dict(user_input.get(CONF_TARGETS, {})),
            CONF_INCLUDE_ENTITIES: list(user_input.get(CONF_INCLUDE_ENTITIES, [])),
            CONF_EXCLUDE_ENTITIES: list(user_input.get(CONF_EXCLUDE_ENTITIES, [])),
        }
        if CONF_ENABLED_CATEGORIES in user_input:
            data[CONF_ENABLED_CATEGORIES] = list(user_input[CONF_ENABLED_CATEGORIES])

        entries = self._async_current_entries()
        if entries:
            self.hass.config_entries.async_update_entry(entries[0], data=data)
            return self.async_abort(reason="already_configured")

        return self.async_create_entry(title=title, data=data)
