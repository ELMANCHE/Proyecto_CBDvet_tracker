#!/usr/bin/env python3
"""Seed: crea tablas auxiliares y usuario admin."""

import os
import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0] if "/" in __file__ else ".")

from database import init_db, get_db_session, Usuario
from api.auth import DEFAULT_API_KEY, seed_default_user


def main():
    init_db()
    db = get_db_session()
    try:
        seed_default_user(db)
        print(f"Usuario admin creado. API Key: {DEFAULT_API_KEY}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
