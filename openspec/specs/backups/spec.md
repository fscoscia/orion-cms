# backups Specification

## Purpose

Permite empaquetar la base de datos y los medios de un sitio en un solo archivo,
inspeccionar ese archivo sin tocar nada y restaurarlo en otro servidor.

## Requirements

### Requirement: A command packages the database and media into one file
Un comando SHALL volcar la base de datos configurada (`DATABASE_URL`) con la herramienta
del motor correspondiente (PostgreSQL o MySQL/MariaDB) y empaquetarla junto con
`MEDIA_ROOT` y los adjuntos privados de formularios en un único archivo, con un manifiesto
que registre el motor, la fecha, la versión de Orion y de Django, y el tamaño de cada
parte.

#### Scenario: PostgreSQL
- **WHEN** `DATABASE_URL` apunta a una base PostgreSQL y se corre el comando de backup
- **THEN** el archivo resultante contiene el volcado de esa base, los medios, los adjuntos
  privados de formularios y el manifiesto

#### Scenario: MySQL o MariaDB
- **WHEN** `DATABASE_URL` apunta a una base MySQL o MariaDB y se corre el comando de backup
- **THEN** el archivo resultante contiene el volcado de esa base, los medios, los adjuntos
  privados de formularios y el manifiesto

#### Scenario: Sin medios ni adjuntos
- **WHEN** `MEDIA_ROOT` o el directorio de adjuntos privados no tienen archivos
- **THEN** el backup se completa igual, sin esas partes vacías

### Requirement: A backup never contains secrets
El archivo de backup MUST NOT contener claves secretas ni otras variables de entorno: solo
lo que ya está en la base de datos y en los directorios de medios y adjuntos.

#### Scenario: Clave secreta ausente
- **WHEN** se inspecciona el contenido de un backup
- **THEN** no aparece `SECRET_KEY` ni ninguna otra variable de entorno

### Requirement: A command inspects a backup without changing anything
Un comando SHALL leer el manifiesto de un archivo de backup y mostrar motor, fecha,
versiones y tamaños, sin modificar la base de datos, los medios ni el archivo inspeccionado.

#### Scenario: Backup válido
- **WHEN** se inspecciona un archivo de backup completo
- **THEN** el comando muestra motor, fecha, versiones y tamaños, y termina sin tocar la
  base de datos ni los archivos del servidor

#### Scenario: Archivo inválido o incompleto
- **WHEN** se inspecciona un archivo que no es un backup de Orion o le falta una parte
- **THEN** el comando falla con un mensaje que explica qué falta, sin tocar nada

### Requirement: A command restores a backup on another server
Un comando SHALL repoblar la base de datos del servidor destino con el volcado del backup
y copiar los medios y los adjuntos privados de formularios a los directorios configurados
en ese servidor, usando la herramienta del motor que indica el manifiesto.

#### Scenario: Restauración completa
- **WHEN** se restaura un backup válido en un servidor con el mismo motor de base de datos
- **THEN** la base de datos, los medios y los adjuntos de formularios quedan como en el
  servidor de origen al momento del backup

#### Scenario: Motor distinto
- **WHEN** el manifiesto del backup indica un motor distinto al de `DATABASE_URL` en el
  servidor destino
- **THEN** la restauración se rechaza antes de tocar la base de datos, con un mensaje que
  nombra ambos motores

### Requirement: Restoring requires explicit confirmation
Como la restauración reemplaza la base de datos y los archivos del servidor destino, el
comando SHALL pedir confirmación explícita antes de aplicar cualquier cambio, y SHALL
aceptar una bandera para saltear esa confirmación en uso automatizado.

#### Scenario: Sin confirmar
- **WHEN** se corre el comando de restauración sin confirmar y sin la bandera de
  automatización
- **THEN** no se modifica la base de datos ni los archivos, y el comando explica cómo
  confirmar o automatizar

#### Scenario: Confirmado
- **WHEN** se confirma la restauración, o se corre con la bandera de automatización
- **THEN** la restauración se aplica

### Requirement: Missing database client tools fail clearly
Si el binario del motor (`pg_dump`, `pg_restore`, `psql`, `mysqldump` o `mysql`) no está
disponible en el servidor, el comando de backup o de restauración SHALL fallar con un
mensaje que nombre la herramienta faltante, antes de dejar archivos o datos a medio
escribir.

#### Scenario: Herramienta no instalada
- **WHEN** el binario que corresponde al motor configurado no está en el `PATH` del
  servidor
- **THEN** el comando falla con un mensaje que nombra esa herramienta, sin dejar un backup
  ni una base de datos a medio escribir
