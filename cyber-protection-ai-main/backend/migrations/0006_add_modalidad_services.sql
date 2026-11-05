-- 0006_add_modalidad_services.sql
-- Agrega services.modalidad: la modalidad del servicio (Proyecto,
-- Recurrente Mensual, etc.) como columna propia. Hasta ahora estaba escrita
-- al final de la descripcion ("... | Modalidad: X"). Esta migracion copia ese
-- valor a la columna nueva sin tocar la descripcion. Idempotente: seguro de
-- correr varias veces.

ALTER TABLE services
    ADD COLUMN IF NOT EXISTS modalidad VARCHAR;

UPDATE services
SET modalidad = trim(substring(description from '\|\s*Modalidad:\s*(.+)$'))
WHERE modalidad IS NULL
  AND description ~ '\|\s*Modalidad:';