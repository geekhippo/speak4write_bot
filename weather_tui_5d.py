#!/usr/bin/env python3
"""
weather_tui_5d.py - 5‑day text‑based weather forecast with a tiny ASCII‑graph.

Features
---------
* Shows min / max temperature for the next 5 days.
* Draws a simple horizontal bar whose length represents the high temperature.
* Colour‑codes bars (blue → cold, green → mild, red → hot).
* Auto‑refreshes every 6 seconds (or on any key press).
* Uses only the standard library + `requests` (pre‑installed in the OpenClaw env).

Usage
-----
    python3 weather_tui_5d.py "<city>"
Example
-------
    python3 weather_tui_5d.py "Moscow"
"""

import sys
import json
import textwrap
import curses
import requests

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def fetch_forecast(city: str) -> dict:
    """
    Query wttr.in for a JSON payload that contains a 7‑day forecast.
    We keep only the first 5 entries (today + next 4 days).
    """
    url = f"http://wttr.in/{city}?format=j1"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


def colour_for_temp(temp_c: float) -> int:
    """
    Return a colour pair index based on temperature.
    - < 0 °C  → colour pair 1 (blue)
    - 0‑25 °C → colour pair 2 (green)
    - > 25 °C → colour pair 3 (red)
    """
    if temp_c < 0:
        return 1
    if temp_c <= 25:
        return 2
    return 3


def draw_bar(max_temp: float, max_bar_len: int) -> str:
    """
    Very small ASCII bar – length proportional to the temperature.
    The bar is capped at `max_bar_len` characters.
    """
    # Normalise: 0 °C → 0 bars, 40 °C → max_bar_len bars (arbitrary ceiling)
    norm = max_temp / 40.0
    length = int(norm * max_bar_len)
    return "[" + "#" * length + ">" + " " * (max_bar_len - length) + "]"


# --------------------------------------------------------------------------- #
# Main TUI
# --------------------------------------------------------------------------- #
def main(stdscr, city):
    curses.curs_set(0)               # hide cursor
    stdscr.nodelay(True)             # non‑blocking key reads
    stdscr.timeout(6000)             # refresh every 6 s

    # Initialise colour pairs (if the terminal supports them)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE,   curses.COLOR_BLACK)   # cold
        curses.init_pair(2, curses.COLOR_GREEN,  curses.COLOR_BLACK)   # mild
        curses.init_pair(3, curses.COLOR_RED,    curses.COLOR_BLACK)   # hot
        curses.init_pair(4, curses.COLOR_WHITE,  curses.COLOR_BLACK)   # default text

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # --------------------------------------------------------------- #
        # Header
        # --------------------------------------------------------------- #
        header = f" 5‑Day Forecast for {city}  "
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(0, (width - len(header)) // 2, header)
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        # --------------------------------------------------------------- #
        # Fetch & parse forecast
        # --------------------------------------------------------------- #
        data = fetch_forecast(city)
        if "error" in data:
            err_msg = f"Error: {data['error']}"
            stdscr.addstr(2, 2, err_msg, curses.color_pair(3))
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord('q'), ord('Q')):
                break
            continue

        # Grab the first 5 entries (today + next 4 days)
        forecast = data.get("weather", [])[:5]
        if not forecast:
            stdscr.addstr(2, 2, "No forecast data", curses.color_pair(3))
            stdscr.refresh()
            continue

        # Determine scaling for the temperature bars
        temps = [float(day["maxtempC"]) for day in forecast]
        max_temp = max(temps)
        max_bar_len = min(30, width - 4)          # never exceed line width

        # --------------------------------------------------------------- #
        # Body – one line per day
        # --------------------------------------------------------------- #
        start_y = 3
        for idx, day in enumerate(forecast):
            y = start_y + idx
            if y >= height - 2:
                break

            # Human‑readable date (wttr.in returns ISO date)
            date_str = day.get("date", "??")
            max_c = day.get("maxtempC", "?")
            min_c = day.get("mintempC", "?")
            precip = day.get("precipMM", "0")     # mm of precipitation

            # Build temperature bar
            bar = draw_bar(float(max_c), max_bar_len)

            # Choose colour based on temperature
            colour_idx = colour_for_temp(float(max_c))
            stdscr.attron(curses.color_pair(colour_idx))
            line = f" {date_str}  Max:{max_c}°C  Min:{min_c}°C  {bar}"
            stdscr.addstr(y, 2, line[: width - 2])   # truncate if too long
            stdscr.attroff(curses.color_pair(colour_idx))

        # --------------------------------------------------------------- #
        # Footer / instructions
        # --------------------------------------------------------------- #
        footer = " Press 'q' to quit, any other key refreshes now "
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height - 1,
                      (width - len(footer)) // 2,
                      footer)
        stdscr.attroff(curses.color_pair(3))

        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        # otherwise loop repeats automatically after the timeout


def run():
    if len(sys.argv) < 2:
        print("Usage: python3 weather_tui_5d.py \"<city>\"")
        sys.exit(1)
    city = sys.argv[1]
    curses.wrapper(main, city)


if __name__ == "__main__":
    run()