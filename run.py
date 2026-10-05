#!/usr/bin/env python3
"""
Development runner for Quantum-Secure Communication & Voting System.
Runs both the FastAPI backend and the Vite frontend concurrently.
Handles graceful shutdown (Ctrl+C) and terminates child processes cleanly.
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
from pathlib import Path

# Enable ANSI escape sequences on Windows
if sys.platform == "win32":
    os.system("")

# Ensure standard streams use UTF-8 and line buffering
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# ANSI color codes
CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "Front_end"


def log(prefix: str, color: str, message: str) -> None:
    for line in message.rstrip().splitlines():
        print(f"{color}{BOLD}[{prefix}]{RESET} {line}", flush=True)


def stream_pipe(pipe, prefix: str, color: str):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            log(prefix, color, line.rstrip("\r\n"))
    except Exception:
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def terminate_process_tree(proc: subprocess.Popen, name: str) -> None:
    if proc.poll() is not None:
        return

    log("system", YELLOW, f"Stopping {name} (PID: {proc.pid})...")
    if sys.platform == "win32":
        try:
            # Forcefully terminate entire process tree on Windows
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            proc.terminate()
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.terminate()

    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        if sys.platform != "win32":
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()


def resolve_backend_cmd(host: str, port: int) -> list[str]:
    # Check if uv is available
    if shutil.which("uv"):
        return ["uv", "run", "fastapi", "dev", "src/main.py", "--host", host, "--port", str(port)]

    # Check for local venv python
    venv_py_win = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    venv_py_nix = BACKEND_DIR / ".venv" / "bin" / "python"
    venv_py = venv_py_win if sys.platform == "win32" else venv_py_nix

    py_bin = str(venv_py) if venv_py.is_file() else sys.executable
    return [
        py_bin,
        "-m",
        "uvicorn",
        "main:app",
        "--reload",
        "--app-dir",
        "src",
        "--host",
        host,
        "--port",
        str(port),
    ]


def resolve_frontend_cmd(port: int | None = None) -> list[str]:
    tool = None
    if shutil.which("bun"):
        tool = "bun"
    elif shutil.which("npm"):
        tool = "npm"
    elif shutil.which("pnpm"):
        tool = "pnpm"
    elif shutil.which("yarn"):
        tool = "yarn"
    else:
        raise RuntimeError("No package manager found for frontend. Please install bun or npm.")

    # On Windows, npm/pnpm/yarn are batch scripts
    if sys.platform == "win32" and tool in ("npm", "pnpm", "yarn"):
        tool_cmd = f"{tool}.cmd" if shutil.which(f"{tool}.cmd") else tool
    else:
        tool_cmd = tool

    cmd = [tool_cmd, "run", "dev"]
    if port:
        cmd.extend(["--", "--port", str(port)])
    return cmd


def main():
    parser = argparse.ArgumentParser(
        description="Run both FastAPI backend and Vite frontend development servers."
    )
    parser.add_argument(
        "--backend-only", action="store_true", help="Start only the backend server"
    )
    parser.add_argument(
        "--frontend-only", action="store_true", help="Start only the frontend server"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Backend host address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--backend-port", type=int, default=8000, help="Backend port (default: 8000)"
    )
    parser.add_argument(
        "--frontend-port", type=int, default=None, help="Frontend port (optional override)"
    )

    args = parser.parse_args()

    # UTF-8 encoding environment for child processes
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    processes: list[tuple[str, subprocess.Popen]] = []
    threads: list[threading.Thread] = []

    try:
        # Start backend
        if not args.frontend_only:
            if not BACKEND_DIR.is_dir():
                log("system", RED, f"Backend directory not found at: {BACKEND_DIR}")
                sys.exit(1)

            backend_cmd = resolve_backend_cmd(args.host, args.backend_port)
            log("system", GREEN, f"Starting backend: {' '.join(backend_cmd)}")

            proc_backend = subprocess.Popen(
                backend_cmd,
                cwd=str(BACKEND_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                preexec_fn=os.setsid if sys.platform != "win32" else None,
            )
            processes.append(("backend", proc_backend))

            t_backend = threading.Thread(
                target=stream_pipe,
                args=(proc_backend.stdout, "backend", CYAN),
                daemon=True,
            )
            t_backend.start()
            threads.append(t_backend)

        # Start frontend
        if not args.backend_only:
            if not FRONTEND_DIR.is_dir():
                log("system", RED, f"Frontend directory not found at: {FRONTEND_DIR}")
                sys.exit(1)

            frontend_cmd = resolve_frontend_cmd(args.frontend_port)
            log("system", GREEN, f"Starting frontend: {' '.join(frontend_cmd)}")

            proc_frontend = subprocess.Popen(
                frontend_cmd,
                cwd=str(FRONTEND_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=(sys.platform == "win32" and frontend_cmd[0].endswith(".cmd")),
                preexec_fn=os.setsid if sys.platform != "win32" else None,
            )
            processes.append(("frontend", proc_frontend))

            t_frontend = threading.Thread(
                target=stream_pipe,
                args=(proc_frontend.stdout, "frontend", MAGENTA),
                daemon=True,
            )
            t_frontend.start()
            threads.append(t_frontend)

        log("system", GREEN, "Both servers are launching! Press Ctrl+C to stop all servers.\n")

        # Wait for any process to exit or Ctrl+C
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    log("system", RED if ret != 0 else YELLOW, f"{name} exited with code {ret}")
                    return
            threading.Event().wait(0.5)

    except KeyboardInterrupt:
        log("system", YELLOW, "\nReceived shutdown signal (Ctrl+C). Terminating servers...")
    finally:
        for name, proc in processes:
            terminate_process_tree(proc, name)
        log("system", GREEN, "All servers stopped.")


if __name__ == "__main__":
    main()
