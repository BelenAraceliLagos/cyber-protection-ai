-- Importancia de cada hito: Crítico, Importante, Necesario, Normal.
ALTER TABLE milestones ADD COLUMN IF NOT EXISTS importancia VARCHAR DEFAULT 'Normal';