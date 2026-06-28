# Hassio Units

Hassio Units is a Home Assistant custom integration that creates normalized
shadow sensors for existing `sensor.*` entities. It leaves original entities
untouched and converts supported units with linear conversions such as
`value * constant + offset`.

Examples:

- `1 kW` becomes `1000 W`
- `3600000 J` becomes `1 kWh`
- `32 °F` becomes `0 °C`
- `1000 mA` becomes `1 A`

## Installation

Add this repository as a HACS custom repository:

```text
https://github.com/tobias-/hassio_units/
```

Choose category `Integration`, install it, restart Home Assistant, then add
**Hassio Units** from **Settings > Devices & services**.

## YAML configuration

YAML is optional. Without YAML, all supported categories are enabled with
practical metric targets such as `W`, `kWh`, `°C`, `Pa`, `m`, `L`, and `g`.

Target units can be overridden in `configuration.yaml`:

```yaml
hassio_units:
  targets:
    power: W
    energy: kWh
    temperature: °C
    pressure: hPa
```

You can also restrict or exclude entities:

```yaml
hassio_units:
  include_entities:
    - sensor.grid_power
    - sensor.grid_energy
  exclude_entities:
    - sensor.raw_debug_value
```

Limit conversion categories:

```yaml
hassio_units:
  enabled_categories:
    - power
    - energy
    - electric_current
    - electric_potential
```

If YAML is changed after setup, restart Home Assistant or reload the
integration.

## Supported categories

Default target units:

| Category | Default target |
| --- | --- |
| `absolute_humidity` | `g/m³` |
| `apparent_power` | `VA` |
| `area` | `m²` |
| `blood_glucose_concentration` | `mg/dL` |
| `carbon_dioxide` | `ppm` |
| `carbon_monoxide` | `μg/m³` |
| `conductivity` | `μS/cm` |
| `data_rate` | `B/s` |
| `distance` | `m` |
| `duration` | `s` |
| `electric_current` | `A` |
| `electric_potential` | `V` |
| `energy` | `kWh` |
| `energy_distance` | `kWh/100km` |
| `frequency` | `Hz` |
| `information` | `B` |
| `irradiance` | `W/m²` |
| `mass` | `g` |
| `mass_volume_concentration` | `μg/m³` |
| `nitrogen_dioxide` | `μg/m³` |
| `nitrogen_monoxide` | `μg/m³` |
| `nitrous_oxide` | `ppb` |
| `ozone` | `μg/m³` |
| `power` | `W` |
| `precipitation_depth` | `mm` |
| `pressure` | `Pa` |
| `ratio` | `%` |
| `reactive_energy` | `varh` |
| `reactive_power` | `var` |
| `speed` | `m/s` |
| `sulphur_dioxide` | `μg/m³` |
| `temperature` | `°C` |
| `volatile_organic_compounds_parts` | `ppm` |
| `volume` | `L` |
| `volume_flow_rate` | `L/min` |
| `volumetric_flux` | `mm/h` |

Unsupported or ambiguous sensors are skipped. For example, Beaufort wind speed
is nonlinear and `mi/kWh` or `km/kWh` vehicle efficiency units are inverse
units, so they are not converted.

When a source sensor disappears, its shadow sensor is removed. If a source
sensor is present but temporarily unavailable, the shadow sensor becomes
unavailable.
