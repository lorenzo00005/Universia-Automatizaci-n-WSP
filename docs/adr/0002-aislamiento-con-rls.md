# ADR 0002: aislamiento entre tenants con Row Level Security

**Estado:** aceptada (Fase 0). **Fecha:** 2026-11-25.

## Contexto
Un error de filtro en el código no puede exponer datos de un negocio a otro.

## Decisión
Además de filtrar por `tenant_id` en el código, todas las tablas de negocio tienen RLS
forzado en Postgres. La app usa un rol que no es dueño de las tablas y fija el tenant por
transacción con `set_config`.

## Consecuencias
- Una consulta sin contexto no devuelve filas, en vez de devolver todo.
- Las migraciones corren con otro usuario (el dueño) y cada tabla nueva de negocio tiene que
  sumarse a `TENANT_SCOPED_TABLES` y tener su política en una migración.
- El panel interno usa `app.operator = on`, fijado sólo después de verificar al operador.
