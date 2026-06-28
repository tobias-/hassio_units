"""Constants for the Hassio Units integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "hassio_units"
PLATFORMS = [Platform.SENSOR]

CONF_ENABLED_CATEGORIES = "enabled_categories"
CONF_EXCLUDE_ENTITIES = "exclude_entities"
CONF_INCLUDE_ENTITIES = "include_entities"
CONF_TARGETS = "targets"

ATTR_CONVERSION_CATEGORY = "conversion_category"
ATTR_SOURCE_ENTITY_ID = "source_entity_id"
ATTR_SOURCE_UNIT = "source_unit"
ATTR_SOURCE_VALUE = "source_value"

DEFAULT_TARGET_UNITS: dict[str, str] = {
    "absolute_humidity": "g/m³",
    "apparent_power": "VA",
    "area": "m²",
    "blood_glucose_concentration": "mg/dL",
    "carbon_monoxide": "μg/m³",
    "carbon_dioxide": "ppm",
    "conductivity": "μS/cm",
    "data_rate": "B/s",
    "distance": "m",
    "duration": "s",
    "electric_current": "A",
    "electric_potential": "V",
    "energy": "kWh",
    "energy_distance": "kWh/100km",
    "frequency": "Hz",
    "information": "B",
    "irradiance": "W/m²",
    "mass": "g",
    "mass_volume_concentration": "μg/m³",
    "nitrogen_dioxide": "μg/m³",
    "nitrogen_monoxide": "μg/m³",
    "nitrous_oxide": "ppb",
    "ozone": "μg/m³",
    "power": "W",
    "precipitation_depth": "mm",
    "pressure": "Pa",
    "reactive_energy": "varh",
    "reactive_power": "var",
    "ratio": "%",
    "speed": "m/s",
    "sulphur_dioxide": "μg/m³",
    "temperature": "°C",
    "volatile_organic_compounds_parts": "ppm",
    "volume": "L",
    "volume_flow_rate": "L/min",
    "volumetric_flux": "mm/h",
}
