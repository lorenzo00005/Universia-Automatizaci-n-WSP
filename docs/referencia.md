# Proyecto de referencia: Aurelio (aurelioagency.com)

> Contexto para el proyecto "chatbot automatizacion". Analizado el 25/11/2026 a partir del sitio público y del video promocional que mandó Lorenzo (90 s, vertical, WhatsApp). Es **referencia de modelo de negocio**, no algo a copiar: nombre, marca, textos y estética son de ellos.

## Qué es, en una línea
Un "empleado IA" que vive **dentro del WhatsApp del dueño de una pyme**. El dueño le habla como a un contacto más (texto, audio, PDF) y el asistente atiende clientes, ordena la agenda y las finanzas, hace contenido y publicidad, y prospecta leads. Se vende con instalación acompañada + mentoría, no como SaaS self-service.

## Lo que muestra el video (narración reconstruida de los subtítulos)
1. **Asistente dentro de tu WhatsApp**: le escribís, le mandás un audio o un documento, como a cualquier contacto. Te recuerda lo importante. (Demo: "Armame la agenda de hoy", nota de voz, "Propuesta.pdf".)
2. **Tareas recurrentes que aprende**: "lo que hacés todos los días, lo encargás una vez y él lo hace solo". La primera vez pregunta cómo lo querés; la segunda ya sabe ("Armame el informe de ventas" → "Hecho. Ya lo mandé"). Tareas programadas: informe de ventas diario, resumen del equipo semanal.
3. **Contenido**: busca lo que se viraliza en tu nicho y te lo adapta a tu marca y estilo. Ideas, textos, edición y posteo.
4. **Publicidad**: gestiona los anuncios y te dice qué funcionó (comparativa Anuncio A video corto 30 consultas vs. Anuncio B carrusel 47).
5. **Conocimiento centralizado + permisos**: todo el equipo usa el mismo asistente; cada uno ve sólo lo que le corresponde.
6. **Finanzas**: le mandás comprobantes y gastos y los ordena (ingresos / gastos / ganancia, gastos categorizados por rubro). Le pedís un informe rápido de lo que está pasando en el negocio.
7. **Prospección**: le pasás una lista de números o mails, les escribe, sigue cada lead y gestiona las respuestas para cerrarlos (pipeline Nuevo → Contactado → Respondió → Cerrado).
8. **Atención al cliente** por WhatsApp e Instagram: responde las preguntas repetidas (detecta "¿Cuál es el horario?" ×12) y hace seguimiento a cada lead.
9. **Mensajes de voz** con tu tono y con tu voz (clonación de voz).
10. **Modular**: se conecta con las herramientas que ya usás.
11. **Acompañamiento**: lo instalan con mentoría y hacen reuniones de revisión periódicas (videollamada) para "sacarle el máximo jugo".
12. CTA: "Escribinos" → link de WhatsApp.

Estética del video: fondo negro, tipografía serif elegante + acentos celeste, mockups de chat de WhatsApp, tarjetas de UI minimalistas.

## Lo que dice el sitio
- Dominio redirige a /en; existen versiones ES, EN y BR. Mercado principal: Argentina/LatAm (número wa.me +54 9 11, estadística de WhatsApp en Argentina).
- Servicios a medida además del asistente: Content Engine, prospección de leads, publicaciones automáticas en catálogos (fuerte foco **Mercado Libre**: "3+ años integrando", pipelines de publicación), IA para WhatsApp y ventas, gestión de leads, procesos internos.
- Onboarding en 3 pasos: **Auditoría** (cómo vendés/atendés hoy) → **Setup** (marca, reglas, equipo, dentro de tu WhatsApp) → **Soporte** (ajuste con uso real). Entrada por formulario "Automation Audit" (nombre, empresa, email, WhatsApp, tamaño de equipo, qué sigue siendo manual) o directo por WhatsApp. Promesa: respuesta humana <24 h, ruta de auditoría en 3 días.
- Regla de negocio clave: **lo que involucra precios, acuerdos o decisiones importantes, el asistente lo prepara y lo consulta con el dueño antes** (human-in-the-loop). "Vos ponés las reglas."
- Comunidad / embudo: "La Casa de Aurelio" (Skool, YouTube, Instagram) y "Aure Apps" (catálogo de alternativas open source a SaaS pagos, instalables con prompts de Claude) como lead magnet.
- **No publican precios** en el sitio. Los planes de 50/100/200 USD que pasó Lorenzo son la referencia de pricing (ver abajo).
- Stack visible: sitio probablemente Next.js (inferido). Sin checkout, login ni pasarela visible: la venta es conversacional.

## Planes de referencia (los que compartió Lorenzo)
| Plan | USD/mes | Incluye |
|---|---|---|
| Base | 50 | Atención al cliente 360° por WhatsApp; asistente personal (agenda y números); conexión con herramientas existentes |
| Pro | 100 | Todo lo anterior + edición de video (5/semana, ≤2 min, con correcciones), contenido y publicación automática en redes, respuesta a comentarios y DMs, gestión de anuncios (inversión a cargo del cliente), página web creada y editable por WhatsApp |
| Ilimitado | 200 | Todo lo de Pro, sin límite de videos |

## Stack probable (inferido, no confirmado)
- **WhatsApp**: WhatsApp Business Cloud API (Meta) o un BSP; para "dentro de tu WhatsApp" lo más probable es que el asistente sea **un número propio** con el que el dueño chatea, y otro número/línea del negocio para clientes (o la API conectada al número del negocio con coexistencia de la app Business).
- **LLM** con tool calling + memoria por negocio (RAG sobre docs/FAQ, historial).
- **Orquestación**: muy probablemente n8n/Make + código propio (ellos mismos recomiendan n8n).
- **Voz**: STT (Whisper o similar) para audios entrantes; TTS con clonación (ElevenLabs o similar) para responder con la voz del dueño.
- **Redes/ads**: Meta Graph API (Instagram/Facebook: publicación, comentarios, DMs), Meta Marketing API; posiblemente TikTok.
- **Video**: edición semi-automática (transcripción + cortes + subtítulos con FFmpeg/Remotion, o herramientas tipo Opus/CapCut) con **revisión humana** (las "correcciones que necesites" sugieren un editor humano en el loop para planes 100/200).
- **Web**: generador de landing (Next.js/Astro sobre plantillas) desplegado en Vercel/Netlify, editable por mensajes.
- **Finanzas**: OCR/visión de LLM sobre fotos de comprobantes → planilla (Google Sheets) o base propia.
- **Integraciones LatAm**: Mercado Libre, Google Calendar/Sheets, probablemente Tiendanube/MercadoPago.

## Lecciones para nuestro producto
- La interfaz es WhatsApp; el dashboard web es secundario (configuración, facturación, permisos).
- El diferencial no es la IA sino **instalación + mentoría + revisión mensual**: el servicio es "done-for-you".
- Human-in-the-loop explícito para precios, acuerdos y publicaciones.
- Multi-usuario con permisos por rol dentro de una misma empresa.
- "Aprende tareas": guardar procedimientos como recetas reutilizables y programables.
- Pricing con límites claros por plan (videos/semana) → necesitamos medición de uso.
