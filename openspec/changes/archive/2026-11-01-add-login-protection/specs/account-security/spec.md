## Purpose
Define cómo se protege el ingreso al admin: el límite de intentos de login y su
desbloqueo, la recuperación de la contraseña por email y el cierre de las sesiones
abiertas cuando cambian las credenciales de una cuenta.

## ADDED Requirements

### Requirement: Failed logins lock the user out for a while
Después de `ORION_LOGIN_FAILURE_LIMIT` intentos fallidos (5 por defecto) con el mismo
usuario desde la misma IP, el login SHALL rechazar ese usuario desde esa IP durante
`ORION_LOGIN_LOCKOUT_MINUTES` minutos (15 por defecto), aun con la contraseña correcta, y
mostrar una pantalla en el estilo del admin que dice cuánto esperar, con código 429. El
mismo usuario desde otra IP y otros usuarios desde la misma IP MUST poder seguir
ingresando. Un login correcto SHALL borrar los intentos fallidos de ese usuario. El
sistema MUST NOT guardar un registro de cada ingreso.

#### Scenario: Fifth wrong password
- **WHEN** alguien escribe mal la contraseña de "ana" 5 veces desde la misma IP
- **THEN** el sexto intento, aunque la contraseña sea correcta, muestra que la cuenta está
  bloqueada por 15 minutos

#### Scenario: Other address
- **WHEN** "ana" está bloqueada desde una IP y entra desde otra con su contraseña
- **THEN** ingresa normalmente

#### Scenario: Lock expires
- **WHEN** pasan 15 minutos desde el bloqueo
- **THEN** "ana" puede volver a ingresar con su contraseña

#### Scenario: Success clears the count
- **WHEN** "ana" se equivoca 4 veces y después ingresa bien
- **THEN** sus intentos fallidos vuelven a cero

### Requirement: A locked account can be unlocked
Quien administra el servidor SHALL poder desbloquear un usuario o una IP antes de que
venza el bloqueo, con un comando.

#### Scenario: Unlock by command
- **WHEN** se corre el comando de desbloqueo con el usuario "ana"
- **THEN** "ana" puede ingresar de inmediato

### Requirement: Passwords can be recovered by email
El login del admin SHALL ofrecer recuperar la contraseña cuando hay un servidor de email
configurado o el sitio está en desarrollo, y MUST NOT ofrecerlo en producción sin servidor
de email. El enlace que llega por email SHALL servir una sola vez y vencer. La respuesta
MUST NOT revelar si el email pertenece a una cuenta. Después de cambiar la contraseña, el
ingreso SHALL seguir pidiendo el segundo factor.

#### Scenario: Recovery
- **WHEN** "ana" pide recuperar su contraseña con su email
- **THEN** recibe un enlace, elige una contraseña nueva, y el enlace ya no sirve otra vez

#### Scenario: Unknown email
- **WHEN** alguien pide recuperar con un email que no es de ninguna cuenta
- **THEN** ve la misma confirmación y no se manda ningún email

#### Scenario: No mail server
- **WHEN** el sitio está en producción sin `EMAIL_HOST`
- **THEN** el login no muestra la opción de recuperar la contraseña

### Requirement: Changing credentials signs out the other sessions
Cuando cambia la contraseña o el email de una cuenta, todas sus sesiones abiertas SHALL
cerrarse, salvo la sesión desde la que el usuario hizo el cambio en su propia cuenta. Las
sesiones abiertas antes de este cambio MUST NOT cerrarse solo por no tener el dato nuevo.

#### Scenario: Email changed by the user
- **WHEN** "ana" tiene el admin abierto en dos equipos y cambia su email desde uno
- **THEN** el otro equipo vuelve al login y el que hizo el cambio sigue adentro

#### Scenario: Email changed by a superuser
- **WHEN** un superusuario cambia el email de "ana" desde Usuarios
- **THEN** todas las sesiones de "ana" se cierran y la del superusuario sigue abierta

#### Scenario: Password changed
- **WHEN** "ana" cambia su contraseña desde un equipo
- **THEN** el otro equipo vuelve al login y el que hizo el cambio sigue adentro
