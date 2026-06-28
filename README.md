# Hassio Units

Hassio Units is a Home Assistant custom integration that creates normalized
shadow sensors for existing `sensor.*` entities. It is intended for setups
where different integrations expose equivalent measurements in different units,
for example `kW` and `W`, or `J`, `Wh`, and `kWh`.

The integration leaves the original sensors untouched. For each eligible source
sensor it creates a separate normalized sensor with a configured target unit.
Only linear conversions are supported: `value * constant + offset`.

Examples:

- `1 kW` becomes `1000 W`
- `3600000 J` becomes `1 kWh`
- `32 °F` becomes `0 °C`
- `1000 mA` becomes `1 A`

## What it does

Hassio Units watches Home Assistant sensor states and creates one shadow sensor
for each source sensor that can be safely converted.

The shadow sensor:

- uses the configured target unit for that category;
- copies compatible metadata such as `device_class`, `state_class`, icon, and
  suggested display precision;
- exposes source metadata as attributes, including `source_entity_id`,
  `source_unit`, `source_value`, and `conversion_category`;
- becomes unavailable when the source sensor is unavailable or temporarily not
  convertible;
- is removed when the source sensor is removed.

Unsupported or ambiguous sensors are skipped. For example, Beaufort wind speed
is nonlinear, and `mi/kWh` or `km/kWh` vehicle efficiency units are inverse
units, so they are not converted. Ambiguous units such as `mm`, `cm`, or `in`
are only converted when Home Assistant provides enough `device_class` metadata
to identify the category.

## Installation with HACS

1. Open HACS.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add this repository:

   ```text
   https://github.com/tobias-/hassio_units/
   ```

4. Select category **Integration**.
5. Install **Hassio Units**.
6. Restart Home Assistant.
7. Go to **Settings > Devices & services** and add **Hassio Units**.

## Manual installation

Copy the integration directory into your Home Assistant config directory:

```text
custom_components/hassio_units
```

The final path should look like this:

```text
/config/custom_components/hassio_units/manifest.json
```

Restart Home Assistant, then add **Hassio Units** from
**Settings > Devices & services**.

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

Someone who prefers joules instead of kilowatt-hours can configure:

```yaml
hassio_units:
  targets:
    energy: J
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

## Local development

Create a virtual environment and install test dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest ruff homeassistant
```

Run the test suite:

```bash
.venv/bin/python -m pytest tests
```

Run linting:

```bash
.venv/bin/python -m ruff check custom_components tests
```

Run a syntax check:

```bash
.venv/bin/python -m compileall custom_components tests
```

## Docker Home Assistant test

This repository includes a minimal test Home Assistant configuration in
`docker-test/configuration.yaml`. It defines two template sensors and enables
Hassio Units with `power: W` and `energy: kWh`.

Validate the configuration with the official Home Assistant container:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/docker-test:/config" \
  -v "$PWD/custom_components/hassio_units:/config/custom_components/hassio_units:ro" \
  ghcr.io/home-assistant/home-assistant:stable \
  python -m homeassistant --script check_config -c /config
```

Run a short smoke test:

```bash
docker rm -f hassio-units-smoke || true
docker run -d \
  --name hassio-units-smoke \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/docker-test:/config" \
  -v "$PWD/custom_components/hassio_units:/config/custom_components/hassio_units:ro" \
  ghcr.io/home-assistant/home-assistant:stable
sleep 60
docker logs hassio-units-smoke --tail 300
docker rm -f hassio-units-smoke
```

The expected Home Assistant log output includes the standard warning that
custom integrations are not tested by Home Assistant. There should be no import,
setup, or config errors for `custom_components.hassio_units`.

## License

Apache License 2.0. See `LICENSE`.
