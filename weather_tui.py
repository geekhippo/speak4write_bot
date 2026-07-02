#!/usr/bin/env python3
"""
weather_tui.py - Simple TUI weather forecast using wttr.in

Usage:
    python3 weather_tui.py <city>
Example:
    python3 weather_tui.py "Moscow"
"""

import sys
import curses
import requests
import textwrap

def fetch_weather(city):
    """Fetch weather from wttr.in in plain text."""
    url = f"http://wttr.in/{city}?format=3"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as e:
        return f"Error fetching weather: {e}"

def fetch_weather_detailed(city):
    """Fetch a more detailed weather report."""
    url = f"http://wttr.in/{city}?format=%l:+%C+%t+%w+%h+%p"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text.strip()
    except Exception as e:
        return f"Error: {e}"

def main(stdscr, city):
    curses.curs_set(0)  # hide cursor
    stdscr.nodelay(True)  # non-blocking getch
    stdscr.timeout(5000)  # refresh every 5 seconds

    # Initialize colors if available
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        # Header
        header = f" Weather forecast for {city} "
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(0, (width - len(header)) // 2, header)
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

        # Fetch weather
        weather = fetch_weather(city)
        detailed = fetch_weather_detailed(city)

        # Display short line
        stdscr.addstr(2, 2, weather, curses.color_pair(1))

        # Display detailed info wrapped
        if detailed and not detailed.startswith("Error"):
            wrapped = textwrap.wrap(detailed, width - 4)
            for i, line in enumerate(wrapped[:height - 6]):
                stdscr.addstr(4 + i, 2, line, curses.color_pair(3))
        else:
            stdscr.addstr(4, 2, detailed, curses.color_pair(4))

        # Footer instructions
        footer = " Press 'q' to quit, any other key to refresh now "
        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(height - 1, (width - len(footer)) // 2, footer)
        stdscr.attroff(curses.color_pair(4))

        stdscr.refresh()

        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            break
        # any other key triggers immediate refresh (timeout will also refresh)

def run():
    if len(sys.argv) < 2:
        print("Usage: python3 weather_tui.py <city>")
        sys.exit(1)
    city = sys.argv[1]
    curses.wrapper(main, city)

if __name__ == "__main__":
    run()