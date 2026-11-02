# Tasks

## 1. Volcado y empaquetado

- [x] 1.1 `orion.core.backups`: volcado de la base por motor (`pg_dump --format=custom` o
  `mysqldump --single-transaction --routines --triggers --events --add-drop-table`) a un
  archivo temporal, con la contraseña por variable de entorno del subproceso
  (`PGPASSWORD`/`MYSQL_PWD`); verificar con `pytest tests/test_backups.py` (volcado
  correcto en PostgreSQL y en MySQL, contraseña ausente de los argumentos del proceso)
- [x] 1.2 Empaquetado en `.tar.gz` (manifiesto `manifest.json`, `database.dump`, `media/`,
  `forms_private/`), permisos `0600` en el archivo resultante, limpieza del volcado
  temporal aunque falle a mitad de camino; verificar con `pytest tests/test_backups.py`
  (estructura del archivo, manifiesto con motor/fecha/versiones/tamaños, permisos, sin
  `MEDIA_ROOT` ni adjuntos deja esas carpetas vacías, temporal borrado tras un error)
- [x] 1.3 `manage.py orion_backup <archivo>`; verificar con
  `pipenv run manage orion_backup /tmp/test.tar.gz` sobre el proyecto de ejemplo y
  `pytest tests/test_backups.py` (binario faltante falla con un mensaje que lo nombra, sin
  dejar el archivo a medio escribir)

## 2. Inspección

- [x] 2.1 `orion.core.backups`: lectura del manifiesto sin extraer el resto del archivo;
  `manage.py orion_inspect_backup <archivo>` imprime motor, fecha, versiones y tamaños;
  verificar con `pytest tests/test_backups.py` (backup válido, archivo que no es un backup
  de Orion, backup al que le falta una parte)

## 3. Restauración

- [x] 3.1 `orion.core.backups`: restauración de la base por motor (`pg_restore --clean
  --if-exists --no-owner --no-privileges` o `mysql <` el `.sql`) desde el volcado extraído
  a un archivo temporal, y copia de `media/` y `forms_private/` a los directorios
  configurados en el servidor destino; verificar con `pytest tests/test_backups.py`
  (restauración completa en PostgreSQL y en MySQL deja la base y los archivos como en el
  origen, binario faltante falla con un mensaje que lo nombra)
- [x] 3.2 Chequeo de motor (manifiesto contra `DATABASES["default"]` del destino) antes de
  tocar cualquier dato; verificar con `pytest tests/test_backups.py` (motor distinto se
  rechaza sin modificar la base ni los archivos, mensaje nombra ambos motores)
- [x] 3.3 `manage.py orion_restore <archivo>` con confirmación interactiva (`input()` solo
  si hay terminal) y `--noinput` para uso automatizado; verificar con
  `pytest tests/test_backups.py` (sin confirmar y sin `--noinput` no cambia nada y explica
  cómo seguir; confirmado o con `--noinput` aplica la restauración; sin terminal y sin
  `--noinput` se niega a correr)

## 4. Documentación y cierre

- [x] 4.1 README (flujo de backup, inspección y restauración entre servidores; binarios
  cliente que necesita cada motor; que el archivo es sensible y no debe subirse a git);
  CHANGELOG
- [x] 4.2 Traducir los textos nuevos; ejecutar la suite en PostgreSQL y MySQL, `ruff`,
  pre-commit, `manage.py check`, `makemigrations --check`; registrar los resultados

## Resultados de verificación (2026-11-02)

- `pytest tests/test_backups.py`: 19 passed, tanto en PostgreSQL (`pipenv run test`) como
  en MySQL (`pipenv run test-mysql`) — empaquetado con manifiesto y las tres partes
  (`database.dump`, `media/`, `forms_private/`), permisos `0600`, sin medios ni adjuntos
  deja esas carpetas afuera del archivo, limpieza del temporal tras un volcado fallido,
  binario faltante nombrado en el error; inspección sin tocar el archivo (`mtime` sin
  cambios), archivo que no es un backup, backup al que le falta `database.dump`;
  restauración completa (base, medios y adjuntos como en el origen), motor distinto
  rechazado antes de tocar la base; comando de restauración sin confirmar no cambia nada,
  confirmado y con `--noinput` restauran, sin terminal y sin `--noinput` se niega a
  correr, motor distinto rechazado sin preguntar.
- `pipenv run test-postgres`: 703 passed. `pipenv run test-mysql`: 702 passed, 1 skipped
  (la prueba de stemming de PostgreSQL de `test_site_search.py`, ya existente).
- Verificación manual sobre el proyecto de ejemplo (`DATABASE_URL=postgres:///orion`):
  `pipenv run manage orion_backup <archivo>` escribe el archivo con permisos `0600`;
  `pipenv run manage orion_inspect_backup <archivo>` muestra motor `postgresql`, versiones
  de Orion y Django, y tamaños, sin restaurar nada.
- `ruff check` y `ruff format --check`: sin errores (se corrigió un `S603` de
  `subprocess.run` con la justificación de que el comando sale de `DATABASES["default"]`,
  no de entrada sin validar, y una línea larga en las pruebas). `pre-commit` sobre los
  archivos nuevos y modificados: sin errores.
- `manage.py check`: sin problemas. No aplica `--deploy` con ajustes de producción: este
  cambio no agrega ni modifica ningún ajuste (usa `DATABASE_URL`, `MEDIA_ROOT` y
  `ORION_FORMS_PRIVATE_ROOT`, ya validados); queda cubierto por las pruebas existentes de
  `test_site_security.py` y `test_settings_base.py`, que pasan en la corrida completa.
- `makemigrations --check --dry-run`: sin cambios (el cambio no agrega modelos).
- Traducciones: ningún texto nuevo usa `gettext` (los comandos de gestión de Orion no
  traducen su salida de consola, igual que `orion_clear_page_cache` o
  `orion_purge_submissions`); no hay nada para traducir.
