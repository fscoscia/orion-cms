# Tasks

## 1. Plantilla de proyecto

- [x] 1.1 Plantilla en `src/orion/project_template/` (`manage.py-tpl`,
  `project_name/{__init__.py, settings.py-tpl, urls.py, wsgi.py-tpl}`,
  `home/{__init__.py, apps.py}`, `templates/README.md`, `.env.example`, `Pipfile` con
  `__ORION_VERSION__` como marcador); verificar con `pytest tests/test_project_template.py`
  (`orion.bin.main` sobre un directorio vacío crea esos archivos; los ajustes generados
  importan `orion.settings.base` y fijan `ROOT_URLCONF`, `WSGI_APPLICATION`, `STATIC_ROOT`,
  `MEDIA_ROOT` y `TEMPLATES[0]["DIRS"]` con el nombre del proyecto dado)
- [x] 1.2 `orion.bin.main` (envuelve `django-admin startproject --template=`) y
  `[project.scripts] orion-start` en `pyproject.toml`; reemplazo de `__ORION_VERSION__` en
  el `Pipfile` generado por `orion.__version__`; verificar con
  `pytest tests/test_project_template.py` (el `Pipfile` generado no tiene el marcador y
  nombra la versión instalada; un destino que ya existe con archivos se rechaza sin
  modificarlo, comportamiento nativo de `startproject`) y, manualmente,
  `pipenv run orion-start` sobre el entorno instalado
- [x] 1.3 El proyecto generado arranca; verificar con `pytest tests/test_project_template.py`
  corriendo `manage.py check` en un subproceso dentro del proyecto generado, con un
  `DATABASE_URL` real y `DEBUG=true`, y confirmando que termina sin errores

## 2. Instalador

- [x] 2.1 `manage.py orion_install`: chequeo de conexión a la base antes de migrar
  (reenvía el error nativo de Django como `CommandError`, sin migrar si falla), `migrate`,
  `createsuperuser` (interactivo o `--noinput` con `DJANGO_SUPERUSER_*`), idioma base
  informado (`settings.LANGUAGE_CODE`), `orion_create_example_forms`; verificar con
  `pytest tests/test_installer.py` (instalación limpia sobre una base vacía deja migrada,
  con superusuario, idioma informado y los formularios de ejemplo; `--noinput` con las
  variables de entorno no pide nada por teclado; correr el comando una segunda vez no
  duplica el contenido de ejemplo y informa en lugar de fallar si el superusuario ya
  existe; una base inalcanzable falla antes de migrar)

## 3. Documentación y cierre

- [x] 3.1 README (`orion-start` y `orion_install`, del comando al sitio funcionando);
  CHANGELOG
- [x] 3.2 Traducir los textos nuevos si corresponde; ejecutar la suite en PostgreSQL y
  MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check`; registrar los
  resultados

## Resultados de verificación (2026-11-02)

- `pytest tests/test_project_template.py` (5) y `tests/test_installer.py` (4): 9 passed,
  tanto en PostgreSQL (`pipenv run test`) como en MySQL (`pipenv run test-mysql`) —
  `orion-start` genera la estructura completa, los ajustes importan `orion.settings.base`
  y fijan `ROOT_URLCONF`/`WSGI_APPLICATION`/`MEDIA_ROOT`/`TEMPLATES[0]["DIRS"]` con el
  nombre dado, el `Pipfile` generado fija la versión instalada (sin el marcador), un
  destino que ya tiene archivos se rechaza sin tocarlo, y el proyecto generado pasa
  `manage.py check` en un subproceso real; `orion_install` deja una instalación limpia
  con superusuario, idioma informado y los formularios de ejemplo, `--noinput` no pide
  nada por teclado, correrlo dos veces no duplica el contenido ni falla por el superusuario
  ya existente, y una base inalcanzable falla antes de migrar sin llamar a ningún otro
  paso.
- `pipenv run test-postgres`: 712 passed. `pipenv run test-mysql`: 711 passed, 1 skipped
  (la prueba de stemming de PostgreSQL de `test_site_search.py`, ya existente).
- Verificación manual: `pipenv install` registra el binario `orion-start`;
  `orion-start mysite <destino>` sobre un directorio real genera el proyecto completo
  (`manage.py`, `mysite/settings.py` con `ROOT_URLCONF = "mysite.urls"`, `urls.py`,
  `wsgi.py`, `home/`, `templates/README.md`, `.env.example`, `Pipfile` con
  `ref = "v0.1.0.dev0"`); `manage.py check` sobre ese proyecto, con `DATABASE_URL` real y
  `DEBUG=true`, termina sin errores.
- `ruff check` y `ruff format --check`: sin errores. `pre-commit` sobre los archivos
  nuevos y modificados (`src/orion/bin.py`, `orion_install.py`, la plantilla completa,
  las pruebas nuevas, `pyproject.toml`, README y CHANGELOG): sin errores.
- `manage.py check`: sin problemas. `makemigrations --check --dry-run`: sin cambios (el
  cambio no agrega modelos).
- Traducciones: los comandos nuevos (`orion_install`, `orion-start`) no usan `gettext` en
  su salida de consola, igual que los demás comandos de gestión de Orion; no hay nada
  para traducir.
