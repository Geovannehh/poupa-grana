"""Run the private portable cluster and the loopback-only development server."""

import ctypes
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
# PostgreSQL Windows binaries need the short path on paths containing accented names.
buffer = ctypes.create_unicode_buffer(32768)
if os.name == "nt" and ctypes.windll.kernel32.GetShortPathNameW(str(ROOT), buffer, len(buffer)):
    portable = Path(buffer.value)
else:
    portable = ROOT
ctl = portable / ".local/postgres/pgsql/bin/pg_ctl.exe"
data = portable / ".local/pg-data"
started = False
try:
    if ctl.exists() and (data / "PG_VERSION").exists():
        running = (
            subprocess.run(
                [str(ctl), "-D", str(data), "status"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        if not running:
            subprocess.run(
                [
                    str(ctl),
                    "-D",
                    str(data),
                    "-l",
                    str(portable / ".local/postgres.log"),
                    "-o",
                    "-h 127.0.0.1 -p 55432",
                    "-w",
                    "start",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            started = True
    print("Poupa Grana: http://127.0.0.1:5089")
    print("Acesso inicial local: arquivo .local/ACESSO.txt. Ctrl+C para encerrar.")
    subprocess.run(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:5089", "--insecure", "--noreload"],
        check=True,
    )
except KeyboardInterrupt:
    pass
finally:
    if started:
        subprocess.run(
            [str(ctl), "-D", str(data), "-m", "fast", "-w", "stop"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
