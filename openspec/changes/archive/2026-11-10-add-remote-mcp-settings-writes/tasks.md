# Tasks

## 1. Alcance y permisos

- [x] 1.1 Pruebas primero (deben fallar): una clave `full` ve y llama a las herramientas de
  nivel `settings`; `read-only` y `draft-only` no; ninguna clave tiene herramientas de publicar
  ni borrar; una `full` ligada a un Editor recibe error de permiso. Luego agregar `Scope.FULL`
  y su entrada en `ACCESS_BY_SCOPE`, con la migración de `choices`. Verificación: las pruebas de
  alcance del paso 3 siguen pasando.
- [x] 1.2 Formulario y vista de creación: `full` solo para superusuarios, validado en el
  servidor; revocar sigue abierto a Administradores. Pruebas: un Administrador no ve la opción
  ni puede enviarla; un superusuario crea la clave; un Administrador revoca una `full`; un
  Editor sigue sin acceso. Textos con gettext y catálogo `es` (`.po` y `.mo`).

## 2. Valor previo y reversión

- [x] 2.1 Pruebas primero: el recibo guarda solo los campos cambiados; sin `operation_key` el
  servidor genera una y la devuelve; con la misma clave y argumentos el reintento no escribe.
  Luego agregar `before` y `reverted_at` a `OperationReceipt` (migración aditiva) y que las
  herramientas de ajustes de una clave siempre creen recibo.
- [x] 2.2 Herramienta `settings_revert` con pruebas: revierte `site_settings_update`,
  `site_texts_update` y `redirect_update`; conflicto si el valor cambió después; segunda vez
  informa "ya revertida"; sobre `redirect_create` da el error que remite al admin y no borra;
  recibo purgado o de otra clave da error; sin permiso del usuario da error de permiso.
- [x] 2.3 Comprobar que la garantía de no publicar ni borrar sigue valiendo: las pruebas
  existentes de ese tipo cubren también las herramientas nuevas.

## 3. Documentación

- [x] 3.1 Actualizar `docs/guias/mcp-en-produccion.md` (alcance `full`, quién lo crea, qué
  cambia al instante, `settings_revert` y sus límites, riesgos de una clave `full` filtrada) y
  `docs/guias/usar-el-mcp.md` si cita los alcances; `CHANGELOG`. Verificación: prueba de enlaces
  del `AGENTS.md` y comandos documentados ejecutados.
- [x] 3.2 Probar de extremo a extremo con el servidor de desarrollo y `curl` sobre una base
  temporal: clave `full` crea una redirección, actualiza un dato, revierte y recibe 401/error
  de herramienta con una `draft-only`. No afirmar nada sobre un asistente real si no se probó. *Hecho con el servidor de desarrollo y `curl` sobre una base SQLite temporal (ya borrada): una clave `full` creó una redirección, actualizó un dato y lo revirtió; revertir la redirección creada dio el error que remite al admin; una `draft-only` recibió «Unknown tool» en `redirect_create` y `settings_revert`. Sin asistente real, Nginx ni cPanel.*

## 4. Cierre

- [x] 4.1 Ejecutar `pipenv run test`, `pipenv run test-postgres`, `pipenv run test-mysql` y
  `pipenv run lint`, y validar con `openspec validate add-remote-mcp-settings-writes --strict`.
  Verificación: salida de los comandos; informar cualquier fallo sin afirmar lo no ejecutado. *`test`: 1111 pasan; `test-postgres`: 1111; `test-mysql`: 1110 y 1 omitida; lint y `makemigrations --check` limpios; el cambio valida con `--strict`. Primera pasada: falló una prueba del modo local porque `settings_revert` aparecía sin clave; se corrigió ocultándola (`needs_key`).*

## Workflow follow-up

- Archivar el cambio cuando esté aprobado, con `/opsx:archive`.
