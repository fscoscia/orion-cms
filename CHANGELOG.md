# Changelog

Todos los cambios relevantes de Orion se registran en este archivo. El formato sigue
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones siguen
[Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added

- Paquete `orion` instalable desde GitHub, con extras `postgres` y `mysql`.
- Ajustes base configurables por variables de entorno, con validación al arrancar (clave
  secreta obligatoria fuera de debug, booleanos inválidos, ruta del admin) y valores
  seguros por defecto fuera de debug.
- Chequeo de sistema `orion.E001` para SSL y TLS de email activados a la vez.
- Endpoint de salud en `/health/`.
- Rutas base: admin en ruta configurable (`ORION_ADMIN_PATH`), documentos y páginas.
- Plantilla base `orion/base.html` y plantilla para páginas genéricas.
- Proyecto de ejemplo, pruebas en PostgreSQL y MySQL, Ruff, pre-commit y
  `docker-compose.yml` opcional.

### Changed

- El email usa TLS por defecto salvo que `EMAIL_USE_SSL` esté activado. **Atención:** un
  proyecto con `EMAIL_HOST` cuyo servidor SMTP no soporta STARTTLS debe definir
  `EMAIL_USE_TLS=false`.
- Sin `LocaleMiddleware`: el sitio se muestra siempre en `LANGUAGE_CODE`, sin importar el
  idioma del navegador (incluida la pantalla de login del admin). Volverá con las URLs por
  idioma de la Fase 1.

### Fixed

- Pruebas de la ruta del admin que dependían del orden de ejecución, y pruebas de ajustes
  que dependían de las variables del `.env` de quien las corre.
- `.env.example` incluye `DATABASE_CONN_MAX_AGE`; una prueba verifica que lista toda
  variable que leen los ajustes base.
- Documentado que `pipenv run` carga `.env` pisando las variables del shell, y cómo
  apuntar las pruebas a las bases de Docker.
