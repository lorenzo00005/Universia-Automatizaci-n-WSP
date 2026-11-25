# Universia Automatización WSP

Un "empleado IA" para pymes que vive dentro de WhatsApp. El dueño y su equipo le hablan como a
un contacto más (texto, audios, fotos, PDFs) y el asistente atiende a los clientes, ordena la
agenda y las finanzas, aprende tareas recurrentes y, en los planes superiores, hace contenido,
videos, anuncios y la web del negocio.

**Estado:** Fase 0 (Fundaciones). Todavía no hay WhatsApp ni agente: eso llega en la Fase 1.
La Fase 0 deja el monorepo, la base multi-tenant, el login del panel y la CI.

## Levantarlo en tu máquina

Necesitás Docker con Compose v2, `make` y `openssl`.

```bash
make dev    # crea .env con claves nuevas y levanta todo
make seed   # crea un operador y un negocio de ejemplo
```

Después:

1. Abrí http://localhost/login y pedí el link con `operador@example.com`.
2. Abrí Mailpit en http://localhost:8025, entrá al mail y tocá el link.
3. Vas a ver tus negocios y el **Panel interno** para dar de alta negocios a mano.

| Servicio | URL |
| --- | --- |
| Panel (dashboard) | http://localhost |
| API (vía Caddy) | http://localhost/api/health |
| Documentación de la API | http://localhost/api/docs |
| Mails de desarrollo (Mailpit) | http://localhost:8025 |
| n8n | http://localhost:5678 |
| S3 local (SeaweedFS) | http://localhost:8333 |

Otros comandos: `make help`, `make logs`, `make migrate`, `make down`, `make reset` (borra los
datos).

## Tests y lint

```bash
make test   # levanta Postgres y Redis del compose y corre pytest
make lint   # ruff + mypy en la API, eslint + tsc en el dashboard
```

Para correr la API fuera de Docker: `cd apps/api && uv sync && uv run uvicorn app.main:app
--reload` (con Postgres y Redis del compose levantados). Para el dashboard: `cd apps/dashboard
&& pnpm install && pnpm dev` (reenvía `/api` a `localhost:8000`).

## Estructura

```
apps/api         FastAPI + SQLAlchemy 2 + Alembic. Dominios en app/domains/
apps/worker      Dockerfile del worker (arq). El código está en apps/api/app/worker/
apps/dashboard   Next.js (App Router) + Tailwind
n8n/workflows    Workflows de n8n versionados como JSON
infra/           Caddyfile y script inicial de Postgres
docs/            Arquitectura, ADRs y referencia del modelo de negocio
```

Más detalle en [docs/arquitectura.md](docs/arquitectura.md) y las decisiones en
[docs/adr/](docs/adr/).

## Planes

Los planes y sus límites viven en la base (`plans`, `plan_features`), no en el código.

| Plan | USD/mes | Incluye |
| --- | --- | --- |
| Base | 50 | Atención al cliente por WhatsApp, asistente personal (agenda y finanzas), integraciones |
| Pro | 100 | Base + 5 videos por semana (hasta 2 min), contenido y publicación en redes, respuesta a comentarios y DMs, anuncios, web editable por WhatsApp |
| Ilimitado | 200 | Pro sin límite semanal de videos (uso razonable configurable) |

## Hoja de ruta

| Fase | Qué trae |
| --- | --- |
| 0 | Fundaciones: monorepo, Docker, modelo de datos, auth, CI |
| 1 | MVP plan base: WhatsApp, agente con herramientas, audios, comprobantes, aprobaciones, simulador |
| 2 | Cobro con Mercado Pago y Stripe, entitlements aplicados, landing |
| 3 | Redes: Instagram, contenido y publicación |
| 4 | Edición de video con revisión humana |
| 5 | Anuncios con Meta Marketing API |
| 6 | Web del negocio editable por WhatsApp |
| 7 | Voz clonada, prospección, integraciones LatAm |
