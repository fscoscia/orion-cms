# mcp-api-keys Specification

## Purpose
Define las claves de API con las que un cliente remoto usa el MCP de un sitio Orion: cómo se
crean, qué guardan, cuándo dejan de servir y quién las administra desde el admin.

## Requirements

### Requirement: A key is tied to a user and a scope
Cada clave SHALL tener un nombre, un usuario de Wagtail, un alcance (`read-only`, `draft-only`
o `full`) y, opcionalmente, un vencimiento, y SHALL registrar quién la creó, cuándo, su último
uso y su revocación. El usuario MUST estar activo y MUST NOT ser superusuario. Solo un
superusuario SHALL poder crear una clave `full`.

#### Scenario: Superuser
- **WHEN** un Administrador intenta crear una clave para un superusuario
- **THEN** el formulario la rechaza con un mensaje que lo explica

#### Scenario: Inactive user
- **WHEN** se elige un usuario inactivo
- **THEN** el formulario lo rechaza

#### Scenario: Full key by an Administrator
- **WHEN** un Administrador que no es superusuario envía el formulario con el alcance `full`
- **THEN** el formulario lo rechaza y no se crea ninguna clave

#### Scenario: Full key by a superuser
- **WHEN** un superusuario crea una clave `full` para un usuario activo que no es superusuario
- **THEN** la clave se crea y el token se muestra una sola vez

### Requirement: The token is shown once and only its hash is stored
Al crear una clave el sistema SHALL generar un token aleatorio de alta entropía con el prefijo
`orion_mcp_`, mostrarlo una sola vez y guardar solo su hash SHA-256 y un prefijo corto para
identificarla. El token MUST NOT guardarse ni escribirse en ningún registro.

#### Scenario: Created
- **WHEN** se crea una clave
- **THEN** la pantalla muestra el token completo una vez y la base de datos no lo contiene

#### Scenario: Listed later
- **WHEN** se vuelve a abrir la lista
- **THEN** solo se ve el prefijo de la clave

### Requirement: A key that cannot be used is refused without saying why
Una petición con una clave ausente, desconocida, vencida, revocada o ligada a un usuario
inactivo o borrado SHALL recibir 401 con `WWW-Authenticate: Bearer` y el mismo mensaje en todos
los casos, de modo que no revele cuál fue la causa.

#### Scenario: Same answer
- **WHEN** se prueba una clave revocada y una que nunca existió
- **THEN** las dos respuestas son idénticas

#### Scenario: User deactivated
- **WHEN** se desactiva al usuario de una clave
- **THEN** la clave deja de servir en la petición siguiente

### Requirement: Use is recorded without a write per request
Cada petición autenticada SHALL actualizar la fecha de último uso de su clave, como mucho una
vez por minuto por clave.

#### Scenario: Frequent calls
- **WHEN** una clave hace diez peticiones en un minuto
- **THEN** su último uso se escribe una sola vez

### Requirement: Administrators manage keys from the admin
Una pantalla en el menú de Ajustes SHALL permitir a los Administradores y superusuarios listar
las claves (nombre, usuario, alcance, prefijo, vencimiento, último uso, estado), crear una y
revocarla. Un Administrador SHALL poder revocar una clave de cualquier alcance, pero el
formulario solo ofrece `full` a superusuarios. Un Editor MUST NOT verla ni poder llamar a sus
URLs.

#### Scenario: Administrator
- **WHEN** un Administrador abre la pantalla
- **THEN** ve las claves y puede crear y revocar

#### Scenario: Editor
- **WHEN** un Editor abre la dirección de la pantalla
- **THEN** recibe un error de permiso y el menú no se la muestra

#### Scenario: Scope choices
- **WHEN** un Administrador que no es superusuario abre el formulario de creación
- **THEN** el alcance `full` no aparece entre las opciones

#### Scenario: Revoking a full key
- **WHEN** un Administrador que no es superusuario revoca una clave `full`
- **THEN** la clave queda revocada

### Requirement: Revoking stops the key at once
Una clave revocada MUST dejar de servir en la petición siguiente y su revocación SHALL quedar
registrada con la fecha.

#### Scenario: Revoke
- **WHEN** un Administrador revoca una clave
- **THEN** la siguiente petición con ella recibe 401
