#!/usr/bin/env python3
"""Install pywebview into the project venv so the launcher can open a native window."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / "venv"
if sys.platform == "win32":
    pip = VENV / "Scripts" / "pip.exe"
else:
    pip = VENV / "bin" / "pip"

if not pip.exists():
    print("venv not found — run the launcher once first, or: python3 -m venv venv")
    sys.exit(1)

pkgs = ["pywebview>=5.0"]
if sys.platform == "darwin":
    pkgs.append("pyobjc-framework-WebKit")
subprocess.check_call([str(pip), "install", *pkgs])
print("Desktop window library installed.")
