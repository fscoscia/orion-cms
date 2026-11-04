## 1. Preparación

- [x] 1.1 Confirmar que `add-project-tailwind-build` está archivado: `openspec list` no lo
  muestra y `openspec/changes/archive/` sí.
- [x] 1.2 Agregar `python-dotenv` a `pyproject.toml` con un rango acotado, actualizar el
  lock y verificar con `pipenv run python -c "import dotenv"`.

## 2. Carga del `.env`

- [x] 2.1 Agregar `load_env_file` a `orion.settings.env` y probar en
  `tests/test_settings_env.py`: variable solo en el archivo, prioridad del entorno,
  archivo ausente y valores con `#`, `$`, `(` y `=`.
- [x] 2.2 Cargar el `.env` en `settings.py-tpl` antes de importar los ajustes de Orion, y
  verificar en `tests/test_project_template.py`, con un subproceso sin esas variables en
  el entorno, que `manage.py check` y la importación de la aplicación WSGI funcionan.
- [x] 2.3 Corregir en el README las guías de VPS y cPanel: el `.env` se lee solo y se
  protege con `chmod 600`, y cPanel instala `django-tailwind-cli`. Actualizar
  `docs/alta-de-cliente.md`, y verificar que los comandos de la guía de cPanel corren en
  orden en un entorno limpio sin `pipenv`.

## 3. Registro de errores

- [x] 3.1 Definir `LOGGING` en `orion/settings/base.py` y probar en
  `tests/test_logging.py` que un error de `django.request` y uno de un logger de
  Orion llegan al handler, y que un 404 no llega.
- [x] 3.2 Documentar en el README dónde queda el log en cada guía y cómo redefinir
  `LOGGING` para usar `mail_admins`, y verificar que los dos destinos están nombrados en
  las guías de VPS y cPanel.

## 4. `.gitignore` de la plantilla

- [x] 4.1 Anclar `/media/` y `/static/`, agregar `/private/`, y probar en
  `tests/test_project_template.py` con `git check-ignore` que `home/static/home/css/site.css`
  no se ignora, y que `static/x`, `.env` y `private/forms/cv.pdf` sí.

- [x] 4.2 Sacar `assets/` del `.gitignore` de la plantilla y agregar
  `assets/project/css/project.css` inicial, y probar en `tests/test_project_template.py`
  que git no lo ignora y que `findstatic` lo encuentra.
- [x] 4.3 Documentar en el README que el CSS del proyecto se compila antes de commitear y
  que el deploy no lo compila, y verificar que las guías de VPS y cPanel no piden
  `css-build`.

## 5. Rutas bajo un prefijo

- [x] 5.1 Crear `orion.core.paths` con `is_admin_request` e `is_asset_request`, y probar
  con y sin `SCRIPT_NAME`, incluyendo `/sub/static/`.
- [x] 5.2 Usarlas en `TwoFactorMiddleware` y probar en `tests/test_two_factor.py` que el
  admin bajo `/sub` redirige al segundo factor y que una página pública no.
- [x] 5.3 Usarlas en la CSP, `PageCacheMiddleware` y `NotFoundMiddleware`, y probar en
  `tests/test_site_security.py` y en las pruebas de caché y 404 los escenarios de
  `site-security`.

## 6. Exportación CSV

- [x] 6.1 Sobrescribir `preprocess_field_value` en `OrionSubmissionsListView` y probar en
  las pruebas de la bandeja: fórmula con `=`, `@`, tabulación, `+` y `-` seguidos de letras
  o salto de línea, teléfono y número sin cambios.
- [x] 6.2 Agregar una prueba de exportación a Excel que confirme que la celda con la
  fórmula es de texto.
- [x] 6.3 Mencionar la neutralización en la sección del README sobre exportaciones, y
  verificar que indica qué valores conservan el formato original.

## 7. Cierre e integración

- [x] 7.1 Agregar las entradas al CHANGELOG, con los pasos manuales para proyectos
  existentes (`design.md`, "Migration Plan"), y verificar que nombran cada archivo a tocar.
- [x] 7.2 Correr `pipenv run lint`, `pipenv run ruff format --check .` y
  `pipenv run manage makemigrations --check --dry-run` sin hallazgos. Lint y migraciones
  limpios. `ruff format --check` solo marca un Markdown archivado ajeno a este cambio
  (`2026-11-04-fix-env-str-empty-fallback/design.md`).
- [x] 7.3 Correr `pipenv run test-postgres`, `pipenv run test-mysql` y las pruebas de punta
  a punta en ambas bases, y registrar aquí los resultados. PostgreSQL: 779 passed, 5
  deselected. MySQL: 778 passed, 1 skipped, 5 deselected. Punta a punta: 5 passed en cada
  base.
- [x] 7.4 Repetir la instalación limpia del wheel sin `pipenv`, con Gunicorn y `DEBUG=false`:
  `manage.py check` funciona solo con el `.env`, y un 500 forzado deja su traza en la
  salida de errores. Registrar aquí el resultado. `manage.py check` y Gunicorn leyeron solo
  el `.env`, con una clave generada por `get_random_secret_key`; el 500 forzado dejó su
  traza y el 404 no dejó nada. Hallazgo: `/` respondió 500 porque faltaba
  `project/css/project.css` (ver la tarea 4.2). Repetido con los pasos de la guía de cPanel
  y el `passenger_wsgi.py` de la guía, en PostgreSQL: `/` y el formulario responden 200, el
  CSS del proyecto 200 y no hay errores en el log.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
- Aplicar a mano en Intervita los pasos de `design.md` ("Migration Plan").
