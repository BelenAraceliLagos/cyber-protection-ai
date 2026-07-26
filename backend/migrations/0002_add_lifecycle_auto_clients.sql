-- 0002_add_lifecycle_auto_clients.sql
-- Agrega clients.lifecycle_auto: controla si el sistema puede avanzar la
-- etapa del ciclo de vida sola (según las oportunidades del cliente), o
-- si quedó "congelada" a un valor elegido a mano. Por defecto, True
-- (automático) para todos los clientes existentes.

ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS lifecycle_auto BOOLEAN DEFAULT true;
