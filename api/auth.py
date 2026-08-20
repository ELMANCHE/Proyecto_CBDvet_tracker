"""Autenticación por API key y roles."""

import os
import secrets
from typing import Optional

from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from database import get_db, Usuario

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
DEFAULT_API_KEY = os.getenv("API_KEY", "cbd-dev-key-change-me")


def seed_default_user(db: Session):
    if not db.query(Usuario).filter_by(username="admin").first():
        db.add(Usuario(
            username="admin",
            api_key=DEFAULT_API_KEY,
            rol="admin",
            activo=True,
        ))
        db.commit()


def get_current_user(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    db: Session = Depends(get_db),
) -> Usuario:
    if not api_key:
        raise HTTPException(status_code=401, detail="API key requerida (header X-API-Key)")
    user = db.query(Usuario).filter_by(api_key=api_key, activo=True).first()
    if not user:
        raise HTTPException(status_code=403, detail="API key inválida")
    return user


def require_role(*roles):
    def checker(user: Usuario = Depends(get_current_user)):
        if user.rol not in roles and user.rol != "admin":
            raise HTTPException(status_code=403, detail=f"Rol requerido: {roles}")
        return user
    return checker
