# Worker

Procesa en segundo plano todo lo lento: hoy los mails de login; desde la Fase 1, llamadas al
LLM, transcripción de audios, envíos de WhatsApp y recetas programadas.

El código vive en `apps/api/app/worker/` porque comparte modelos y dominios con la API. Esta
carpeta tiene el `Dockerfile`, que construye desde `apps/api` y arranca `arq`.
