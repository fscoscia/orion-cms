# Proposal

## Why

El MCP local de solo lectura (`add-local-readonly-mcp`) deja que un asistente consulte el
sitio, pero no que prepare nada: el equipo sigue copiando a mano al admin los textos, las
redirecciones y los ajustes que el asistente propone. Es el paso 2 de la hoja de ruta hacia
un MCP usable en producción. Antes de abrir escritura hace falta una capa que centralice las
reglas (permisos, validación, revisiones) para que ni el MCP local ni el endpoint remoto
posterior las repitan ni las salteen.

## What Changes

- Paquete nuevo `orion.operations`: operaciones de contenido independientes del MCP, sobre
  las revisiones y los permisos de Wagtail. Crear una página como borrador; actualizar un
  borrador con revisión esperada; crear y actualizar redirecciones; actualizar los datos del
  sitio y los textos del sitio por idioma. Nunca publican, despublican ni borran.
- El MCP local gana seis herramientas de escritura (`page_create_draft`,
  `page_update_draft`, `redirect_create`, `redirect_update`, `site_settings_update`,
  `site_texts_update`), **opt-in**: `manage.py orion_mcp --allow-writes`. Escribe siempre como
  una **cuenta técnica dedicada**, `orion-agent`, que nadie elige. Sin la bandera el servidor
  sigue siendo de solo lectura y esas herramientas no existen.
- Comando nuevo `manage.py orion_create_agent_user`: crea la cuenta técnica (contraseña
  inutilizable, grupo Editores) una vez por sitio. No lo ejecuta `orion_install`.
- `page_get` devuelve `latest_revision_id`, que se usa como revisión esperada.
- Los permisos de la cuenta mandan; ninguno se eleva. Como Editores no gestiona redirecciones
  ni datos del sitio, salvo que el equipo la agregue al grupo Administradores.
- Documentación: se amplía `docs/guias/usar-el-mcp.md` con la escritura, la cuenta técnica
  y las precauciones de seguridad.
- Fuera de alcance: el admin de Wagtail no pasa a usar la capa; sin borrados; sin
  publicar; sin clave de operación ni recibos (paso 3); sin endpoint HTTP ni claves de API
  (paso 3); sin medios ni menús.

## Capabilities

### New Capabilities
- `content-operations`: operaciones de escritura de contenido con permisos, validación y
  revisiones, independientes del transporte.

### Modified Capabilities
- `mcp-server`: modo de escritura opt-in, herramientas de escritura y guía actualizada.

## Impact

- Código: paquete nuevo `src/orion/operations/`; en `src/orion/mcp/` el comando
  (`--allow-writes` y la comprobación de la cuenta), el comando `orion_create_agent_user`, las
  herramientas de escritura y `page_get`.
- `orion.operations` entra en `INSTALLED_APPS` solo si hace falta (no tiene modelos ni
  migraciones; se evalúa en el diseño).
- Sin migraciones ni dependencias nuevas.
- Riesgos: HTML inseguro en texto enriquecido, instrucciones ajenas que lleven al asistente
  a escribir algo no deseado, y pisar cambios de otra persona; ver `design.md`.
