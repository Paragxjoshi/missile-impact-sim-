import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.geocoding import GeocodingService
from app.services.impact_physics import (
    calculate_great_circle_distance_km,
    check_within_range,
    compute_impact_effects,
    load_missiles,
)


class TestMissileSimulator(unittest.TestCase):

    def setUp(self):
        self.missiles = {m["id"]: m for m in load_missiles()}

    def test_missiles_data(self):
        self.assertEqual(len(self.missiles), 8)
        for m in self.missiles.values():
            self.assertGreater(m["max_range_km"], 0)
            self.assertGreater(m["yield_kt"], 0)

    def test_distance_calculation(self):
        # new delhi to beijing
        dist = calculate_great_circle_distance_km(77.2090, 28.6139, 116.4074, 39.9042)
        self.assertGreater(dist, 3700)
        self.assertLess(dist, 3900)

    def test_range_limit(self):
        agni_v = self.missiles["agni_v"]
        self.assertTrue(check_within_range(3790, agni_v))
        self.assertFalse(check_within_range(6000, agni_v))

    def test_impact_effects(self):
        effects = compute_impact_effects(self.missiles["agni_v"], pop_density_per_km2=5000.0)
        radii = effects["radii_km"]
        self.assertGreater(radii["fireball_km"], 0)
        self.assertGreater(radii["heavy_blast_20psi_km"], radii["fireball_km"])
        self.assertGreater(radii["moderate_blast_5psi_km"], radii["heavy_blast_20psi_km"])
        self.assertGreater(radii["light_blast_1psi_km"], radii["moderate_blast_5psi_km"])
        self.assertGreater(effects["estimates"]["estimated_fatalities"], 0)

    def test_density_changes_casualties(self):
        agni_v = self.missiles["agni_v"]
        sparse = compute_impact_effects(agni_v, 2603.0)
        dense = compute_impact_effects(agni_v, 11300.0)
        self.assertNotEqual(sparse["estimates"]["estimated_fatalities"], dense["estimates"]["estimated_fatalities"])
        self.assertNotEqual(sparse["radii_km"]["heavy_blast_20psi_km"], dense["radii_km"]["heavy_blast_20psi_km"])

    def test_offline_geocoding_fallback(self):
        geo = GeocodingService()
        candidates = geo.search_city("Delhi")
        self.assertGreaterEqual(len(candidates), 1)
        self.assertIn("Delhi", candidates[0].label)

    def test_simulator_api(self):
        from app.services.bridge_server import SimulatorApi
        api = SimulatorApi()
        sim = api.simulate_launch(
            origin={"longitude": 77.2090, "latitude": 28.6139},
            dest={"longitude": 116.4074, "latitude": 39.9042, "label": "Beijing, China"},
            missile_id="agni_v",
        )
        self.assertTrue(sim["success"])
        self.assertIn("impact", sim)
        self.assertGreater(sim["population_info"]["population"], 0)

        too_far = api.simulate_launch(
            origin={"longitude": 77.2090, "latitude": 28.6139},
            dest={"longitude": -74.0, "latitude": 40.7, "label": "New York"},
            missile_id="agni_v",
        )
        self.assertFalse(too_far["success"])


if __name__ == "__main__":
    unittest.main()
