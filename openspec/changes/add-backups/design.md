## Context

Ver proposal.md - Why. `DATABASES["default"]` ya trae motor, nombre, usuario, contraseña,
host y puerto (resueltos por `dj_database_url` desde `DATABASE_URL`); `MEDIA_ROOT` y
`ORION_FORMS_PRIVATE_ROOT` (resuelto por `orion.forms.storage`) son los dos árboles de
archivos del sitio. No hay todavía ningún comando que toque el sistema de archivos fuera de
esos directorios ni que invoque binarios externos: `orion.core.management.commands` solo
tiene comandos que operan sobre el ORM o la caché.

## Goals / Non-Goals

**Goals:**
- Un archivo por backup, autocontenido y verificable sin tocar la base de datos de destino.
- Mismo comando sirve para PostgreSQL y MySQL/MariaDB, sin que el operador arme los
  parámetros de `pg_dump`/`mysqldump` a mano.
- Fallar temprano y con un mensaje claro: herramienta faltante, motor distinto, archivo
  incompleto, falta de confirmación.

**Non-Goals:**
- Migrar datos entre motores distintos (PostgreSQL ↔ MySQL): formatos de volcado
  incompatibles; fuera de alcance (ver proposal.md).
- Progreso incremental o reanudable de un backup o restauración interrumpida.
- Compresión o cifrado adicional del archivo más allá de la compresión de `tar.gz`.

## Decisions

### 1. Binarios cliente del motor por `subprocess`, sin dependencia nueva

`pg_dump`/`pg_restore` (PostgreSQL) y `mysqldump`/`mysql` (MySQL/MariaDB) ya son lo que pide
la especificación funcional. Se invocan con `subprocess.run`, igual que cualquier guía de
deploy asume tener el cliente del motor instalado. Alternativa descartada: `django-dbbackup`
(empaqueta algo similar, pero agrega una dependencia con su propio formato de storage
backends cuando acá alcanza con un archivo local y los dos binarios que la base de datos ya
necesita en el servidor).

- PostgreSQL: `pg_dump --format=custom --no-owner --no-privileges` (formato comprimido y
  flexible en el orden de restauración) a un archivo temporal; restauración con
  `pg_restore --clean --if-exists --no-owner --no-privileges --dbname=<NAME>` (el `--clean`
  resuelve el reemplazo de contenido existente sin exigir una base vacía).
- MySQL/MariaDB: `mysqldump --single-transaction --routines --triggers --events
  --add-drop-table --default-character-set=utf8mb4` a un archivo temporal (SQL plano, ya
  trae su propio `DROP TABLE` por tabla); restauración con `mysql < archivo.sql`.
- La contraseña no va en la línea de comandos (aparecería en `ps`): PostgreSQL la recibe por
  la variable de entorno `PGPASSWORD` del subproceso; MySQL, por `MYSQL_PWD`. Host, puerto,
  usuario y nombre de base salen de `DATABASES["default"]`.
- Si el binario no está (`FileNotFoundError` de `subprocess`), el comando lo informa por su
  nombre y motor antes de escribir nada.

### 2. Un `.tar.gz` con manifiesto, sin dependencia nueva

`tarfile` y `gzip` (ambos de la biblioteca estándar) alcanzan: no hace falta `zipfile` ni una
dependencia de compresión de terceros. Estructura del archivo:

```
manifest.json         # engine, orion_version, django_version, created_at, sizes
database.dump          # pg_dump -Fc, o el .sql de mysqldump
media/                  # copia de MEDIA_ROOT
forms_private/          # copia de ORION_FORMS_PRIVATE_ROOT
```

El volcado de la base se escribe primero a un archivo temporal (`tempfile`) y se agrega al
`tar` con `add()`, que transmite el contenido sin duplicarlo en memoria; igual para `media/`
y `forms_private/`, agregados árbol por árbol. El archivo temporal se borra al terminar,
también si el comando falla a mitad de camino.

### 3. Comandos de gestión en `orion.core`, sin modelos nuevos

`orion.core.backups` (módulo con las funciones de volcar, empaquetar, inspeccionar y
restaurar, reusadas por los tres comandos) y:
- `manage.py orion_backup <archivo>`
- `manage.py orion_inspect_backup <archivo>`
- `manage.py orion_restore <archivo>`

No hay modelo ni migración: no hay nada que una base de datos deba recordar sobre sus
propios backups. Siguen el patrón de `orion_clear_page_cache` y `orion_generate_renditions`:
comandos de `orion.core` que no son específicos de un dominio con modelos propios.

### 4. Confirmación de la restauración, con el patrón nativo de Django

`BaseCommand` con el argumento `--noinput` (el mismo nombre que usan `flush` o `migrate`) y,
sin él, una confirmación por `input()` solo si `self.stdin.isatty()`; sin terminal y sin
`--noinput`, el comando se niega a correr en lugar de asumir una respuesta. El motor del
manifiesto se compara con el de `DATABASES["default"]` del servidor destino antes de pedir
confirmación: un motor distinto corta ahí, sin preguntar nada.

### 5. Adjuntos privados de formularios dentro del backup

La especificación dice "base de datos y medios"; `ORION_FORMS_PRIVATE_ROOT` queda fuera de
`MEDIA_ROOT` a propósito (privacidad, ver `openspec/specs/forms`), pero sus archivos son
parte del contenido del sitio igual que los medios: sin ellos, una restauración deja envíos
de formularios con adjuntos rotos. Se agrega como una carpeta más del archivo, documentado
en proposal.md como ampliación del alcance literal.

### Dependencias

Ninguna nueva. `tarfile`, `gzip`, `tempfile`, `subprocess` y `json` son de la biblioteca
estándar; `pg_dump`/`pg_restore`/`mysqldump`/`mysql` son los binarios cliente del motor que
el servidor ya necesita para administrar su base de datos.

### Migraciones

Ninguna.

## Risks / Trade-offs

- [El backup contiene todo el contenido de la base y los adjuntos privados de formularios]
  → Es un archivo sensible: el comando lo crea con permisos `0600` y el README advierte no
  subirlo a git ni dejarlo en un directorio servido por el sitio.
- [`pg_restore --clean` o `mysqldump --add-drop-table` sobre una base con datos] → Es
  intencional (restaurar reemplaza lo que había); la confirmación explícita y el chequeo de
  motor son la salvaguarda, no el contenido de la base destino.
- [Un backup muy grande (medios de varios GB)] → `tarfile` transmite archivo por archivo sin
  cargarlo entero en memoria; el tiempo de backup/restauración queda limitado por disco y
  red, no por este diseño.
- [Versión de `pg_dump`/`mysqldump` del servidor distinta a la del destino] → Los formatos
  son compatibles entre versiones menores recientes del mismo motor; una restauración entre
  versiones mayores muy distintas queda fuera de alcance y el manifiesto deja registrada la
  versión de referencia para diagnosticar.
