-- 0007: textos editables por servicio (modo sin IA, D-11).
-- Idempotente: se puede aplicar varias veces sin error.
ALTER TABLE services ADD COLUMN IF NOT EXISTS texto_descripcion   TEXT;
ALTER TABLE services ADD COLUMN IF NOT EXISTS texto_justificacion TEXT;
ALTER TABLE services ADD COLUMN IF NOT EXISTS texto_beneficio     TEXT;
