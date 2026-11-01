# Tasks

## 1. Modelo y admin

- [x] 1.1 App `orion.snippets` con `CodeSnippet` (revisiones, alcance, validación), `SnippetViewSet` con aviso y menú solo con permiso, migración; verificar con `pytest tests/test_code_snippets.py` (superusuario gestiona, Administradora no ve ni accede, grupo con permiso sí, alcance sin páginas rechazado, historial con autor y restauración) y `makemigrations --check`

## 2. Inserción

- [x] 2.1 `{% code_snippets %}` en las tres ubicaciones de `orion/base.html`, con alcance, idioma, interruptor de emergencia, sin vistas previas y con la lista en caché por generación; señal de caché de página; verificar con `pytest tests/test_code_snippets.py tests/test_query_budget.py` (cada ubicación, desactivado, sección con y sin subpáginas, tipo de página, idioma, vista sin página, `ORION_SCRIPTS_DISABLED`, vista previa del editor y compartida, admin, caché vaciada al guardar, presupuesto de consultas sin cambios)

## 3. Navegador y cierre

- [x] 3.1 Verificar en el navegador: crear un fragmento como superusuario, verlo en el sitio y no en la vista previa, desactivarlo, restaurar una versión, Administradora sin acceso, en escritorio y celular
- [x] 3.2 Traducir los textos nuevos; actualizar README (fragmentos, permiso, interruptor) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_code_snippets.py` 20 passed (tres ubicaciones, desactivado, sección
  con y sin subpáginas, tipo de página, idioma, vista sin página, interruptor, vista
  previa del editor y compartida, admin, caché vaciada al guardar, alta desde el admin,
  alcance sin páginas rechazado, Administradora sin acceso, grupo con permiso, ningún
  grupo con el permiso, historial con autor y restauración, aviso del interruptor);
  `tests/test_query_budget.py` sin cambios en los presupuestos.
- Navegador (Chrome headless, 1280 px y 390 px), 14/14: alta como superusuario, código en
  el sitio y no en la vista previa compartida ni en el admin, segunda versión, historial
  con autor, restauración de la primera, desactivado, formulario sin desborde en el
  celular, Administradora sin menú ni acceso. Hallado y corregido: la columna "Activo"
  mostraba "False" (ahora un ícono).
- Traducciones: 0 sin traducir ni dudosas.
- `pipenv run test-postgres` 570 passed; `pipenv run test-mysql` 569 passed, 1 skipped.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó
  `orion_snippets.0001_initial` en PostgreSQL y MySQL (`.env` restaurado).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-code-snippets` cuando esté aprobado.
