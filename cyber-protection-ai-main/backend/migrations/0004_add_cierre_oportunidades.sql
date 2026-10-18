-- Cierre de oportunidades: fecha, motivo de pérdida y comentario.
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS motivo_cierre VARCHAR;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS detalle_cierre TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS motivo_previo VARCHAR;