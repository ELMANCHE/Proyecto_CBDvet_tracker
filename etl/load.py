"""Carga a staging y persistencia de metadatos."""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from database import StagingCarga
from logger import get_logger

logger = get_logger("etl.load")


def load_to_staging(session: Session, rows: List[Dict[str, Any]]) -> str:
    batch_id = str(uuid.uuid4())
    for i, row in enumerate(rows):
        session.add(StagingCarga(
            batch_id=batch_id,
            fila_num=i + 1,
            payload=json.dumps(row, default=str),
            estado="pendiente",
        ))
    session.commit()
    logger.info(f"Loaded {len(rows)} rows to staging batch {batch_id}")
    return batch_id


def validate_staging_batch(session: Session, batch_id: str) -> Dict[str, int]:
    rows = session.query(StagingCarga).filter_by(batch_id=batch_id).all()
    stats = {"valido": 0, "error": 0}
    for row in rows:
        try:
            data = json.loads(row.payload)
            required = ["tipo_especie_id", "peso_kg", "enfermedad_id", "dosis_mg_kg"]
            missing = [k for k in required if k not in data or data[k] is None]
            if missing:
                row.estado = "error"
                row.errores = f"Missing: {missing}"
                stats["error"] += 1
            else:
                row.estado = "valido"
                stats["valido"] += 1
        except Exception as e:
            row.estado = "error"
            row.errores = str(e)
            stats["error"] += 1
    session.commit()
    return stats
