"""Normalized unit sensors for Hassio Units."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_STATE_CHANGED,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType

try:
    from homeassistant.core import CALLBACK_TYPE
except ImportError:  # pragma: no cover - compatibility with older HA typing exports
    CALLBACK_TYPE = Callable[[], None]

from .const import (
    ATTR_CONVERSION_CATEGORY,
    ATTR_SOURCE_ENTITY_ID,
    ATTR_SOURCE_UNIT,
    ATTR_SOURCE_VALUE,
    CONF_ENABLED_CATEGORIES,
    CONF_EXCLUDE_ENTITIES,
    CONF_INCLUDE_ENTITIES,
    CONF_TARGETS,
    DOMAIN,
)
from .conversions import (
    ResolvedConversion,
    convert_state_value,
    default_enabled_categories,
    resolve_conversion,
)

SOURCE_DOMAIN = "sensor"
STATE_CLASS = "state_class"
SUGGESTED_DISPLAY_PRECISION = "suggested_display_precision"


@dataclass(frozen=True)
class UnitRuntimeConfig:
    """Runtime conversion configuration."""

    enabled_categories: set[str]
    include_entities: set[str]
    exclude_entities: set[str]
    target_units: dict[str, str]

    def allows(self, entity_id: str) -> bool:
        """Return true if an entity can be considered."""
        if self.include_entities and entity_id not in self.include_entities:
            return False
        return entity_id not in self.exclude_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up normalized unit sensors."""
    config = _runtime_config(entry)
    manager = UnitSensorManager(hass, entry, config, async_add_entities)
    hass.data[DOMAIN][entry.entry_id] = manager
    manager.async_start()


def _runtime_config(entry: ConfigEntry) -> UnitRuntimeConfig:
    """Build runtime configuration from a config entry."""
    enabled_categories = set(
        entry.data.get(CONF_ENABLED_CATEGORIES) or default_enabled_categories()
    )
    return UnitRuntimeConfig(
        enabled_categories=enabled_categories,
        include_entities=set(entry.data.get(CONF_INCLUDE_ENTITIES, [])),
        exclude_entities=set(entry.data.get(CONF_EXCLUDE_ENTITIES, [])),
        target_units=dict(entry.data.get(CONF_TARGETS, {})),
    )


class UnitSensorManager:
    """Discover source sensors and create normalized shadow sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: UnitRuntimeConfig,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.entry = entry
        self.config = config
        self.async_add_entities = async_add_entities
        self.entities: dict[str, HassioUnitsSensor] = {}
        self._remove_listener: CALLBACK_TYPE | None = None

    @callback
    def async_start(self) -> None:
        """Start discovery and state tracking."""
        self._cleanup_stale_registry_entries()
        new_entities = [
            self._create_entity(state)
            for state in self.hass.states.async_all(SOURCE_DOMAIN)
            if self._is_eligible_source(state)
        ]
        if new_entities:
            self.async_add_entities(new_entities)

        self._remove_listener = self.hass.bus.async_listen(
            EVENT_STATE_CHANGED, self._async_state_changed
        )

    @callback
    def _cleanup_stale_registry_entries(self) -> None:
        """Remove stale shadow entries whose source state is no longer present."""
        registry = er.async_get(self.hass)
        for entity_entry in er.async_entries_for_config_entry(
            registry, self.entry.entry_id
        ):
            unique_id = entity_entry.unique_id
            prefix = f"{DOMAIN}_"
            if not unique_id.startswith(prefix):
                continue
            source_entity_id = unique_id.removeprefix(prefix)
            if (
                self.hass.states.get(source_entity_id) is None
                and registry.async_get(source_entity_id) is None
            ):
                registry.async_remove(entity_entry.entity_id)

    @callback
    def async_stop(self) -> None:
        """Stop state tracking."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @callback
    def _async_state_changed(self, event: Event) -> None:
        """Handle Home Assistant state changes."""
        entity_id = event.data.get("entity_id")
        if (
            not isinstance(entity_id, str)
            or entity_id.split(".", 1)[0] != SOURCE_DOMAIN
        ):
            return

        existing = self.entities.get(entity_id)
        new_state = event.data.get("new_state")
        if existing is not None:
            if new_state is None:
                self._remove_shadow_entity(entity_id)
                return
            existing.async_schedule_update_ha_state()
            return

        if isinstance(new_state, State) and self._is_eligible_source(new_state):
            self.async_add_entities([self._create_entity(new_state)])

    @callback
    def _remove_shadow_entity(self, source_entity_id: str) -> None:
        """Remove the shadow entity for a removed source entity."""
        entity = self.entities.pop(source_entity_id, None)
        if entity is None:
            return

        if entity.entity_id is not None:
            registry = er.async_get(self.hass)
            if registry.async_get(entity.entity_id) is not None:
                registry.async_remove(entity.entity_id)

        self.hass.async_create_task(entity.async_remove(force_remove=True))

    def _is_eligible_source(self, state: State) -> bool:
        """Return true if the state should get a normalized entity."""
        entity_id = state.entity_id
        if not self.config.allows(entity_id):
            return False
        if state.attributes.get(ATTR_SOURCE_ENTITY_ID):
            return False
        if entity_id in self.entities:
            return False
        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return False

        source_unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        device_class = state.attributes.get(ATTR_DEVICE_CLASS)
        return (
            resolve_conversion(
                source_unit,
                device_class,
                self.config.enabled_categories,
                self.config.target_units,
            )
            is not None
        )

    def _create_entity(self, state: State) -> HassioUnitsSensor:
        """Create and remember a normalized sensor entity."""
        entity = HassioUnitsSensor(self.hass, self.entry, self.config, state.entity_id)
        self.entities[state.entity_id] = entity
        return entity


class HassioUnitsSensor(SensorEntity, RestoreEntity):
    """Sensor exposing a normalized unit value for a source sensor."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        config: UnitRuntimeConfig,
        source_entity_id: str,
    ) -> None:
        """Initialize the normalized sensor."""
        self.hass = hass
        self.entry = entry
        self.config = config
        self.source_entity_id = source_entity_id
        self._attr_unique_id = f"{DOMAIN}_{source_entity_id}"

    @property
    def name(self) -> str:
        """Return the sensor name."""
        state = self.hass.states.get(self.source_entity_id)
        friendly_name = (
            state.attributes.get(ATTR_FRIENDLY_NAME)
            if state is not None
            else self.source_entity_id
        )
        return f"{friendly_name} Normalized"

    @property
    def available(self) -> bool:
        """Return true if the source sensor can currently be converted."""
        return self._current_conversion() is not None

    @property
    def native_value(self) -> StateType:
        """Return the converted sensor state."""
        current = self._current_conversion()
        if current is None:
            return None
        converted, _resolved, _state = current
        return converted

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the configured target unit."""
        current = self._current_conversion()
        if current is None:
            return None
        _converted, resolved, _state = current
        return resolved.target_unit

    @property
    def device_class(self) -> str | None:
        """Copy the source device class."""
        state = self.hass.states.get(self.source_entity_id)
        if state is None:
            return None
        return state.attributes.get(ATTR_DEVICE_CLASS)

    @property
    def state_class(self) -> str | None:
        """Copy the source state class."""
        state = self.hass.states.get(self.source_entity_id)
        if state is None:
            return None
        return state.attributes.get(STATE_CLASS)

    @property
    def suggested_display_precision(self) -> int | None:
        """Copy the source suggested display precision."""
        state = self.hass.states.get(self.source_entity_id)
        if state is None:
            return None
        return state.attributes.get(SUGGESTED_DISPLAY_PRECISION)

    @property
    def icon(self) -> str | None:
        """Copy the source icon when present."""
        state = self.hass.states.get(self.source_entity_id)
        if state is None:
            return None
        return state.attributes.get(ATTR_ICON)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return source and conversion attributes."""
        state = self.hass.states.get(self.source_entity_id)
        attrs: dict[str, Any] = {ATTR_SOURCE_ENTITY_ID: self.source_entity_id}
        if state is None:
            return attrs

        attrs[ATTR_SOURCE_VALUE] = state.state
        attrs[ATTR_SOURCE_UNIT] = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        current = self._current_conversion()
        if current is not None:
            _converted, resolved, _state = current
            attrs[ATTR_CONVERSION_CATEGORY] = resolved.spec.category
        return attrs

    def _current_conversion(self) -> tuple[float, ResolvedConversion, State] | None:
        """Return the current converted value and metadata."""
        state = self.hass.states.get(self.source_entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None

        source_unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        device_class = state.attributes.get(ATTR_DEVICE_CLASS)
        converted = convert_state_value(
            state.state,
            source_unit,
            device_class,
            self.config.enabled_categories,
            self.config.target_units,
        )
        if converted is None:
            return None

        value, resolved = converted
        return value, resolved, state
