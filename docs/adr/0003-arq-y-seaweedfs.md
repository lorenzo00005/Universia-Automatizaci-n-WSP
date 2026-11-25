# ADR 0003: arq para la cola y SeaweedFS como S3 local

**Estado:** aceptada (Fase 0). **Fecha:** 2026-11-25.

## arq en vez de Celery
arq es async como FastAPI, comparte el mismo código de dominio sin adaptadores y es mucho
más liviano. Para los volúmenes de los primeros clientes alcanza; si hiciera falta
priorización compleja, se puede migrar a Celery o a Dramatiq.

## SeaweedFS en vez de MinIO en local
El prompt maestro sugería MinIO para desarrollo, pero MinIO dejó de publicar imágenes en
Docker Hub. SeaweedFS expone la misma API S3 en `http://localhost:8333` y se usa sólo en
local. En producción va Cloudflare R2; el código va a hablar S3 genérico, así que el cambio
es sólo de configuración (`S3_ENDPOINT` y claves).
