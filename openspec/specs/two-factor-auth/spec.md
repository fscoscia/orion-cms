# two-factor-auth Specification

## Purpose
Define el segundo factor obligatorio para entrar al admin: cómo se configura la primera
vez, cómo se verifica en cada ingreso, cómo se administran los códigos de respaldo y cómo se
recupera el acceso si se pierde el teléfono.

## Requirements

### Requirement: Every admin user must verify a second factor
Después de la contraseña, todo usuario con acceso al admin SHALL verificar un código de su
app autenticadora o un código de respaldo antes de ver cualquier pantalla del admin. El
sitio público MUST NOT pedirlo.

#### Scenario: Sign in with a code
- **WHEN** un editor con 2FA configurado ingresa usuario y contraseña
- **THEN** el admin le pide el código y, con un código válido, muestra el panel de inicio

#### Scenario: Skipping the code
- **WHEN** un usuario que ingresó la contraseña pero no el código abre una pantalla del
  admin
- **THEN** el admin lo lleva a la pantalla del código

#### Scenario: Public site
- **WHEN** ese usuario abre una página del sitio
- **THEN** la página se muestra sin pedir el código

### Requirement: Setting up the second factor is mandatory
Un usuario del admin sin 2FA configurado SHALL configurarlo en su primer ingreso: ve un
código QR y la clave para escribir a mano, confirma con un código de su app y recibe 10
códigos de respaldo, que se muestran una sola vez. Hasta confirmar MUST NOT ver otras
pantallas del admin.

#### Scenario: First sign-in
- **WHEN** un usuario sin 2FA ingresa su contraseña
- **THEN** ve la pantalla de configuración con el código QR

#### Scenario: Confirming the app
- **WHEN** escribe el código que muestra su app
- **THEN** el admin muestra sus 10 códigos de respaldo y después el panel de inicio

### Requirement: Backup codes work once
Cada código de respaldo SHALL servir para un solo ingreso. El usuario SHALL poder
regenerarlos desde su cuenta, lo que invalida los anteriores.

#### Scenario: Reusing a backup code
- **WHEN** alguien ingresa con un código de respaldo y después intenta usarlo de nuevo
- **THEN** el segundo intento es rechazado

### Requirement: Repeated wrong codes are slowed down
Después de códigos incorrectos seguidos, el admin SHALL rechazar los intentos siguientes
durante una espera que crece con cada error, aun si el código es correcto.

#### Scenario: Guessing codes
- **WHEN** alguien escribe varios códigos incorrectos seguidos
- **THEN** el admin rechaza el siguiente intento e indica que espere

### Requirement: Administrators can reset a lost second factor
Un Administrador o un superusuario SHALL poder resetear el 2FA de otro usuario, que lo
vuelve a configurar en su próximo ingreso. Un Administrador MUST NOT poder resetear el 2FA
de un superusuario, y un Editor MUST NOT poder resetear el de nadie.

#### Scenario: Lost phone
- **WHEN** un Administrador resetea el 2FA de una editora
- **THEN** en su próximo ingreso la editora configura el 2FA de nuevo

### Requirement: Disabling the requirement is visible
El requisito SHALL poder desactivarse por configuración para desarrollo local, y los
chequeos del sistema SHALL avisar si está desactivado con `DEBUG` apagado.

#### Scenario: Production without 2FA
- **WHEN** `ORION_2FA_REQUIRED` es falso y `DEBUG` está apagado
- **THEN** `manage.py check` muestra un aviso
