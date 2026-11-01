# forms Specification

## Purpose
Define los formularios públicos que arma el editor: sus campos y adjuntos, qué ve quien
los envía, cómo se protegen de bots, cómo se registra el consentimiento, qué límites
tiene el editor y cómo se avisa de cada envío.

## Requirements

### Requirement: Editors build forms from the admin
El editor SHALL crear páginas de tipo Formulario y agregarles campos de texto, área de
texto, email, teléfono, número, lista desplegable, opciones, casillas, casilla única,
fecha y archivo adjunto, con etiqueta, ayuda, opciones, valor inicial y obligatoriedad,
en el orden que elija. La página SHALL mostrar el formulario con el diseño del sitio y
validar cada campo en el servidor.

#### Scenario: Contact form
- **WHEN** un editor crea "Contacto" con nombre, email y mensaje obligatorios
- **THEN** la página muestra esos campos y rechaza un envío sin email válido con un
  mensaje junto al campo

#### Scenario: Phone field
- **WHEN** el formulario tiene un campo de teléfono
- **THEN** el campo usa `type="tel"` y acepta números con espacios, guiones y `+`

### Requirement: Attachments are private and limited
Un campo de archivo SHALL aceptar solo los tipos configurados (por defecto PDF, DOC,
DOCX, ODT, JPG y PNG) y hasta el peso configurado (por defecto 5 MB), con un mensaje claro
al rechazar. El archivo SHALL guardarse fuera de la carpeta pública de medios y MUST
poder descargarse solo desde el admin por quien puede ver los envíos de ese formulario.

#### Scenario: CV
- **WHEN** alguien adjunta su CV en PDF en "Trabajá con nosotros"
- **THEN** el envío guarda el archivo y en el admin hay un enlace para descargarlo

#### Scenario: Not allowed
- **WHEN** alguien adjunta un `.exe` o un PDF de 20 MB
- **THEN** el formulario lo rechaza y no se guarda nada

#### Scenario: Direct access
- **WHEN** un visitante sin permiso pide la descarga de un adjunto
- **THEN** no la obtiene

### Requirement: Visitors see a confirmation after sending
Después de un envío válido, el visitante SHALL ver el texto de agradecimiento del
formulario o, si el editor eligió una página, SHALL ir a esa página.

#### Scenario: Thank-you text
- **WHEN** alguien envía "Contacto" sin página de redirección elegida
- **THEN** ve el texto de agradecimiento con el diseño del sitio

#### Scenario: Redirect
- **WHEN** el formulario tiene "Gracias" como página de destino
- **THEN** el visitante termina en "Gracias"

### Requirement: Forms can be placed in any page
Un bloque Formulario SHALL insertar un formulario elegido en cualquier página con
bloques; el envío SHALL procesarse igual que en la página del formulario. Un formulario
sin publicar MUST NOT mostrarse.

#### Scenario: Home page
- **WHEN** un editor agrega el bloque con "Contacto" a la portada
- **THEN** la portada muestra el formulario y un envío válido llega a los envíos de
  "Contacto"

### Requirement: Spam protection is always on
Todo formulario SHALL rechazar envíos sin token CSRF válido, con el campo trampa
completado, enviados antes del tiempo mínimo desde que se mostró el formulario (por
defecto 3 segundos) o desde una IP que superó el límite de envíos (por defecto 5 cada 10
minutos por formulario). El editor MUST NOT poder apagar estas defensas. Un envío
rechazado por trampa o tiempo MUST NOT guardarse ni avisarse, y al visitante SHALL
mostrársele un mensaje genérico.

#### Scenario: Bot
- **WHEN** un bot completa el campo trampa
- **THEN** no se guarda el envío ni se manda email

#### Scenario: Too many submissions
- **WHEN** la misma IP envía el sexto formulario en 10 minutos
- **THEN** el formulario lo rechaza pidiendo esperar

### Requirement: Consent is recorded with every submission
Todo formulario SHALL terminar con una casilla obligatoria de aceptación de la política
de privacidad, con enlace a la página elegida en Datos del sitio (en el idioma de la
visita) o sin enlace si no hay ninguna. El envío SHALL guardar que se aceptó y cuándo.
El editor MUST NOT poder quitarla.

#### Scenario: Not accepted
- **WHEN** alguien envía sin marcar la casilla
- **THEN** el formulario lo rechaza

#### Scenario: Accepted
- **WHEN** la marca y envía
- **THEN** el envío registra la aceptación con fecha y hora

### Requirement: Projects limit what editors can add
Cada proyecto SHALL poder fijar qué tipos de campo puede usar el editor y la cantidad
máxima de campos por formulario (por defecto todos los tipos y 30 campos). Guardar un
formulario que no cumple MUST rechazarse con un mensaje en el admin.

#### Scenario: Too many fields
- **WHEN** un editor guarda un formulario con 31 campos
- **THEN** el admin lo rechaza y explica el máximo

### Requirement: Each submission notifies by email
Cada formulario SHALL tener destinatarios, asunto, nombre y dirección del remitente. Un
envío válido SHALL mandar un email a los destinatarios con los datos (y, para los
adjuntos, el nombre del archivo y un enlace al admin, nunca el archivo); responder al
email SHALL ir al email que dejó quien envió, si dejó uno. Desde el admin SHALL poder
mandarse un email de prueba a los destinatarios. Un error al mandar el email MUST NOT
perder el envío. Cada envío de un formulario con destinatarios SHALL guardar si su aviso
salió o quedó pendiente. Un comando SHALL reenviar los avisos pendientes de los últimos
`ORION_FORMS_EMAIL_RETRY_DAYS` días (3 por defecto), armados con los datos guardados, y
marcarlos como enviados cuando salen; los más viejos MUST quedar pendientes sin reenviarse.

#### Scenario: Reply
- **WHEN** Ana envía "Contacto" con su email
- **THEN** los destinatarios reciben el aviso y responder le escribe a Ana

#### Scenario: Test email
- **WHEN** una Administradora pide un email de prueba de "Contacto"
- **THEN** los destinatarios reciben un email marcado como prueba y el admin confirma o
  muestra el error

#### Scenario: Mail server down
- **WHEN** el servidor de email falla durante un envío
- **THEN** el envío queda guardado con el aviso pendiente y el visitante ve la
  confirmación

#### Scenario: Retry with the cron
- **WHEN** el servidor vuelve y corre `orion_retry_form_emails`
- **THEN** los destinatarios reciben el aviso de ese envío con sus datos y el envío queda
  con el aviso enviado

#### Scenario: Too old to retry
- **WHEN** un aviso quedó pendiente hace 5 días y corre el comando
- **THEN** no se reenvía y sigue pendiente en la bandeja

### Requirement: Example forms can be created with a command
Un comando SHALL crear, bajo la portada del idioma base, los formularios "Contacto" y
"Trabajá con nosotros" (con adjunto de CV) si todavía no existen, publicados y listos para
editar, y MUST NOT modificar ni duplicar formularios existentes.

#### Scenario: Run twice
- **WHEN** el comando se corre dos veces
- **THEN** hay un solo "Contacto" y un solo "Trabajá con nosotros"
