#!/usr/bin/env python3
"""Backup de PostgreSQL usando pg_dump."""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKUP_DIR = Path(__file__).parent.parent / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BACKUP_DIR / f"cbdanalisis_{ts}.sql"
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("DATABASE_PASSWORD", "admin")

    cmd = [
        "pg_dump",
        "-h", os.getenv("DATABASE_HOST", "localhost"),
        "-p", os.getenv("DATABASE_PORT", "5432"),
        "-U", os.getenv("DATABASE_USER", "postgres"),
        "-d", os.getenv("DATABASE_NAME", "cbdanalisis"),
        "-f", str(out),
    ]
    subprocess.run(cmd, check=True, env=env)
    print(f"Backup guardado: {out}")


if __name__ == "__main__":
    backup()
