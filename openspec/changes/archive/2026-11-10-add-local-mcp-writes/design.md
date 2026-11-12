# Design

## Context

`add-local-readonly-mcp` dejó un servidor MCP local por stdio con un registro de
herramientas separado del transporte (`orion.mcp.registry`) y la función
`handle_message`. Orion no tiene una capa de operaciones de contenido: el admin de Wagtail
escribe con las formas de Wagtail, y los permisos viven en los grupos Editores y
Administradores (`orion.editor.roles`). Observado en el código y en Wagtail 7.4:

- `Page.save_revision(user, changed, log_action, clean)` guarda una revisión a nombre del
  usuario y puede registrar la acción; `PagePermissionTester` (`page.permissions_for_user`)
  ofrece `can_add_subpage`, `can_edit`, `can_publish`, etc. y tiene en cuenta los bloqueos.
- Los Editores no gestionan redirecciones (`wagtailredirects` solo para Administradores) ni
  los datos del sitio (`change_sitesettings`), y sí los textos del sitio (`add_sitetexts`,
  `change_sitetexts`).
- `Redirect` tiene `old_path`, `redirect_page`, `redirect_link` y `is_permanent`.

Como referencia se leyó el MCP de ruweb-cms (`PageOperations`, `SettingOperations`,
`expected_revision`, recibos de operación); no se ejecutó.

## Goals / Non-Goals

**Goals:**
- Una capa de operaciones que centralice permisos, validación y revisiones, reutilizable por
  el endpoint remoto del paso 3.
- Escritura local opt-in, solo de borradores y ajustes, a nombre de una cuenta técnica con
  permisos acotados.

**Non-Goals:**
- Que el admin de Wagtail use la capa (decisión del usuario: no en este cambio).
- Publicar, despublicar, borrar o mover; medios y menús.
- Claves de API, endpoint HTTP, recibos de operación y claves de operación (paso 3).

## Decisions

- **Hoja de ruta (sin cambios).**
  1. `add-local-readonly-mcp`: hecho.
  2. Este cambio: capa de operaciones y escritura local.
  3. Claves de API con hash, alcance, vencimiento y revocación; endpoint HTTP dentro del
     sitio con solo lectura y solo borradores; recibos y claves de operación.
  4. Escritura completa en producción, tras probar el flujo de aprobación con un sitio real.
- **Paquete `orion.operations` sin modelos.** Es un paquete de funciones; no necesita
  `INSTALLED_APPS` ni migraciones. Cada función recibe el usuario como primer argumento.
- **Seguridad del modo local: no hay una URL.** El servidor es un subproceso que lanza el
  asistente en la máquina del desarrollador, sin red ni puerto. Lo usa quien pueda ejecutar
  `manage.py` en esa carpeta, que ya tiene las credenciales de la base en `.env`. El riesgo
  nuevo no es de acceso sino de **qué hace el asistente**, que puede estar influido por
  texto ajeno que lea. Se limita con cuatro frenos: opt-in, usuario con sus permisos, solo
  borradores y sin borrados.
- **Actor: una cuenta técnica dedicada, `orion-agent` (decisión del usuario).** Con
  `--allow-writes` el servidor escribe siempre como esa cuenta; nadie la elige. Así el historial
  de Wagtail separa lo que hizo el asistente y no se puede escoger un autor con más permisos
  que los previstos. Alternativas descartadas: un usuario indicado con `--user` (quien lanza el
  comando elige el autor, incluso uno con todos los permisos) y un superusuario implícito
  (salta los permisos de Wagtail).
- **La cuenta la crea un comando propio, no el instalador.**
  `manage.py orion_create_agent_user` la crea una vez por sitio, también en los ya instalados:
  activa, sin email, en el grupo Editores y con contraseña inutilizable
  (`set_unusable_password`), de modo que nadie puede entrar al admin con ella y el segundo
  factor no se aplica. `orion_install` no la crea para no sumar una cuenta a sitios que no usan
  el MCP. Es idempotente: si la cuenta existe no la modifica, y si es superusuaria falla en
  lugar de corregirla, para que nada cambie por sorpresa.
- **Validación al lanzar.** `orion_mcp --allow-writes` termina antes de aceptar mensajes si la
  cuenta no existe (el error nombra el comando que la crea), está inactiva o es superusuaria, y
  avisa por stderr con qué cuenta y qué grupos escribe. Sin la bandera no mira la cuenta.
- **Qué puede y qué no.** Como Editores puede crear y editar borradores y editar los textos del
  sitio, y **no** puede gestionar redirecciones ni datos del sitio. El equipo puede agregarla
  al grupo Administradores desde el admin; es una decisión explícita y visible, y aun así nunca
  publica ni borra. La guía lo documenta.
- **Qué protege y qué no.** Lo que protege contra el asistente es qué comandos tiene permitido
  ejecutar: si puede abrir un shell o `manage.py shell`, se salta el MCP y escribe directo en la
  base. La cuenta técnica da atribución separada y permisos acotados, pero no impide que quien
  lanza el comando use la base. En el paso 3, las claves de API quedan ligadas a un usuario y a
  un alcance, y ahí quien llama no elige el autor.
- **Opt-in en dos niveles.** Sin `--allow-writes` las herramientas de escritura no existen (no
  se listan ni se pueden llamar). Con la bandera se valida la cuenta. Un contexto de servidor
  (`allow_writes`, `actor`) viaja de `handle_message` a las herramientas de escritura; las de
  lectura no lo reciben.
- **Escribir solo por revisiones.** Una página nueva se crea con `live=False` y una primera
  revisión; una actualización guarda una revisión nueva de la última versión. Nada toca
  `live`, `first_published_at` ni el árbol salvo `add_child`. Publicar queda para una persona
  en el admin.
- **Campos permitidos.** Título, slug, título y descripción SEO y los campos de contenido
  del tipo de página (los que `orion.mcp` ya describe en `schema`). Se rechaza todo lo demás
  con un error de validación en lugar de ignorarlo.
- **Validación como el editor.** Se asignan los valores campo por campo con `to_python` del
  campo, el cuerpo pasa por `stream_block.clean` y se llama a `full_clean()` del modelo.
- **Texto enriquecido.** Wagtail no limpia el HTML guardado de un texto enriquecido al
  mostrarlo; el editor lo evita porque Draftail solo produce las funciones permitidas. La capa
  normaliza el texto con el conversor `ContentstateConverter` (de la base de datos al estado de
  contenido y de vuelta) con las funciones del bloque o del campo. **Verificado el 10 de
  noviembre de 2026:** quita `<script>` (queda su texto sin etiqueta), los atributos de eventos
  como `onclick` y los estilos; un enlace `javascript:` queda sin `href`; las etiquetas que el
  bloque no permite se aplanan a párrafos. Con una etiqueta vacía como `<img>` lanza
  `AssertionError`, que la capa convierte en un error de validación. Basta, sin limpieza
  adicional. Se recorren los bloques anidados (estructuras, listas y flujos) y un tipo de bloque
  desconocido es un error: Wagtail lo descartaría en silencio.
- **Destinos de una redirección.** El campo de enlace de la redirección de Wagtail es una URL
  y exige esquema, así que un destino de este mismo sitio se da como página (por su id) y uno
  externo como URL absoluta http o https. Un enlace que lleva de vuelta al origen se rechaza
  solo si apunta a un dominio de los sitios.
- **Permisos por operación:**

  | Operación | Permiso que se comprueba |
  |---|---|
  | `page_create_draft` | `padre.permissions_for_user(u).can_add_subpage()` y tipo permitido bajo ese padre |
  | `page_update_draft` | `page.permissions_for_user(u).can_edit()` (incluye bloqueos) |
  | `redirect_create` / `redirect_update` | `wagtailredirects.add_redirect` / `change_redirect` |
  | `site_settings_update` | `orion_site_data.change_sitesettings` |
  | `site_texts_update` | `orion_site_data.add_sitetexts` o `change_sitetexts` |

  Un usuario inactivo no opera. Un superusuario pasa todas las comprobaciones, como en Wagtail,
  por eso el servidor rechaza una cuenta técnica superusuaria.
- **Concurrencia.** `expected_revision` es obligatorio al actualizar y se compara con el id
  de la última revisión. Si cambió, un `RevisionConflictError` pide leer de nuevo. `page_get`
  devuelve `latest_revision_id`.
- **Sin recibos ni claves de operación.** ruweb los usa para reintentos seguros por red. En
  local, repetir una creación falla por el slug repetido y repetir una actualización falla por
  la revisión esperada; no hace falta una tabla nueva. Se retoman en el paso 3.
- **Errores.** La capa lanza `PermissionDenied`, `ValidationError` (de Django) y
  `RevisionConflictError`. El MCP los convierte en un resultado `isError` con la causa; no
  son errores de protocolo.
- **Trazabilidad.** Las revisiones y el historial de Wagtail llevan a `orion-agent`. No se
  agrega una marca de origen: la cuenta ya identifica que lo hizo el asistente.
- **Admin sin cambios.** La capa nace para el MCP; que el admin la use es un cambio posterior.

## Risks / Trade-offs

- **Instrucciones ajenas que llevan al asistente a escribir** (un texto de página o de un
  envío con órdenes) → escritura opt-in, solo borradores, permisos del usuario, sin borrados y
  revisión humana antes de publicar; la guía lo advierte.
- **HTML inseguro en texto enriquecido** → normalización y prueba con `<script>`; si el
  conversor no basta, limpieza explícita.
- **Pisar el trabajo de otra persona** → revisión esperada obligatoria y bloqueos de Wagtail.
- **Muchos borradores creados de golpe** → no hay límite en este paso; se evalúa en el paso 3
  junto con los límites de uso del endpoint remoto.
- **La cuenta agregada a Administradores** puede cambiar redirecciones y datos del sitio →
  decisión explícita del equipo, visible en el admin; el servidor la avisa al arrancar y rechaza
  una cuenta superusuaria.
- **Un asistente que ejecuta comandos libres** se salta el MCP → es el límite real, y la guía
  lo dice; se controla con lo que el asistente tiene permitido ejecutar.
- **Dos formas de escribir** (el admin y la capa) pueden divergir → se acepta hasta que el
  admin migre; las pruebas de la capa fijan el comportamiento.

## Migration Plan

Sin datos ni migraciones. El modo por defecto no cambia. Para revertir, dejar de pasar
`--allow-writes`; quitar la capa no afecta al resto del sitio.
