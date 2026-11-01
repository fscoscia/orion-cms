## Context

El email ya se configura por variables de entorno (Fase 0): con `EMAIL_HOST` se usa el
backend SMTP de Django; sin él, la consola en desarrollo y el backend `dummy` en
producción, que descarta los emails. Los formularios (Fase 4, cambio 1) mandan el aviso en
`FormPage.send_mail`, capturan el error y lo dejan en el log; el envío queda en la bandeja,
pero nada dice que el aviso no salió. El flujo de aprobación manda sus avisos con
`wagtail.admin.mail`, que abre la conexión por su cuenta (`connection.open()`) y también
captura y loguea los errores. El panel de inicio ya tiene un aviso para administradores
(`SchedulingWarningPanel`, publicación programada atrasada) y `is_site_administrator`
define quién es administrador. En la v1 las únicas integraciones reales son el email por
SMTP y los mapas de OpenStreetMap; el resto está a futuro.

## Goals / Non-Goals

**Goals:**
- Saber, desde el admin, si los emails salen y por qué no, sin entrar al servidor.
- Probar el SMTP con un clic.
- Que ningún aviso de formulario se pierda en silencio: registrado y reintentado.
- Una guía de alta para la agencia.

**Non-Goals:**
- Integraciones externas y su carga de claves públicas en el admin (a futuro).
- Reintentar los avisos del flujo de aprobación.
- Monitoreo activo (probar el SMTP periódicamente o avisar por otro canal).

## Decisions

### 1. App nueva `orion.integrations`

Pantalla, estado del email, backend y panel no son propios de los formularios ni del
editor; una app chica los junta y es el lugar natural para las integraciones futuras. El
comando de reintento vive en `orion.forms`, porque trabaja sobre sus envíos.

### 2. El estado se registra en un backend SMTP propio

`orion.integrations.mail.EmailBackend` hereda de
`django.core.mail.backends.smtp.EmailBackend` y sobrescribe `open()` y `send_messages()`:
ante una excepción registra el error y la vuelve a lanzar; si `send_messages` devuelve
menos mensajes de los recibidos (con `fail_silently`), registra un error genérico; si sale,
registra el éxito. Cubrir `open()` hace falta porque Wagtail abre la conexión antes de
mandar. Los ajustes base usan este backend cuando hay `EMAIL_HOST`; un proyecto que ponga
otro `EMAIL_BACKEND` pierde el registro y la pantalla lo indica.

Alternativas descartadas: registrar solo en `FormPage.send_mail` (no ve el flujo de
aprobación ni la prueba de formularios) y la señal de Django (no existe una para envíos).

### 3. Un registro de una sola fila

Modelo `EmailStatus` con `last_success_at`, `last_failure_at` y `last_error` (texto
recortado a 500 caracteres), cargado con `EmailStatus.load()` (fila `pk=1`, como el
patrón de ajustes). La escritura es un `update_or_create` envuelto en `try/except` para
que un error de base no impida el envío, y se hace dentro de un `atomic` propio: si el
envío ocurre dentro de una transacción que después se revierte, se pierde el registro,
lo que es aceptable. No guarda destinatarios ni contenido. El texto de las excepciones de
`smtplib` trae el código y el mensaje del servidor, no la contraseña.

Alternativa descartada: la caché de Django, porque con `locmem` cada proceso tendría su
propio estado y se pierde al reiniciar.

El estado que muestra la pantalla se calcula, no se guarda: apagado sin `EMAIL_HOST`; con
errores si la configuración está incompleta o `last_failure_at` es más reciente que
`last_success_at`; sin probar si no hay ninguno; activo en otro caso.

### 4. El aviso del formulario sale desde los datos guardados

`FormSubmission` suma `email_notice` (`""` no corresponde, `"sent"`, `"pending"`).
`FormPage.send_mail(form, submission)` pasa a armar el mensaje con
`build_notice(submission)`, que usa `submission.form_data` y los campos del
formulario (etiqueta, tipo, adjuntos como nombre y enlace), y deja el estado en `sent` o
`pending`. Así el primer envío y el reintento producen el mismo email. Los envíos ya
existentes quedan con `""` y no se reintentan.

`orion_retry_form_emails` busca los `pending` con `submit_time` dentro de
`ORION_FORMS_EMAIL_RETRY_DAYS` (3) cuyo formulario sigue teniendo destinatarios, los manda
con una sola conexión y marca los que salen; si la conexión falla, corta y lo informa
(los demás quedan para la próxima vuelta). Se recomienda correrlo cada 15 minutos. Tres
días evitan mandar avisos viejos que ya no sirven; el envío igual sigue en la bandeja.

### 5. La pantalla y el panel

Vista `orion_integrations` en `register_admin_urls`, ítem en el menú Configuración visible
con `is_site_administrator`, y la vista lo vuelve a comprobar (403). La prueba es un
formulario Django (`EmailField`, por defecto el email del usuario) por POST; usa
`EmailMessage` con `DEFAULT_FROM_EMAIL`, captura el error para mostrarlo y vuelve con
`messages` a la pantalla (PRG). La guía es parte de la plantilla, traducible.

`EmailWarningPanel` (orden 6, junto al de publicación programada) se muestra a
administradores si: `not DEBUG` y sin `EMAIL_HOST`; el estado es con errores; o hay
envíos `pending` (cuenta). Son dos consultas indexadas como mucho y solo para
administradores.

### 6. Checklist como documento

`docs/alta-de-cliente.md`, para la agencia: cuentas del cliente, invitación a la agencia,
datos que pasa, variables de entorno, crons (`publish_scheduled`,
`orion_retry_form_emails`, `orion_purge_submissions`) y la prueba final en Integraciones.
El README enlaza el checklist y suma el cron del reintento.

### Dependencias

Ninguna nueva.

### Migraciones

`orion_integrations.0001_initial` (tabla `EmailStatus`) y una migración de `orion_forms`
que agrega `email_notice` con valor por defecto `""`. Ninguna toca datos existentes.

## Risks / Trade-offs

- [Un proyecto con otro `EMAIL_BACKEND` no registra el estado] → La pantalla muestra el
  backend en uso y que el registro no está disponible.
- [Escribir en la base por cada email] → Una fila, una escritura por envío; los sitios
  institucionales mandan pocos emails.
- [El estado "activo" solo dice que el último envío salió] → Un email aceptado por el
  servidor puede igual terminar en spam; la guía explica SPF y DKIM.
- [Sin el cron, los pendientes nunca se reenvían] → El panel los cuenta y el checklist
  pide configurarlo.
- [Cambiar `send_mail` de los formularios] → Las pruebas actuales del aviso (respuesta,
  adjuntos, error del servidor) siguen corriendo contra la nueva versión.
