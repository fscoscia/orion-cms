## MODIFIED Requirements

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
