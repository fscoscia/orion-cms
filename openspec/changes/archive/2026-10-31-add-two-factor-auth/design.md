## Context

Ver proposal.md (Why). El admin de Wagtail usa la autenticación de Django; su login es
`orion.editor.forms.LoginForm` (cambio 3). Las vistas que se registran con
`register_admin_urls` exigen sesión y acceso al admin. `orion.editor.roles` define
`is_site_administrator`. Se evaluó `wagtail-2fa` 1.8.0: compatible con Wagtail 7, pero sin
códigos de respaldo, sin español y con la dependencia `six`.

## Goals / Non-Goals

**Goals:**
- Segundo factor obligatorio, con recuperación que no dependa del desarrollador.
- Pantallas en el estilo del admin y en español.

**Non-Goals:**
- Otros factores (WebAuthn, SMS, email).
- Sesiones "recordar este dispositivo".

## Decisions

### Dependencias: django-otp y segno
`django-otp` (>=1.7,<2; 1.7.5, licencia BSD) es la base estándar de 2FA en Django: modelos
de dispositivos TOTP (`otp_totp`) y de códigos estáticos (`otp_static`), verificación con
límite de intentos y espera creciente, y `OTPMiddleware`, que marca `user.is_verified()`.
`segno` (>=1.6,<2; 1.6.6, BSD) dibuja el código QR como SVG en línea, en Python puro y sin
dependencias. Alternativas: `wagtail-2fa` (faltan códigos de respaldo y español; suma
`six`); `qrcode` (necesita Pillow para imágenes o genera SVG menos compacto).

### Middleware
`orion.editor.middleware.TwoFactorMiddleware` hereda de `OTPMiddleware` (va después de
`AuthenticationMiddleware`). Si `ORION_2FA_REQUIRED` es verdadero y un usuario con acceso
al admin pide una URL del admin sin estar verificado, lo redirige a "verificar" si tiene un
dispositivo confirmado o a "configurar" si no. Quedan libres el login, el logout, las
vistas del 2FA, el catálogo de JavaScript, el sprite de íconos y la hoja de colores. El
sitio público no se toca. No hace falta vaciar el menú lateral: ninguna página del admin
que lo muestre se abre sin verificar.

### Vistas (en `orion.editor`, rutas del admin)
- **Verificar** (`orion_2fa_verify`): un campo para el código. `django_otp.match_token`
  prueba el código contra los dispositivos del usuario (TOTP y estático, cada uno con su
  límite de intentos) y `django_otp.login` marca la sesión; redirige a `next`. La pantalla
  usa el diseño del login de Wagtail (`wagtailadmin/admin_base.html`, clase `login`) e
  incluye "Cerrar sesión". Ese diseño oculta los errores de los campos, así que se
  muestran como mensajes arriba del formulario, igual que en el login de Wagtail.
- **Configurar** (`orion_2fa_setup`): crea o reusa un `TOTPDevice` sin confirmar, muestra el
  QR (SVG de `segno` a partir de `config_url`, con el nombre del sitio como emisor) y la
  clave en base32 en grupos de 4 (django-otp la guarda en hexadecimal; las apps la piden
  en base32); al confirmar con un código válido marca el dispositivo,
  crea un `StaticDevice` con 10 códigos de 8 caracteres y muestra los códigos (una sola
  vez, desde la sesión).
- **Mi doble factor** (`orion_2fa_manage`, en el menú de la cuenta con
  `register_account_menu_item`): estado, cantidad de códigos de respaldo que quedan,
  "Regenerar códigos de respaldo" y "Configurar otro teléfono" (borra los dispositivos y
  lleva a configurar), ambos por POST con confirmación.
- **Resetear el 2FA de un usuario** (`orion_2fa_reset`, botón en la lista de usuarios con
  `register_user_listing_buttons`): pantalla de confirmación y POST que borra sus
  dispositivos. Lo permite `is_site_administrator`; si el destino es superusuario, solo
  otro superusuario. Nadie se restablece a sí mismo (para eso está "Mi doble factor"). Sin
  permiso responde `PermissionDenied`, que el admin de Wagtail convierte en una
  redirección con aviso.

### Ajuste y chequeo
`ORION_2FA_REQUIRED = env_bool("ORION_2FA_REQUIRED", True)` en los ajustes base;
`orion.W002` avisa si es falso con `DEBUG` apagado. `OTP_TOTP_ISSUER` toma
`WAGTAIL_SITE_NAME`.

### Pruebas existentes
Las pruebas del admin que no tratan del 2FA lo desactivan con un fixture automático en
`conftest.py`; las del 2FA lo activan.

### Entorno de desarrollo
`pre-commit` instala `python-discovery` en su entorno virtual; se fija en 1.6.3 en las
dependencias de desarrollo porque las versiones más nuevas tenían días de publicadas.

## Risks / Trade-offs

- [Todos los usuarios configuran el 2FA en su próximo ingreso al instalar] → es lo
  decidido; el README lo avisa para coordinar con el cliente.
- [Perder el teléfono y los códigos bloquea al último administrador] → un superusuario lo
  resetea; si no hay ninguno con acceso, `manage.py shell` o el comando de django-otp
  (`otp_static` / borrar dispositivos) lo resuelven; el README lo documenta.
- [Rutas del admin libres del 2FA] → lista explícita y corta, con prueba.

## Migration Plan

Las migraciones de `otp_totp` y `otp_static` crean sus tablas. Revertir: quitar el
middleware y las apps; las tablas quedan sin uso.
