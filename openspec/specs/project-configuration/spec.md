# project-configuration Specification

## Purpose
Define cómo un proyecto construido sobre Orion obtiene su configuración del entorno,
qué valores son obligatorios y qué configuraciones inseguras impiden que el sitio arranque.

## Requirements

### Requirement: Configuration comes from environment variables
El sistema SHALL leer la clave secreta, el modo debug, los hosts permitidos, la conexión a
la base de datos, el idioma, la zona horaria y la configuración de email desde variables de
entorno, sin valores secretos escritos en el código.

#### Scenario: Database configured by URL
- **WHEN** la variable `DATABASE_URL` apunta a una base PostgreSQL o MySQL
- **THEN** el sistema se conecta a esa base sin otra configuración

#### Scenario: Comma-separated hosts
- **WHEN** `ALLOWED_HOSTS` vale `ejemplo.com,www.ejemplo.com`
- **THEN** el sistema acepta pedidos para ambos hosts y rechaza los demás

### Requirement: Debug mode is off by default
El sistema SHALL funcionar con el modo debug apagado salvo que una variable de entorno lo
encienda explícitamente.

#### Scenario: Variable absent
- **WHEN** `DEBUG` no está definida
- **THEN** el modo debug está apagado

#### Scenario: Explicit opt-in
- **WHEN** `DEBUG` vale `true`
- **THEN** el modo debug está encendido

### Requirement: Secret key is mandatory outside debug
El sistema MUST negarse a arrancar sin una clave secreta cuando el modo debug está apagado.

#### Scenario: Production without secret key
- **WHEN** `DEBUG` está apagado y `SECRET_KEY` no está definida
- **THEN** el arranque falla con un mensaje que nombra la variable faltante

#### Scenario: Local development
- **WHEN** `DEBUG` está encendido y `SECRET_KEY` no está definida
- **THEN** el sistema arranca con una clave de desarrollo no apta para producción

### Requirement: Secure defaults outside debug
Con el modo debug apagado, el sistema SHALL enviar las cookies de sesión y de CSRF solo por
HTTPS, marcar la cookie de sesión como no accesible desde JavaScript y prohibir que otros
sitios muestren el sitio dentro de un marco.

#### Scenario: Production cookies
- **WHEN** el modo debug está apagado
- **THEN** las cookies de sesión y CSRF se marcan como seguras y la de sesión como HttpOnly

### Requirement: Contradictory email security is rejected
El sistema MUST rechazar al arrancar una configuración de email que active SSL y TLS a la vez.

#### Scenario: SSL and TLS both enabled
- **WHEN** `EMAIL_USE_SSL` y `EMAIL_USE_TLS` valen `true`
- **THEN** la verificación de arranque informa un error que indica usar solo uno

#### Scenario: Only one enabled
- **WHEN** solo una de las dos vale `true`
- **THEN** la verificación de arranque no informa errores de email

### Requirement: Invalid boolean values are rejected
El sistema MUST rechazar valores booleanos de entorno que no sean reconocibles en lugar de
interpretarlos en silencio.

#### Scenario: Typo in a boolean
- **WHEN** `DEBUG` vale `ture`
- **THEN** el arranque falla con un mensaje que nombra la variable y los valores aceptados

### Requirement: Email uses TLS unless SSL is chosen
El sistema SHALL usar TLS para el email cuando ninguna variable de entorno elige otro
modo, y MUST dejar de usar TLS cuando se activa SSL sin indicar TLS.

#### Scenario: Neither variable defined
- **WHEN** `EMAIL_USE_TLS` y `EMAIL_USE_SSL` no están definidas
- **THEN** el email usa TLS y no usa SSL

#### Scenario: Only SSL enabled
- **WHEN** `EMAIL_USE_SSL` vale `true` y `EMAIL_USE_TLS` no está definida
- **THEN** el email usa SSL, no usa TLS y la verificación de arranque no informa errores
  de email

#### Scenario: TLS explicitly disabled
- **WHEN** `EMAIL_USE_TLS` vale `false` y `EMAIL_USE_SSL` no está definida
- **THEN** el email no usa TLS ni SSL
