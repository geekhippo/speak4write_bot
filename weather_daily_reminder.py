#!/usr/bin/env python3
import os, sys, subprocess, textwrap
import requests

CITY = "Yekaterinburg"

# fetch current weather in short format
url = f"http://wttr.in/{CITY}?format=3"
try:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    weather = r.text.strip()
except Exception as e:
    weather = f"❗ couldn't fetch weather: {e}"

# send message via openclaw command
cmd = ["openclaw", "message", "send", "--target", "telegram:6975303", "--message", f"Погода на сегодня: {weather}"]
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print(proc.stdout)
print(proc.stderr, file=sys.stderr)

if proc.returncode != 0:
    sys.exit(proc.returncode)

PY