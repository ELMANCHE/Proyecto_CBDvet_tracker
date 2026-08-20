#!/usr/bin/env python3
"""Recrea la vista dataset_ia_cbd."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine

VIEW_SQL = """
CREATE OR REPLACE VIEW dataset_ia_cbd AS
SELECT
    c.id AS consulta_id,
    p.codigo_paciente,
    e.nombre AS especie,
    r.nombre AS raza,
    p.sexo,
    p.esterilizado,
    c.peso,
    enf.nombre AS enfermedad,
    d.severidad,
    cc.nivel_estres,
    cc.alt,
    cc.ast,
    cc.actividad_fisica,
    cc.apetito,
    t.dosis_mg_kg,
    t.frecuencia,
    t.tipo_extracto,
    res.nivel_mejora,
    res.respuesta,
    c.fecha
FROM consulta c
JOIN paciente p ON c.paciente_id = p.id
JOIN tipo_especie e ON p.tipo_especie_id = e.id
LEFT JOIN raza r ON p.raza_id = r.id
LEFT JOIN diagnostico d ON d.consulta_id = c.id
LEFT JOIN enfermedad enf ON d.enfermedad_id = enf.id
LEFT JOIN condiciones_clinicas cc ON cc.consulta_id = c.id
LEFT JOIN tratamiento_cbd t ON t.consulta_id = c.id
LEFT JOIN resultado res ON res.tratamiento_id = t.id;
"""


def main():
    with engine.begin() as conn:
        conn.execute(text("DROP VIEW IF EXISTS dataset_ia_cbd"))
        conn.execute(text(VIEW_SQL))
    print("Vista dataset_ia_cbd recreada.")


if __name__ == "__main__":
    main()
