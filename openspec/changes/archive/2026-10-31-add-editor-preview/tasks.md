# Tasks

## 1. Implementación

- [x] 1.1 `DesktopPreviewMixin` en los tipos de página de Orion; verificar con `pytest tests/test_editor_preview.py` (tamaño por defecto escritorio y tamaños disponibles)
- [x] 1.2 `orion/editor/editor.js` (estado inicial y textos de los botones) cargado con `insert_editor_js`, y estilos; verificar con `pytest tests/test_editor_preview.py` (el editor carga el script con los textos traducidos)
- [x] 1.3 `orion/js/preview.js` cargado por `orion/base.html` solo en la vista previa; verificar con `pytest tests/test_editor_preview.py` (presente en la vista previa, ausente en la página publicada)

## 2. Navegador y cierre

- [x] 2.1 Verificar en el navegador: primera edición a 1280 px con la vista previa abierta a la mitad y en escritorio; cerrarla y que siga cerrada; botón con texto; clic en un enlace dentro de la vista previa sin navegar; enlace "En vivo" en otra pestaña; en celular, sin apertura automática, "Vista previa" a pantalla completa y "Editar" de vuelta
- [x] 2.2 Traducir los textos nuevos, actualizar README y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check` y `makemigrations --check`; registrar los resultados

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-editor-preview` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 284 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 284 pruebas pasaron.
- `ruff`, `pre-commit run --all-files`, `manage.py check` y `makemigrations --check` en
  ambas bases (sin migraciones) y `msgfmt --check`: sin errores.
- Chrome sin interfaz, con el almacenamiento del navegador vacío: a 1280 px la primera
  edición abre la vista previa en 640 px y tamaño escritorio, con el botón "Vista previa";
  "En vivo" apunta a la página publicada en otra pestaña; clics en un enlace externo del
  texto y en un ítem del menú dentro de la vista previa no la cambian; cerrada, sigue
  cerrada al editar otra página; a 390 px no se abre sola aunque estuviera guardada como
  abierta, al abrirla ocupa toda la pantalla en tamaño celular y "Editar" vuelve al
  formulario; sin errores de consola.
- Hallazgo que cambió la implementación: en el celular la vista previa quedaba en tamaño
  escritorio (reducida e ilegible); en pantallas angostas se fija el tamaño celular.
