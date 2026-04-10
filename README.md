# vehicle-emissions-package

A configurable Python package for calculating transport lifecycle emissions.
It generates a DataFrame with **Well-to-Wheel (WTW)** and **embodied/LCA** emissions
for 18 vehicle technologies across 9 transport modes, expressed in **gCO2eq per passenger-km**.

## Installation

```bash
# From local repository
pip install -e .

# From GitHub
pip install git+https://github.com/j0anpau/vehicle-emissions-package.git
```

Requirements: Python >= 3.10, pandas >= 2.0

## Quick start

```python
from vehicle_emissions_package import build_df_merged_final

df = build_df_merged_final(electric_wtt=563.72)  # gCO2/kWh (ITF 2020, World)
print(df)
```

## Output DataFrame

The function `build_df_merged_final()` returns a DataFrame with **18 rows** (one per technology)
and **12 columns**. All emissions are in **gCO2eq/pkm** (grams of CO2 equivalent per passenger-kilometre).

### Identifier columns

| Column | Type | Description |
|--------|------|-------------|
| `mode` | str | Transport mode: Walk, Bike, BikeSharing, Moped, Car, Taxi, Bus, Train |
| `tech` | str | Specific vehicle technology (see technology table below) |

### Well-to-Wheel (WTW) columns -- Operational emissions

| Column | Units | Description |
|--------|-------|-------------|
| `TTW_gCO2eq_per_pkm` | gCO2eq/pkm | **Tank-to-Wheel**: direct tailpipe emissions from vehicle operation |
| `WTT_gCO2eq_per_pkm` | gCO2eq/pkm | **Well-to-Tank**: upstream emissions from fuel production and distribution |
| `WTW_gCO2eq_per_pkm` | gCO2eq/pkm | **Well-to-Wheel**: total operational emissions (TTW + WTT) |

### LCA columns -- Embodied emissions (lifecycle)

| Column | Units | Component | Description |
|--------|-------|-----------|-------------|
| `B1_flu_pkm` | gCO2eq/pkm | Fluids | Production of fluids and lubricants |
| `B1_mfg_pkm` | gCO2eq/pkm | Manufacturing | Vehicle manufacturing (materials, energy) |
| `B1_asm_pkm` | gCO2eq/pkm | Assembly | Final vehicle assembly |
| `B1_tra_pkm` | gCO2eq/pkm | Transport | Vehicle transport to point of sale |
| `B2_inf_pkm` | gCO2eq/pkm | Infrastructure | Construction and maintenance of infrastructure (roads, tracks, bike lanes) |
| `B2_svc_pkm` | gCO2eq/pkm | Service | Vehicle maintenance and repair over its lifetime |
| `B3_dis_pkm` | gCO2eq/pkm | Disposal | End-of-life scrapping, recycling, and disposal |

## Calculations

### 1. Well-to-Wheel emissions (Stream A)

Operational emissions per passenger-km are computed for each technology.

**Simple technologies** (non-PHEV):

```
TTW_gCO2eq_per_pkm = (consumption x emission_factor_ttw) / passenger_load
WTT_gCO2eq_per_pkm = (consumption x emission_factor_wtt) / passenger_load
WTW_gCO2eq_per_pkm = TTW + WTT
```

Where:
- `consumption` = vehicle energy consumption (L/km for combustion, kWh/km for electric)
- `emission_factor_ttw` = Tank-to-Wheel emission factor for the fuel type (gCO2/L or gCO2/kWh)
- `emission_factor_wtt` = Well-to-Tank emission factor for the fuel type (gCO2/L or gCO2/kWh)
- `passenger_load` = average vehicle occupancy (passengers/vehicle)

**PHEV technologies** (plug-in hybrid electric vehicles):

A weighted average between electric mode and combustion mode is computed:

```
TTW = (ev_share x consumption_ev x ttw_electric + ice_share x consumption_ice x ttw_fuel) / passenger_load
WTT = (ev_share x consumption_ev x wtt_electric + ice_share x consumption_ice x wtt_fuel) / passenger_load
WTW = TTW + WTT
```

Where `ev_share` is the fraction of km driven in electric mode (e.g. 0.66 for Car_PHEV)
and `ice_share = 1 - ev_share`.

### 2. Embodied/LCA emissions (Stream B)

For each LCA component, the emission per passenger-km is calculated as:

```
component_pkm = component_value / passenger_load
```

Where `component_value` is the fixed value for that technology in gCO2eq/vkm
(already amortised over vehicle lifetime and annual mileage).

### 3. Final merge

Both streams are merged on `(mode, tech)` and sorted alphabetically.

## Default emission factors

| Fuel | WTT (gCO2/unit) | TTW (gCO2/unit) | Unit |
|------|------------------:|------------------:|------|
| Electric | 563.72 | 0.00 | kWh |
| Gasoline | 450.58 | 2320.72 | L |
| Diesel | 503.12 | 2480.34 | L |
| Human | 0.00 | 0.00 | -- |

> The electric WTT factor (grid carbon intensity) is the primary lever for scenario analysis.

## Included technologies (18)

| Mode | Technology | Fuel | Consumption | Passenger load |
|------|-----------|------|-------------|---------------:|
| Walk | Walk | human | 0 | 1.0 |
| Bike | Bike_Standalone | human | 0 | 1.0 |
| Bike | eBike | electric | 0.020 kWh/km | 1.0 |
| BikeSharing | BikeSharing_Standalone | human | 0 | 1.0 |
| BikeSharing | eBikeSharing | electric | 0.020 kWh/km | 1.0 |
| Moped | Moped_ICE | gasoline | 0.019 L/km | 1.0 |
| Moped | Moped_BEV | electric | 0.040 kWh/km | 1.0 |
| Car | Car_ICE_Gasoline | gasoline | 0.068 L/km | 1.5 |
| Car | Car_ICE_Diesel | diesel | 0.054 L/km | 1.5 |
| Car | Car_PHEV | gasoline + electric | 0.051 L/km + 0.190 kWh/km | 1.5 |
| Car | Car_BEV | electric | 0.190 kWh/km | 1.5 |
| Taxi | Taxi_ICE | gasoline | 0.068 L/km | 0.62 |
| Taxi | Taxi_PHEV | gasoline + electric | 0.051 L/km + 0.190 kWh/km | 0.62 |
| Taxi | Taxi_BEV | electric | 0.190 kWh/km | 0.62 |
| Bus | Bus_ICE | diesel | 0.409 L/km | 15.3 |
| Bus | Bus_PHEV | diesel + electric | 0.300 L/km + 0.000 kWh/km | 15.3 |
| Bus | Bus_BEV | electric | 1.370 kWh/km | 15.3 |
| Train | Rail_EV | electric | 17.72 kWh/km | 190.0 |

### Default PHEV electric-drive shares

| Technology | % electric | % combustion |
|-----------|----------:|------------:|
| Car_PHEV | 66% | 34% |
| Taxi_PHEV | 36% | 64% |
| Bus_PHEV | 0% | 100% |

## Example output

Running with default parameters (`electric_wtt=563.72` gCO2/kWh, world average):

| mode        | tech                   |   TTW |   WTT |   WTW |   B1_flu |   B1_mfg |   B1_asm |   B1_tra |   B2_inf |   B2_svc |   B3_dis |
|:------------|:-----------------------|------:|------:|------:|---------:|---------:|---------:|---------:|---------:|---------:|---------:|
| Bike        | Bike_Standalone        |  0.00 |  0.00 |  0.00 |     0.22 |     5.40 |     0.83 |     0.78 |     9.47 |     0.00 |     0.24 |
| Bike        | eBike                  |  0.00 | 11.27 | 11.27 |     0.25 |     9.50 |     1.43 |     1.05 |     9.48 |     0.00 |     0.30 |
| BikeSharing | BikeSharing_Standalone |  0.00 |  0.00 |  0.00 |     0.71 |    16.71 |     2.60 |     2.55 |     9.49 |    24.70 |     0.74 |
| BikeSharing | eBikeSharing           |  0.00 | 11.27 | 11.27 |     0.82 |    27.72 |     4.59 |     3.02 |     9.50 |    24.70 |     0.98 |
| Bus         | Bus_BEV                |  0.00 | 50.48 | 50.48 |     0.09 |    12.80 |     1.77 |     0.22 |     3.93 |     5.06 |     0.36 |
| Bus         | Bus_ICE                | 66.30 | 13.45 | 79.75 |     0.38 |     7.18 |     0.92 |     0.16 |     3.60 |     7.98 |     0.26 |
| Bus         | Bus_PHEV               | 48.63 |  9.87 | 58.50 |     0.40 |     7.11 |     0.96 |     0.16 |     3.56 |     5.88 |     0.26 |
| Car         | Car_BEV                |  0.00 | 71.40 | 71.40 |     0.75 |    33.45 |     5.81 |     0.62 |    12.20 |     0.00 |     1.02 |
| Car         | Car_ICE_Diesel         | 89.29 | 18.11 |107.40 |     3.01 |    16.54 |     2.96 |     0.51 |    12.48 |     0.00 |     0.84 |
| Car         | Car_ICE_Gasoline       |105.21 | 20.43 |125.63 |     3.01 |    16.54 |     2.96 |     0.51 |    12.48 |     0.00 |     0.84 |
| Car         | Car_PHEV               | 26.83 | 52.34 | 79.16 |     3.35 |    22.74 |     4.06 |     0.61 |    12.94 |     0.00 |     1.00 |
| Moped       | Moped_BEV              |  0.00 | 22.55 | 22.55 |     0.25 |     7.14 |     1.28 |     0.84 |    11.35 |     0.00 |     0.29 |
| Moped       | Moped_ICE              | 44.09 |  8.56 | 52.65 |     0.28 |     5.52 |     1.03 |     0.86 |    11.39 |     0.00 |     0.29 |
| Taxi        | Taxi_BEV               |  0.00 |172.23 |172.23 |     2.18 |    46.83 |     8.15 |     0.83 |    25.91 |    26.08 |     1.37 |
| Taxi        | Taxi_ICE               |253.75 | 49.27 |303.02 |     7.26 |    21.33 |     3.81 |     0.66 |    26.51 |    45.81 |     1.09 |
| Taxi        | Taxi_PHEV              |121.80 | 85.65 |207.45 |     6.72 |    29.32 |     5.24 |     0.78 |    27.49 |    31.24 |     1.28 |
| Train       | Rail_EV                |  0.00 | 52.57 | 52.57 |     0.00 |     1.74 |     0.20 |     0.03 |    11.00 |     0.00 |     0.06 |
| Walk        | Walk                   |  0.00 |  0.00 |  0.00 |     0.00 |     0.00 |     0.00 |     0.00 |     0.00 |     0.00 |     0.00 |

All values in **gCO2eq/pkm**. Column headers abbreviated: TTW = `TTW_gCO2eq_per_pkm`, WTT = `WTT_gCO2eq_per_pkm`, WTW = `WTW_gCO2eq_per_pkm`, B1-B3 columns = `{component}_pkm`.

## Override system

The model supports 4 configuration layers (from lowest to highest priority):

1. **Package defaults**
2. **Global emission factor overrides** (`electric_wtt`, `emission_factor_overrides`)
3. **Mode-level overrides** (`mode_overrides`) -- applied to all technologies within a mode
4. **Technology-level overrides** (`technology_overrides`) -- highest priority

```python
df = build_df_merged_final(
    # 1. Global override: electric grid carbon intensity
    electric_wtt=450.0,

    # 2. Fuel-type emission factor overrides
    emission_factor_overrides={
        "diesel": {"wtt": 520.0},
    },

    # 3. Mode-level overrides: apply to ALL technologies in the mode
    mode_overrides={
        "Car": {"passenger_load": 1.7},
        "Bus": {"passenger_load": 20.0},
    },

    # 4. Technology-level overrides: highest priority
    technology_overrides={
        "Car_BEV": {"consumption": 0.16, "B1_mfg": 44.0},
    },

    # 5. PHEV electric-drive share overrides
    phev_share_overrides={
        "Car_PHEV": 0.72,
    },
)
```

## Full API

| Function | Description |
|----------|-------------|
| `build_df_merged_final(**kwargs)` | Main entry point. Accepts overrides and returns the final DataFrame |
| `build_df_merged_final_from_config(config)` | Builds the DataFrame from a fully resolved config dict |
| `get_default_model_config()` | Returns a deep copy of the default configuration |
| `resolve_model_config(**kwargs)` | Resolves overrides on top of defaults and validates the configuration |
| `build_stream_a_dataframe(config)` | Computes only the WTW columns (TTW, WTT, WTW) |
| `build_stream_b_dataframe(config)` | Computes only the LCA columns (B1_*, B2_*, B3_*) |

### Explicit configuration workflow

```python
from vehicle_emissions_package import (
    get_default_model_config,
    build_df_merged_final_from_config,
)

config = get_default_model_config()
config["emission_factors"]["electric"]["wtt"] = 420.0
config["vehicle_params"]["Car_BEV"]["consumption"] = 0.15
config["vehicle_params"]["Bus_BEV"]["passenger_load"] = 22.0

df = build_df_merged_final_from_config(config)
```

## Validation

The model automatically validates inputs and raises `ValueError` if:

- An emission factor is negative
- `passenger_load` is <= 0
- Required fields are missing (consumption, fuel type, LCA components)
- A referenced fuel type does not exist in the emission factors
- A PHEV electric-drive share is not between 0 and 1

## Interactive web application

An interactive web tool is deployed at [j0anpau.github.io/vehicle-emissions-package](https://j0anpau.github.io/vehicle-emissions-package/) where you can:

- Adjust parameters dynamically (grid carbon intensity, passenger loads, consumption, PHEV shares)
- Visualise and compare lifecycle emissions across all transport technologies
- Download the resulting data for your own sustainability studies

This tool is designed for researchers, urban planners, and policymakers who need to assess transport emission profiles at the vehicle, city, regional, or country level -- enabling evidence-based decisions on fleet electrification, modal shift strategies, and infrastructure investment.

## License

MIT -- see [LICENSE](LICENSE).
