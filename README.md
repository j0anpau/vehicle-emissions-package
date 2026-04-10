# vehicle-emissions-package

Paquete Python configurable para calcular las emisiones de ciclo de vida del transporte.
Genera un DataFrame con emisiones **Well-to-Wheel (WTW)** y **componentes embodied/LCA**
para 18 tecnologias de vehiculo en 9 modos de transporte, expresadas en **gCO2eq por pasajero-km**.

## Instalacion

```bash
# Desde el repositorio local
pip install -e .

# Desde GitHub
pip install git+https://github.com/j0anpau/vehicle-emissions-package.git
```

Requisitos: Python >= 3.10, pandas >= 2.0

## Inicio rapido

```python
from vehicle_emissions_package import build_df_merged_final

df = build_df_merged_final(electric_wtt=563.72)  # gCO2/kWh (ITF 2020, World)
print(df)
```

## DataFrame de salida

La funcion `build_df_merged_final()` devuelve un DataFrame con **18 filas** (una por tecnologia)
y **12 columnas**. Todas las emisiones estan en **gCO2eq/pkm** (gramos de CO2 equivalente por pasajero-kilometro).

### Columnas identificadoras

| Columna | Tipo | Descripcion |
|---------|------|-------------|
| `mode` | str | Modo de transporte: Walk, Bike, BikeSharing, Moped, Car, Taxi, Bus, Train |
| `tech` | str | Tecnologia especifica del vehiculo (ver tabla de tecnologias mas abajo) |

### Columnas Well-to-Wheel (WTW) — Emisiones operacionales

| Columna | Unidades | Descripcion |
|---------|----------|-------------|
| `TTW_gCO2eq_per_pkm` | gCO2eq/pkm | **Tank-to-Wheel**: emisiones directas por combustion del vehiculo |
| `WTT_gCO2eq_per_pkm` | gCO2eq/pkm | **Well-to-Tank**: emisiones upstream de produccion y distribucion del combustible |
| `WTW_gCO2eq_per_pkm` | gCO2eq/pkm | **Well-to-Wheel**: total operacional (TTW + WTT) |

### Columnas LCA — Emisiones embodied (ciclo de vida)

| Columna | Unidades | Componente | Descripcion |
|---------|----------|------------|-------------|
| `B1_flu_pkm` | gCO2eq/pkm | Fluidos | Produccion de fluidos y lubricantes |
| `B1_mfg_pkm` | gCO2eq/pkm | Fabricacion | Fabricacion del vehiculo (materiales, energia) |
| `B1_asm_pkm` | gCO2eq/pkm | Ensamblaje | Ensamblaje final del vehiculo |
| `B1_tra_pkm` | gCO2eq/pkm | Transporte | Transporte del vehiculo al punto de venta |
| `B2_inf_pkm` | gCO2eq/pkm | Infraestructura | Construccion y mantenimiento de infraestructura (carreteras, vias, carriles bici) |
| `B2_svc_pkm` | gCO2eq/pkm | Mantenimiento | Mantenimiento y reparacion del vehiculo durante su vida util |
| `B3_dis_pkm` | gCO2eq/pkm | Fin de vida | Desguace, reciclaje y eliminacion del vehiculo |

## Calculos realizados

### 1. Emisiones Well-to-Wheel (Stream A)

Para cada tecnologia se calculan las emisiones operacionales por pasajero-km.

**Tecnologias simples** (no-PHEV):

```
TTW_gCO2eq_per_pkm = (consumo × factor_ttw) / carga_pasajeros
WTT_gCO2eq_per_pkm = (consumo × factor_wtt) / carga_pasajeros
WTW_gCO2eq_per_pkm = TTW + WTT
```

Donde:
- `consumo` = consumo energetico del vehiculo (L/km para combustion, kWh/km para electricos)
- `factor_ttw` = factor de emision Tank-to-Wheel del combustible (gCO2/L o gCO2/kWh)
- `factor_wtt` = factor de emision Well-to-Tank del combustible (gCO2/L o gCO2/kWh)
- `carga_pasajeros` = ocupacion media del vehiculo (pasajeros/vehiculo)

**Tecnologias PHEV** (hibridas enchufables):

Se calcula una media ponderada entre el modo electrico y el modo combustion:

```
TTW = (ev_share × consumo_ev × ttw_electric + ice_share × consumo_ice × ttw_fuel) / carga_pasajeros
WTT = (ev_share × consumo_ev × wtt_electric + ice_share × consumo_ice × wtt_fuel) / carga_pasajeros
WTW = TTW + WTT
```

Donde `ev_share` es la fraccion de km recorridos en modo electrico (ej: 0.66 para Car_PHEV)
e `ice_share = 1 - ev_share`.

### 2. Emisiones embodied/LCA (Stream B)

Para cada componente LCA, la emision por pasajero-km se calcula como:

```
componente_pkm = valor_componente / carga_pasajeros
```

Donde `valor_componente` es el valor fijo asociado a esa tecnologia en gCO2eq/vkm
(ya amortizado sobre vida util y kilometraje anual).

### 3. Merge final

Los dos streams se fusionan por `(mode, tech)` y se ordenan alfabeticamente.

## Factores de emision por defecto

| Combustible | WTT (gCO2/unidad) | TTW (gCO2/unidad) | Unidad |
|-------------|-------------------:|-------------------:|--------|
| Electrico | 563.72 | 0.00 | kWh |
| Gasolina | 450.58 | 2320.72 | L |
| Diesel | 503.12 | 2480.34 | L |
| Humano | 0.00 | 0.00 | — |

> El factor WTT electrico (intensidad de la red) es el parametro principal para analisis de escenarios.

## Tecnologias incluidas (18)

| Modo | Tecnologia | Combustible | Consumo | Carga pasajeros |
|------|-----------|-------------|---------|----------------:|
| Walk | Walk | humano | 0 | 1.0 |
| Bike | Bike_Standalone | humano | 0 | 1.0 |
| Bike | eBike | electrico | 0.020 kWh/km | 1.0 |
| BikeSharing | BikeSharing_Standalone | humano | 0 | 1.0 |
| BikeSharing | eBikeSharing | electrico | 0.020 kWh/km | 1.0 |
| Moped | Moped_ICE | gasolina | 0.019 L/km | 1.0 |
| Moped | Moped_BEV | electrico | 0.040 kWh/km | 1.0 |
| Car | Car_ICE_Gasoline | gasolina | 0.068 L/km | 1.5 |
| Car | Car_ICE_Diesel | diesel | 0.054 L/km | 1.5 |
| Car | Car_PHEV | gasolina + electrico | 0.051 L/km + 0.190 kWh/km | 1.5 |
| Car | Car_BEV | electrico | 0.190 kWh/km | 1.5 |
| Taxi | Taxi_ICE | gasolina | 0.068 L/km | 0.62 |
| Taxi | Taxi_PHEV | gasolina + electrico | 0.051 L/km + 0.190 kWh/km | 0.62 |
| Taxi | Taxi_BEV | electrico | 0.190 kWh/km | 0.62 |
| Bus | Bus_ICE | diesel | 0.409 L/km | 15.3 |
| Bus | Bus_PHEV | diesel + electrico | 0.300 L/km + 0.000 kWh/km | 15.3 |
| Bus | Bus_BEV | electrico | 1.370 kWh/km | 15.3 |
| Train | Rail_EV | electrico | 17.72 kWh/km | 190.0 |

### Reparto electrico PHEV por defecto

| Tecnologia | % electrico | % combustion |
|-----------|------------:|-------------:|
| Car_PHEV | 66% | 34% |
| Taxi_PHEV | 36% | 64% |
| Bus_PHEV | 0% | 100% |

## Sistema de overrides

El modelo soporta 4 niveles de configuracion (de menor a mayor prioridad):

1. **Valores por defecto** del paquete
2. **Factores de emision globales** (`electric_wtt`, `emission_factor_overrides`)
3. **Overrides por modo** (`mode_overrides`) — se aplican a todas las tecnologias de un modo
4. **Overrides por tecnologia** (`technology_overrides`) — maxima prioridad

```python
df = build_df_merged_final(
    # 1. Override global: intensidad de red electrica
    electric_wtt=450.0,

    # 2. Override de factores de emision por combustible
    emission_factor_overrides={
        "diesel": {"wtt": 520.0},
    },

    # 3. Override por modo: afecta a TODAS las tecnologias del modo
    mode_overrides={
        "Car": {"passenger_load": 1.7},
        "Bus": {"passenger_load": 20.0},
    },

    # 4. Override por tecnologia: maxima prioridad
    technology_overrides={
        "Car_BEV": {"consumption": 0.16, "B1_mfg": 44.0},
    },

    # 5. Override de reparto PHEV
    phev_share_overrides={
        "Car_PHEV": 0.72,
    },
)
```

## API completa

| Funcion | Descripcion |
|---------|-------------|
| `build_df_merged_final(**kwargs)` | Punto de entrada principal. Acepta overrides y devuelve el DataFrame final |
| `build_df_merged_final_from_config(config)` | Construye el DataFrame a partir de un dict de configuracion completo |
| `get_default_model_config()` | Devuelve una copia de la configuracion por defecto |
| `resolve_model_config(**kwargs)` | Resuelve overrides sobre los defaults y valida la configuracion |
| `build_stream_a_dataframe(config)` | Solo calcula las columnas WTW (TTW, WTT, WTW) |
| `build_stream_b_dataframe(config)` | Solo calcula las columnas LCA (B1_*, B2_*, B3_*) |

### Workflow con configuracion explicita

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

## Validacion

El modelo valida automaticamente y lanza `ValueError` si:

- Un factor de emision es negativo
- `passenger_load` es <= 0
- Faltan campos requeridos (consumo, tipo combustible, componentes LCA)
- Un tipo de combustible referenciado no existe en los factores de emision
- El reparto PHEV no esta entre 0 y 1

## Licencia

MIT — ver [LICENSE](LICENSE).
