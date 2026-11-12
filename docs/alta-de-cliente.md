# Checklist de alta de cliente

Para la agencia, al poner en marcha el sitio de un cliente nuevo sobre Orion. Las cuentas
son del cliente: la agencia entra como usuario invitado y nunca pide contraseñas por
email ni chat (se cargan una vez en el servidor o se usa un gestor de contraseñas
compartido).

## 1. Cuentas que crea el cliente

- [ ] **Dominio** a nombre del cliente, con acceso a su DNS.
- [ ] **Hosting** con Python 3.12 y PostgreSQL o MySQL 8 (un VPS o un cPanel con "Setup
  Python App").
- [ ] **Casilla de email del sitio** en el cPanel del dominio, por ejemplo
  `no-responder@dominio`. Es la opción por defecto para los emails del sitio; un
  proveedor dedicado (Brevo, Amazon SES) queda para mucho volumen o problemas de spam.
- [ ] **Casilla que recibe los formularios**, por ejemplo `contacto@dominio`, que alguien
  del cliente lee.
- [ ] Opcional: **Google Search Console** para el dominio.

## 2. Cómo invita a la agencia

- [ ] En el hosting (cPanel o el panel del VPS), un usuario para la agencia o acceso de
  colaborador; si el hosting no lo permite, el cliente cambia la contraseña al terminar.
- [ ] En el registrador del dominio, acceso a la zona DNS o un contacto que cargue los
  registros que pase la agencia.
- [ ] En Search Console, la agencia como usuario con permiso completo.

## 3. Datos que pasa el cliente

- [ ] Nombre del sitio, logos, datos de contacto y redes sociales (se cargan en **Datos
  del sitio**).
- [ ] Servidor SMTP, puerto, seguridad (SSL en el 465, TLS en el 587), usuario y
  contraseña de la casilla del sitio (en cPanel: **Email → Cuentas de email → Conectar
  dispositivos**).
- [ ] Las direcciones que reciben cada formulario.
- [ ] Las personas que usan el admin, con su rol (Editores o Administradores) y su email.

## 4. Variables de entorno del servidor

Las claves secretas van solo en el `.env` del proyecto, protegido con `chmod 600`, nunca
en el admin ni en el repositorio (ver `.env.example`). Los ajustes del proyecto lo leen
solos:

- [ ] `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y
  `WAGTAILADMIN_BASE_URL` con la dirección pública del sitio.
- [ ] `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`,
  `EMAIL_USE_SSL` o `EMAIL_USE_TLS`, y `DEFAULT_FROM_EMAIL` con la casilla del sitio.
- [ ] Si el hosting obliga a mandar desde `localhost`: `EMAIL_HOST=localhost`, sin
  usuario ni contraseña y con la seguridad que indique el hosting.

- [ ] Solo si el cliente va a usar un asistente de IA desde fuera del servidor:
  `ORION_MCP_ENDPOINT=true` (viene apagado), con HTTPS y, detrás de Nginx,
  `ORION_TRUSTED_PROXIES=1`. Las claves se crean después, en el admin. Ver
  [el MCP en producción](guias/mcp-en-produccion.md).

## 5. DNS del email

- [ ] Si el DNS del dominio no está en el hosting, cargar los registros **SPF** y
  **DKIM** que muestra cPanel en **Email → Entregabilidad del email**. Sin ellos, los
  emails terminan en spam.
- [ ] Tener en cuenta el límite de emails por hora del hosting y que la reputación del
  servidor es compartida con los otros sitios.

## 6. Tareas programadas

- [ ] `publish_scheduled` cada 5 minutos (publicaciones y bajas programadas).
- [ ] `orion_retry_form_emails` cada 15 minutos (reenvía los avisos de formularios que no
  salieron, de los últimos 3 días).
- [ ] `orion_purge_submissions` una vez por día (borra los envíos más viejos que la
  retención, 12 meses por defecto).

```cron
*/5 * * * * cd /ruta/al/proyecto && .venv/bin/python manage.py publish_scheduled
*/15 * * * * cd /ruta/al/proyecto && .venv/bin/python manage.py orion_retry_form_emails
0 3 * * * cd /ruta/al/proyecto && .venv/bin/python manage.py orion_purge_submissions
```

En cPanel (**Tareas Cron**), con el Python del entorno de "Setup Python App", por ejemplo
`~/virtualenv/proyecto/3.12/bin/python`.

## 7. Prueba final

- [ ] En el admin, **Configuración → Integraciones**: el email no muestra problemas y la
  prueba llega a una casilla del cliente, fuera de spam.
- [ ] Un envío real de cada formulario llega a sus destinatarios y aparece en su bandeja.
- [ ] El panel de inicio no muestra avisos de email ni de publicación programada.
- [ ] Cada usuario del cliente entró y activó la verificación en dos pasos.
- [ ] Si se activó el MCP: una clave de prueba con vencimiento responde (`initialize` y
  `tools/list` con `curl`), el alcance es el mínimo necesario y las claves que no se usan
  están revocadas.
