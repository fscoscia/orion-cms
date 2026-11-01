# integrations Specification

## Purpose
Define la pantalla de Integraciones del admin: el estado de cada integración, la prueba y
la guía para activarla, el registro de los envíos de email, el aviso en el panel cuando
los emails no salen y el checklist de alta de cliente.

## Requirements

### Requirement: The Integrations screen shows each integration's state
El admin SHALL tener una pantalla Integraciones en el menú Configuración, visible solo para
Administradores y superusuarios; a cualquier otro usuario MUST negarle el acceso. SHALL
mostrar el email (SMTP) con uno de estos estados: apagado (sin `EMAIL_HOST`), sin probar
(configurado y sin envíos registrados), activo (el último envío salió) o con errores (el
último envío falló o la configuración está incompleta: usuario sin contraseña, contraseña
sin usuario o el remitente por defecto `webmaster@localhost`). SHALL mostrar el servidor,
el puerto, el usuario, la seguridad (TLS, SSL o ninguna), el remitente, la fecha del último
envío correcto y el último error. La contraseña MUST NOT mostrarse: solo si está cargada o
falta. SHALL mostrar también el proveedor de mapas en uso y, si es OpenStreetMap, que su
política de uso no admite tráfico alto.

#### Scenario: Not configured
- **WHEN** una Administradora abre Integraciones en un sitio sin `EMAIL_HOST`
- **THEN** el email aparece apagado con la explicación de que los envíos de formularios
  quedan en la bandeja sin avisar por email

#### Scenario: Configured
- **WHEN** el sitio tiene `EMAIL_HOST=mail.ejemplo.com`, usuario y contraseña
- **THEN** la pantalla muestra el servidor y el usuario, indica que la contraseña está
  cargada y no la muestra

#### Scenario: Editors have no access
- **WHEN** una editora intenta abrir Integraciones
- **THEN** el admin le niega el acceso y el menú no muestra la opción

### Requirement: The email can be tested from the screen
La pantalla SHALL permitir mandar un email de prueba a una dirección, por defecto la del
usuario. SHALL confirmar el envío o mostrar el error del servidor, y el resultado SHALL
quedar registrado como cualquier otro envío. La prueba MUST hacerse por POST con
protección CSRF y MUST rechazar una dirección inválida.

#### Scenario: Test passes
- **WHEN** una Administradora manda la prueba a su email con el SMTP bien configurado
- **THEN** recibe el email, la pantalla lo confirma y el email pasa a activo

#### Scenario: Test fails
- **WHEN** el servidor rechaza el usuario o la contraseña
- **THEN** la pantalla muestra el error y el email pasa a con errores

### Requirement: Every email delivery is recorded
Cada intento de envío por SMTP del sitio (avisos de formularios, flujo de aprobación,
pruebas) SHALL registrar la fecha del último envío correcto o del último error, con el
mensaje de error recortado. El registro MUST NOT guardar destinatarios, contenido de los
emails ni claves, y MUST NOT impedir el envío si el registro falla.

#### Scenario: Server down
- **WHEN** un aviso del flujo de aprobación no puede salir porque el servidor no responde
- **THEN** Integraciones muestra el email con errores, la fecha y el error de conexión

#### Scenario: Recovery
- **WHEN** después un envío sale bien
- **THEN** el email vuelve a activo y el último error sigue visible con su fecha

### Requirement: The admin home warns when emails do not go out
El panel de inicio SHALL mostrar a Administradores y superusuarios un aviso, con enlace a
Integraciones, cuando en producción no hay SMTP configurado, cuando el último envío falló
o cuando hay envíos de formularios con el aviso por email pendiente (con la cantidad). Los
demás usuarios MUST NOT verlo. Sin ninguna de esas condiciones el aviso MUST NOT aparecer.

#### Scenario: Failing server
- **WHEN** el último envío falló y quedan 3 envíos de formularios sin avisar
- **THEN** la Administradora ve en el panel que los emails no están saliendo y que hay 3
  envíos pendientes de aviso

#### Scenario: Everything fine
- **WHEN** el último envío salió y no hay avisos pendientes
- **THEN** el panel no muestra el aviso

### Requirement: Each integration explains how to activate it
Cada integración de la pantalla SHALL traer los pasos para activarla: para el email, crear
una casilla del dominio en cPanel (por ejemplo `no-responder@dominio`) como opción por
defecto, qué variables de entorno cargar y qué se edita en el admin (remitente,
destinatarios y respuesta de cada formulario), y las advertencias sobre los límites de
envío del hosting, SPF y DKIM y los hostings que obligan a usar `localhost`.

#### Scenario: Guide on the screen
- **WHEN** una Administradora abre Integraciones con el email apagado
- **THEN** ve los pasos para crear la casilla en cPanel y las variables que tiene que
  cargar quien administra el servidor

### Requirement: A client onboarding checklist is documented
La documentación SHALL incluir un checklist de alta de cliente: las cuentas que crea el
cliente (dominio, hosting, casilla de email del sitio), cómo invita a la agencia como
usuario, qué datos pasa, qué variables de entorno se cargan y qué tareas programadas
(publicación programada, reintento de avisos y depuración de envíos) se dejan andando.

#### Scenario: New client
- **WHEN** la agencia da de alta un sitio nuevo
- **THEN** sigue el checklist y termina con el email probado desde Integraciones y las
  tareas programadas configuradas
