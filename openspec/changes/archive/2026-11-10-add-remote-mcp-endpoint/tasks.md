# Tasks

## 1. Niveles de acceso en el registro

- [x] 1.1 Pasar la bandera `writes` de las herramientas a un nivel de acceso (`read`, `draft`,
  `settings`) y el contexto del servidor a un conjunto de niveles permitidos; un nivel ausente o
  desconocido no se permite. Verificación: las pruebas existentes de `test_mcp.py` y
  `test_mcp_writes.py` pasan sin cambios de comportamiento, más pruebas de los niveles y de que
  una herramienta sin nivel no se lista.
- [x] 1.2 Marcar cada herramienta con su nivel (`page_create_draft` y `page_update_draft`:
  `draft`; `redirect_*` y `site_*_update`: `settings`; el resto: `read`) y que el modo local con
  `--allow-writes` permita los tres. Verificación: una prueba por herramienta que comprueba su
  nivel y que el modo local sigue ofreciendo las mismas herramientas que antes.

## 2. Claves y recibos

- [x] 2.1 Modelos `ApiKey` y `OperationReceipt` con una migración aditiva. Verificación:
  `makemigrations --check` sin cambios pendientes, migración aplicada y revertida en PostgreSQL y
  MySQL, y la migración no toca tablas existentes. *Hecho: aplicada, revertida y vuelta a aplicar en PostgreSQL; `makemigrations --check` sin cambios; una prueba comprueba que solo crea tablas. En MySQL se aplica en cada corrida de `test-mysql`, pero revertirla no se probó: el usuario de la base no puede crear bases extra.*
- [x] 2.2 Generación del token (`orion_mcp_` más 48 caracteres), hash SHA-256, prefijo, creación
  y revocación, con la validación del usuario (activo y no superusuario). Verificación: pruebas de
  que solo se guarda el hash, de que el token completo no está en la base, y de las validaciones.
- [x] 2.3 Autenticación por clave: ausente, desconocida, vencida, revocada y de un usuario
  inactivo o borrado dan el mismo 401 con `WWW-Authenticate`; `last_used_at` una vez por minuto.
  Verificación: pruebas de cada causa con respuestas idénticas y de que diez llamadas escriben
  una vez.

## 3. Endpoint

- [x] 3.1 Ajustes `ORION_MCP_ENDPOINT`, `ORION_MCP_ALLOWED_ORIGINS`, `ORION_MCP_MAX_BODY` y
  `ORION_MCP_RATE_LIMIT` en los ajustes base, con validación al arrancar. Verificación: pruebas
  en `test_settings_env.py` de los valores por defecto y de valores inválidos.
- [x] 3.2 Vista `POST /_mcp/` registrada en `orion.urls` antes de las páginas, con la ruta en
  `is_internal_request`: JSON-RPC, 202 para notificaciones, 405 para GET y DELETE, 404 apagado,
  `no-store`, sin CSRF, `Origin` 403, `MCP-Protocol-Version` 400, cuerpo 413. Verificación:
  pruebas de cada respuesta y de que la ruta no entra al caché de páginas ni al registro de 404.
- [x] 3.3 Límites de uso (intentos fallidos por IP con `get_client_ip`; peticiones por clave) con
  429 y `Retry-After`, y el registro por llamada sin secretos. Verificación: pruebas que superan
  los límites y que comprueban con `caplog` que el registro no contiene el token ni los argumentos.

## 4. Alcances y recibos

- [x] 4.1 Alcances de las claves: `read-only` y `draft-only` filtran `tools/list` y `tools/call`
  por nivel; la clave actúa como su usuario. Verificación: tabla de pruebas de cada herramienta por
  alcance (incluidas las denegadas, también con un usuario Administrador) y de la atribución de la
  revisión al usuario de la clave.
- [x] 4.2 `operation_key` en las herramientas de escritura de una clave con los recibos:
  repetición idéntica, conflicto y purga oportunista de los de más de 30 días. Verificación:
  pruebas de una sola página creada con dos llamadas iguales, del conflicto y de la purga, esta
  última sin más de una ejecución por hora.

## 5. Pantalla del admin

- [x] 5.1 Pantalla en el menú de Ajustes para Administradores y superusuarios: lista, creación
  con el token mostrado una vez, y revocación; las URLs comprueban el permiso. Verificación:
  pruebas con Administrador (ve y crea y revoca), Editor (403 y sin menú), el token una sola vez y
  la clave revocada que da 401.

## 6. Documentación

- [x] 6.1 Guía `docs/guias/mcp-en-produccion.md` y enlaces desde `usar-el-mcp.md`, el README
  (Integraciones), `docs/alta-de-cliente.md`, el `AGENTS.md` de la plantilla y el `CHANGELOG`;
  variables comentadas en el `.env.example` de la plantilla. Verificación: la prueba de enlaces del
  `AGENTS.md` pasa y los comandos documentados se ejecutaron. *Los de `curl` se ejecutaron contra el servidor de desarrollo; Nginx, Passenger y la cabecera `Authorization` en cPanel no se probaron.*
- [x] 6.2 Prueba de extremo a extremo con el cliente de Django: `initialize`, `tools/list` y un
  borrador con una clave `draft-only`, y la misma sesión contra una base temporal con el servidor
  de desarrollo y `curl`. Verificación: salida de las dos; no se afirma nada sobre un asistente
  real si no se probó. *Hecho con el servidor de desarrollo y `curl` sobre una base temporal (ya borrada): 401 sin clave, 405 en GET, 403 con `Origin`, `initialize`, 202 en la notificación, lista de herramientas de una clave `draft-only`, un borrador creado y su reintento con la misma `operation_key` (una sola página), y `redirect_create` desconocida. Sin asistente real.*

## 7. Cierre

- [x] 7.1 Ejecutar `pipenv run test`, `pipenv run test-mysql` y `pipenv run lint`, y validar con
  `openspec validate add-remote-mcp-endpoint --strict`. Verificación: salida de los cuatro comandos;
  informar cualquier fallo sin afirmar lo no ejecutado.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado, con `/opsx:archive`.
- Abrir el paso 4 de la hoja de ruta (escritura completa en producción) con `/opsx:propose`.
