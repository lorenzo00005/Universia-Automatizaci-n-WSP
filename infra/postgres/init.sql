-- Se ejecuta una sola vez, al crear el volumen de Postgres.
-- El usuario dueño (POSTGRES_USER) corre las migraciones. La app usa `universia_app`,
-- que NO es dueño de las tablas, así Row Level Security siempre aplica.
CREATE EXTENSION IF NOT EXISTS vector;

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'universia_app') THEN
    CREATE ROLE universia_app LOGIN PASSWORD 'universia_app';
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO universia_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO universia_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO universia_app;

-- Base separada para n8n.
CREATE DATABASE n8n;
