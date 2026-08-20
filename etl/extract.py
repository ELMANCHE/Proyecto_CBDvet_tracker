"""Extracción de datos desde PostgreSQL."""

import pandas as pd
from sqlalchemy import text

from logger import get_logger

logger = get_logger("etl.extract")

DATASET_VIEW_SQL = "SELECT * FROM dataset_ia_cbd"

FULL_JOIN_SQL = """
SELECT
    c.id as consulta_id, p.id as paciente_id, p.sexo,
    EXTRACT(YEAR FROM AGE(p.fecha_nacimiento)) as edad_anios,
    p.esterilizado, c.peso as peso_kg, c.fecha, c.motivo,
    te.nombre as especie, r.nombre as raza,
    d.severidad, d.duracion_dias, e.nombre as enfermedad,
    t.dosis_mg_kg, t.frecuencia, t.duracion_dias as cbd_duracion_dias, t.tipo_producto,
    cc.comorbilidades, cc.medicamentos_previos, cc.estado_nutricional,
    cc.presion_arterial, cc.alt, cc.ast, cc.nivel_estres, cc.tipo_dolor,
    res.respuesta, res.nivel_mejora, res.efectos_secundarios, res.cumplimiento,
    ctx.epoca, ctx.ubicacion, ctx.precio
FROM consulta c
LEFT JOIN paciente p ON c.paciente_id = p.id
LEFT JOIN tipo_especie te ON p.tipo_especie_id = te.id
LEFT JOIN raza r ON p.raza_id = r.id
LEFT JOIN diagnostico d ON d.consulta_id = c.id
LEFT JOIN enfermedad e ON d.enfermedad_id = e.id
LEFT JOIN tratamiento_cbd t ON t.consulta_id = c.id
LEFT JOIN condiciones_clinicas cc ON cc.consulta_id = c.id
LEFT JOIN resultado res ON res.tratamiento_id = t.id
LEFT JOIN contexto ctx ON ctx.consulta_id = c.id
ORDER BY c.id ASC
"""


def extract_from_view(session) -> pd.DataFrame:
    """Extrae desde vista dataset_ia_cbd (preferida)."""
    try:
        df = pd.read_sql(text(DATASET_VIEW_SQL), session.bind)
        # Normalizar nombres de columnas de la vista
        if "peso" in df.columns and "peso_kg" not in df.columns:
            df["peso_kg"] = df["peso"]
        logger.info(f"Extracted {len(df)} records from dataset_ia_cbd view")
        return df
    except Exception as e:
        logger.warning(f"View extract failed ({e}), falling back to JOIN")
        return extract_from_join(session)


def extract_from_join(session) -> pd.DataFrame:
    df = pd.read_sql(text(FULL_JOIN_SQL), session.bind)
    logger.info(f"Extracted {len(df)} records from JOIN query")
    return df
