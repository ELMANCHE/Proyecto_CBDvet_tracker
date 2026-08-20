-- Script para arreglar autoincrement en tabla paciente
-- Ejecutar en PostgreSQL

-- Crear una secuencia si no existe
CREATE SEQUENCE IF NOT EXISTS paciente_id_seq;

-- Asociar la secuencia a la columna id
ALTER TABLE paciente ALTER COLUMN id SET DEFAULT nextval('paciente_id_seq');

-- Establecer el valor inicial de la secuencia al máximo id actual + 1
SELECT setval('paciente_id_seq', COALESCE((SELECT MAX(id) FROM paciente), 0) + 1, false);
