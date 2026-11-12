## MODIFIED Requirements

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
