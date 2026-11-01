import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent / "scenarios.db"

HTTP_TIMEOUT = 4
CACHE_RADIUS_DEG = 0.25

# density tiers based on city population
POP_MEGACITY = 8_000_000
DENSITY_MEGACITY = 14500.0

POP_METROPOLIS = 3_000_000
DENSITY_METROPOLIS = 8500.0

POP_LARGE_CITY = 1_000_000
DENSITY_LARGE_CITY = 5200.0

POP_MID_CITY = 250_000
DENSITY_MID_CITY = 2800.0

POP_SMALL_CITY = 50_000
DENSITY_SMALL_CITY = 1400.0

DENSITY_TOWN = 450.0

DEFAULT_RURAL_POP = 15000
DEFAULT_RURAL_DENSITY = 150.0

DEFAULT_REMOTE_POP = 2500
DEFAULT_REMOTE_DENSITY = 45.0


class PopulationService:
    """fetches population and density data and caches to sqlite"""

    OPENDATASOFT_URL = (
        "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
        "geonames-all-cities-with-a-population-1000/records"
    )

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_cache_table()

    def _init_cache_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS population_cache (
                        cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        place_name TEXT NOT NULL,
                        longitude REAL NOT NULL,
                        latitude REAL NOT NULL,
                        population INTEGER NOT NULL,
                        density_per_km2 REAL NOT NULL,
                        country TEXT,
                        data_source TEXT,
                        cached_at TEXT
                    )
                    """
                )
        finally:
            conn.close()

    def _lookup_cache(self, lon: float, lat: float) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM population_cache 
                WHERE abs(longitude - ?) < ? AND abs(latitude - ?) < ?
                ORDER BY abs(longitude - ?) + abs(latitude - ?) ASC
                LIMIT 1
                """,
                (lon, CACHE_RADIUS_DEG, lat, CACHE_RADIUS_DEG, lon, lat),
            ).fetchone()
            if row:
                return dict(row)
        except sqlite3.Error as err:
            print(f"population cache read error: {err}")
        finally:
            conn.close()
        return None

    def _save_cache(
        self,
        place_name: str,
        lon: float,
        lat: float,
        population: int,
        density: float,
        country: str,
        source: str,
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO population_cache (
                        place_name, longitude, latitude, population,
                        density_per_km2, country, data_source, cached_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        place_name,
                        lon,
                        lat,
                        int(population),
                        float(density),
                        country,
                        source,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        except sqlite3.Error as err:
            print(f"population cache write error: {err}")
        finally:
            conn.close()

    def get_population_and_density(
        self, longitude: float, latitude: float, fallback_label: str = ""
    ) -> Dict[str, Any]:
        """looks up population and urban density for coordinates"""
        cached = self._lookup_cache(longitude, latitude)
        if cached:
            return {
                "place_name": cached["place_name"],
                "country": cached.get("country", "Unknown"),
                "population": cached["population"],
                "density_per_km2": cached["density_per_km2"],
                "data_source": f"SQLite Cache ({cached.get('data_source', 'Cached')})",
                "is_water": cached["population"] == 0,
            }

        # query opendatasoft geonames dataset for nearby cities
        try:
            params = f"where=within_distance(coordinates,%20geom'POINT({longitude}%20{latitude})',%2060km)&order_by=population%20desc&limit=1"
            url = f"{self.OPENDATASOFT_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "MissileImpactSimulator/2.0"})
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
                records = data.get("results", [])
                if records:
                    city_data = records[0]
                    pop = int(city_data.get("population", 0))
                    city_name = city_data.get("name") or fallback_label or "Target Urban Center"
                    country = city_data.get("cou_name_en") or "Global Territory"

                    # estimate density based on city size
                    if pop > POP_MEGACITY:
                        density = DENSITY_MEGACITY
                    elif pop > POP_METROPOLIS:
                        density = DENSITY_METROPOLIS
                    elif pop > POP_LARGE_CITY:
                        density = DENSITY_LARGE_CITY
                    elif pop > POP_MID_CITY:
                        density = DENSITY_MID_CITY
                    elif pop > POP_SMALL_CITY:
                        density = DENSITY_SMALL_CITY
                    else:
                        density = DENSITY_TOWN

                    self._save_cache(
                        city_name,
                        longitude,
                        latitude,
                        pop,
                        density,
                        country,
                        "OpenDataSoft / GeoNames",
                    )
                    return {
                        "place_name": city_name,
                        "country": country,
                        "population": pop,
                        "density_per_km2": density,
                        "data_source": "OpenDataSoft / GeoNames",
                        "is_water": False,
                    }
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as err:
            print(f"opendatasoft query error: {err}")

        # fallback to nominatim reverse geocode
        try:
            osm_url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}&extratags=1"
            req = urllib.request.Request(osm_url, headers={"User-Agent": "MissileSimulator/2.0"})
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
                osm_data = json.loads(response.read().decode("utf-8"))
                extratags = osm_data.get("extratags", {})
                pop_str = extratags.get("population")
                address = osm_data.get("address", {})
                place = (
                    address.get("city")
                    or address.get("town")
                    or address.get("municipality")
                    or address.get("village")
                    or address.get("county")
                    or osm_data.get("name")
                    or fallback_label
                    or "Rural Zone"
                )
                country = address.get("country", "Unknown")

                if pop_str and pop_str.isdigit():
                    pop = int(pop_str)
                    density = max(100.0, min(15000.0, pop / 40.0))
                else:
                    pop = DEFAULT_RURAL_POP
                    density = DEFAULT_RURAL_DENSITY

                self._save_cache(
                    place, longitude, latitude, pop, density, country, "OpenStreetMap Nominatim"
                )
                return {
                    "place_name": place,
                    "country": country,
                    "population": pop,
                    "density_per_km2": density,
                    "data_source": "OpenStreetMap Nominatim",
                    "is_water": False,
                }
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as err:
            print(f"osm reverse query error: {err}")

        # default for remote or maritime regions
        default_name = fallback_label if fallback_label else f"Coordinates ({latitude:.2f}, {longitude:.2f})"
        default_pop = DEFAULT_REMOTE_POP
        default_density = DEFAULT_REMOTE_DENSITY

        self._save_cache(
            default_name,
            longitude,
            latitude,
            default_pop,
            default_density,
            "Open Territory",
            "Spatial Estimation",
        )
        return {
            "place_name": default_name,
            "country": "Open Territory",
            "population": default_pop,
            "density_per_km2": default_density,
            "data_source": "Spatial Estimation",
            "is_water": False,
        }
