-- 0003_add_plazo_meses_opportunities.sql
-- Agrega opportunities.plazo_meses: el plazo contratado (3/6/9/12 meses)
-- del proyecto, elegido directamente en el modal del Kanban. Se usa para
-- calcular el valor TOTAL del contrato (valor_uf mensual × plazo) en el
-- desglose de "Valor ganado" del CRM.

ALTER TABLE opportunities
    ADD COLUMN IF NOT EXISTS plazo_meses INTEGER;
