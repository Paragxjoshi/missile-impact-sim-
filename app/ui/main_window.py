import os
import sys
import ctypes
import threading
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any

import webview

from app.services.geocoding import PlaceCandidate, GeocodingError
from app.services.impact_physics import calculate_great_circle_distance_km, check_within_range
from app.services.bridge_server import GlobeBridgeServer, SimulatorApi

# deep dark palette with a single accent colour
BG = "#0b0b0f"
PANEL = "#121218"
FIELD = "#1b1b23"
TEXT = "#ececf0"
MUTED = "#7b7b88"
ACCENT = "#ff5a1f"

FONT = ("Segoe UI", 10)
FONT_LABEL = ("Segoe UI Semibold", 8)
FONT_BIG = ("Segoe UI Light", 34)
FONT_TITLE = ("Segoe UI Semibold", 11)

# display scale (1.0 at 100%). set by enable_dpi_awareness() before tk starts.
UI_SCALE = 1.0


def px(n: float) -> int:
    return int(round(n * UI_SCALE))


def enable_dpi_awareness() -> None:
    """make tkinter dpi-aware so it uses the same physical pixels as the embedded webview"""
    global UI_SCALE
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            return
    try:
        UI_SCALE = ctypes.windll.user32.GetDpiForSystem() / 96.0
    except (AttributeError, OSError):
        UI_SCALE = 1.0


def label(parent, text="", fg=TEXT, bg=PANEL, font=FONT, **kw) -> tk.Label:
    return tk.Label(parent, text=text, fg=fg, bg=bg, font=font, anchor="w", **kw)


class MissileSimulatorApp(tk.Tk):
    """left controls, embedded globe in the middle, results on the right"""

    def __init__(self, api: SimulatorApi, bridge: GlobeBridgeServer):
        super().__init__()
        self.api = api
        self.bridge = bridge
        self.missiles = api.missiles

        self.title("Missile Impact Simulator")
        self.geometry(f"{px(1440)}x{px(860)}")
        self.minsize(px(1120), px(700))
        self.configure(bg=BG)

        self.child_hwnd: Optional[int] = None
        self.current_width = 700
        self.current_height = 800

        self.places: Dict[str, Optional[PlaceCandidate]] = {"origin": None, "destination": None}
        self.pick_mode = "origin"
        self._pick_seq = {"origin": 0, "destination": 0}  # drops stale name lookups
        self._fly_seq = 0

        self._build_styles()
        left = tk.Frame(self, bg=PANEL, width=px(320))
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._build_controls(left)

        right = tk.Frame(self, bg=PANEL, width=px(340))
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self.results = tk.Frame(right, bg=PANEL)
        self.results.pack(fill="both", expand=True, padx=px(22), pady=px(22))

        self.viewport = tk.Frame(self, bg=BG)
        self.viewport.pack(side="left", fill="both", expand=True)
        self.viewport.bind("<Configure>", self._on_viewport_resize)
        self.update()
        self.tk_hwnd = self.viewport.winfo_id()

        self._set_pick_mode("origin")
        self._on_missile_changed()
        self._show_placeholder()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- layout ----
    def _build_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TCombobox", fieldbackground=FIELD, background=FIELD, foreground=TEXT, arrowcolor=MUTED,
            bordercolor=FIELD, lightcolor=FIELD, darkcolor=FIELD, selectbackground=FIELD, selectforeground=TEXT, padding=6,
        )
        style.map("TCombobox", fieldbackground=[("readonly", FIELD)], selectbackground=[("readonly", FIELD)],
                  selectforeground=[("readonly", TEXT)])
        self.option_add("*TCombobox*Listbox.background", FIELD)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

    def _build_controls(self, parent: tk.Frame) -> None:
        pad = px(22)
        box = tk.Frame(parent, bg=PANEL)
        box.pack(fill="both", expand=True, padx=pad, pady=pad)

        label(box, "MISSILE IMPACT SIMULATOR", font=FONT_TITLE).pack(fill="x", pady=(0, px(22)))

        self.entries: Dict[str, tk.Entry] = {}
        for role, title in (("origin", "LAUNCH SITE"), ("destination", "TARGET")):
            label(box, title, fg=MUTED, font=FONT_LABEL).pack(fill="x", pady=(px(10), px(4)))
            entry = tk.Entry(
                box, bg=FIELD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT,
                highlightthickness=1, highlightbackground=FIELD, highlightcolor=ACCENT,
            )
            entry.pack(fill="x", ipady=px(6))
            entry.bind("<Return>", lambda _e, r=role: self._search(r))
            entry.bind("<FocusIn>", lambda _e, r=role: self._set_pick_mode(r))
            self.entries[role] = entry

        label(box, "MISSILE", fg=MUTED, font=FONT_LABEL).pack(fill="x", pady=(px(18), px(4)))
        self.missile_combo = ttk.Combobox(
            box, state="readonly", font=FONT, values=[f"{m['name']}  ·  {m['country']}" for m in self.missiles]
        )
        self.missile_combo.current(0)
        self.missile_combo.pack(fill="x")
        self.missile_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_missile_changed())

        self.status = label(box, "Click the globe to place the launch site", fg=MUTED, font=("Segoe UI", 9),
                            wraplength=px(270), justify="left")
        self.status.pack(fill="x", pady=(px(24), px(10)))

        self.launch_btn = tk.Button(
            box, text="LAUNCH", command=self._launch, font=FONT_LABEL, relief="flat", bd=0, cursor="hand2",
            bg=ACCENT, fg="#ffffff", activebackground="#ff7a47", activeforeground="#ffffff",
            disabledforeground=MUTED,
        )
        self.launch_btn.pack(fill="x", ipady=px(9))
        tk.Button(
            box, text="Clear", command=self._clear, font=("Segoe UI", 9), relief="flat", bd=0, cursor="hand2",
            bg=PANEL, fg=MUTED, activebackground=PANEL, activeforeground=TEXT,
        ).pack(pady=(px(8), 0))

    # ---- state helpers ----
    @property
    def missile(self) -> Dict[str, Any]:
        return self.missiles[self.missile_combo.current()]

    def _fly(self, lon: float, lat: float, height: float) -> Dict[str, Any]:
        """camera move for the globe; a unique id makes it repeat-safe"""
        self._fly_seq += 1
        return {"lon": lon, "lat": lat, "height": height, "fly_id": self._fly_seq}

    def _set_status(self, text: str, color: str = MUTED) -> None:
        self.status.config(text=text, fg=color)

    def _set_pick_mode(self, mode: str) -> None:
        self.pick_mode = mode
        self.bridge.update_state(pick_mode=mode)

    def _set_place(self, role: str, cand: Optional[PlaceCandidate], fly_height: Optional[float] = None) -> None:
        self.places[role] = cand
        entry = self.entries[role]
        entry.delete(0, "end")
        if cand:
            entry.insert(0, cand.label)
        # place the launch site first, then the target, then stop taking map clicks
        if self.places["origin"] and not self.places["destination"]:
            self._set_pick_mode("destination")
        elif self.places["origin"] and self.places["destination"]:
            self._set_pick_mode("none")
        if fly_height and cand:
            self.bridge.update_state(fly_to=self._fly(cand.longitude, cand.latitude, fly_height))
        self._refresh()

    def _refresh(self) -> None:
        """inputs changed: redraw pins and range, drop any old impact, update the status line"""
        pin = lambda c: {"label": c.label, "longitude": c.longitude, "latitude": c.latitude} if c else None
        o, d = self.places["origin"], self.places["destination"]
        self.bridge.update_state(
            origin=pin(o), destination=pin(d), missile=self.missile, launched=False, impact=None,
        )
        self._show_placeholder()

        if not o or not d:
            self._set_status("Place the launch site and the target" if not o and not d
                             else "Place the target" if o else "Place the launch site")
            self.launch_btn.config(state="disabled", bg=FIELD)
            return
        dist = calculate_great_circle_distance_km(o.longitude, o.latitude, d.longitude, d.latitude)
        if check_within_range(dist, self.missile):
            self._set_status(f"In range  ·  {dist:,.0f} of {self.missile['max_range_km']:,} km")
            self.launch_btn.config(state="normal", bg=ACCENT)
        else:
            self._set_status(f"Out of range  ·  {dist:,.0f} km, max {self.missile['max_range_km']:,} km", ACCENT)
            self.launch_btn.config(state="disabled", bg=FIELD)

    def _on_missile_changed(self) -> None:
        self._refresh()

    # ---- place selection ----
    def _search(self, role: str) -> None:
        query = self.entries[role].get().strip()
        if not query:
            return
        self._set_status("Searching...")

        def worker():
            try:
                found = self.api.geocoding_service.search_city(query)
                err = None if found else f"No place found for '{query}'"
            except (GeocodingError, OSError) as e:
                found, err = [], f"Search failed: {e}"
            self.after(0, lambda: self._on_search_done(role, found, err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_search_done(self, role: str, found, err: Optional[str]) -> None:
        if err:
            self._set_status(err, ACCENT)
        else:
            self._set_place(role, found[0], fly_height=450000.0)

    def on_globe_pick(self, role: str, lon: float, lat: float) -> None:
        """map click or pin drag. the pin lands at once with coordinates, then the place name fills in."""
        self._pick_seq[role] += 1
        seq = self._pick_seq[role]
        coords = PlaceCandidate(f"Coordinates ({lat:.3f}, {lon:.3f})", lon, lat, "manual-pin")
        self.after(0, lambda: self._set_place(role, coords))

        def worker():
            data = self.api.reverse_geocode(lon, lat)
            cand = PlaceCandidate(data["label"], data["longitude"], data["latitude"], data.get("provider_place_id", "pin"))
            self.after(0, lambda: self._apply_name(role, cand, seq))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_name(self, role: str, cand: PlaceCandidate, seq: int) -> None:
        if seq == self._pick_seq[role]:  # ignore if the pin was moved again meanwhile
            self._set_place(role, cand)

    # ---- launch and results ----
    def _launch(self) -> None:
        o, d = self.places["origin"], self.places["destination"]
        if not o or not d:
            return
        self.launch_btn.config(state="disabled", bg=FIELD, text="...")
        pt = lambda c: {"label": c.label, "longitude": c.longitude, "latitude": c.latitude}
        missile_id = self.missile["id"]

        def worker():
            res = self.api.simulate_launch(pt(o), pt(d), missile_id)
            self.after(0, lambda: self._on_launched(res))

        threading.Thread(target=worker, daemon=True).start()

    def _on_launched(self, res: Dict[str, Any]) -> None:
        self.launch_btn.config(state="normal", bg=ACCENT, text="LAUNCH")
        if not res.get("success"):
            self._set_status(res.get("error", "Simulation failed"), ACCENT)
            return
        d = self.places["destination"]
        impact = res["impact"]
        self.bridge.update_state(
            launched=True, impact=impact,
            fly_to=self._fly(d.longitude, d.latitude, max(impact["radii_km"]["light_blast_1psi_km"] * 3500.0, 150000.0)),
        )
        self._render_results(res)

    def _clear_results(self) -> None:
        for w in self.results.winfo_children():
            w.destroy()

    def _show_placeholder(self) -> None:
        self._clear_results()
        label(self.results, "Choose a launch site, a target and a missile, then launch.",
              fg=MUTED, font=("Segoe UI", 10), wraplength=px(290), justify="left").pack(fill="x")

    def _render_results(self, res: Dict[str, Any]) -> None:
        self._clear_results()
        est, radii = res["impact"]["estimates"], res["impact"]["radii_km"]
        pop = res["population_info"]

        for title, value in (("FATALITIES", est["estimated_fatalities"]), ("INJURIES", est["estimated_injuries"])):
            label(self.results, title, fg=MUTED, font=FONT_LABEL).pack(fill="x")
            label(self.results, f"{value:,}", font=FONT_BIG, fg=ACCENT if title == "FATALITIES" else TEXT).pack(fill="x", pady=(0, px(14)))

        label(self.results, "EFFECTS", fg=MUTED, font=FONT_LABEL).pack(fill="x", pady=(px(8), px(6)))
        for name, key in (("Fireball", "fireball_km"), ("Heavy blast  ·  20 psi", "heavy_blast_20psi_km"),
                          ("Moderate blast  ·  5 psi", "moderate_blast_5psi_km"), ("3rd-degree burns", "thermal_3rd_deg_km"),
                          ("Light blast  ·  1 psi", "light_blast_1psi_km")):
            row = tk.Frame(self.results, bg=PANEL)
            row.pack(fill="x", pady=px(2))
            label(row, name, bg=PANEL).pack(side="left")
            km = radii[key]
            tk.Label(row, text=f"{km * 1000:,.0f} m" if km < 1 else f"{km:,.1f} km", fg=MUTED, bg=PANEL, font=FONT).pack(side="right")

        label(self.results, "TARGET AREA", fg=MUTED, font=FONT_LABEL).pack(fill="x", pady=(px(22), px(6)))
        label(self.results, f"Population  ·  {pop.get('population', 0):,}").pack(fill="x")
        label(self.results, f"Density  ·  {pop.get('density_per_km2', 0):,.0f} per km²").pack(fill="x", pady=(px(2), 0))

    def _clear(self) -> None:
        for role in self.places:
            self._pick_seq[role] += 1
            self.places[role] = None
            self.entries[role].delete(0, "end")
        self._set_pick_mode("origin")
        self._refresh()
        self.bridge.update_state(fly_to=self._fly(0.0, 20.0, 18000000.0))

    # ---- window ----
    def _on_viewport_resize(self, event: tk.Event) -> None:
        self.current_width, self.current_height = event.width, event.height
        if self.child_hwnd and sys.platform == "win32":
            ctypes.windll.user32.MoveWindow(wintypes.HWND(self.child_hwnd), 0, 0, event.width, event.height, True)

    def _on_close(self) -> None:
        try:
            self.destroy()
        finally:
            os._exit(0)


def launch_simulator_app() -> None:
    """starts the bridge server, then runs tkinter with the pywebview globe embedded in its middle column"""
    app_ref: Dict[str, Any] = {"app": None}
    ready = threading.Event()

    enable_dpi_awareness()
    bridge = GlobeBridgeServer(on_globe_pick=lambda role, lon, lat: app_ref["app"] and app_ref["app"].on_globe_pick(role, lon, lat))
    globe_url = bridge.start()

    def run_tkinter():
        app = MissileSimulatorApp(bridge.api, bridge)
        app_ref["app"] = app
        ready.set()
        app.mainloop()

    # tkinter runs on its own thread so webview can use the main thread
    threading.Thread(target=run_tkinter, daemon=True).start()
    ready.wait()
    app = app_ref["app"]

    win = webview.create_window(
        title="Globe", url=globe_url, width=app.current_width, height=app.current_height, text_select=False,
    )

    def on_shown():
        # re-parent the webview window into the tkinter middle column as a borderless child
        if sys.platform != "win32":
            return
        try:
            child = win.native.Handle.ToInt64()
            u32 = ctypes.windll.user32
            u32.SetParent(wintypes.HWND(child), wintypes.HWND(app.tk_hwnd))
            style = u32.GetWindowLongW(child, -16)
            style &= ~(0x80000000 | 0x00C00000 | 0x00040000)  # popup, caption, thick frame
            style |= 0x40000000  # child
            u32.SetWindowLongW(child, -16, style)
            u32.MoveWindow(wintypes.HWND(child), 0, 0, app.current_width, app.current_height, True)
            app.child_hwnd = child
        except OSError as err:
            print(f"native embedding notice: {err}")

    win.events.shown += on_shown
    webview.start(debug=False)
