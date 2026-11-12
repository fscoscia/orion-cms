# Tasks

## 1. Protocolo y comando

- [x] 1.1 Crear la app `orion.mcp` (`apps.py`, `__init__.py`), agregarla a `INSTALLED_APPS` de
  `orion.settings.base` y sumar `orion.mcp` a las pruebas de ajustes si enumeran las apps.
  Verificación: `pipenv run manage check` sin avisos y la prueba de ajustes pasa.
- [x] 1.2 Contrastar la versión del protocolo MCP con la especificación vigente y fijarla en
  una constante. Verificación: la constante y la fuente consultada quedan anotadas en el
  `design.md`. *Hecho: la revisión actual es la 2026-07-28, sin `initialize`; se soportan las
  anteriores. Ver el `design.md`.*
- [x] 1.3 Escribir `handle_message(mensaje)` para `initialize`, `tools/list`, `tools/call` y
  `ping`, con notificaciones sin respuesta y los errores `-32600`, `-32601` y `-32602`.
  Verificación: pruebas unitarias de cada método y de cada error, sin subprocesos.
- [x] 1.4 Escribir el comando `orion_mcp`: lee líneas de la entrada estándar, llama a
  `handle_message`, escribe una línea por respuesta, manda los registros a la salida de
  errores y termina al cerrarse la entrada. Verificación: prueba con un subproceso que envía
  `initialize` y `tools/list` y recibe respuestas válidas, y otra donde una herramienta hace
  `print` sin ensuciar la salida estándar.

## 2. Registro y herramientas del sitio

- [x] 2.1 Escribir el registro de herramientas (nombre, descripción, esquema de entrada,
  función), la validación de parámetros, la paginación acotada a 100 y los errores de
  herramienta como resultado `isError`. Verificación: pruebas del registro sin stdio, con
  `per_page` de 500 rechazado y una herramienta que falla sin tumbar el proceso.
- [x] 2.2 Herramientas `site_overview` y `site_settings` (con textos por idioma y sin
  secretos). Verificación: pruebas con un sitio de dos idiomas, uno no público.
- [x] 2.3 Herramienta `schema`: tipos de página con sus campos y bloques del cuerpo con los
  suyos, incluidos los del proyecto. Verificación: prueba que compara contra
  `get_page_models()` y los bloques de `orion.core.blocks`, más un tipo y un bloque de
  prueba definidos por el "proyecto".
- [x] 2.4 Herramientas `page_tree` y `page_get` (cuerpo en el formato guardado). Verificación:
  pruebas con una portada y dos hijas, una sin publicar, y una página inexistente.

## 3. Herramientas de diagnóstico

- [x] 3.1 Herramientas `redirects_list` y `not_found_list`, ordenadas y acotadas.
  Verificación: pruebas con tres rutas 404 y dos redirecciones.
- [x] 3.2 Herramienta `forms_list`, sin envíos ni adjuntos. Verificación: prueba con un
  formulario con envíos que comprueba que ningún dato de ellos aparece en el resultado.
- [x] 3.3 Extraer la consulta de imágenes sin uso de `orion_unused_images` y el chequeo de
  base de `/health/` a funciones reutilizables, y agregar las herramientas
  `conventions_check`, `unused_images` y `health`. Verificación: las pruebas existentes del
  comando y de la vista siguen pasando sin cambios y las herramientas dan el mismo resultado
  que ellos.

## 4. Garantías

- [x] 4.1 Prueba de solo lectura: ejecutar todas las herramientas con
  `CaptureQueriesContext` y comprobar que no hay `INSERT`, `UPDATE` ni `DELETE`. Verificación:
  la prueba pasa y falla si se agrega una escritura de ejemplo a una herramienta.
- [x] 4.2 Prueba de datos personales: recorrer los resultados de todas las herramientas y
  comprobar que no aparecen emails ni nombres de cuentas ni datos de envíos. Verificación: la
  prueba pasa con usuarios y envíos creados a propósito.

## 5. Documentación

- [x] 5.1 Escribir `docs/guias/usar-el-mcp.md`: comando, ejemplo de `.mcp.json` para Claude
  Code, lista de herramientas, lo que no expone, y advertencias sobre datos personales y
  contenido ajeno. Verificación: lanzar el comando documentado, enviarle `initialize` y
  `tools/list` a mano y comprobar que responde como dice la guía; la conexión con un asistente
  real solo se afirma si se probó. *Hecho con mensajes a mano; no se probó con un asistente real.*
- [x] 5.2 Enlazar la guía desde el `AGENTS.md` de la plantilla, el README y
  `trabajar-con-ia.md`, y registrar el cambio en `CHANGELOG.md`. Verificación: la prueba que
  comprueba los enlaces del `AGENTS.md` incluye la guía nueva y pasa.

## 6. Cierre

- [x] 6.1 Ejecutar `pipenv run test`, `pipenv run test-mysql` y `pipenv run lint`, y validar
  con `openspec validate add-local-readonly-mcp --strict`. Verificación: salida de los
  cuatro comandos; informar cualquier fallo sin afirmar lo no ejecutado.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado, con `/opsx:archive`.
- Abrir el cambio 2 de la hoja de ruta (capa de operaciones) con `/opsx:propose`.
