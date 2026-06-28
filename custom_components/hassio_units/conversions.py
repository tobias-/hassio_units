"""Unit conversion policy for Hassio Units."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Protocol

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    UnitOfIrradiance,
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfVolumetricFlux,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.unit_conversion import (
    AreaConverter,
    BloodGlucoseConcentrationConverter,
    ConductivityConverter,
    DataRateConverter,
    DistanceConverter,
    DurationConverter,
    ElectricCurrentConverter,
    ElectricPotentialConverter,
    EnergyConverter,
    InformationConverter,
    MassConverter,
    PowerConverter,
    PressureConverter,
    SpeedConverter,
    TemperatureConverter,
    UnitlessRatioConverter,
    VolumeConverter,
    VolumeFlowRateConverter,
)

from .const import DEFAULT_TARGET_UNITS


class UnitConverter(Protocol):
    """Protocol for Home Assistant unit converter classes."""

    VALID_UNITS: set[str | None]

    @classmethod
    def convert(cls, value: float, from_unit: str | None, to_unit: str | None) -> float:
        """Convert a value."""


@dataclass(frozen=True)
class LinearUnitConverter:
    """Small linear converter for HA units not covered by util.unit_conversion."""

    VALID_UNITS: set[str]
    ratios_to_base: Mapping[str, float]

    def convert(
        self, value: float, from_unit: str | None, to_unit: str | None
    ) -> float:
        """Convert using ratios to a category base unit."""
        if from_unit not in self.ratios_to_base or to_unit not in self.ratios_to_base:
            raise HomeAssistantError("Unsupported Hassio Units conversion")
        base_value = value * self.ratios_to_base[from_unit]
        return base_value / self.ratios_to_base[to_unit]


@dataclass(frozen=True)
class ConversionSpec:
    """Conversion category metadata."""

    category: str
    converter: type[UnitConverter] | LinearUnitConverter
    default_target_unit: str
    device_classes: frozenset[str] = frozenset()
    excluded_source_units: frozenset[str] = frozenset()

    @property
    def source_units(self) -> set[str]:
        """Return all supported source units after category exclusions."""
        return {
            unit
            for unit in self.converter.VALID_UNITS
            if unit is not None and unit not in self.excluded_source_units
        }

    def supports(self, unit: str | None) -> bool:
        """Return true if a source unit can be converted by this spec."""
        return unit in self.source_units

    def supports_target(self, unit: str | None) -> bool:
        """Return true if a target unit is valid for this category."""
        return (
            unit in self.converter.VALID_UNITS
            and unit not in self.excluded_source_units
        )

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert a source value to the selected target unit."""
        converted = self.converter.convert(value, from_unit, to_unit)
        if not isfinite(converted):
            raise HomeAssistantError("Conversion returned a non-finite value")
        return converted


IRRADIANCE_CONVERTER = LinearUnitConverter(
    VALID_UNITS={unit.value for unit in UnitOfIrradiance},
    ratios_to_base={
        UnitOfIrradiance.WATTS_PER_SQUARE_METER: 1.0,
        UnitOfIrradiance.BTUS_PER_HOUR_SQUARE_FOOT: 3.154590745,
    },
)

APPARENT_POWER_CONVERTER = LinearUnitConverter(
    VALID_UNITS={"mVA", "VA", "kVA"},
    ratios_to_base={
        "mVA": 0.001,
        "VA": 1.0,
        "kVA": 1000.0,
    },
)

REACTIVE_POWER_CONVERTER = LinearUnitConverter(
    VALID_UNITS={"mvar", "var", "kvar"},
    ratios_to_base={
        "mvar": 0.001,
        "var": 1.0,
        "kvar": 1000.0,
    },
)

REACTIVE_ENERGY_CONVERTER = LinearUnitConverter(
    VALID_UNITS={"varh", "kvarh"},
    ratios_to_base={
        "varh": 1.0,
        "kvarh": 1000.0,
    },
)

ENERGY_DISTANCE_CONVERTER = LinearUnitConverter(
    VALID_UNITS={"kWh/100km", "Wh/km", "mi/kWh", "km/kWh"},
    ratios_to_base={
        "kWh/100km": 1.0,
        "Wh/km": 0.1,
    },
)

FREQUENCY_CONVERTER = LinearUnitConverter(
    VALID_UNITS={"mHz", "Hz", "kHz", "MHz", "GHz"},
    ratios_to_base={
        "mHz": 0.001,
        "Hz": 1.0,
        "kHz": 1_000.0,
        "MHz": 1_000_000.0,
        "GHz": 1_000_000_000.0,
    },
)

_AMBIENT_IDEAL_GAS_MOLAR_VOLUME = 0.024055450596


def _gas_mass_converter(molar_mass: float, *, ppm: bool = False) -> LinearUnitConverter:
    """Build a gas ratio to mass concentration converter."""
    ratios = {
        "ppb": molar_mass / (_AMBIENT_IDEAL_GAS_MOLAR_VOLUME * 1000),
        "μg/m³": 1.0,
    }
    if ppm:
        ratios["ppm"] = molar_mass / _AMBIENT_IDEAL_GAS_MOLAR_VOLUME
    if ppm:
        ratios["mg/m³"] = 1000.0

    return LinearUnitConverter(VALID_UNITS=set(ratios), ratios_to_base=ratios)


CARBON_MONOXIDE_CONVERTER = _gas_mass_converter(28.01, ppm=True)
NITROGEN_DIOXIDE_CONVERTER = _gas_mass_converter(46.0055, ppm=True)
NITROGEN_MONOXIDE_CONVERTER = _gas_mass_converter(30.0061)
OZONE_CONVERTER = _gas_mass_converter(48.0, ppm=True)
SULPHUR_DIOXIDE_CONVERTER = _gas_mass_converter(64.066)

PRECIPITATION_DEPTH_CONVERTER = LinearUnitConverter(
    VALID_UNITS={unit.value for unit in UnitOfPrecipitationDepth},
    ratios_to_base={
        UnitOfPrecipitationDepth.MILLIMETERS: 1.0,
        UnitOfPrecipitationDepth.CENTIMETERS: 10.0,
        UnitOfPrecipitationDepth.INCHES: 25.4,
    },
)

MASS_VOLUME_CONCENTRATION_CONVERTER = LinearUnitConverter(
    VALID_UNITS={"g/m³", "mg/m³", "μg/m³", "μg/ft³"},
    ratios_to_base={
        "μg/m³": 1.0,
        "mg/m³": 1_000.0,
        "g/m³": 1_000_000.0,
        "μg/ft³": 35.314666721,
    },
)

VOLUMETRIC_FLUX_CONVERTER = LinearUnitConverter(
    VALID_UNITS={unit.value for unit in UnitOfVolumetricFlux},
    ratios_to_base={
        UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR: 1.0,
        UnitOfVolumetricFlux.MILLIMETERS_PER_DAY: 1.0 / 24.0,
        UnitOfVolumetricFlux.INCHES_PER_HOUR: 25.4,
        UnitOfVolumetricFlux.INCHES_PER_DAY: 25.4 / 24.0,
    },
)

def _device_classes(*names: str) -> frozenset[str]:
    """Return device class values that exist in the installed HA version."""
    return frozenset(
        getattr(device_class, "value", str(device_class))
        for name in names
        if (device_class := getattr(SensorDeviceClass, name, None)) is not None
    )


SPEC_BY_CATEGORY: dict[str, ConversionSpec] = {
    "absolute_humidity": ConversionSpec(
        "absolute_humidity",
        MASS_VOLUME_CONCENTRATION_CONVERTER,
        DEFAULT_TARGET_UNITS["absolute_humidity"],
        _device_classes("ABSOLUTE_HUMIDITY"),
    ),
    "apparent_power": ConversionSpec(
        "apparent_power",
        APPARENT_POWER_CONVERTER,
        DEFAULT_TARGET_UNITS["apparent_power"],
        _device_classes("APPARENT_POWER"),
    ),
    "area": ConversionSpec(
        "area",
        AreaConverter,
        DEFAULT_TARGET_UNITS["area"],
        _device_classes("AREA"),
    ),
    "blood_glucose_concentration": ConversionSpec(
        "blood_glucose_concentration",
        BloodGlucoseConcentrationConverter,
        DEFAULT_TARGET_UNITS["blood_glucose_concentration"],
        _device_classes("BLOOD_GLUCOSE_CONCENTRATION"),
    ),
    "carbon_monoxide": ConversionSpec(
        "carbon_monoxide",
        CARBON_MONOXIDE_CONVERTER,
        DEFAULT_TARGET_UNITS["carbon_monoxide"],
        _device_classes("CO"),
    ),
    "carbon_dioxide": ConversionSpec(
        "carbon_dioxide",
        UnitlessRatioConverter,
        DEFAULT_TARGET_UNITS["carbon_dioxide"],
        _device_classes("CO2"),
    ),
    "conductivity": ConversionSpec(
        "conductivity",
        ConductivityConverter,
        DEFAULT_TARGET_UNITS["conductivity"],
        _device_classes("CONDUCTIVITY"),
    ),
    "data_rate": ConversionSpec(
        "data_rate",
        DataRateConverter,
        DEFAULT_TARGET_UNITS["data_rate"],
        _device_classes("DATA_RATE"),
    ),
    "distance": ConversionSpec(
        "distance",
        DistanceConverter,
        DEFAULT_TARGET_UNITS["distance"],
        _device_classes("DISTANCE"),
    ),
    "duration": ConversionSpec(
        "duration",
        DurationConverter,
        DEFAULT_TARGET_UNITS["duration"],
        _device_classes("DURATION"),
    ),
    "electric_current": ConversionSpec(
        "electric_current",
        ElectricCurrentConverter,
        DEFAULT_TARGET_UNITS["electric_current"],
        _device_classes("CURRENT"),
    ),
    "electric_potential": ConversionSpec(
        "electric_potential",
        ElectricPotentialConverter,
        DEFAULT_TARGET_UNITS["electric_potential"],
        _device_classes("VOLTAGE"),
    ),
    "energy": ConversionSpec(
        "energy",
        EnergyConverter,
        DEFAULT_TARGET_UNITS["energy"],
        _device_classes("ENERGY", "ENERGY_STORAGE"),
    ),
    "energy_distance": ConversionSpec(
        "energy_distance",
        ENERGY_DISTANCE_CONVERTER,
        DEFAULT_TARGET_UNITS["energy_distance"],
        _device_classes("ENERGY_DISTANCE"),
        frozenset({"km/kWh", "mi/kWh"}),
    ),
    "frequency": ConversionSpec(
        "frequency",
        FREQUENCY_CONVERTER,
        DEFAULT_TARGET_UNITS["frequency"],
        _device_classes("FREQUENCY"),
    ),
    "information": ConversionSpec(
        "information",
        InformationConverter,
        DEFAULT_TARGET_UNITS["information"],
        _device_classes("DATA_SIZE"),
    ),
    "irradiance": ConversionSpec(
        "irradiance",
        IRRADIANCE_CONVERTER,
        DEFAULT_TARGET_UNITS["irradiance"],
        _device_classes("IRRADIANCE"),
    ),
    "mass": ConversionSpec(
        "mass",
        MassConverter,
        DEFAULT_TARGET_UNITS["mass"],
        _device_classes("WEIGHT"),
    ),
    "mass_volume_concentration": ConversionSpec(
        "mass_volume_concentration",
        MASS_VOLUME_CONCENTRATION_CONVERTER,
        DEFAULT_TARGET_UNITS["mass_volume_concentration"],
        _device_classes("PM1", "PM10", "PM25", "PM4"),
    ),
    "nitrogen_dioxide": ConversionSpec(
        "nitrogen_dioxide",
        NITROGEN_DIOXIDE_CONVERTER,
        DEFAULT_TARGET_UNITS["nitrogen_dioxide"],
        _device_classes("NITROGEN_DIOXIDE"),
    ),
    "nitrogen_monoxide": ConversionSpec(
        "nitrogen_monoxide",
        NITROGEN_MONOXIDE_CONVERTER,
        DEFAULT_TARGET_UNITS["nitrogen_monoxide"],
        _device_classes("NITROGEN_MONOXIDE"),
    ),
    "nitrous_oxide": ConversionSpec(
        "nitrous_oxide",
        UnitlessRatioConverter,
        DEFAULT_TARGET_UNITS["nitrous_oxide"],
        _device_classes("NITROUS_OXIDE"),
    ),
    "ozone": ConversionSpec(
        "ozone",
        OZONE_CONVERTER,
        DEFAULT_TARGET_UNITS["ozone"],
        _device_classes("OZONE"),
    ),
    "power": ConversionSpec(
        "power",
        PowerConverter,
        DEFAULT_TARGET_UNITS["power"],
        _device_classes("POWER"),
    ),
    "precipitation_depth": ConversionSpec(
        "precipitation_depth",
        PRECIPITATION_DEPTH_CONVERTER,
        DEFAULT_TARGET_UNITS["precipitation_depth"],
        _device_classes("PRECIPITATION"),
    ),
    "pressure": ConversionSpec(
        "pressure",
        PressureConverter,
        DEFAULT_TARGET_UNITS["pressure"],
        _device_classes("ATMOSPHERIC_PRESSURE", "PRESSURE"),
    ),
    "reactive_energy": ConversionSpec(
        "reactive_energy",
        REACTIVE_ENERGY_CONVERTER,
        DEFAULT_TARGET_UNITS["reactive_energy"],
        _device_classes("REACTIVE_ENERGY"),
    ),
    "reactive_power": ConversionSpec(
        "reactive_power",
        REACTIVE_POWER_CONVERTER,
        DEFAULT_TARGET_UNITS["reactive_power"],
        _device_classes("REACTIVE_POWER"),
    ),
    "ratio": ConversionSpec(
        "ratio",
        UnitlessRatioConverter,
        DEFAULT_TARGET_UNITS["ratio"],
        _device_classes("BATTERY", "HUMIDITY", "MOISTURE", "POWER_FACTOR"),
    ),
    "speed": ConversionSpec(
        "speed",
        SpeedConverter,
        DEFAULT_TARGET_UNITS["speed"],
        _device_classes("SPEED", "WIND_SPEED"),
        frozenset(
            {
                UnitOfSpeed.BEAUFORT,
                UnitOfVolumetricFlux.INCHES_PER_DAY,
                UnitOfVolumetricFlux.INCHES_PER_HOUR,
                UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
                UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
            }
        ),
    ),
    "sulphur_dioxide": ConversionSpec(
        "sulphur_dioxide",
        SULPHUR_DIOXIDE_CONVERTER,
        DEFAULT_TARGET_UNITS["sulphur_dioxide"],
        _device_classes("SULPHUR_DIOXIDE"),
    ),
    "temperature": ConversionSpec(
        "temperature",
        TemperatureConverter,
        DEFAULT_TARGET_UNITS["temperature"],
        _device_classes("TEMPERATURE"),
    ),
    "volume": ConversionSpec(
        "volume",
        VolumeConverter,
        DEFAULT_TARGET_UNITS["volume"],
        _device_classes("VOLUME", "VOLUME_STORAGE", "GAS", "WATER"),
    ),
    "volatile_organic_compounds_parts": ConversionSpec(
        "volatile_organic_compounds_parts",
        UnitlessRatioConverter,
        DEFAULT_TARGET_UNITS["volatile_organic_compounds_parts"],
        _device_classes("VOLATILE_ORGANIC_COMPOUNDS_PARTS"),
    ),
    "volume_flow_rate": ConversionSpec(
        "volume_flow_rate",
        VolumeFlowRateConverter,
        DEFAULT_TARGET_UNITS["volume_flow_rate"],
        _device_classes("VOLUME_FLOW_RATE"),
    ),
    "volumetric_flux": ConversionSpec(
        "volumetric_flux",
        VOLUMETRIC_FLUX_CONVERTER,
        DEFAULT_TARGET_UNITS["volumetric_flux"],
        _device_classes("PRECIPITATION_INTENSITY"),
    ),
}


DEVICE_CLASS_TO_CATEGORY: dict[str, str] = {
    device_class: spec.category
    for spec in SPEC_BY_CATEGORY.values()
    for device_class in spec.device_classes
}


@dataclass(frozen=True)
class ResolvedConversion:
    """A conversion selected for a concrete source sensor."""

    spec: ConversionSpec
    target_unit: str


def normalize_device_class(device_class: object) -> str | None:
    """Return a string device class value."""
    if device_class is None:
        return None
    return getattr(device_class, "value", str(device_class))


def resolve_conversion(
    source_unit: str | None,
    device_class: object,
    enabled_categories: set[str],
    target_units: Mapping[str, str],
) -> ResolvedConversion | None:
    """Resolve a source unit and device class into a conversion spec."""
    if source_unit is None:
        return None

    device_class_value = normalize_device_class(device_class)
    category = DEVICE_CLASS_TO_CATEGORY.get(device_class_value or "")
    if category:
        spec = SPEC_BY_CATEGORY[category]
        return _resolve_spec(spec, source_unit, enabled_categories, target_units)

    candidates = [
        spec
        for spec in SPEC_BY_CATEGORY.values()
        if spec.category in enabled_categories and spec.supports(source_unit)
    ]
    if len(candidates) != 1:
        return None

    return _resolve_spec(candidates[0], source_unit, enabled_categories, target_units)


def _resolve_spec(
    spec: ConversionSpec,
    source_unit: str,
    enabled_categories: set[str],
    target_units: Mapping[str, str],
) -> ResolvedConversion | None:
    """Resolve a conversion for a known category."""
    if spec.category not in enabled_categories or not spec.supports(source_unit):
        return None

    target_unit = target_units.get(spec.category, spec.default_target_unit)
    if not spec.supports_target(target_unit):
        return None

    return ResolvedConversion(spec=spec, target_unit=target_unit)


def convert_state_value(
    value: str,
    source_unit: str | None,
    device_class: object,
    enabled_categories: set[str],
    target_units: Mapping[str, str],
) -> tuple[float, ResolvedConversion] | None:
    """Convert a Home Assistant state string if it is eligible."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if not isfinite(numeric_value):
        return None

    resolved = resolve_conversion(
        source_unit, device_class, enabled_categories, target_units
    )
    if resolved is None:
        return None

    try:
        converted = resolved.spec.convert(
            numeric_value, source_unit or "", resolved.target_unit
        )
    except HomeAssistantError:
        return None

    return converted, resolved


def default_enabled_categories() -> set[str]:
    """Return all categories enabled by default."""
    return set(SPEC_BY_CATEGORY)
