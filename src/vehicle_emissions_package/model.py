from __future__ import annotations

"""Configurable vehicle emissions model.

This module exposes a small, stable API for generating a merged emissions
DataFrame equivalent to the historical ``df_merged_final.csv`` output while
allowing callers to override:

- global emission factors
- per-mode defaults
- per-technology parameters
- PHEV electric-drive shares

The design is intentionally JSON-friendly so it can be called from Python
backends that serve interactive HTML applications.
"""

from copy import deepcopy
from typing import Any

import pandas as pd


DEFAULT_ELECTRIC_WTT = 563.720573199372

DEFAULT_EMISSION_FACTORS = {
    "electric": {"wtt": DEFAULT_ELECTRIC_WTT, "ttw": 0.0},
    "gasoline": {"wtt": 450.57852, "ttw": 2320.7184},
    "diesel": {"wtt": 503.12412, "ttw": 2480.34453333},
    "human": {"wtt": 0.0, "ttw": 0.0},
}

DEFAULT_VEHICLE_PARAMS = {
    "Walk": {
        "mode": "Walk",
        "consumption": 0.0,
        "fuel_type": "human",
        "lifetime_years": 1,
        "annual_mileage": 1000,
        "passenger_load": 1.0,
        "B1_flu": 0.0,
        "B1_mfg": 0.0,
        "B1_asm": 0.0,
        "B1_tra": 0.0,
        "B2_inf": 0.0,
        "B2_svc": 0.0,
        "B3_dis": 0.0,
    },
    "Bike_Standalone": {
        "mode": "Bike",
        "consumption": 0.0,
        "fuel_type": "human",
        "lifetime_years": 5.6,
        "annual_mileage": 2400,
        "passenger_load": 1.0,
        "B1_flu": 0.224901215,
        "B1_mfg": 5.400336036,
        "B1_asm": 0.827378502,
        "B1_tra": 0.778913390,
        "B2_inf": 9.471154571,
        "B2_svc": 0.0,
        "B3_dis": 0.235561443,
    },
    "eBike": {
        "mode": "Bike",
        "consumption": 0.020,
        "fuel_type": "electric",
        "lifetime_years": 5.6,
        "annual_mileage": 2400,
        "passenger_load": 1.0,
        "B1_flu": 0.253786021,
        "B1_mfg": 9.501605555,
        "B1_asm": 1.431827099,
        "B1_tra": 1.046224365,
        "B2_inf": 9.479360310,
        "B2_svc": 0.0,
        "B3_dis": 0.304479625,
    },
    "BikeSharing_Standalone": {
        "mode": "BikeSharing",
        "consumption": 0.0,
        "fuel_type": "human",
        "lifetime_years": 1.9,
        "annual_mileage": 2900,
        "passenger_load": 1.0,
        "B1_flu": 0.707715431,
        "B1_mfg": 16.708397728,
        "B1_asm": 2.603581009,
        "B1_tra": 2.551951990,
        "B2_inf": 9.489688571,
        "B2_svc": 24.702442,
        "B3_dis": 0.741260860,
    },
    "eBikeSharing": {
        "mode": "BikeSharing",
        "consumption": 0.020,
        "fuel_type": "electric",
        "lifetime_years": 1.9,
        "annual_mileage": 2900,
        "passenger_load": 1.0,
        "B1_flu": 0.819318999,
        "B1_mfg": 27.721421927,
        "B1_asm": 4.593881813,
        "B1_tra": 3.016138620,
        "B2_inf": 9.502686633,
        "B2_svc": 24.702442,
        "B3_dis": 0.980757250,
    },
    "Moped_ICE": {
        "mode": "Moped",
        "consumption": 1.9 / 100,
        "fuel_type": "gasoline",
        "lifetime_years": 10,
        "annual_mileage": 4900,
        "passenger_load": 1.0,
        "B1_flu": 0.280874404,
        "B1_mfg": 5.516413347,
        "B1_asm": 1.033295634,
        "B1_tra": 0.860375093,
        "B2_inf": 11.394557605,
        "B2_svc": 0.0,
        "B3_dis": 0.294187739,
    },
    "Moped_BEV": {
        "mode": "Moped",
        "consumption": 0.040,
        "fuel_type": "electric",
        "lifetime_years": 10,
        "annual_mileage": 4900,
        "passenger_load": 1.0,
        "B1_flu": 0.247612325,
        "B1_mfg": 7.142978091,
        "B1_asm": 1.278492543,
        "B1_tra": 0.841914969,
        "B2_inf": 11.354081196,
        "B2_svc": 0.0,
        "B3_dis": 0.287875676,
    },
    "Car_ICE_Gasoline": {
        "mode": "Car",
        "consumption": 6.8 / 100,
        "fuel_type": "gasoline",
        "lifetime_years": 15,
        "annual_mileage": 15000,
        "passenger_load": 1.5,
        "B1_flu": 4.517058591,
        "B1_mfg": 24.812507826,
        "B1_asm": 4.434004786,
        "B1_tra": 0.769209863,
        "B2_inf": 18.714685941,
        "B2_svc": 0.0,
        "B3_dis": 1.262397517,
    },
    "Car_ICE_Diesel": {
        "mode": "Car",
        "consumption": 5.4 / 100,
        "fuel_type": "diesel",
        "lifetime_years": 15,
        "annual_mileage": 15000,
        "passenger_load": 1.5,
        "B1_flu": 4.517058591,
        "B1_mfg": 24.812507826,
        "B1_asm": 4.434004786,
        "B1_tra": 0.769209863,
        "B2_inf": 18.714685941,
        "B2_svc": 0.0,
        "B3_dis": 1.262397517,
    },
    "Car_PHEV": {
        "mode": "Car",
        "consumption_ev": 0.190,
        "consumption_ice": 5.1 / 100,
        "fuel_type_ice": "gasoline",
        "lifetime_years": 15,
        "annual_mileage": 15000,
        "passenger_load": 1.5,
        "B1_flu": 5.023062034,
        "B1_mfg": 34.116190396,
        "B1_asm": 6.096555980,
        "B1_tra": 0.910510017,
        "B2_inf": 19.405554801,
        "B2_svc": 0.0,
        "B3_dis": 1.494293871,
    },
    "Car_BEV": {
        "mode": "Car",
        "consumption": 0.190,
        "fuel_type": "electric",
        "lifetime_years": 15,
        "annual_mileage": 15000,
        "passenger_load": 1.5,
        "B1_flu": 1.123393941,
        "B1_mfg": 50.172147491,
        "B1_asm": 8.712736825,
        "B1_tra": 0.933541182,
        "B2_inf": 18.295736177,
        "B2_svc": 0.0,
        "B3_dis": 1.532091730,
    },
    "Taxi_ICE": {
        "mode": "Taxi",
        "consumption": 6.8 / 100,
        "fuel_type": "gasoline",
        "lifetime_years": 7.1,
        "annual_mileage": 48000,
        "passenger_load": 0.6219,
        "B1_flu": 4.517058591,
        "B1_mfg": 13.263779292,
        "B1_asm": 2.370242511,
        "B1_tra": 0.411188983,
        "B2_inf": 16.485477554,
        "B2_svc": 28.48797368,
        "B3_dis": 0.674827476,
    },
    "Taxi_PHEV": {
        "mode": "Taxi",
        "consumption_ev": 0.190,
        "consumption_ice": 5.1 / 100,
        "fuel_type_ice": "gasoline",
        "lifetime_years": 7.1,
        "annual_mileage": 48000,
        "passenger_load": 0.6219,
        "B1_flu": 4.181287614,
        "B1_mfg": 18.237157762,
        "B1_asm": 3.258976220,
        "B1_tra": 0.486722422,
        "B2_inf": 17.094053252,
        "B2_svc": 19.42505166,
        "B3_dis": 0.798790039,
    },
    "Taxi_BEV": {
        "mode": "Taxi",
        "consumption": 0.190,
        "fuel_type": "electric",
        "lifetime_years": 7.1,
        "annual_mileage": 48000,
        "passenger_load": 0.6219,
        "B1_flu": 1.354105272,
        "B1_mfg": 29.120754419,
        "B1_asm": 5.065524286,
        "B1_tra": 0.518330168,
        "B2_inf": 16.116431183,
        "B2_svc": 16.22100628,
        "B3_dis": 0.850663451,
    },
    "Bus_ICE": {
        "mode": "Bus",
        "consumption": 40.9 / 100,
        "fuel_type": "diesel",
        "lifetime_years": 9,
        "annual_mileage": 44000,
        "passenger_load": 15.3,
        "B1_flu": 5.738779901,
        "B1_mfg": 109.870948560,
        "B1_asm": 14.143192359,
        "B1_tra": 2.453556905,
        "B2_inf": 55.117412150,
        "B2_svc": 122.1205625,
        "B3_dis": 4.026682823,
    },
    "Bus_PHEV": {
        "mode": "Bus",
        "consumption_ev": 0.0,
        "consumption_ice": 30.0 / 100,
        "fuel_type_ice": "diesel",
        "lifetime_years": 9,
        "annual_mileage": 44000,
        "passenger_load": 15.3,
        "B1_flu": 6.053613983,
        "B1_mfg": 108.730109750,
        "B1_asm": 14.614393859,
        "B1_tra": 2.454628804,
        "B2_inf": 54.428327743,
        "B2_svc": 89.89806374,
        "B3_dis": 4.028441984,
    },
    "Bus_BEV": {
        "mode": "Bus",
        "consumption": 1.370,
        "fuel_type": "electric",
        "lifetime_years": 9,
        "annual_mileage": 44000,
        "passenger_load": 15.3,
        "B1_flu": 1.433815373,
        "B1_mfg": 195.840180720,
        "B1_asm": 27.157321266,
        "B1_tra": 3.400324215,
        "B2_inf": 60.074368871,
        "B2_svc": 77.45520676,
        "B3_dis": 5.580480764,
    },
    "Rail_EV": {
        "mode": "Train",
        "consumption": 17.72,
        "fuel_type": "electric",
        "lifetime_years": 40,
        "annual_mileage": 66000,
        "passenger_load": 190.0,
        "B1_flu": 0.410677680,
        "B1_mfg": 330.792274220,
        "B1_asm": 37.949131257,
        "B1_tra": 5.413036622,
        "B2_inf": 2090.646808,
        "B2_svc": 0.0,
        "B3_dis": 10.804428810,
    },
}

DEFAULT_PHEV_EV_SHARE = {
    "Car_PHEV": 0.66,
    "Taxi_PHEV": 0.36,
    "Bus_PHEV": 0.00,
}

LCA_COMPONENTS = ["B1_flu", "B1_mfg", "B1_asm", "B1_tra", "B2_inf", "B2_svc", "B3_dis"]
MERGED_OUTPUT_COLUMNS = [
    "mode",
    "tech",
    "TTW_gCO2eq_per_pkm",
    "WTT_gCO2eq_per_pkm",
    "WTW_gCO2eq_per_pkm",
    "B1_flu_pkm",
    "B1_mfg_pkm",
    "B1_asm_pkm",
    "B1_tra_pkm",
    "B2_inf_pkm",
    "B2_svc_pkm",
    "B3_dis_pkm",
]


def get_default_model_config() -> dict[str, Any]:
    """Return a deep copy of the package default configuration."""
    return {
        "emission_factors": deepcopy(DEFAULT_EMISSION_FACTORS),
        "mode_defaults": {},
        "vehicle_params": deepcopy(DEFAULT_VEHICLE_PARAMS),
        "phev_ev_share": deepcopy(DEFAULT_PHEV_EV_SHARE),
    }


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries without mutating the inputs."""
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _apply_mode_defaults(
    vehicle_params: dict[str, dict[str, Any]],
    mode_defaults: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Apply mode-level overrides to every technology belonging to a mode."""
    if not mode_defaults:
        return deepcopy(vehicle_params)

    resolved = deepcopy(vehicle_params)
    for technology, params in resolved.items():
        mode = params["mode"]
        overrides = mode_defaults.get(mode)
        if overrides:
            params.update(deepcopy(overrides))
    return resolved


def _validate_config(config: dict[str, Any]) -> None:
    """Validate the resolved model configuration and raise clear errors."""
    emission_factors = config["emission_factors"]
    vehicle_params = config["vehicle_params"]
    phev_ev_share = config["phev_ev_share"]

    for fuel_type, factors in emission_factors.items():
        for field in ("wtt", "ttw"):
            if field not in factors:
                raise ValueError(f"Emission factor '{fuel_type}' is missing '{field}'.")
            if factors[field] < 0:
                raise ValueError(f"Emission factor '{fuel_type}.{field}' must be >= 0.")

    for technology, params in vehicle_params.items():
        if "mode" not in params:
            raise ValueError(f"Technology '{technology}' is missing 'mode'.")
        if params.get("passenger_load", 0) <= 0:
            raise ValueError(f"Technology '{technology}' must have passenger_load > 0.")

        is_phev = technology in phev_ev_share
        if is_phev:
            required_fields = ("consumption_ev", "consumption_ice", "fuel_type_ice")
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"PHEV technology '{technology}' is missing '{field}'.")
        else:
            required_fields = ("consumption", "fuel_type")
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"Technology '{technology}' is missing '{field}'.")

        fuel_types = []
        if "fuel_type" in params:
            fuel_types.append(params["fuel_type"])
        if "fuel_type_ice" in params:
            fuel_types.append(params["fuel_type_ice"])
        for fuel_type in fuel_types:
            if fuel_type not in emission_factors:
                raise ValueError(
                    f"Technology '{technology}' references unknown fuel type '{fuel_type}'."
                )

        for component in LCA_COMPONENTS:
            if component not in params:
                raise ValueError(f"Technology '{technology}' is missing '{component}'.")

    for technology, share in phev_ev_share.items():
        if technology not in vehicle_params:
            raise ValueError(f"PHEV share provided for unknown technology '{technology}'.")
        if not 0 <= share <= 1:
            raise ValueError(f"PHEV EV share for '{technology}' must be between 0 and 1.")


def resolve_model_config(
    *,
    electric_wtt: float | None = None,
    emission_factor_overrides: dict[str, dict[str, float]] | None = None,
    mode_overrides: dict[str, dict[str, Any]] | None = None,
    technology_overrides: dict[str, dict[str, Any]] | None = None,
    phev_share_overrides: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Resolve the final model configuration from defaults plus overrides.

    Parameters are ordered from broadest to most specific. Technology-level
    overrides win over mode-level overrides.
    """
    config = get_default_model_config()

    if electric_wtt is not None:
        if electric_wtt < 0:
            raise ValueError("electric_wtt must be >= 0.")
        config["emission_factors"]["electric"]["wtt"] = electric_wtt

    if emission_factor_overrides:
        config["emission_factors"] = _deep_merge(
            config["emission_factors"],
            emission_factor_overrides,
        )

    config["vehicle_params"] = _apply_mode_defaults(
        config["vehicle_params"],
        mode_overrides,
    )

    if technology_overrides:
        config["vehicle_params"] = _deep_merge(
            config["vehicle_params"],
            technology_overrides,
        )

    if phev_share_overrides:
        config["phev_ev_share"] = _deep_merge(
            config["phev_ev_share"],
            phev_share_overrides,
        )

    _validate_config(config)
    return config


def _calc_wtw_vkm(consumption: float, fuel_type: str, emission_factors: dict[str, Any]) -> dict[str, float]:
    """Calculate WTW emissions per vehicle-km for a non-PHEV technology."""
    fuel = emission_factors[fuel_type]
    ef_wtt = fuel["wtt"]
    ef_ttw = fuel["ttw"]
    return {
        "ef_wtt_gco2_per_unit": ef_wtt,
        "ef_ttw_gco2_per_unit": ef_ttw,
        "wtw_vkm": consumption * (ef_wtt + ef_ttw),
    }


def _calc_wtw_vkm_phev(
    *,
    technology: str,
    params: dict[str, Any],
    emission_factors: dict[str, Any],
    phev_ev_share: dict[str, float],
) -> dict[str, float]:
    """Calculate WTW emissions per vehicle-km for a PHEV technology."""
    ev_share = phev_ev_share[technology]
    ice_share = 1.0 - ev_share

    ev_result = _calc_wtw_vkm(params["consumption_ev"], "electric", emission_factors)
    ice_result = _calc_wtw_vkm(
        params["consumption_ice"],
        params["fuel_type_ice"],
        emission_factors,
    )

    ef_wtt_eff = (
        ev_share * emission_factors["electric"]["wtt"] * params["consumption_ev"]
        + ice_share
        * emission_factors[params["fuel_type_ice"]]["wtt"]
        * params["consumption_ice"]
    )
    ef_ttw_eff = (
        ev_share * emission_factors["electric"]["ttw"] * params["consumption_ev"]
        + ice_share
        * emission_factors[params["fuel_type_ice"]]["ttw"]
        * params["consumption_ice"]
    )

    return {
        "ef_wtt_gco2_per_unit": ef_wtt_eff,
        "ef_ttw_gco2_per_unit": ef_ttw_eff,
        "wtw_vkm": ev_share * ev_result["wtw_vkm"] + ice_share * ice_result["wtw_vkm"],
        "phev_ev_share": ev_share,
    }


def build_stream_a_dataframe(config: dict[str, Any]) -> pd.DataFrame:
    """Build the Well-to-Wheel stream using the resolved configuration."""
    rows = []
    emission_factors = config["emission_factors"]
    vehicle_params = config["vehicle_params"]
    phev_ev_share = config["phev_ev_share"]

    for technology, params in vehicle_params.items():
        if technology in phev_ev_share:
            result = _calc_wtw_vkm_phev(
                technology=technology,
                params=params,
                emission_factors=emission_factors,
                phev_ev_share=phev_ev_share,
            )
            ttw_vkm = result["ef_ttw_gco2_per_unit"]
            wtt_vkm = result["ef_wtt_gco2_per_unit"]
        else:
            result = _calc_wtw_vkm(
                params["consumption"],
                params["fuel_type"],
                emission_factors,
            )
            ttw_vkm = result["ef_ttw_gco2_per_unit"] * params["consumption"]
            wtt_vkm = result["ef_wtt_gco2_per_unit"] * params["consumption"]

        passenger_load = params["passenger_load"]
        rows.append(
            {
                "mode": params["mode"],
                "tech": technology,
                "TTW_gCO2eq_per_pkm": ttw_vkm / passenger_load,
                "WTT_gCO2eq_per_pkm": wtt_vkm / passenger_load,
                "WTW_gCO2eq_per_pkm": result["wtw_vkm"] / passenger_load,
            }
        )

    return pd.DataFrame(rows)


def build_stream_b_dataframe(config: dict[str, Any]) -> pd.DataFrame:
    """Build the embodied/LCA stream using the resolved configuration."""
    rows = []
    for technology, params in config["vehicle_params"].items():
        passenger_load = params["passenger_load"]
        row = {"mode": params["mode"], "tech": technology}
        for component in LCA_COMPONENTS:
            row[f"{component}_pkm"] = params[component] / passenger_load
        rows.append(row)

    return pd.DataFrame(rows)


def build_df_merged_final(
    electric_wtt: float | None = None,
    *,
    mode_overrides: dict[str, dict[str, Any]] | None = None,
    technology_overrides: dict[str, dict[str, Any]] | None = None,
    emission_factor_overrides: dict[str, dict[str, float]] | None = None,
    phev_share_overrides: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Build the merged output DataFrame.

    This is the main convenience API. It supports the most common interactive
    use case where a frontend or application adjusts a few scenario levers and
    needs an updated DataFrame.
    """
    config = resolve_model_config(
        electric_wtt=electric_wtt,
        emission_factor_overrides=emission_factor_overrides,
        mode_overrides=mode_overrides,
        technology_overrides=technology_overrides,
        phev_share_overrides=phev_share_overrides,
    )
    return build_df_merged_final_from_config(config)


def build_df_merged_final_from_config(config: dict[str, Any]) -> pd.DataFrame:
    """Build the merged output DataFrame from a fully resolved configuration."""
    _validate_config(config)
    stream_a = build_stream_a_dataframe(config)
    stream_b = build_stream_b_dataframe(config)
    merged = pd.merge(stream_a, stream_b, on=["mode", "tech"], how="outer")
    return merged[MERGED_OUTPUT_COLUMNS].sort_values(["mode", "tech"]).reset_index(drop=True)
