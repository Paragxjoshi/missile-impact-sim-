# Missile Impact Simulator

A Python desktop project combining a Tkinter GUI with an embedded Mapbox GL JS 3D globe inside pywebview. It lets you select an origin and target city anywhere in the world, pick a missile system, and calculate great-circle trajectory distance, flight times, and blast effects using the Glasstone-Dolan scaling laws.

---

## Layout

- **Left:** launch site and target (search, or click the globe), a missile dropdown (8 missiles, each with its real warhead yield), range check and a Launch button.
- **Center:** Mapbox GL JS 3D globe in pywebview, with pins, range circle, trajectory line and blast rings. Needs a Mapbox access token in the `MAPBOX_TOKEN` environment variable.
- **Right:** fatalities, injuries, the five blast radii, and the target's population and density.

---

## Blast Physics Model (Glasstone & Dolan, 1977)

Concentric hazard radii scale with the warhead yield `Y` (kilotons TNT equivalent):

- **Fireball**: `0.09 * Y^0.40` km
- **Heavy blast (20 psi)**: `0.28 * Y^(1/3)` km (98% fatalities)
- **Moderate blast (5 psi)**: `0.70 * Y^(1/3)` km (50% fatalities)
- **3rd-degree burns**: `0.67 * Y^0.41` km
- **Light blast (1 psi)**: `1.90 * Y^(1/3)` km (5% fatalities, 35% injuries)

Radii are adjusted for the target's population density, which is looked up online and cached in SQLite.

---

## How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the desktop application**:
   ```bash
   python app/main.py
   ```
   *(Or run `run_simulator.bat` on Windows)*

3. **Run unit tests**:
   ```bash
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

---

## Project Structure

```
├── requirements.txt
├── run_simulator.bat
├── README.md
├── app/
│   ├── main.py                 # entry point
│   ├── ui/main_window.py       # tkinter window with the globe embedded
│   ├── services/
│   │   ├── bridge_server.py    # simulator api + local http server linking tkinter and the globe
│   │   ├── impact_physics.py   # distance, range check, blast scaling
│   │   └── geocoding.py        # city search, reverse geocoding, population lookup
│   ├── data/reference_data.json  # the 8 missiles
│   └── visualization/globe/index.html  # mapbox gl js globe
└── tests/test_all.py
```
