# Design

## Context

Los pasos 1 y 2 dejaron `orion.mcp` con un manejo de mensajes sin transporte
(`handle_message(message, context)`), un registro de herramientas con la bandera booleana
`writes`, un contexto de servidor (`allow_writes`, `actor`), la capa `orion.operations` y la
cuenta técnica del modo local. Observado en el código:

- `orion.urls` registra las rutas antes de las páginas, y las que no son páginas llevan un
  guion bajo (`_preview/`). `orion.core.paths.is_internal_request` decide qué no entra al caché
  de páginas.
- `orion.core.client_ip.get_client_ip` da la IP real según `ORION_TRUSTED_PROXIES`.
- `orion.integrations` ya tiene una pantalla en el menú de Ajustes solo para Administradores
  (`AdministratorMenuItem`, `is_site_administrator`).
- Las integraciones de Orion viven apagadas por defecto.
- El middleware de segundo factor y `django-axes` actúan sobre las rutas del admin y el
  inicio de sesión, no sobre una ruta con clave.

Como referencia se leyó el MCP de ruweb-cms (`POST /mcp/rpc` con claves con hash y alcance, una
lista blanca de lectura, herramientas desconocidas denegadas a claves restringidas, recibos por
clave de operación y revisión esperada). No se ejecutó.

## Goals / Non-Goals

**Goals:**
- Un endpoint dentro del sitio, apagado por defecto, que un cliente remoto use con una clave.
- Claves que se puedan limitar, vencer y revocar, y que un Administrador gestione sin código.
- Solo lectura y borradores de páginas, con reintentos seguros.

**Non-Goals (paso 4 o posteriores):**
- Escribir redirecciones, datos y textos del sitio con una clave; publicar o borrar.
- Claves de acceso completo, OAuth, la revisión 2026-07-28 del protocolo y respuestas en streaming.
- Límites de uso exactos entre procesos (hay un límite de mejor esfuerzo).

## Decisions

- **Hoja de ruta.** 1 y 2 hechos. 3 es este cambio. 4: escritura completa en producción (ajustes
  y redirecciones remotos, quizá claves de acceso completo), tras probar el flujo de aprobación
  con un sitio real (Fase 7).
- **Apagado por defecto, decisión por defecto sin confirmar.** `ORION_MCP_ENDPOINT` (booleano de
  entorno, falso por defecto), como el resto de las integraciones. Con el ajuste apagado la ruta
  responde 404, como si no existiera; el ajuste se lee en cada petición para poder probarlo.
- **Ruta fija `/_mcp/`, decisión por defecto sin confirmar.** El guion bajo la deja fuera de
  los slugs de páginas, como `_preview/`. Se registra en `orion.urls` antes de las páginas y se
  suma a `is_internal_request`, de modo que no entra al caché de páginas ni al registro de 404.
  No es configurable: menos variantes que documentar y que proteger.
- **Subconjunto de Streamable HTTP.** Un POST por mensaje; las peticiones responden
  `application/json`, las notificaciones 202 sin cuerpo y GET y DELETE 405 (la especificación
  permite no ofrecer el flujo de eventos). Sin sesiones de protocolo ni streaming: encaja con
  servidores síncronos como Gunicorn y Passenger, que fallarían con conexiones largas. Reutiliza
  `handle_message`, así que soporta las revisiones con `initialize` (hasta 2025-11-25). Un
  cliente que solo hable la 2026-07-28 queda fuera, como en el modo local.
- **Cabeceras.** Una cabecera `Origin` se rechaza con 403 salvo que esté en
  `ORION_MCP_ALLOWED_ORIGINS` (vacía por defecto): los clientes de API no la envían y un
  navegador sí, que es el vector del rebinding de DNS que la especificación manda evitar. Una
  `MCP-Protocol-Version` desconocida da 400. Cuerpo máximo `ORION_MCP_MAX_BODY` (1 MB), con 413.
  Sin sesión ni CSRF (`csrf_exempt`): la autenticación es solo la clave. `Cache-Control:
  no-store`. Con HTTPS fuera de depuración por el redireccionamiento ya existente.
- **Claves.** Modelo `ApiKey` en `orion.mcp`, con migración aditiva. Token `orion_mcp_` más 48
  caracteres aleatorios de `secrets`; se guarda el SHA-256 (suficiente para un valor aleatorio de
  alta entropía, a diferencia de una contraseña) y un prefijo de ocho caracteres para
  identificarla. Se busca por hash. El token se muestra una vez y no se escribe en ningún
  registro. Todo rechazo da el mismo 401, sin distinguir la causa.
- **Una clave actúa como un usuario elegido al crearla (decisión del usuario).** Ese usuario fija
  el autor y los permisos máximos, recortados por el alcance. No puede ser superusuario ni estar
  inactivo; si se desactiva o se borra, la clave deja de servir. Alternativa descartada: actuar
  siempre como `orion-agent`, porque no distingue quién hizo cada cambio.
- **Gestión solo por Administradores (decisión del usuario).** Pantalla en Ajustes, como
  Integraciones, para Administradores y superusuarios; las URLs comprueban el permiso, no solo
  ocultan el menú.
- **Niveles de acceso en el registro.** La bandera `writes` pasa a `access` (`read`, `draft`,
  `settings`) y el contexto permite un conjunto de niveles: el modo local con `--allow-writes`
  permite los tres, una clave `read-only` solo `read`, `draft-only` `read` y `draft`. Un nivel
  desconocido o ausente se trata como no permitido. Los modos y pruebas del paso 2 no cambian de
  comportamiento (es un refactor con pruebas de no regresión primero).
- **Qué puede una clave.** `read-only`: herramientas de lectura. `draft-only`: además
  `page_create_draft` y `page_update_draft`. `redirect_*`, `site_settings_update` y
  `site_texts_update` entran en vigor al guardarse y no son borradores: quedan para el paso 4.
  `update_page_draft` solo guarda revisiones y nunca toca la fila en vivo, así que no hace falta
  comprobar el estado bajo bloqueo como en ruweb.
- **Recibos de operación.** `operation_key` opcional en las herramientas de escritura de una
  clave. Modelo `OperationReceipt` (clave, herramienta, clave de operación, hash canónico de los
  argumentos, resultado en JSON), único por (clave, herramienta, clave de operación). Misma
  clave y mismos argumentos: devuelve lo guardado; otros argumentos: conflicto. Se purgan los de
  más de 30 días al registrar uno, como mucho una vez por hora (marca en el caché), sin tarea
  programada nueva. En el modo local no hay recibos: no hay clave a la que ligarlos.
- **Límites de mejor esfuerzo con el caché de Django.** Intentos fallidos por IP y peticiones
  por clave por minuto (`ORION_MCP_RATE_LIMIT`), con 429 y `Retry-After`. Con varios procesos y un
  caché local el límite es por proceso: la guía lo dice y recomienda un caché compartido.
- **Registro.** Un registro por llamada autenticada con el prefijo de la clave, la herramienta y
  ok/error. Nunca el token ni los argumentos.
- **Última utilización.** `last_used_at` se escribe como mucho una vez por minuto por clave
  (marca en el caché) para no escribir en cada petición.

## Seguridad dicha con honestidad

- Una clave filtrada permite lo que su alcance y su usuario permiten hasta que se revoque o
  venza; por eso se recomienda un vencimiento y un usuario con pocos permisos.
- Frente a un asistente remoto, el límite real es el alcance de la clave: `read-only` no puede
  cambiar nada; `draft-only` solo deja borradores que una persona revisa.
- Un endpoint público es una superficie nueva. Por eso viene apagado, exige HTTPS, no usa
  sesiones, limita el uso y rechaza peticiones de navegador.
- El contenido ajeno que el asistente lea (una página, un texto) puede inducirlo a escribir
  borradores. No hay un límite de cuántos borradores crea una clave salvo la tasa de peticiones.

## Risks / Trade-offs

- **Clave filtrada** → alcance acotado, vencimiento, revocación inmediata, registro por prefijo.
- **Fuerza bruta de claves** → token de alta entropía y límite de intentos por IP.
- **Límite por proceso con caché local** → documentado; caché compartido recomendado.
- **El refactor del registro rompe el modo local** → pruebas de no regresión antes de cambiar.
- **Migraciones en sitios existentes** → solo tablas nuevas, sin tocar datos; se revisan en MySQL
  y PostgreSQL.
- **Usuario ligado con permisos de más** → la guía recomienda un Editor; el alcance recorta el resto.
- **Peticiones largas o bloqueantes** → sin streaming; cuerpo máximo; los trabajos de las
  herramientas son consultas y escrituras cortas.

## Migration Plan

Una migración aditiva con las dos tablas. El endpoint viene apagado: actualizar Orion no expone
nada. Para activarlo: poner `ORION_MCP_ENDPOINT=true`, comprobar HTTPS y crear una clave. Para
revertir: apagar el ajuste y revocar las claves; las tablas pueden quedar.

## Open Questions

- Si conviene un caché compartido por defecto para los límites; no cambia las especificaciones y
  se decide tras probar el endpoint con un sitio real.
