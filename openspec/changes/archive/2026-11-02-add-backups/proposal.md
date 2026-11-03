## Why

Hoy un sitio en producción no tiene forma de respaldarse ni de moverse a otro servidor sin
copiar la base de datos y los medios a mano. La especificación pide un comando que empaquete
base de datos y medios en un archivo, lo inspeccione y lo restaure en otro servidor. Es el
cambio 3 de la Fase 5 (seguridad y operación), después de acceso (`add-login-protection`) y
headers y HTTPS (`add-security-headers`).

## What Changes

- **Backup en un solo archivo:** comando que vuelca la base de datos con `pg_dump`
  (PostgreSQL) o `mysqldump` (MySQL/MariaDB), según el motor de `DATABASE_URL`, y empaqueta
  ese volcado junto con `MEDIA_ROOT` y `ORION_FORMS_PRIVATE_ROOT` (adjuntos de formularios,
  privados y fuera de `MEDIA_ROOT`) en un único archivo `.tar.gz` con un manifiesto (motor,
  versión de Orion y de Django, fecha, tamaños). Sin las claves secretas: viven solo en
  variables de entorno y nunca llegan a la base de datos.
- **Inspección sin tocar nada:** comando que lee el manifiesto de un archivo de backup y
  muestra motor, fecha, versión y tamaños, para confirmar qué se restauraría sin aplicar
  ningún cambio.
- **Restauración en otro servidor:** comando que, a partir de ese archivo, repuebla la base
  de datos (`pg_restore`/`psql` o `mysql`, según el motor del backup, igual al del servidor
  destino) y copia los medios y adjuntos a los directorios configurados. Es destructivo (pisa
  la base de datos y los archivos del servidor destino): pide confirmación explícita salvo
  que se pase una bandera para automatizarlo.
- **Documentación:** README con el flujo de backup, verificación y restauración entre
  servidores, y los binarios cliente que cada motor necesita en el servidor.

**Fuera del alcance:** programar backups automáticos (lo ve la tarea de cron de la fase,
cuando se defina dónde se guardan y por cuánto tiempo); subir el archivo a almacenamiento
externo (S3, FTP) o cifrarlo; restaurar entre motores distintos (backup de PostgreSQL
restaurado en MySQL o viceversa); backups incrementales o parciales (una sola tabla o
colección de páginas); una interfaz en el admin de Wagtail.

## Capabilities

### New Capabilities
- `backups`: comandos de gestión para empaquetar base de datos y medios en un archivo,
  inspeccionarlo y restaurarlo en otro servidor.

### Modified Capabilities
(ninguna: no cambia ningún requisito existente)

## Impact

- **Código nuevo:** comandos de gestión (`orion_backup`, `orion_inspect_backup`,
  `orion_restore`), utilidades para volcar/restaurar por motor y empaquetar el archivo,
  pruebas.
- **Código modificado:** README, `.env.example` si se agrega alguna variable de
  configuración, CHANGELOG.
- **Dependencias nuevas:** ninguna prevista (ver justificación en design.md).
- **Migraciones:** ninguna.
- **Compatibilidad:** no afecta contenido ni StreamField existente; el formato del archivo de
  backup es propio de este cambio, sin versiones previas que migrar.
- **Operación:** requiere los binarios cliente de PostgreSQL o MySQL instalados en el
  servidor donde corre el comando (ya asumido por las guías de deploy de la fase); un
  backup contiene todo el contenido de la base de datos y los adjuntos privados de
  formularios, así que debe tratarse como dato sensible.
