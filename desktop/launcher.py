#!/usr/bin/env python3
"""
ILovePDF Personal — native desktop launcher.

Double-click on macOS or Windows. Starts FastAPI + Next.js in the background,
opens a native window, and stops both engines when the window closes.
No terminal required.
"""
from __future__ import annotations

import os
import sys
import time
import signal
import shutil
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = ROOT / "venv"
DATA_DIR = ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
PID_FILE = DATA_DIR / "desktop.pids"

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
APP_URL = f"http://127.0.0.1:{FRONTEND_PORT}"

backend_proc: subprocess.Popen | None = None
frontend_proc: subprocess.Popen | None = None
status_lines: list[str] = []


def log(msg: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    status_lines.append(line)
    if len(status_lines) > 80:
        del status_lines[0]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / "desktop.log", "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)


def python_bin() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def npm_bin() -> str:
    return "npm.cmd" if sys.platform == "win32" else "npm"


def port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        try:
            return s.connect_ex((host, port)) == 0
        except OSError:
            return False


def wait_for_port(port: int, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_open(port):
            return True
        time.sleep(0.4)
    return False


def kill_port(port: int) -> None:
    """Best-effort free of a local port so relaunch always works."""
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                f'netstat -ano | findstr :{port}',
                shell=True, text=True, stderr=subprocess.DEVNULL,
            )
            pids = set()
            for line in out.splitlines():
                parts = line.split()
                if parts:
                    pids.add(parts[-1])
            for pid in pids:
                if pid.isdigit() and pid != "0":
                    subprocess.run(["taskkill", "/F", "/PID", pid],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        return
    try:
        out = subprocess.check_output(["lsof", "-t", f"-i:{port}"], text=True, stderr=subprocess.DEVNULL)
        for pid in out.split():
            try:
                os.kill(int(pid), signal.SIGKILL)
            except Exception:
                pass
    except Exception:
        pass


def ensure_env() -> None:
    env_file = ROOT / ".env"
    example = ROOT / ".env.example"
    if not env_file.exists() and example.exists():
        shutil.copy(example, env_file)
        log("Created .env from .env.example")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "storage" / "originals").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "storage" / "outputs").mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def ensure_venv() -> Path:
    py = python_bin()
    created = False
    if not py.exists():
        log("First launch: creating Python virtual environment…")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        created = True
    pip = VENV_DIR / ("Scripts/pip.exe" if sys.platform == "win32" else "bin/pip")
    if created:
        subprocess.check_call([str(pip), "install", "--upgrade", "pip"])
        subprocess.check_call([str(pip), "install", "-r", str(BACKEND_DIR / "requirements.txt")])
        log("Python environment ready.")
    # Native window library (best-effort; browser fallback if it fails)
    try:
        subprocess.check_call(
            [str(py), "-c", "import webview"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        log("Installing native window library (pywebview)…")
        pkgs = ["pywebview>=5.0"]
        if sys.platform == "darwin":
            pkgs.append("pyobjc-framework-WebKit")
        try:
            subprocess.check_call([str(pip), "install", *pkgs])
        except Exception as exc:
            log(f"Could not install pywebview ({exc}); will use the system browser.")
    return python_bin()


def ensure_frontend() -> None:
    if not (FRONTEND_DIR / "node_modules").exists():
        log("First launch: installing frontend packages (this can take a minute)…")
        subprocess.check_call([npm_bin(), "install"], cwd=str(FRONTEND_DIR))
    if not (FRONTEND_DIR / ".next").exists():
        log("First launch: building the studio UI…")
        subprocess.check_call([npm_bin(), "run", "build"], cwd=str(FRONTEND_DIR))
    log("Frontend ready.")


def start_backend(py: Path) -> subprocess.Popen:
    log(f"Starting PDF engine on {BACKEND_HOST}:{BACKEND_PORT}…")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    env["PYTHONUNBUFFERED"] = "1"
    log_path = LOG_DIR / "backend.log"
    fh = open(log_path, "ab")
    proc = subprocess.Popen(
        [str(py), "-m", "uvicorn", "app.main:app",
         "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)],
        cwd=str(ROOT),
        env=env,
        stdout=fh,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return proc


def start_frontend() -> subprocess.Popen:
    log(f"Starting studio UI on {APP_URL}…")
    log_path = LOG_DIR / "frontend.log"
    fh = open(log_path, "ab")
    env = os.environ.copy()
    env["PORT"] = str(FRONTEND_PORT)
    proc = subprocess.Popen(
        [npm_bin(), "run", "start"],
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=fh,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    return proc


def stop_engines() -> None:
    global backend_proc, frontend_proc
    log("Stopping local engines…")
    for proc in (frontend_proc, backend_proc):
        if proc is None:
            continue
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass
    kill_port(BACKEND_PORT)
    kill_port(FRONTEND_PORT)
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except Exception:
            pass
    backend_proc = None
    frontend_proc = None
    log("Engines stopped.")


def write_pids() -> None:
    pids = []
    if backend_proc and backend_proc.pid:
        pids.append(str(backend_proc.pid))
    if frontend_proc and frontend_proc.pid:
        pids.append(str(frontend_proc.pid))
    PID_FILE.write_text("\n".join(pids), encoding="utf-8")


def boot() -> None:
    global backend_proc, frontend_proc
    ensure_env()
    kill_port(BACKEND_PORT)
    kill_port(FRONTEND_PORT)
    py = ensure_venv()
    ensure_frontend()
    backend_proc = start_backend(py)
    frontend_proc = start_frontend()
    write_pids()
    if not wait_for_port(BACKEND_PORT, 40):
        log("WARNING: backend did not answer on port 8000. Check data/logs/backend.log")
    else:
        log("PDF engine is healthy.")
    if not wait_for_port(FRONTEND_PORT, 50):
        log("WARNING: studio UI did not answer on port 3000. Check data/logs/frontend.log")
    else:
        log("Studio UI is ready.")


def open_native_window() -> None:
    """Prefer a native window (pywebview). Fall back to the system browser."""
    try:
        import webview  # type: ignore
    except Exception:
        log("Opening in your default browser (install pywebview for an app window).")
        webbrowser.open(APP_URL)
        # Keep engines alive until the user closes this process
        try:
            while True:
                time.sleep(1)
                if backend_proc and backend_proc.poll() is not None:
                    log("Backend exited unexpectedly.")
                    break
                if frontend_proc and frontend_proc.poll() is not None:
                    log("Frontend exited unexpectedly.")
                    break
        except KeyboardInterrupt:
            pass
        return

    log("Opening native app window…")

    class Api:
        def status(self) -> str:
            return "\n".join(status_lines[-12:])

        def shutdown(self) -> None:
            stop_engines()

    window = webview.create_window(
        title="ILovePDF Personal — Local Private Edition",
        url=APP_URL,
        width=1280,
        height=860,
        min_size=(960, 640),
        background_color="#0f172a",
        confirm_close=False,
        js_api=Api(),
    )
    webview.start(gui=None, debug=False)


def main() -> None:
    os.chdir(ROOT)
    log("ILovePDF Personal desktop launcher starting…")
    try:
        boot()
        open_native_window()
    except Exception as exc:
        log(f"Launcher error: {exc}")
        # Last-resort: still try to open the browser if engines came up
        if port_open(FRONTEND_PORT):
            webbrowser.open(APP_URL)
            time.sleep(2)
        raise
    finally:
        stop_engines()


if __name__ == "__main__":
    main()
