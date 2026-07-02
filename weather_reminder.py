#!/usr/bin/env python3
import subprocess

msg = "Проверьте скрипт погоды ☂️"
# Send message via OpenClaw CLI
subprocess.run(["openclaw", "message", "send", "--target", "telegram:6975303", "--message", msg])
