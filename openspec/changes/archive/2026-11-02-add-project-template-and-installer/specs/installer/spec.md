## Purpose

Deja un sitio construido sobre Orion listo para usar con un solo comando: requisitos
validados, base migrada, administrador creado, idioma base confirmado y contenido de
ejemplo cargado.

## ADDED Requirements

### Requirement: A command validates the database requirements before migrating
Un comando de gestión SHALL verificar, antes de migrar, que el driver de base de datos que
corresponde al motor de `DATABASE_URL` está instalado y que la base responde, y MUST
fallar con un mensaje claro (qué falta o qué pasó) sin intentar migrar cuando alguna de
esas condiciones no se cumple.

#### Scenario: Missing database driver
- **WHEN** `DATABASE_URL` apunta a un motor cuyo driver de Python no está instalado
- **THEN** el comando falla antes de migrar, con un mensaje que nombra el driver o el
  extra de instalación que falta

#### Scenario: Database unreachable
- **WHEN** la base configurada no responde (servidor caído, credenciales inválidas)
- **THEN** el comando falla antes de migrar, con un mensaje que explica que no pudo
  conectarse

### Requirement: The command installs a site in one step
Superadas las validaciones, el comando SHALL migrar la base, crear un superusuario
administrador, confirmar el idioma base configurado y cargar el contenido de ejemplo de
Orion.

#### Scenario: Fresh installation
- **WHEN** se corre el comando sobre una base vacía con los requisitos cumplidos
- **THEN** la base queda migrada, existe un superusuario, se informa el idioma base
  configurado y existen los formularios de ejemplo

#### Scenario: Automated installation
- **WHEN** se corre con las opciones de `createsuperuser --noinput` y las variables
  `DJANGO_SUPERUSER_*`
- **THEN** el comando se completa sin pedir nada por teclado

### Requirement: Running the installer again does not duplicate or break anything
Correr el comando sobre un sitio ya instalado SHALL dejarlo como estaba, sin duplicar el
contenido de ejemplo ni fallar por la migración o el superusuario ya existentes.

#### Scenario: Run twice
- **WHEN** el comando se corre una segunda vez sobre el mismo sitio
- **THEN** la base sigue migrada, el contenido de ejemplo no se duplica y el comando
  informa en lugar de fallar si el superusuario ya existe
