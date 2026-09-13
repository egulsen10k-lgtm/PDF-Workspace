#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def cleanup():
    print("🧹 Cleaning up build artifacts, cache, and heavy dev directories...")
    
    # Folders to purge for sharing
    purge_dirs = [
        ROOT / "node_modules",
        ROOT / "frontend" / "node_modules",
        ROOT / "frontend" / ".next",
        ROOT / "venv",
        ROOT / "__pycache__",
        ROOT / "backend" / "__pycache__",
        ROOT / "backend" / "app" / "__pycache__",
        ROOT / "backend" / "app" / "routers" / "__pycache__",
        ROOT / "backend" / "app" / "services" / "__pycache__",
        ROOT / ".pytest_cache",
        ROOT / "dist"
    ]
    
    for d in purge_dirs:
        if d.exists():
            print(f"  Removing {d.relative_to(ROOT)}...")
            shutil.rmtree(d, ignore_errors=True)
            
    # Remove junk files
    for p in ROOT.rglob("*.pyc"):
        try:
            p.unlink()
        except:
            pass

    print("\n✨ Cleanup complete! The folder is now lightweight and ready to zip & share.")
    print("   When the recipient double-clicks Launch ILovePDF.bat or Launch ILovePDF.command,")
    print("   dependencies and environment will auto-rebuild on their machine instantly.")

if __name__ == "__main__":
    cleanup()
