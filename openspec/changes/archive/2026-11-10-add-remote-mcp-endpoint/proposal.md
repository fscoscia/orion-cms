# Proposal

## Why

El MCP local (pasos 1 y 2) sirve a quien tiene el proyecto en su máquina. Para que un
asistente trabaje contra un sitio real, o para que lo use alguien sin acceso al servidor,
hace falta un endpoint dentro del propio sitio, con autenticación que se pueda crear, limitar
y revocar. Es el paso 3 de la hoja de ruta. A diferencia del modo local, esto abre una
superficie pública nueva, así que viene apagada, con claves de alcance limitado y solo puede
leer y guardar borradores.

## What Changes

- Endpoint `POST /_mcp/` dentro del sitio, **apagado por defecto** (`ORION_MCP_ENDPOINT`), que
  habla JSON-RPC con el mismo servidor de mensajes del modo local (subconjunto de Streamable
  HTTP: un mensaje por POST, respuestas JSON).
- Claves de API (`ApiKey`): token aleatorio que se guarda solo como hash, ligado a un usuario
  de Wagtail, con alcance `read-only` o `draft-only`, vencimiento opcional y revocación.
- Pantalla en el admin (Ajustes) para que los Administradores creen y revoquen claves; el
  token se muestra una sola vez.
- Alcances: `read-only` solo lee; `draft-only` además guarda borradores de páginas. Ninguna
  clave remota escribe redirecciones ni datos del sitio.
- Recibos de operación: una `operation_key` opcional hace seguros los reintentos de las
  herramientas de escritura.
- Límites de uso por IP (intentos fallidos) y por clave, registro por llamada sin secretos y
  respuestas que no se cachean.
- Refactor del registro: de la bandera `writes` a niveles de acceso (`read`, `draft`,
  `settings`), sin cambiar el comportamiento del modo local.
- Documentación: guía `docs/guias/mcp-en-produccion.md`, enlaces, variables en el
  `.env.example` de la plantilla y `CHANGELOG`.
- Fuera de alcance (paso 4): escribir redirecciones, datos y textos del sitio con una clave,
  publicar, borrar, claves de "acceso completo", OAuth y la revisión 2026-07-28 del protocolo.

## Capabilities

### New Capabilities
- `mcp-api-keys`: claves de API del MCP y la pantalla del admin que las gestiona.

### Modified Capabilities
- `mcp-server`: transporte HTTP, alcances, recibos, límites, registro y guía.

## Impact

- Código: `src/orion/mcp/` (modelos `ApiKey` y `OperationReceipt` con migraciones aditivas,
  vista del endpoint, autenticación, límites, pantalla del admin y hooks), `orion.urls`,
  `orion.core.paths`, ajustes base (`ORION_MCP_*`).
- Sin dependencias nuevas.
- Documentación: guía nueva, `usar-el-mcp.md`, README, `docs/alta-de-cliente.md`,
  `AGENTS.md` y `.env.example` de la plantilla, `CHANGELOG`.
- Riesgos: una clave filtrada, instrucciones ajenas que lleven a escribir borradores, un
  endpoint público como superficie nueva y límites de uso de mejor esfuerzo; ver `design.md`.
