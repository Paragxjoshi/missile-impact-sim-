from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PlaceCandidate:
    """geocoding search result candidate"""
    label: str
    longitude: float
    latitude: float
    provider_place_id: str
    attribution: str = "OpenStreetMap"


@dataclass
class Scenario:
    """saved simulation scenario row"""
    scenario_name: str
    origin_city_label: str
    origin_longitude: float
    origin_latitude: float
    destination_city_label: str
    destination_longitude: float
    destination_latitude: float
    map_provider: str = "OpenStreetMap"
    source_info: str = ""
    missile_id: Optional[str] = None
    params: str = '{"is_nuclear": true, "yield_kt": 250.0}'
    population_data_source: str = "GeoNames / OpenStreetMap"
    notes: str = "Blast estimation using Glasstone-Dolan scaling."
    scenario_id: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
