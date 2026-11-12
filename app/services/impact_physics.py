import json
import math
from pathlib import Path
from typing import Dict, Any, List
from app.services.geocoding import validate_lon_lat


# ---- great-circle distance ----
EARTH_MEAN_RADIUS_KM = 6371.0088


def calculate_great_circle_distance_km(
    origin_lon: float,
    origin_lat: float,
    dest_lon: float,
    dest_lat: float,
) -> float:
    """calculates great-circle distance in kilometers using haversine"""
    validate_lon_lat(origin_lon, origin_lat)
    validate_lon_lat(dest_lon, dest_lat)

    lat1_rad = math.radians(origin_lat)
    lat2_rad = math.radians(dest_lat)
    delta_lat = math.radians(dest_lat - origin_lat)
    delta_lon = math.radians(dest_lon - origin_lon)

    a = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return round(EARTH_MEAN_RADIUS_KM * c, 2)


# ---- blast physics ----
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "reference_data.json"

# glasstone & dolan (1977) blast scaling constants (yield Y in kt TNT)
FIREBALL_COEFF = 0.09
FIREBALL_EXP = 0.40
HEAVY_BLAST_20PSI_COEFF = 0.28
MODERATE_BLAST_5PSI_COEFF = 0.70
# 3rd-degree burn radius fit: ~2.0 km at 15 kt, ~11.4 km at 1 Mt (airburst, clear air),
# in line with NUKEMAP. the previous 1.20 overstated it ~1.8x (20.8 km at 1 Mt).
THERMAL_NUCLEAR_COEFF = 0.67
THERMAL_NUCLEAR_EXP = 0.41
LIGHT_BLAST_1PSI_COEFF = 1.90

# annular zone casualty & damage fractions
FATALITY_RATE_HEAVY = 0.98
FATALITY_RATE_MODERATE = 0.50
FATALITY_RATE_LIGHT = 0.05

INJURY_RATE_HEAVY = 0.02
INJURY_RATE_MODERATE = 0.45
INJURY_RATE_LIGHT = 0.35


def load_missiles() -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("missiles", [])


def check_within_range(distance_km: float, missile: Dict[str, Any]) -> bool:
    return distance_km <= float(missile["max_range_km"])


def get_target_environment_factors(density: float) -> Dict[str, Any]:
    """blast and thermal modifiers by urban density: buildings reflect blast and block heat"""
    if density >= 12000.0:
        urban_heavy = 1.04
        urban_mod = 0.94
        urban_light = 0.88
        thermal_scale = 0.76
        pattern = "Dense urban canyon reflection with structural thermal shielding"
    elif density >= 5000.0:
        urban_heavy = 1.02
        urban_mod = 0.97
        urban_light = 0.93
        thermal_scale = 0.85
        pattern = "Metropolitan mixed-structure reflection and partial shadowing"
    elif density >= 1500.0:
        urban_heavy = 1.00
        urban_mod = 0.99
        urban_light = 0.97
        thermal_scale = 0.92
        pattern = "Suburban distributed propagation with moderate line-of-sight"
    else:
        urban_heavy = 1.00
        urban_mod = 1.01
        urban_light = 1.04
        thermal_scale = 1.02
        pattern = "Open terrain planar expansion with unshielded thermal field"

    return {
        "heavy_factor": urban_heavy,
        "mod_factor": urban_mod,
        "light_factor": urban_light,
        "thermal_factor": thermal_scale,
        "blast_pattern": pattern,
    }


def compute_impact_effects(missile: Dict[str, Any], pop_density_per_km2: float) -> Dict[str, Any]:
    """blast radii (km) and casualty estimates for the missile's fixed warhead yield"""
    yield_kt = float(missile["yield_kt"])
    y_cbrt = yield_kt ** (1.0 / 3.0)
    env = get_target_environment_factors(pop_density_per_km2)

    # blast and thermal radii in km with target environmental effects
    fireball_km = round(FIREBALL_COEFF * (yield_kt ** FIREBALL_EXP), 3)
    heavy_blast_20psi_km = round(HEAVY_BLAST_20PSI_COEFF * y_cbrt * env["heavy_factor"], 3)
    heavy_blast_20psi_km = max(heavy_blast_20psi_km, round(fireball_km + 0.001, 3))

    moderate_blast_5psi_km = round(MODERATE_BLAST_5PSI_COEFF * y_cbrt * env["mod_factor"], 3)
    moderate_blast_5psi_km = max(moderate_blast_5psi_km, round(heavy_blast_20psi_km + 0.001, 3))

    thermal_3rd_deg_km = round(THERMAL_NUCLEAR_COEFF * (yield_kt ** THERMAL_NUCLEAR_EXP) * env["thermal_factor"], 3)

    light_blast_1psi_km = round(LIGHT_BLAST_1PSI_COEFF * y_cbrt * env["light_factor"], 3)
    light_blast_1psi_km = max(light_blast_1psi_km, round(moderate_blast_5psi_km + 0.001, 3))

    # exposure is density x area for each ring, not capped by the nearest town's population
    area_heavy = math.pi * (heavy_blast_20psi_km ** 2)
    area_moderate_ring = max(0.0, math.pi * (moderate_blast_5psi_km ** 2) - area_heavy)
    outer_radius = max(light_blast_1psi_km, thermal_3rd_deg_km)
    area_light_ring = max(0.0, math.pi * (outer_radius ** 2) - (area_heavy + area_moderate_ring))

    pop_heavy = area_heavy * pop_density_per_km2
    pop_moderate = area_moderate_ring * pop_density_per_km2
    pop_light = area_light_ring * pop_density_per_km2

    return {
        "yield_kt": yield_kt,
        "radii_km": {
            "fireball_km": fireball_km,
            "heavy_blast_20psi_km": heavy_blast_20psi_km,
            "moderate_blast_5psi_km": moderate_blast_5psi_km,
            "thermal_3rd_deg_km": thermal_3rd_deg_km,
            "light_blast_1psi_km": light_blast_1psi_km,
        },
        "estimates": {
            "estimated_fatalities": int(round(
                pop_heavy * FATALITY_RATE_HEAVY + pop_moderate * FATALITY_RATE_MODERATE + pop_light * FATALITY_RATE_LIGHT
            )),
            "estimated_injuries": int(round(
                pop_heavy * INJURY_RATE_HEAVY + pop_moderate * INJURY_RATE_MODERATE + pop_light * INJURY_RATE_LIGHT
            )),
        },
    }
