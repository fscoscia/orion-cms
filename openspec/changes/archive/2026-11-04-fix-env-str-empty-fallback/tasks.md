## 1. Corregir `env_str`

- [x] 1.1 En `src/orion/settings/env.py`, cambiar `env_str` para que una variable
  presente y vacía (o solo espacios) caiga al `default`, con el mismo criterio que ya
  usan `env_bool`, `env_int` y `env_list` (ver `design.md`, "Decisions"). Verificar
  leyendo el diff: la función sigue sin lanzar excepciones y sigue aceptando
  `default=""`.
- [x] 1.2 Agregar a `tests/test_settings_env.py`, en `TestEnvStr`, un caso que fije
  `ORION_TEST_VALUE=""` con `monkeypatch.setenv` y confirme que
  `env_str("ORION_TEST_VALUE", "fallback") == "fallback"`; verificar con
  `pipenv run test -k test_settings_env`.
- [x] 1.3 Confirmar que los casos existentes de `TestEnvStr`,
  `TestEnvBool.test_uses_default_when_absent_or_empty`, `TestEnvInt` y `TestEnvList`
  siguen pasando sin cambios (no deben verse afectados por este fix); verificar con
  `pipenv run test -k test_settings_env`. Los 20 casos de `test_settings_env.py` pasan.

## 2. Verificar la reproducción original

- [x] 2.1 En un shell de Django con `ORION_SEARCH_CONFIG=""` en el entorno y
  `LANGUAGE_CODE=es`, confirmar que `settings.ORION_SEARCH_CONFIG == "spanish"` (antes
  del fix daba `""`); verificar a mano o agregando el caso a
  `tests/test_site_search.py::TestSearchConfig` si ese archivo ya parametriza variables
  de entorno para sus `settings` (revisar el fixture existente antes de decidir si
  amerita un caso nuevo ahí o si el de `tests/test_settings_env.py` ya alcanza).
  Verificado a mano con `pipenv run manage shell -c`: devuelve `'spanish'`. El test
  existente `test_site_search.py::test_config_follows_the_base_language` usa el
  fixture `settings` de pytest-django sobre un proceso ya arrancado y no reimporta
  `settings/base.py`, así que no puede parametrizar variables de entorno sin recargar
  el módulo completo; el caso de `tests/test_settings_env.py` (nivel de la función que
  tiene el bug) ya cubre la regresión sin esa complejidad.
- [x] 2.2 Sobre el proyecto Intervita (`/Users/fscoscia/Proyectos/intervita`, generado
  en el cambio `validate-intervita-site`), quitar el workaround
  `ORION_SEARCH_CONFIG=spanish` de su `.env` (dejarla vacía, como la distribuye
  `.env.example`), reinstalar la versión corregida de Orion
  (`pipenv run pip install -e /Users/fscoscia/Proyectos/orion`, ya es editable así que
  solo hace falta confirmar que toma el cambio) y correr
  `pipenv run python manage.py orion_install --noinput` sobre una base limpia; verificar
  que termina sin el `psycopg.errors.InvalidName` original. El path local editable toma
  el fix sin reinstalar; `orion_install` sobre una base `intervita` recién creada
  terminó con "Installation complete." y los dos formularios de ejemplo creados, sin el
  error original.

## 3. Pruebas completas

- [x] 3.1 Correr la suite completa en PostgreSQL (`pipenv run test-postgres`) y en
  MySQL (`pipenv run test-mysql`), y verificar que ambas terminan en verde (regla del
  proyecto: probar en los dos motores). PostgreSQL: 738 passed, 5 deselected. MySQL:
  737 passed, 1 skipped, 5 deselected.
- [x] 3.2 Correr `pipenv run lint` y verificar que no reporta hallazgos nuevos sobre
  `src/orion/settings/env.py`. "All checks passed!"
