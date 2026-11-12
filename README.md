# Missile Impact Simulator

Pick a launch site, pick a target, pick a missile, and hit **Launch**. The app flies the missile across a 3D globe and shows how far the blast reaches and roughly how many people would be affected.

It is a Python desktop app: a Tkinter window with a Mapbox GL JS globe embedded in the middle via pywebview.

> Educational project. The numbers are rough estimates from published scaling laws, not a prediction of any real event.

## What it does

1. Search for a city, or click the globe, to set the **launch site** and the **target**. Pins can be dragged.
2. Choose one of 8 missiles. Each has a fixed max range and warhead yield.
3. The app checks the target is within the missile's range.
4. On **Launch**, a missile flies the great-circle path to the target and the blast zones expand on impact.
5. A results panel slides in with fatalities, injuries, strike stats (distance, range used, warhead, area affected) and the target's population and density.

## Quick start

You need Python 3.10+ and a [Mapbox public token](https://account.mapbox.com/).

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root (it is git-ignored):

```
MAPBOX_TOKEN=pk.your_token_here
```

`.env.example` shows the format. Then run:

```bash
python app/main.py
```

On Windows you can also double-click `run_simulator.bat`.

Tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## How the numbers work

Blast radii come from the Glasstone & Dolan (1977) scaling laws, where `Y` is the warhead yield in kilotons of TNT:

| Zone | Radius | Effect |
|---|---|---|
| Fireball | `0.09 * Y^0.40` km | total destruction |
| Heavy blast (20 psi) | `0.28 * Y^(1/3)` km | 98% fatalities |
| Moderate blast (5 psi) | `0.70 * Y^(1/3)` km | 50% fatalities |
| 3rd-degree burns | `0.67 * Y^0.41` km | severe thermal injury |
| Light blast (1 psi) | `1.90 * Y^(1/3)` km | 5% fatalities, 35% injuries |

Radii are adjusted for how built-up the target is. Casualties are population density multiplied by the area of each ring and its fatality rate. Population density is looked up online and cached in a local SQLite file.

Distances use the great-circle (haversine) formula.

## How it fits together

```
Tkinter window (controls + results)
      |  calls
SimulatorApi (range check, physics, population)
      |  state served over
Local HTTP server  <--polls every 250ms--  Globe page (Mapbox GL JS in pywebview)
```

The Tkinter side and the globe page don't call each other directly. Python keeps the app state, the local server exposes it at `/api/state`, and the globe polls it and redraws. Clicks and pin drags on the globe are sent back with `POST /api/pick`.

## Project structure

```
├── app/
│   ├── main.py                       # entry point
│   ├── ui/main_window.py             # Tkinter window, controls and results panel
│   ├── services/
│   │   ├── bridge_server.py          # SimulatorApi + local HTTP server, loads .env
│   │   ├── impact_physics.py         # distance, range check, blast scaling
│   │   └── geocoding.py              # city search, reverse geocoding, population lookup
│   ├── data/reference_data.json      # the 8 missiles (range, yield)
│   └── visualization/globe/index.html  # globe, pins, flight animation, blast zones
├── tests/test_all.py
├── .env.example
├── requirements.txt
└── run_simulator.bat
```

## Notes

- The globe needs internet for map tiles and for geocoding/population lookups.
- The map attribution (© Mapbox, © OpenStreetMap) is required by their terms and stays on the map as a small info button.
- Never commit your `.env`. Mapbox public tokens (`pk.`) are meant for client use, but restrict yours by URL in your Mapbox account if you can.
