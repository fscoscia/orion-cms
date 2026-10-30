# Tasks

## 1. Paquete y entorno

- [x] 1.1 Crear `pyproject.toml` (metadatos, dependencias, extras `postgres` y `mysql`, configuración de Ruff y pytest) y `src/orion/__init__.py` con la versión; verificar con `pipenv run python -c "import orion"`
- [x] 1.2 Crear `Pipfile` con Python 3.12, Orion editable con ambos extras y las dependencias de desarrollo; verificar que `pipenv install --dev` termina sin errores y genera `Pipfile.lock`
- [x] 1.3 Crear `.gitignore`, `.editorconfig`, `.env.example` y `.pre-commit-config.yaml`; verificar con `pipenv run pre-commit run --all-files`

## 2. Configuración por entorno

- [x] 2.1 Implementar `orion.settings.env` (`env_str`, `env_bool`, `env_list`) con pruebas de valores válidos, ausentes e inválidos; verificar con `pytest tests/test_settings_env.py`
- [x] 2.2 Implementar `orion.settings.base` (apps, middleware, templates, base de datos, idioma, email, valores seguros fuera de debug, ruta del admin validada) con pruebas que recargan el módulo con distintos entornos; verificar con `pytest tests/test_settings_base.py`
- [x] 2.3 Implementar la app `orion.core` y el chequeo `orion.E001` de SSL y TLS de email con pruebas; verificar con `pytest tests/test_checks.py`

## 3. Rutas, salud y plantilla mínima

- [x] 3.1 Implementar la vista de salud con pruebas de éxito, base caída, métodos y caché; verificar con `pytest tests/test_health.py`
- [x] 3.2 Implementar `orion.urls` y las plantillas `orion/base.html` y `wagtailcore/page.html` con pruebas del admin, la raíz y la página genérica; verificar con `pytest tests/test_routing.py`

## 4. Proyecto de ejemplo

- [x] 4.1 Crear `example/` (`manage.py`, ajustes que extienden los de Orion, rutas, WSGI) y verificar con `pipenv run python example/manage.py check` y `migrate` en una base vacía
- [x] 4.2 Crear `docker-compose.yml` opcional con PostgreSQL 17 y MySQL 8.4; verificar con `docker compose config`

## 5. Documentación y verificación integral

- [x] 5.1 Escribir README (instalación, comandos, uso desde un proyecto), AGENTS.md con enlace CLAUDE.md, y CHANGELOG.md; verificar que los comandos del README se ejecutan como están escritos
- [x] 5.2 Ejecutar la suite completa en PostgreSQL y en MySQL, `ruff check`, `ruff format --check` y `manage.py check --deploy` con entorno de producción; registrar los resultados en el resumen del cambio

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-project-skeleton` cuando esté aprobado.

## Resultados de verificación

- `pipenv run test-postgres` (PostgreSQL 14.13 local): 57 pruebas pasaron.
- `pipenv run test-mysql` (MySQL 9.0.1 local): 57 pruebas pasaron.
- `ruff check .` y `ruff format --check .`: sin errores.
- `pre-commit run` sobre todos los archivos nuevos: todos los hooks pasaron.
- `manage.py check` y `migrate` en PostgreSQL y MySQL: sin errores. En MySQL, Django
  avisa `models.W036` (MySQL no soporta restricciones únicas con condición; afecta a un
  modelo de Wagtail y es una limitación conocida).
- `manage.py check --deploy` con entorno de producción: avisos `security.W004` (HSTS) y
  `security.W008` (redirección a HTTPS), previstos para la Fase 5, y `security.W019`,
  esperado porque `X_FRAME_OPTIONS` es `SAMEORIGIN` para la vista previa de Wagtail.
- `docker compose config`: válido. Los contenedores no se levantaron en esta verificación.
- `pipenv run manage runserver`: `/health/` 200, `/admin/login/` 200, `/` 200 y una ruta
  inexistente 404. Del README no se ejecutaron tal cual `createsuperuser` ni el comando de
  creación de bases MySQL (las bases se crearon con comandos equivalentes).
