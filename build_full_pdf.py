import os
import sys
import json
import html
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\vedan\Desktop\Project")
DESKTOP_DIR = Path(r"C:\Users\vedan\Desktop")
OUTPUT_HTML = DESKTOP_DIR / "Missile_Simulator_Full_Project_Documentation.html"
OUTPUT_PDF = DESKTOP_DIR / "Missile_Simulator_Full_Project_Documentation.pdf"
PROJECT_PDF = PROJECT_ROOT / "Missile_Simulator_Full_Project_Documentation.pdf"

print("Compiling project files...")

# Read all project files
files_to_include = [
    ("app/main.py", "Primary Application Entry Point (Tkinter Bootstrapper)", "python"),
    ("app/ui/main_window.py", "Tkinter Core Desktop GUI & Embedded Viewport Host", "python"),
    ("app/ui/city_search.py", "Reusable Tkinter Search & Autocomplete Component", "python"),
    ("app/services/webview_api.py", "Python-to-JavaScript IPC API Bridge", "python"),
    ("app/services/bridge_server.py", "Local HTTP & REST Fallback Bridge Server", "python"),
    ("app/services/impact_physics.py", "Glasstone-Dolan Blast Physics & Casualty Engine", "python"),
    ("app/services/distance_service.py", "Haversine Great-Circle Geodesic Calculation", "python"),
    ("app/services/mapbox_geocoding.py", "Multi-Provider Wi-Fi Geocoding & Transliteration", "python"),
    ("app/services/population_service.py", "Public Urban Population Engine with SQLite Cache", "python"),
    ("app/data/models.py", "Core Dataclasses & Data Schemas", "python"),
    ("app/data/database.py", "SQLite Scenario Persistence Layer", "python"),
    ("tests/test_all.py", "Complete Automated Unit Verification Suite (8 Tests)", "python"),
    ("requirements.txt", "Python Runtime Dependencies", "text"),
    ("run_simulator.bat", "One-Click Windows Desktop Launcher", "bat"),
    ("README.md", "Project Architecture & Technical Documentation", "markdown"),
    ("app/visualization/globe/index.html", "3D CesiumJS Earth Viewport, HUD Overlays & Modals", "html"),
    ("app/data/reference_data.json", "58-Missile Technical Database (Complete JSON)", "json"),
]

file_contents = {}
for rel_path, desc, lang in files_to_include:
    fpath = PROJECT_ROOT / rel_path
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        file_contents[rel_path] = {
            "desc": desc,
            "lang": lang,
            "content": content,
            "lines": len(content.splitlines()),
            "size_bytes": len(content.encode("utf-8")),
        }
        print(f"Loaded {rel_path} ({len(content.splitlines())} lines)")
    else:
        print(f"WARNING: File not found: {rel_path}")

# Load 58 missiles for catalog table
ref_data_path = PROJECT_ROOT / "app/data/reference_data.json"
missiles = []
if ref_data_path.exists():
    try:
        missiles = json.loads(ref_data_path.read_text(encoding="utf-8")).get("missiles", [])
    except Exception as e:
        print(f"Error loading missiles: {e}")

print(f"Total missiles loaded: {len(missiles)}")

# Construct CSS styles for clean, crisp, publication-grade PDF output
css_styles = """
<style>
  @page {
    size: A4;
    margin: 15mm 15mm 18mm 15mm;
    @bottom-right {
      content: "Page " counter(page);
      font-size: 8pt;
      color: #64748b;
      font-family: 'Segoe UI', system-ui, sans-serif;
    }
    @bottom-left {
      content: "Real-World Missile Impact Simulator — Full Technical Reference";
      font-size: 8pt;
      color: #64748b;
      font-family: 'Segoe UI', system-ui, sans-serif;
    }
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
    color: #1e293b;
    background: #ffffff;
    margin: 0;
    padding: 0;
    font-size: 9.5pt;
  }

  .cover-page {
    page-break-after: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 92vh;
    padding: 40px 20px;
  }

  .cover-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    background: #e0f2fe;
    color: #0369a1;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 20px;
  }

  .cover-title {
    font-size: 28pt;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.15;
    margin: 0 0 10px 0;
    letter-spacing: -0.5px;
  }

  .cover-subtitle {
    font-size: 13pt;
    color: #475569;
    margin: 0 0 30px 0;
    line-height: 1.4;
  }

  .badge-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 35px;
  }

  .pill {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 8.5pt;
    font-weight: 600;
    color: #334155;
  }
  .pill.highlight { background: #fee2e2; border-color: #fca5a5; color: #991b1b; }
  .pill.tech { background: #eff6ff; border-color: #bfdbfe; color: #1e40af; }
  .pill.geo { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }

  .meta-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px 20px;
    margin-top: 30px;
    font-size: 9pt;
  }

  .meta-box table { width: 100%; border-collapse: collapse; }
  .meta-box td { padding: 4px 0; }
  .meta-box td:first-child { font-weight: 700; color: #475569; width: 180px; }
  .meta-box td:last-child { color: #0f172a; }

  h1 {
    font-size: 18pt;
    font-weight: 800;
    color: #0f172a;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 6px;
    margin-top: 36px;
    margin-bottom: 16px;
    page-break-before: always;
  }
  h1:first-of-type { page-break-before: avoid; }

  h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #1e293b;
    border-left: 4px solid #0284c7;
    padding-left: 8px;
    margin-top: 22px;
    margin-bottom: 10px;
  }

  h3 {
    font-size: 10.5pt;
    font-weight: 700;
    color: #334155;
    margin-top: 14px;
    margin-bottom: 6px;
  }

  p { margin: 0 0 10px 0; text-align: justify; }

  ul, ol { margin: 0 0 12px 0; padding-left: 20px; }
  li { margin-bottom: 4px; }

  .callout {
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin: 12px 0;
    font-size: 9pt;
  }
  .callout.important { background: #eff6ff; border-left-color: #3b82f6; }
  .callout.warning { background: #fffbeb; border-left-color: #f59e0b; }
  .callout.caution { background: #fef2f2; border-left-color: #ef4444; }

  .callout-title {
    font-weight: 700;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  table.data-table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 8.5pt;
    page-break-inside: auto;
  }
  table.data-table th, table.data-table td {
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    text-align: left;
  }
  table.data-table th {
    background: #0f172a;
    color: #ffffff;
    font-weight: 700;
    font-size: 8.5pt;
  }
  table.data-table tr:nth-child(even) { background: #f8fafc; }
  table.data-table tr { page-break-inside: avoid; }

  .code-container {
    margin: 14px 0 24px 0;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    overflow: hidden;
    page-break-inside: avoid;
  }

  .code-header {
    background: #1e293b;
    color: #f8fafc;
    padding: 6px 12px;
    font-size: 8.5pt;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #334155;
  }

  .code-header .file-path { font-family: Consolas, monospace; color: #38bdf8; }
  .code-header .file-meta { font-size: 7.5pt; color: #94a3b8; }

  pre.code-block {
    background: #090e17;
    color: #e2e8f0;
    font-family: Consolas, 'Fira Code', 'Courier New', monospace;
    font-size: 7.5pt;
    line-height: 1.35;
    padding: 10px 12px;
    margin: 0;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }

  .toc-item {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
    border-bottom: 1px dotted #cbd5e1;
    font-size: 9.5pt;
  }
  .toc-item a { text-decoration: none; color: #0284c7; font-weight: 600; }
  .toc-item .dots { flex: 1; border-bottom: 1px dotted #94a3b8; margin: 0 6px 4px 6px; }

  .prompt-box {
    background: #f8fafc;
    border: 2px dashed #0284c7;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 14px 0;
    font-family: Consolas, monospace;
    font-size: 8.5pt;
    color: #0f172a;
    line-height: 1.4;
    white-space: pre-wrap;
  }
</style>
"""

# Build HTML Body
html_content = [
    "<!DOCTYPE html>",
    "<html lang='en'>",
    "<head>",
    "  <meta charset='UTF-8' />",
    "  <title>Real-World Missile Impact Simulator — Full Technical & Code Dossier</title>",
    css_styles,
    "</head>",
    "<body>",
]

# ----------------- COVER PAGE -----------------
html_content.append("""
<div class="cover-page">
  <div>
    <span class="cover-badge">Complete System Dossier & Source Repository</span>
  </div>
  <h1 class="cover-title" style="page-break-before: avoid;">REAL-WORLD MISSILE IMPACT SIMULATOR</h1>
  <div class="cover-subtitle">
    Technical Architecture, Scientific Physics Equations, Geospatial 3D Engine, & Verbatim Full Codebase
  </div>

  <div class="badge-grid">
    <span class="pill highlight">Mandatory Tkinter Core GUI</span>
    <span class="pill tech">PyView (pywebview 6.2+)</span>
    <span class="pill geo">CesiumJS 3D Earth Globe</span>
    <span class="pill tech">Glasstone-Dolan Blast Physics</span>
    <span class="pill highlight">58-Missile Global Database</span>
    <span class="pill geo">Live OpenStreetMap Geocoding</span>
    <span class="pill tech">OpenDataSoft Population Engine</span>
    <span class="pill highlight">SQLite Local Persistence</span>
    <span class="pill tech">Python 3.13 Runtime</span>
    <span class="pill geo">Public GitHub Repository</span>
  </div>

  <p style="font-size: 10.5pt; color: #334155; line-height: 1.6;">
    This document contains the complete, unabridged architectural design, physical calculations, mathematical equations,
    interactive features, and verbatim source code of the <b>Real-World Missile Impact Simulator</b>.
    It is explicitly structured for direct upload to <b>Google Gemini</b> to analyze the entire application in context,
    answer questions, and generate precise engineering prompts for further feature extensions and refactorings.
  </p>

  <div class="meta-box">
    <table>
      <tr>
        <td>Repository URL:</td>
        <td><a href="https://github.com/Salvius2422/missile-impact-simulator" target="_blank" style="color: #0284c7; font-weight: 600;">https://github.com/Salvius2422/missile-impact-simulator</a> (Public)</td>
      </tr>
      <tr>
        <td>Primary Author:</td>
        <td>Vedant Antil (GitHub: <b>Salvius2422</b>) & Google DeepMind Antigravity Pair Programming Agent</td>
      </tr>
      <tr>
        <td>Core Framework:</td>
        <td>Python Tkinter (Primary Mandatory Window) with embedded PyView CesiumJS 3D viewport</td>
      </tr>
      <tr>
        <td>Scientific Standard:</td>
        <td>Glasstone-Dolan (1977) Nuclear & Conventional Blast Overpressure Scaling Laws</td>
      </tr>
      <tr>
        <td>Geospatial Data:</td>
        <td>WGS84 Ellipsoid, OpenStreetMap Nominatim, OpenDataSoft GeoNames Worldwide Cities</td>
      </tr>
      <tr>
        <td>Weapons Inventory:</td>
        <td>58 Global Systems across 10 Powers (India, USA, Russia, China, France, UK, Israel, Iran, ROK, DPRK)</td>
      </tr>
      <tr>
        <td>Document Date:</td>
        <td>November 1, 2026 &bull; Version 2.5 (Fully Updated & Synchronized)</td>
      </tr>
    </table>
  </div>
</div>
""")

# ----------------- TABLE OF CONTENTS -----------------
html_content.append("""
<h1>TABLE OF CONTENTS</h1>
<div style="margin: 20px 0;">
  <div class="toc-item"><span>1. Executive Summary & Project Purpose</span><span class="dots"></span><span>Section 1</span></div>
  <div class="toc-item"><span>2. System Architecture & Dual-Framework Design</span><span class="dots"></span><span>Section 2</span></div>
  <div class="toc-item"><span>3. Detailed Module Breakdown & Engineering Specifications</span><span class="dots"></span><span>Section 3</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.1 Tkinter Master Application & Viewport Hosting</span><span class="dots"></span><span>3.1</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.2 3D CesiumJS Viewport & HUD Command Overlay</span><span class="dots"></span><span>3.2</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.3 Python-JavaScript Bidirectional IPC Bridge</span><span class="dots"></span><span>3.3</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.4 Glasstone-Dolan Blast Physics & Casualties</span><span class="dots"></span><span>3.4</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.5 Live Public Geocoding & Transliteration Engine</span><span class="dots"></span><span>3.5</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.6 Urban Population & Automatic Density Lookup</span><span class="dots"></span><span>3.6</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.7 58-Missile Technical Database Catalog</span><span class="dots"></span><span>3.7</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.8 SQLite Scenario Persistence & Models</span><span class="dots"></span><span>3.8</span></div>
  <div class="toc-item" style="padding-left: 15px;"><span>3.9 Automated Unit Testing Suite</span><span class="dots"></span><span>3.9</span></div>
  <div class="toc-item"><span>4. 58-Missile Master Technical Catalog Table</span><span class="dots"></span><span>Section 4</span></div>
  <div class="toc-item"><span>5. Verbatim Full Codebase Listing (All 17 Source Files)</span><span class="dots"></span><span>Section 5</span></div>
  <div class="toc-item"><span>6. Gemini Prompt Engineering Guide & Extension Templates</span><span class="dots"></span><span>Section 6</span></div>
</div>
""")

# ----------------- SECTION 1: EXECUTIVE SUMMARY -----------------
html_content.append("""
<h1>1. EXECUTIVE SUMMARY & PROJECT PURPOSE</h1>
<p>
  The <b>Real-World Missile Impact Simulator</b> is a comprehensive, map-centric desktop software application designed
  to model ballistic, cruise, and hypersonic missile trajectories, verify physical range envelopes between arbitrary
  global coordinates, simulate nuclear and conventional detonations based on empirical blast physics, and assess
  humanitarian casualties using live public urban population databases over Wi-Fi.
</p>

<div class="callout important">
  <div class="callout-title">🎯 Core Mission Requirements Achieved:</div>
  <ul>
    <li><b>Mandatory Tkinter Core Framework:</b> Tkinter acts as the root window (<code>MissileSimulatorApp(tk.Tk)</code>) hosting top menus, toolbar controls, status bar telemetry, and technical modal dialogs.</li>
    <li><b>Hardware-Accelerated 3D Earth:</b> Directly embeds CesiumJS running within PyView (<code>pywebview</code>) into a native Tkinter frame—completely avoiding separate popup browser windows or disconnected HTML files.</li>
    <li><b>Glasstone-Dolan (1977) Physics:</b> Models cube-root scaled blast overpressures (20 psi, 5 psi, 1 psi), fireball vaporization, and 3rd-degree thermal burns for arbitrary kiloton yields or conventional explosives.</li>
    <li><b>No Private API Keys Needed:</b> Operates over Wi-Fi using open public endpoints from OpenStreetMap Nominatim and OpenDataSoft GeoNames datasets.</li>
    <li><b>Extensive 58-Missile Inventory:</b> Features 58 real-world systems across 10 major world powers (with all Pakistani missiles permanently excluded).</li>
    <li><b>Interactive Dropdown City Search:</b> Provides live debounced autocomplete for both Launch Site (Origin) and Target (Destination) with single-click pin placement and camera fly-to.</li>
    <li><b>Camera Rotation vs. Pin Placement:</b> Prevents accidental pin drops while revolving Earth by enforcing a mouse movement travel threshold (&ge; 6 pixels).</li>
  </ul>
</div>
""")

# ----------------- SECTION 2: SYSTEM ARCHITECTURE -----------------
html_content.append("""
<h1>2. SYSTEM ARCHITECTURE & DUAL-FRAMEWORK DESIGN</h1>
<p>
  The simulator utilizes a hybrid architecture combining the reliable native desktop controls of <b>Python Tkinter</b>
  with the WebGL 3D rendering capabilities of <b>CesiumJS</b> via <b>PyView (`pywebview`)</b>.
</p>

<h2>2.1 High-Level Architecture Diagram</h2>
<div class="code-container" style="page-break-inside: avoid;">
  <div class="code-header"><span class="file-path">System Architecture Topology</span><span class="file-meta">ASCII Block Diagram</span></div>
  <pre class="code-block">
+--------------------------------------------------------------------------------------------------------+
|                                    TKINTER MASTER WINDOW (tk.Tk)                                       |
|  - Menu Bar (File, Missiles, Scenarios, Physics, Help)                                                |
|  - Quick-Action Toolbar (Missile Catalog, Saved Scenarios, Save Mission, Blast Physics)               |
+--------------------------------------------------------------------------------------------------------+
|                                                                                                        |
|  +--------------------------------------------------------------------------------------------------+  |
|  |                NATIVE TKINTER CONTAINER FRAME (self.viewport_frame: winfo_id = HWND)              |  |
|  |                                                                                                  |  |
|  |  +--------------------------------------------------------------------------------------------+  |  |
|  |  |                      EMBEDDED PYVIEW (pywebview) 3D VIEWPORT (CHILD HWND)                  |  |  |
|  |  |                                                                                            |  |  |
|  |  |   +-------------------------------------------------------------------------------------+  |  |  |
|  |  |   |                     CESIUMJS 3D EARTH (Hardware-Accelerated WebGL)                  |  |  |  |
|  |  |   |   - WGS84 Ellipsoid, High-Res ArcGis Satellite Imagery, Starfield & Atmosphere      |  |  |  |
|  |  |   |   - Green Origin Pin (Launch Site) & Red Destination Pin (Target)                   |  |  |  |
|  |  |   |   - Cyan Maximum Range Geodesic Circle Envelope & Range Status Interlock            |  |  |  |
|  |  |   |   - Concentric Blast Hazard Rings: Fireball, 20 psi, 5 psi, Thermal, 1 psi          |  |  |  |
|  |  |   +-------------------------------------------------------------------------------------+  |  |  |
|  |  |   |                     FLOATING HUD COMMAND OVERLAY (Glassmorphism CSS)                |  |  |  |
|  |  |   |   - Origin/Target City Autocomplete Search with Live Dropdowns                      |  |  |  |
|  |  |   |   - 58-Missile Filter & System Selector + Spec Card (Country, Mach, Range)          |  |  |  |
|  |  |   |   - Nuclear Warhead Toggle & Kiloton Yield Selector (1 kt to 1000 kt)               |  |  |  |
|  |  |   |   - Live Public Population Indicator (OpenDataSoft / GeoNames Wi-Fi lookup)         |  |  |  |
|  |  |   |   - "SIMULATE LAUNCH & IMPACT" Button & Post-Impact Assessment Modal                |  |  |  |
|  |  |   +-------------------------------------------------------------------------------------+  |  |  |
|  |  +--------------------------------------------------------------------------------------------+  |  |
|  +--------------------------------------------------------------------------------------------------+  |
|                                                                                                        |
+--------------------------------------------------------------------------------------------------------+
|  STATUS BAR: 🟢 Tkinter Core Engine: ACTIVE | PyView: EMBEDDED | Wi-Fi: OSM/GeoNames | DB: 58 Missiles   |
+--------------------------------------------------------------------------------------------------------+
         |                                                                      ^
         | IPC Bridge (window.pywebview.api)                                    | HTTP / REST Fallback
         v                                                                      |
+--------------------------------------------------------------------------------------------------------+
|                                    PYTHON BACKEND SERVICES & ENGINES                                   |
|  - SimulatorApi: Exposed methods (search_city, reverse_geocode, get_population, simulate_launch)      |
|  - GlobeBridgeServer: Threading HTTP server serving static globe files & REST API fallback endpoints   |
|  - MapboxGeocodingService: OSM Nominatim + OpenDataSoft + Unicode transliteration clean_label()       |
|  - PopulationService: Live municipal population queries & density estimation with SQLite caching       |
|  - ImpactPhysics: Glasstone-Dolan cube-root scaling equations & annular casualty integrations          |
|  - ScenarioDatabase: SQLite scenarios.db schema & CRUD persistence                                    |
+--------------------------------------------------------------------------------------------------------+
  </pre>
</div>

<h2>2.2 Process Lifecycle & Initialization Sequence</h2>
<ol>
  <li><b>Bootstrap:</b> User runs <code>python app/main.py</code> or double-clicks <code>run_simulator.bat</code>.</li>
  <li><b>Bridge Server Start:</b> <code>GlobeBridgeServer(port=8765)</code> spins up a background daemon HTTP server serving the CesiumJS web assets.</li>
  <li><b>Tkinter Root Construction:</b> <code>MissileSimulatorApp</code> builds the root window, top menu bar, command toolbar, status bar, and central <code>tk.Frame</code>.</li>
  <li><b>PyView Window Creation:</b> <code>webview.create_window()</code> initializes a hardware-accelerated WebView2 window pointing to <code>http://127.0.0.1:8765/index.html</code>.</li>
  <li><b>Native OS Embedding:</b> When the PyView window emits its <code>shown</code> event, the Win32 API <code>SetParent</code> reparents the window into the Tkinter container frame HWND, stripping popup/caption window styles (<code>WS_CHILD</code>), making the 3D globe a seamless sub-view of Tkinter.</li>
  <li><b>Window Resizing Synchronization:</b> The Tkinter container binds to <code>&lt;Configure&gt;</code>, calling <code>MoveWindow</code> to resize the embedded WebGL viewport dynamically whenever the user resizes the Tkinter window.</li>
</ol>
""")

# ----------------- SECTION 3: DETAILED MODULE BREAKDOWN -----------------
html_content.append("""
<h1>3. DETAILED MODULE BREAKDOWN & ENGINEERING SPECIFICATIONS</h1>

<h2>3.1 Tkinter Master Application (`app/ui/main_window.py`)</h2>
<p>
  Serves as the mandatory top-level GUI framework. Key classes:
</p>
<ul>
  <li><code>MissileSimulatorApp(tk.Tk)</code>: Root window hosting menus, action buttons, embedded viewport frame, and status bar.</li>
  <li><code>MissileCatalogDialog(tk.Toplevel)</code>: Interactive searchable catalog using <code>ttk.Treeview</code> listing all 58 missiles with filtering by name, country, or classification.</li>
  <li><code>ScenarioManagerDialog(tk.Toplevel)</code>: Scenario persistence manager allowing users to browse, load, or delete saved scenarios from <code>scenarios.db</code>.</li>
  <li><code>PhysicsInfoDialog(tk.Toplevel)</code>: Dedicated scientific documentation window explaining the Glasstone-Dolan equations and overpressure thresholds.</li>
  <li><code>launch_simulator_app()</code>: Bootstrapping function that initializes threading, Tkinter root, and PyView embedding.</li>
</ul>

<h2>3.2 3D CesiumJS Viewport & HUD Overlay (`app/visualization/globe/index.html`)</h2>
<p>
  A single-page WebGL application running inside the embedded viewport:
</p>
<ul>
  <li><b>CesiumJS Viewer:</b> Utilizes ArcGis World Imagery, WGS84 ellipsoid coordinates, and depth testing for terrain.</li>
  <li><b>Camera Drag Threshold:</b> Differentiates between dragging to rotate the Earth (&ge; 6px movement) versus a deliberate stationary click (&lt; 6px) to select pins.</li>
  <li><b>Interactive HUD:</b> Glassmorphism panel featuring Origin/Destination city search inputs with debounced live autocomplete dropdowns, 58-missile system selectors, country filters, and yield controls.</li>
  <li><b>Range Circle & Launch Interlock:</b> Renders a cyan geodesic circle around the launch site. If distance exceeds the missile's maximum range, the banner turns red and launch is locked.</li>
  <li><b>Post-Impact Assessment Modal:</b> Displays concentric glowing blast rings, flight time, distance, verified population, and an animated casualty chart.</li>
</ul>

<h2>3.3 Python-JavaScript IPC Bridge (`app/services/webview_api.py`)</h2>
<p>
  Exposes high-level Python methods directly to JavaScript under <code>window.pywebview.api</code>:
</p>
<ul>
  <li><code>search_city(query)</code>: Queries geocoding service and returns matching candidates.</li>
  <li><code>reverse_geocode(lon, lat)</code>: Converts clicked coordinates into city/state/country labels.</li>
  <li><code>get_population(lon, lat, label)</code>: Fetches live verified municipal population over Wi-Fi.</li>
  <li><code>simulate_launch(origin, dest, missile_id, is_nuclear, yield_kt)</code>: Verifies range, computes blast effects, and returns the impact assessment.</li>
  <li><code>save_scenario(...)</code> and <code>list_scenarios()</code>: Database operations for mission persistence.</li>
</ul>

<h2>3.4 Glasstone-Dolan Blast Physics & Casualties (`app/services/impact_physics.py`)</h2>
<p>
  Implements the standard <b>Glasstone-Dolan (1977)</b> nuclear and conventional weapons blast equations:
</p>
<ul>
  <li><b>Cube-Root Scaling:</b> Concentric radii scale proportionally to \(Y^{1/3}\), where \(Y\) is yield in kilotons TNT:
    <div style="background: #f8fafc; padding: 10px; border-left: 3px solid #0284c7; margin: 8px 0; font-family: Consolas, monospace;">
      r_fireball = 0.048 &times; Y<sup>0.4</sup> km<br/>
      r_heavy (20 psi) = 0.28 &times; Y<sup>1/3</sup> km<br/>
      r_moderate (5 psi) = 0.65 &times; Y<sup>1/3</sup> km<br/>
      r_thermal (3rd deg) = 1.15 &times; Y<sup>0.41</sup> km<br/>
      r_light (1 psi) = 1.60 &times; Y<sup>1/3</sup> km
    </div>
  </li>
  <li><b>Humanitarian Casualties:</b> Evaluated across annular rings:
    <ul>
      <li>Fireball Zone: 100% fatalities.</li>
      <li>20 psi Zone: 90% fatalities, 10% severe injuries (complete structural collapse).</li>
      <li>5 psi Zone: 50% fatalities, 40% injuries (residential structural collapse).</li>
      <li>Thermal Burn Zone: 15% fatalities, 50% second- and third-degree burn injuries.</li>
    </ul>
  </li>
</ul>

<h2>3.5 Multi-Provider Geocoding & Transliteration (`app/services/mapbox_geocoding.py`)</h2>
<p>
  Ensures global geocoding works seamlessly across all small towns and districts worldwide without requiring private API tokens:
</p>
<ul>
  <li><b>Triple-Tier Redundancy:</b> Mapbox v6 forward/reverse (if configured) &rarr; OpenStreetMap Nominatim API (free public Wi-Fi) &rarr; OpenDataSoft GeoNames global dataset &rarr; Built-in offline major cities catalog.</li>
  <li><b>Unicode Transliteration (<code>clean_label</code>):</b> Decomposes and transliterates accented characters (e.g. <code>Sonīpat</code> &rarr; <code>Sonipat</code>) using <code>unicodedata.normalize('NFKD')</code> to prevent Windows <code>cp1252</code> charmap encoding exceptions.</li>
  <li><b>Deduplication:</b> Coordinates and labels are normalized and deduplicated before rendering in the dropdown list.</li>
</ul>

<h2>3.6 Urban Population & SQLite Caching (`app/services/population_service.py`)</h2>
<p>
  Automatically resolves real-world population and density without prompting the user:
</p>
<ul>
  <li>Queries OpenDataSoft / GeoNames worldwide cities database matching coordinates within &plusmn;0.35&deg; bounding box.</li>
  <li>Calculates realistic urban population densities per km&sup2; based on city population tiers.</li>
  <li>Maintains an internal SQLite cache (<code>population_cache</code> table) to store query results locally for instant sub-millisecond retrieval.</li>
</ul>

<h2>3.7 Comprehensive 58-Missile Inventory (`app/data/reference_data.json`)</h2>
<p>
  Contains 58 real-world missile systems across 10 global powers: India, United States, Russia, China, France, United Kingdom, Israel, Iran, South Korea, and North Korea. All Pakistani missiles have been completely removed.
</p>

<h2>3.8 SQLite Scenario Persistence (`app/data/database.py`, `models.py`)</h2>
<p>
  Provides local database storage in <code>scenarios.db</code> using Python's built-in <code>sqlite3</code> library. Saves mission scenarios with full coordinate tracking, missile configuration, warhead yield, and timestamps.
</p>

<h2>3.9 Unit Verification Suite (`tests/test_all.py`)</h2>
<p>
  Includes 8 automated test cases verifying missile dataset integrity, Haversine distance, range limit interlocks, nuclear blast radii calculations, geocoding fallbacks, SQLite persistence, Python API bridges, and Tkinter Treeview dialog rendering.
</p>
""")

# ----------------- SECTION 4: 58-MISSILE MASTER TABLE -----------------
html_content.append("""
<h1>4. 58-MISSILE MASTER TECHNICAL CATALOG TABLE</h1>
<p>
  The following table provides the complete technical specifications of all 58 missiles currently configured in the database:
</p>
<table class="data-table">
  <thead>
    <tr>
      <th>#</th>
      <th>Country</th>
      <th>Missile System</th>
      <th>Classification</th>
      <th>Max Range (km)</th>
      <th>Speed (Mach)</th>
      <th>Warhead Type</th>
      <th>Default Yield</th>
    </tr>
  </thead>
  <tbody>
""")

for i, m in enumerate(missiles, start=1):
    nuke = "☢ Nuclear" if m.get("nuclear_capable") else "💥 Conventional"
    y_str = f"{m.get('default_nuclear_yield_kt')} kt" if m.get("nuclear_capable") else "N/A"
    html_content.append(f"""
    <tr>
      <td>{i}</td>
      <td><b>{m.get('country')}</b></td>
      <td>{m.get('name')}</td>
      <td>{m.get('type')}</td>
      <td style="text-align: right;">{m.get('max_range_km', 0):,} km</td>
      <td style="text-align: center;">Mach {m.get('speed_mach', 1.0)}</td>
      <td style="text-align: center;">{nuke}</td>
      <td style="text-align: right;">{y_str}</td>
    </tr>
    """)

html_content.append("""
  </tbody>
</table>
""")

# ----------------- SECTION 5: VERBATIM FULL CODEBASE -----------------
html_content.append("""
<h1>5. VERBATIM FULL CODEBASE LISTING (ALL 17 SOURCE FILES)</h1>
<p>
  Below is the complete, unabridged source code for every file in the project repository.
  Lines and formatting are strictly preserved.
</p>
""")

for rel_path, desc, lang in files_to_include:
    if rel_path in file_contents:
        item = file_contents[rel_path]
        escaped_code = html.escape(item["content"])
        html_content.append(f"""
<div class="code-container">
  <div class="code-header">
    <span class="file-path">{rel_path}</span>
    <span class="file-meta">{item['lines']} lines &bull; {item['size_bytes']:,} bytes &bull; {item['desc']}</span>
  </div>
  <pre class="code-block"><code>{escaped_code}</code></pre>
</div>
""")

# ----------------- SECTION 6: GEMINI PROMPT ENGINEERING GUIDE -----------------
html_content.append("""
<h1>6. GEMINI PROMPT ENGINEERING GUIDE & EXTENSION TEMPLATES</h1>
<p>
  This section is specifically formulated to assist you when uploading this PDF to <b>Google Gemini</b>.
  By providing Gemini with this PDF, Gemini will have the entire codebase, architecture, physics equations,
  and constraints in its context window. You can copy-paste any of the prompt templates below directly into Gemini.
</p>

<h2>6.1 System Prompt Context to Paste into Gemini</h2>
<div class="prompt-box">
I have uploaded the complete technical dossier and source code of my desktop project:
"Real-World Missile Impact Simulator" (written in Python with Tkinter and PyView/CesiumJS).
Please read and internalize the architecture, specifically:
1. Tkinter (app/ui/main_window.py) is the MANDATORY primary GUI framework hosting the window, menus, dialogs, and toolbar.
2. PyView / CesiumJS (app/visualization/globe/index.html) is embedded as a child window inside Tkinter via Win32 SetParent.
3. Impact physics uses Glasstone-Dolan cube-root scaling (app/services/impact_physics.py).
4. Live geocoding and population lookups are handled over Wi-Fi without proprietary API keys (OpenStreetMap & GeoNames).
5. All 58 missiles across 10 powers are defined in app/data/reference_data.json (Pakistani missiles excluded).

Whenever I ask for modifications or features, ensure:
- The code you provide maintains Tkinter as the primary GUI.
- You provide exact diffs or complete drop-in replacement files.
- You keep all existing features (dropdown search, blast rings, live population, SQLite persistence) intact.
</div>

<h2>6.2 Ready-to-Use Task Prompts for Gemini</h2>

<h3>Template A: Adding Ballistic Trajectory Curve Animations</h3>
<div class="prompt-box">
Gemini, based on the uploaded codebase, I want to add an animated 3D parabolic ballistic flight trajectory arc on the Cesium globe when "SIMULATE LAUNCH & IMPACT" is pressed.
- In app/visualization/globe/index.html, calculate an apogee altitude based on missile range (e.g., ICBM apogee up to 1,200 km, cruise missiles low altitude 50 km).
- Animate a glowing projectile traveling along the geodesic arc from Origin to Target before triggering the impact blast rings.
- Show an on-screen HUD flight countdown timer.
Please provide the exact JavaScript code modifications for index.html.
</div>

<h3>Template B: Adding Anti-Ballistic Missile (ABM) Interception Mechanics</h3>
<div class="prompt-box">
Gemini, based on the uploaded codebase, I want to introduce an Air Defense / Missile Interceptor simulation (e.g. S-400, Patriot PAC-3, Iron Dome, Arrow 3, David's Sling).
- Extend app/data/reference_data.json to add an "interceptors" section with operational ranges, intercept altitudes, and kill probability (Pk).
- Add an option in the Tkinter toolbar and HUD to place an Air Defense Battery.
- Calculate whether the incoming missile passes through the interception envelope and simulate interception success vs failure.
Please outline the architectural changes and provide the code updates for impact_physics.py, webview_api.py, and index.html.
</div>

<h3>Template C: Nuclear Fallout Plume & Wind Vector Modeling</h3>
<div class="prompt-box">
Gemini, based on the uploaded codebase, I want to model radioactive fallout plumes based on atmospheric wind direction and speed.
- In impact_physics.py, add equations for cigar-shaped fallout dispersion ellipses (Early Fallout: 300 rad/hr, 100 rad/hr, 10 rad/hr).
- In index.html, render the asymmetric fallout plume extending downwind from the ground-zero coordinates.
- Calculate prolonged radiation casualties in addition to immediate blast fatalities.
Please provide the physics formulas and code implementation.
</div>

<h3>Template D: Exporting Detailed Mission Assessment Reports to PDF / CSV</h3>
<div class="prompt-box">
Gemini, based on the uploaded codebase, I want to add an "Export Mission Report" button to both the Tkinter toolbar and the Post-Impact Assessment modal.
- It should generate a detailed PDF report containing the scenario parameters, origin/target coordinates, verified urban population, blast radii, estimated casualties, and missile technical specifications.
- Please provide the Python backend function in webview_api.py and the Tkinter menu action in main_window.py.
</div>
""")

html_content.append("</body></html>")

full_html = "\n".join(html_content)
OUTPUT_HTML.write_text(full_html, encoding="utf-8")
print(f"HTML Dossier generated: {OUTPUT_HTML} ({len(full_html):,} bytes)")

# Convert to PDF via Microsoft Edge Headless
print("Rendering PDF via Microsoft Edge Headless...")
edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not Path(edge_exe).exists():
    edge_exe = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

cmd = [
    edge_exe,
    "--headless=new",
    "--disable-gpu",
    "--run-all-compositor-stages-before-draw",
    "--no-pdf-header-footer",
    f"--print-to-pdf={OUTPUT_PDF}",
    str(OUTPUT_HTML.as_uri()),
]

res = subprocess.run(cmd, capture_output=True, text=True)
if OUTPUT_PDF.exists():
    pdf_size = OUTPUT_PDF.stat().st_size
    print(f"SUCCESS: PDF created at {OUTPUT_PDF} ({pdf_size:,} bytes)")
    # Copy to project folder as well
    try:
        import shutil
        shutil.copy2(OUTPUT_PDF, PROJECT_PDF)
        print(f"Copied PDF to project folder: {PROJECT_PDF}")
    except Exception as e:
        print(f"Warning copying to project: {e}")
else:
    print(f"FAILED to generate PDF. Edge stderr: {res.stderr}")
