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
HTTPS, marcar la cookie de sesión como no accesible desde JavaScript, prohibir que otros
sitios muestren el sitio dentro de un marco, redirigir HTTP a HTTPS y mandar HSTS.

#### Scenario: Production cookies
- **WHEN** el modo debug está apagado
- **THEN** las cookies de sesión y CSRF se marcan como seguras y la de sesión como HttpOnly

#### Scenario: Production HTTPS
- **WHEN** el modo debug está apagado
- **THEN** la redirección a HTTPS está activa y HSTS dura un año

#### Scenario: Development
- **WHEN** el modo debug está encendido
- **THEN** no hay redirección a HTTPS ni HSTS

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

### Requirement: A text variable with a default falls back when present but empty
Cuando una variable de entorno de texto tiene un valor por defecto no vacío, el sistema
SHALL usar ese default tanto si la variable está ausente como si está presente pero
vacía (o solo espacios).

#### Scenario: Variable absent
- **WHEN** `ORION_SEARCH_CONFIG` no está definida y `LANGUAGE_CODE` vale `es`
- **THEN** la configuración de búsqueda de PostgreSQL es `spanish`

#### Scenario: Variable present and empty
- **WHEN** `ORION_SEARCH_CONFIG` está definida como cadena vacía y `LANGUAGE_CODE` vale
  `es`
- **THEN** la configuración de búsqueda de PostgreSQL es `spanish`, igual que si la
  variable estuviera ausente

#### Scenario: Variable present with an explicit value
- **WHEN** `ORION_SEARCH_CONFIG` vale `simple`
- **THEN** la configuración de búsqueda de PostgreSQL es `simple`

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

### Requirement: The visitor's address is read behind trusted proxies
El sistema SHALL tomar la IP del visitante de `REMOTE_ADDR` cuando
`ORION_TRUSTED_PROXIES` vale 0 (por defecto). Con un valor N mayor que 0 SHALL tomarla de
`X-Forwarded-For`, contando N direcciones desde la derecha, y MUST ignorar las que el
visitante agregue a la izquierda. Si el header tiene menos direcciones que N, SHALL usar
la primera. El límite de intentos de login y el de envíos de formularios SHALL usar esa
IP.

#### Scenario: Directly exposed
- **WHEN** `ORION_TRUSTED_PROXIES` vale 0 y llega `X-Forwarded-For: 1.2.3.4`
- **THEN** la IP es la de `REMOTE_ADDR` y el header se ignora

#### Scenario: Behind Nginx
- **WHEN** `ORION_TRUSTED_PROXIES` vale 1 y llega `X-Forwarded-For: 9.9.9.9, 1.2.3.4`
- **THEN** la IP es `1.2.3.4`, la que agregó Nginx, aunque el visitante haya inventado
  `9.9.9.9`

### Requirement: A project's env file is read without pipenv
El sistema SHALL ofrecer a los proyectos una forma de cargar las variables de un archivo
`.env` antes de leer los ajustes, sin depender de cómo se lance el proceso. Una variable
ya definida en el entorno MUST conservar su valor, y la ausencia del archivo MUST NOT ser
un error.

#### Scenario: Variable only in the file
- **WHEN** `SECRET_KEY` está en el `.env` y no en el entorno
- **THEN** los ajustes usan el valor del archivo

#### Scenario: Variable in both places
- **WHEN** `DEBUG` vale `false` en el entorno y `true` en el `.env`
- **THEN** los ajustes usan `false`

#### Scenario: No file
- **WHEN** el proyecto no tiene `.env` y las variables están en el entorno
- **THEN** los ajustes se cargan sin error

#### Scenario: Values with special characters
- **WHEN** `SECRET_KEY` en el `.env` contiene `#`, `$`, `(` o `=`
- **THEN** los ajustes reciben el valor completo y sin cambios

### Requirement: Server errors are logged outside debug
Fuera de debug, el sistema SHALL escribir en la salida de errores del proceso cada error
del servidor, con su traza, y los avisos de la aplicación, sin depender de que haya
destinatarios de email configurados.

#### Scenario: Unhandled error in a request
- **WHEN** una vista lanza una excepción no controlada con `DEBUG` apagado
- **THEN** la respuesta es 500 y la traza de la excepción aparece en la salida de errores

#### Scenario: Error logged by Orion
- **WHEN** falla el envío del aviso de un formulario con `DEBUG` apagado
- **THEN** el error aparece en la salida de errores

### Requirement: Not-found requests stay out of the error log
El sistema MUST NOT escribir en la salida de errores las respuestas 404 ni otras
respuestas 4xx, para que el tráfico de bots no tape los errores reales.

#### Scenario: Missing page
- **WHEN** una visita pide una ruta inexistente con `DEBUG` apagado
- **THEN** la salida de errores no registra esa petición
