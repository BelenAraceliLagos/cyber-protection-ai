-- 0001_add_updated_at_opportunities.sql
-- Agrega opportunities.updated_at (necesario para las alertas de
-- oportunidades estancadas en el CRM). Idempotente: seguro de correr
-- aunque ya exista la columna.

ALTER TABLE opportunities
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
