# ADR 0001: una sola línea interna compartida

**Estado:** aceptada (Fase 0). **Fecha:** 2026-11-25.

## Contexto
El dueño y su equipo chatean con el asistente por una "línea interna". Se puede tener un
número por tenant o un número nuestro compartido.

## Decisión
Un solo número nuestro para todos los tenants. El usuario se identifica por su teléfono
(`users.phone`). Si alguien pertenece a más de un negocio, el asistente le pregunta con cuál
quiere trabajar y lo recuerda en la conversación.

## Consecuencias
- Un solo número para verificar y mantener con Meta, en vez de uno por cliente.
- El "contacto" del asistente es el mismo para todos; la marca de cada negocio se ve en la
  línea del negocio (la de clientes), no en la interna.
- Si un cliente pide un número propio para su equipo, el modelo de `channels` ya lo soporta
  (`purpose = internal` con su `phone_number_id`).
