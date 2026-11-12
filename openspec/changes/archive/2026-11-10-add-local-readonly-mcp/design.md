# Design

## Context

Orion no tiene API ni una capa de operaciones de contenido: se apoya en los modelos, las
revisiones, los permisos y los flujos de trabajo de Wagtail. Lo que sí existe y se puede
leer: los tipos de página (`orion.pages`, `orion.forms`), los bloques (`orion.core.blocks`),
`SiteSettings` y `SiteTexts` (`orion.site_data`), el registro de 404 (`NotFoundPath` en
`orion.seo`), las redirecciones de `wagtail.contrib.redirects`, `check_project()` de
`orion.core.conventions`, la consulta de imágenes sin uso (hoy dentro del comando
`orion_unused_images`) y el chequeo de base de `/health/` (hoy dentro de la vista).

Como referencia se leyó el MCP de ruweb-cms (un solo endpoint JSON-RPC dentro del sitio,
claves con hash y alcance, lista blanca de herramientas de lectura, reintentos seguros con
clave de operación, revisión esperada). No se ejecutó; se analizó su código y su
documentación.

## Goals / Non-Goals

**Goals:**
- Un MCP local de solo lectura que un desarrollador puede conectar a su asistente.
- Herramientas que no dependan del transporte, para reutilizarlas.
- Dejar escrito el camino hasta producción.

**Non-Goals:**
- Escribir contenido, claves de API, endpoint HTTP, auditoría de agentes.
- Entregar un `.mcp.json` dentro de la plantilla.
- Exponer envíos de formularios o cuentas de usuario.

## Decisions

- **Hoja de ruta de cuatro cambios independientes**, cada uno útil por sí solo:
  1. Este: MCP local, solo lectura.
  2. Capa de operaciones de contenido, sobre las revisiones y los permisos de Wagtail,
     usada por el admin y por el MCP; MCP local con escritura en desarrollo.
  3. Claves de API (con hash, alcance, vencimiento, revocación y último uso, generadas desde
     el admin) y endpoint HTTP dentro del sitio, con solo lectura y solo borradores.
  4. Escritura completa en producción; depende de haber probado el flujo de aprobación con
     un sitio real (Fase 7, el sitio de Intervita).
  La capa de operaciones del paso 2 llega antes de cualquier escritura para no rehacerla.
- **Ideas tomadas de ruweb-cms para los pasos 2 a 4:** claves con hash y alcance; lista
  blanca de herramientas de lectura con las desconocidas denegadas; clave de operación para
  reintentos seguros; revisión esperada para no pisar cambios ajenos; errores de permiso
  como respuestas con una pista de recuperación, no como fallos del servidor. No se copia
  su modelo de controladores que se llaman entre sí.
- **Protocolo escrito a mano, sin dependencia.** JSON-RPC por líneas es pequeño y ruweb
  también lo escribió a mano. Alternativa descartada: el SDK oficial `mcp`, que sumaría una
  dependencia (la regla del proyecto exige justificarla) para un protocolo de cuatro
  métodos. Se reevalúa si el protocolo crece.
- **Una función pura de mensajes.** `handle_message(mensaje) -> respuesta | None` no toca
  la entrada ni la salida; el comando solo lee líneas, la llama y escribe. Así se prueba sin
  subprocesos y otro transporte (HTTP) la reutiliza.
- **Estándar de salida limpia.** Los clientes de MCP por stdio leen solo mensajes de la
  salida estándar. El comando redirige la salida estándar al error mientras corre cada
  herramienta, de modo que un `print` perdido no rompa el protocolo.
- **Solo lectura por construcción.** Las herramientas solo usan consultas; no hay un modo de
  escritura que activar. Una prueba ejecuta todas las herramientas y comprueba que ninguna
  sentencia de la base es de escritura.
- **App `orion.mcp` en `INSTALLED_APPS` base.** Un comando de gestión solo existe si su app
  está instalada. Cambia los ajustes de todos los proyectos pero no agrega rutas ni
  migraciones, y el comando no hace nada si nadie lo ejecuta.
- **Extracciones mínimas.** La consulta de imágenes sin uso y el chequeo de base pasan a
  funciones que usan el comando o la vista y la herramienta, sin cambiar su comportamiento
  ni sus pruebas.
- **Resultados acotados.** `per_page` hasta 100, con total y `has_more`, como en ruweb.
- **Versión del protocolo.** Contrastada el 10 de noviembre de 2026 con la especificación
  en modelcontextprotocol.io: la revisión vigente es la `2026-07-28`, que **elimina el
  `initialize`**; cada petición lleva su versión en `_meta` y el servidor debe ofrecer
  `server/discover`. Las revisiones hasta la `2025-11-25` abren con `initialize`. Este cambio
  soporta solo las que tienen `initialize` (`2025-11-25`, `2025-06-18`, `2025-03-26` y
  `2024-11-05`): responde la versión que pide el cliente si la conoce y, si no, la más
  nueva que soporta. El subconjunto que implementa (herramientas de solo lectura) es el
  mismo en todas; no se probó con cada cliente. Un cliente que solo habla la revisión
  `2026-07-28` no podrá conectarse hasta un cambio que sume `server/discover` y la
  versión por petición (servidor de doble era, que la especificación permite). Los clientes
  de doble era caen a `initialize` cuando el servidor no responde como moderno.

## Risks / Trade-offs

- **Instrucciones ajenas en el contenido leído** (por ejemplo, un texto de página escrito
  por un tercero) → el servidor es de solo lectura, así que el daño posible es de
  información; la guía lo advierte y los textos se devuelven como datos.
- **Datos personales si se carga una copia de producción en local** → no se exponen envíos
  ni cuentas, pero el contenido de páginas sí se lee; la guía lo dice.
- **El protocolo cambia** → versión declarada en una constante y pruebas que la fijan.
- **Una herramienta futura con escritura** → la prueba de solo lectura falla y obliga a
  decidirlo en un cambio propio.
- **Tamaño de las respuestas** (el esquema de bloques puede ser grande) → se acota y se
  entrega por tipo o por páginas.

## Migration Plan

No hay datos que migrar. El comando es nuevo y los proyectos existentes lo reciben al
actualizar Orion. Para revertir, quitar `orion.mcp` de `INSTALLED_APPS`.

## Open Questions

- Si la plantilla de proyectos debe traer un `.mcp.json` listo; no cambia las
  especificaciones y se decide después de probar la guía con un equipo.
