# vehicle-emissions-package

`vehicle-emissions-package` is a configurable Python package for generating
transport lifecycle emissions outputs from a reusable model configuration.

The package was extracted to support application-driven scenario analysis,
including frontend tools such as `LifeCycle.html`, where multiple transport
assumptions may be adjusted dynamically and the final emissions outcome must be
recomputed consistently.

## Features

- Builds a merged dataframe equivalent to the existing `df_merged_final.csv`
- Separates Well-to-Wheel and embodied/LCA logic into reusable functions
- Supports global, mode-level, and technology-level overrides
- Supports custom PHEV electric-drive shares
- Uses plain Python dictionaries that map cleanly from JSON payloads
- Validates inputs and raises descriptive `ValueError` exceptions

## Repository layout

```text
vehicle_emissions_package/
├── pyproject.toml
├── README.md
├── LICENSE
└── src/
    └── vehicle_emissions_package/
        ├── __init__.py
        ├── api.py
        └── model.py
```

## Installation

### Install locally in editable mode

```bash
pip install -e .
```

### Install directly from GitHub

```bash
pip install git+https://github.com/YOUR_GITHUB_USERNAME/vehicle-emissions-package.git
```

## Quick start

```python
from vehicle_emissions_package import build_df_merged_final

df = build_df_merged_final(electric_wtt=563.720573199372)
print(df.head())
```

## Public API

### Convenience API

Use this function when your application exposes a few scenario levers and needs
an updated merged dataframe directly.

```python
from vehicle_emissions_package import build_df_merged_final

df = build_df_merged_final(
    electric_wtt=450.0,
    mode_overrides={
        "Car": {"passenger_load": 1.7},
        "Bus": {"passenger_load": 20.0},
    },
    technology_overrides={
        "Car_BEV": {"consumption": 0.16, "B1_mfg": 44.0},
        "Rail_EV": {"annual_mileage": 72000},
    },
    emission_factor_overrides={
        "diesel": {"wtt": 520.0},
    },
    phev_share_overrides={
        "Car_PHEV": 0.72,
    },
)
```

### Full configuration API

Use this workflow when your backend manages a scenario object explicitly.

```python
from vehicle_emissions_package import (
    build_df_merged_final_from_config,
    get_default_model_config,
)

config = get_default_model_config()
config["emission_factors"]["electric"]["wtt"] = 420.0
config["vehicle_params"]["Car_BEV"]["consumption"] = 0.15
config["vehicle_params"]["Bus_BEV"]["passenger_load"] = 22.0

df = build_df_merged_final_from_config(config)
```

### Lower-level helpers

The package also exposes:

- `get_default_model_config()`
- `resolve_model_config()`
- `build_stream_a_dataframe()`
- `build_stream_b_dataframe()`
- `build_df_merged_final_from_config()`

## Configuration model

The model supports four layers of control:

1. Package defaults
2. Global emission factor overrides
3. Mode-level overrides
4. Technology-level overrides

Technology overrides take precedence over mode-level overrides.

## Mode overrides

Mode overrides are useful when a frontend exposes one lever per transport mode.

```python
mode_overrides = {
    "Car": {"passenger_load": 1.8},
    "Bike": {"B2_svc": 1.5},
}
```

Every technology with the matching `mode` receives those values unless a
technology-specific override replaces them.

## Technology overrides

Technology overrides are intended for more granular scenario design.

```python
technology_overrides = {
    "Car_BEV": {"consumption": 0.145, "B1_mfg": 41.5},
    "Taxi_BEV": {"passenger_load": 0.75},
}
```

## Output schema

The merged dataframe contains the following columns:

- `mode`
- `tech`
- `TTW_gCO2eq_per_pkm`
- `WTT_gCO2eq_per_pkm`
- `WTW_gCO2eq_per_pkm`
- `B1_flu_pkm`
- `B1_mfg_pkm`
- `B1_asm_pkm`
- `B1_tra_pkm`
- `B2_inf_pkm`
- `B2_svc_pkm`
- `B3_dis_pkm`

## Integration pattern for HTML applications

A typical backend flow for `LifeCycle.html` or similar tools is:

1. Receive a scenario payload from the frontend
2. Map the payload into `mode_overrides`, `technology_overrides`, and optional
   emission factor overrides
3. Call `build_df_merged_final(...)`
4. Serialize the dataframe to JSON records for the frontend

Because the package uses standard dictionaries for configuration, it integrates
cleanly with JSON APIs without requiring a custom serialization layer.

## Validation

The model validates:

- non-negative emission factors
- positive passenger load
- required fields for simple technologies and PHEVs
- valid fuel type references
- valid PHEV electric-drive shares

Invalid input raises `ValueError` with descriptive messages.

## Release notes

The current defaults intentionally mirror the values embedded in the existing
project outputs so the package can act as a stable backend extraction of the
original model.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
