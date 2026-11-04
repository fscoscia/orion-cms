# Tasks

## 1. Infraestructura

- [x] 1.1 Agregar `pytest-playwright` como dependencia de desarrollo (`Pipfile`); marcador
  `e2e` registrado en `pyproject.toml` y `addopts` con `-m "not e2e"`; scripts
  `test-e2e-postgres` y `test-e2e-mysql` en el `Pipfile` (mismo patrón que
  `test-postgres`/`test-mysql`); verificar con `pipenv install --dev` y
  `pipenv run test-postgres` (sigue sin correr nada de `tests/e2e/`)
- [x] 1.2 `tests/e2e/conftest.py`: fixture `live_server_page` que combina `page` (de
  `pytest-playwright`) con `live_server` (de `pytest-django`); verificar con una prueba
  mínima que navega a `live_server.url` y encuentra el título de la página de inicio

## 2. Admin: alta y publicación de una página

- [x] 2.1 `tests/e2e/test_admin_page_lifecycle.py`: iniciar sesión en `/admin/` con
  credenciales válidas, crear una página hija de la página de inicio y publicarla;
  verificar que la página publicada se puede abrir desde el sitio público con su
  contenido; correr con `pipenv run test-e2e-postgres -k test_admin_page_lifecycle`
- [x] 2.2 En el mismo archivo: intentar iniciar sesión con una contraseña incorrecta y
  verificar que el admin muestra el error de credenciales sin iniciar sesión; correr con
  `pipenv run test-e2e-postgres -k test_admin_page_lifecycle`

## 3. Sitio público: JavaScript, CSP y navegación

- [x] 3.1 `tests/e2e/test_site_rendering.py`: cargar una página publicada que use un
  componente de Alpine.js y verificar que queda inicializado y funciona (sin que la CSP
  con nonce lo bloquee, sin errores de consola de CSP); correr con
  `pipenv run test-e2e-postgres -k test_site_rendering`
- [x] 3.2 En el mismo archivo: hacer clic en un enlace del menú hacia otra página
  publicada y verificar que el navegador llega a esa página; correr con
  `pipenv run test-e2e-postgres -k test_site_rendering`

## 4. Formularios

- [x] 4.1 `tests/e2e/test_form_submission.py`: usando el comando existente
  `orion_create_example_forms` como datos de prueba, completar los campos requeridos de
  un formulario publicado y enviarlo con el navegador; verificar que se ve la página o
  el mensaje de agradecimiento configurado; correr con
  `pipenv run test-e2e-postgres -k test_form_submission`

## 5. Cierre

- [x] 5.1 README (instalar el navegador con `playwright install chromium`, qué cubre la
  suite de punta a punta, cómo correrla, por qué no corre con `pipenv run test`);
  CHANGELOG; traducir los textos nuevos si corresponde
- [x] 5.2 Ejecutar `pipenv run test-e2e-postgres` y `pipenv run test-e2e-mysql` completos,
  y además `pipenv run test-postgres` / `pipenv run test-mysql` (confirmar que no suman
  tiempo ni dependen del navegador); `ruff`, pre-commit, `manage.py check`,
  `makemigrations --check`; registrar los resultados

## Resultados de verificación (2026-11-03)

- `pipenv run test-postgres`: 737 passed, 5 deselected (las de `tests/e2e/`), en
  112.98s — igual que antes del cambio; no suma tiempo ni necesita el navegador.
- `pipenv run test-mysql`: 736 passed, 1 skipped (prueba de stemming de PostgreSQL de
  `test_site_search.py`, preexistente), 5 deselected, en 117.83s — igual que antes.
- `pipenv run test-e2e-postgres`: 5 passed, 737 deselected, en 17.06s.
- `pipenv run test-e2e-mysql`: 5 passed, 737 deselected, en 20.45s.
- `ruff check` y `ruff format --check`: sin errores (un archivo necesitó
  `ruff format`, aplicado). `pre-commit` sobre los archivos nuevos y modificados: sin
  errores. `manage.py check`: sin problemas. `makemigrations --check --dry-run`: sin
  cambios.
- Al implementar `test_admin_page_lifecycle.py` (alta y publicación de una página desde
  el admin) se encontraron tres problemas reales de la interacción con el editor de
  Wagtail, no anticipados en el diseño, documentados en design.md (Riesgos): el campo
  `slug` vive en la pestaña "Promocionar" (colapsada) y se completa con JS a partir del
  título, lo que hacía fallar la publicación por una carrera con ese JS; "Publicar" es
  una acción secundaria (este proyecto tiene moderación habilitada), colapsada en el
  menú desplegable del pie de página tras "Guardar borrador"; y la URL del formulario de
  alta ya calzaba con el patrón usado para esperar la redirección tras publicar, por lo
  que esa espera no esperaba nada. Los tres se repitieron en una corrida en bucle (8+
  veces) hasta confirmar que la prueba corregida no es intermitente.
- Traducciones: README y CHANGELOG son documentación; el código de las pruebas no tiene
  textos visibles para usuarios finales. Nada para traducir.
