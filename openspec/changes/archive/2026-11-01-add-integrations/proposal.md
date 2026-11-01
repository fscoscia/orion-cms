## Why

Hoy nadie se entera si los emails del sitio dejan de salir: un SMTP mal cargado o caído
solo deja una línea en el log, y en producción sin SMTP los emails se descartan en
silencio. La especificación pide una pantalla de Integraciones con el estado y una prueba,
un aviso en el panel cuando los emails no salen, el reintento de los avisos de formularios
con el cron y un checklist de alta de cliente. Es el cambio 5, el último de la Fase 4.

## What Changes

- **Pantalla Integraciones** en el menú Configuración, para Administradores y
  superusuarios. Muestra cada integración de la v1 con su estado:
  - **Email (SMTP):** apagada (sin `EMAIL_HOST`), activa, sin probar o con errores, con la
    configuración que se usa (servidor, puerto, usuario, seguridad, remitente; la
    contraseña solo como "cargada" o "falta") y el último envío correcto y el último error.
    Trae un botón para mandar un email de prueba y una guía para activarla (casilla de
    cPanel recomendada, qué va en las variables de entorno y qué en el admin, SPF y DKIM,
    límites del hosting).
  - **Mapas:** el proveedor de teselas en uso, con el aviso de la política de uso de
    OpenStreetMap.
- **Registro de cada envío de email** del sitio (formularios, flujo de aprobación,
  pruebas): un backend SMTP propio guarda el último envío correcto y el último error, sin
  datos personales ni claves.
- **Aviso en el panel** para Administradores y superusuarios cuando los emails no salen:
  sin SMTP en producción, el último envío falló o hay envíos de formularios cuyo aviso
  quedó pendiente. Enlaza a Integraciones.
- **Reintento de los avisos de formularios:** cada envío guarda si su email salió; el
  comando `orion_retry_form_emails`, pensado para el cron, reenvía los pendientes de los
  últimos 3 días (`ORION_FORMS_EMAIL_RETRY_DAYS`).
- **Checklist de alta de cliente** en `docs/alta-de-cliente.md`: cuentas que crea el
  cliente, cómo invita a la agencia, qué datos pasa y qué crons hay que dejar andando.

**Fuera del alcance:** integraciones con servicios externos (Brevo por API, Turnstile,
Analytics, CDN, Sentry), que siguen a futuro, y por lo tanto la carga de claves públicas
desde el admin; reintentar los emails del flujo de aprobación (los manda Wagtail y no
guarda cuáles fallaron); avisar por otro canal cuando falla el email; probar el envío
desde el arranque o con un cron.

## Capabilities

### New Capabilities
- `integrations`: pantalla de Integraciones con el estado, la prueba y la guía de cada
  integración, registro de los envíos de email, aviso en el panel y checklist de alta.

### Modified Capabilities
- `forms`: el aviso por email de cada envío queda registrado como enviado o pendiente y
  los pendientes se reintentan con un comando.

## Impact

- **Código nuevo:** app `orion.integrations` (modelo del estado del email, backend SMTP,
  vista, panel, plantillas, traducciones), comando `orion_retry_form_emails`,
  `docs/alta-de-cliente.md`.
- **Código modificado:** `orion.forms` (envío del aviso desde los datos guardados y estado
  del aviso en el envío), ajustes base (backend de email, `ORION_FORMS_EMAIL_RETRY_DAYS`),
  `.env.example`, README (crons), CHANGELOG y especificación.
- **Dependencias nuevas:** ninguna.
- **Migraciones:** una tabla nueva y un campo nuevo en los envíos de formularios, con
  valor vacío para los existentes. No tocan datos.
- **Seguridad:** la pantalla nunca muestra la contraseña del SMTP; los errores guardados
  se recortan y solo los ven Administradores y superusuarios.
