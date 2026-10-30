## 1. Pruebas aisladas

- [x] 1.1 Reemplazar `reload_urls` en `tests/test_routing.py` por un fixture que aplique la ruta del admin con `override_settings` y recargue las URLs antes y después de restaurarla; usarlo también en la prueba de ruta por defecto; verificar que `pipenv run pytest tests/test_routing.py::TestAdminPath::test_admin_moves_to_custom_path tests/test_routing.py::TestAdminPath::test_admin_login_uses_default_path` pasa en ese orden
- [x] 1.2 Hacer que `load_settings` en `tests/test_settings_base.py` borre todas las variables leídas por `orion.settings.base` (lista obtenida de su código fuente); verificar con `PIPENV_DONT_LOAD_ENV=1 ORION_ADMIN_PATH=panel/ LANGUAGE_CODE=en EMAIL_USE_SSL=true pipenv run pytest` sin fallas

## 2. Ajustes base

- [x] 2.1 Quitar `LocaleMiddleware` de `orion.settings.base` y agregar a `tests/test_routing.py` una prueba de que una página pedida con `Accept-Language: fr` declara `lang="es"`; verificar con `pipenv run pytest tests/test_routing.py`
- [x] 2.2 Hacer que `EMAIL_USE_TLS` tome por defecto `not EMAIL_USE_SSL`, con pruebas de los tres escenarios del delta de `project-configuration`; verificar con `pipenv run pytest tests/test_settings_base.py`

## 3. `.env.example` y documentación

- [x] 3.1 Agregar `DATABASE_CONN_MAX_AGE` a `.env.example` y una prueba que verifique que toda variable leída por `orion.settings.base` figura en `.env.example`; verificar con `pipenv run pytest tests/test_settings_base.py`
- [x] 3.2 Documentar que `pipenv run` carga `.env` pisando el shell (cabecera de `.env.example`, README y comentario de `docker-compose.yml` con las URLs de Docker para copiar a `.env`); corregir el comentario de `example/example/settings.py`; verificar con `grep -n "PIPENV_DONT_LOAD_ENV" README.md .env.example docker-compose.yml`
- [x] 3.3 Registrar los cambios en `CHANGELOG.md` (incluido el aviso de TLS por defecto); verificar con `pipenv run pre-commit run --files CHANGELOG.md`

## 4. Verificación integral

- [x] 4.1 Ejecutar `pipenv run test-postgres`, `pipenv run test-mysql`, `pipenv run lint`, `ruff format --check .`, `openspec validate fix-skeleton-qa-findings` y `manage.py check` en los dos motores; registrar los resultados en este archivo

## Workflow follow-up

- Archivar `add-project-skeleton` antes que este cambio (los deltas de este solo agregan requisitos a capacidades que crea aquel).

## Resultados de verificación

Ejecutado con PostgreSQL 14.13 y MySQL 9.0.1 locales. Las bases de Docker no se levantaron.

- **Suites completas:**
  - `pipenv run test-postgres`: 62 pruebas pasaron.
  - `pipenv run test-mysql`: 62 pruebas pasaron.
- **Lint y validación:**
  - `pipenv run lint` y `ruff format --check .`: sin errores.
  - `openspec validate fix-skeleton-qa-findings --strict`: válido.
  - `pre-commit run` sobre los archivos de documentación modificados: todos los hooks
    pasaron.
- **`manage.py check`:** sin problemas en PostgreSQL y en MySQL, ejecutado con
  `PIPENV_DONT_LOAD_ENV=1 DATABASE_URL=…`.
- **Aislamiento:**
  - La suite pasa (62) con
    `PIPENV_DONT_LOAD_ENV=1 ORION_ADMIN_PATH=panel/ LANGUAGE_CODE=en EMAIL_USE_SSL=true`;
    antes fallaban 2.
  - Las dos pruebas de la ruta del admin pasan en orden inverso; antes fallaba una.
- **Cobertura de `.env.example`:** la prueba falla si se borra `DATABASE_CONN_MAX_AGE` de
  `.env.example` (se comprobó y se restauró el archivo).
- **Vía documentada para cambiar la base de pruebas:**
  `PIPENV_DONT_LOAD_ENV=1 POSTGRES_TEST_URL=<URL inalcanzable> pipenv run test-postgres`
  da 13 errores de conexión. Prueba que la variable ahora se usa; antes se ignoraba y
  pasaban 57.
- **Email:**
  - Con solo `EMAIL_USE_SSL=true`, `manage.py check` no informa errores.
  - Con SSL y TLS en `true`, sigue informando `orion.E001`.
- **Admin sin `LocaleMiddleware`:** un usuario con idioma preferido `en` ve el admin con
  `lang="en"`, y uno con `es` lo ve con `lang="es"`. Se verificó con una prueba temporal
  que no quedó en el repositorio.
