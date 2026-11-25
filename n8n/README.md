# n8n

n8n corre en http://localhost:5678 con su propia base (`n8n`) en el mismo Postgres.
Lo usamos para integraciones de terceros por cliente (Google Calendar, Sheets, CRMs,
Mercado Libre, Tiendanube) y flujos programados.

- Los workflows se versionan como JSON en `n8n/workflows/` y se montan en el contenedor en
  `/workflows` (sólo lectura).
- Importar todos: `docker compose exec n8n n8n import:workflow --separate --input=/workflows`
- Exportar después de editarlos en la UI:
  `docker compose exec n8n n8n export:workflow --all --separate --output=/tmp/wf` y copiarlos
  a esta carpeta.
- Desde n8n, la API interna está en `http://api:8000` (variable `UNIVERSIA_API_URL`).

En la Fase 1 la herramienta `integraciones.ejecutar` del agente va a disparar estos workflows
con un payload validado.
