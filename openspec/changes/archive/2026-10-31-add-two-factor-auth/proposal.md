## Why

La especificación pide doble factor para entrar al admin, como ruweb; se decidió que sea
obligatorio para todos los usuarios del admin. Una contraseña filtrada hoy alcanza para
publicar o borrar contenido. Es el cambio 4 de la Fase 2.

## What Changes

- **Verificación después de la contraseña**: quien entra al admin escribe un código de su
  app autenticadora (TOTP) o un código de respaldo; hasta entonces no ve nada del admin.
- **Alta obligatoria**: quien todavía no configuró el 2FA, al entrar, ve un código QR (y la
  clave para escribirla a mano), confirma con un código y recibe 10 códigos de respaldo de
  un solo uso que se muestran una única vez.
- **Desde su cuenta**: ver el estado, regenerar los códigos de respaldo y cambiar de
  teléfono (vuelve a configurar).
- **Recuperación**: un Administrador (o un superusuario) resetea el 2FA de un usuario que
  perdió el teléfono; un Administrador no puede resetear el de un superusuario.
- **Límite de intentos** de los códigos, con la espera creciente de django-otp.
- `ORION_2FA_REQUIRED` (verdadero por defecto, desactivable para desarrollo local); un
  chequeo avisa si está desactivado sin `DEBUG`.

**Fuera del alcance:** límite de intentos de la contraseña (django-axes, Fase 5); cerrar
otras sesiones al cambiar la contraseña (Fase 5); llaves de seguridad (WebAuthn) y códigos
por SMS o email (a futuro); 2FA en el sitio público (no tiene usuarios).

## Capabilities

### New Capabilities
- `two-factor-auth`: cómo se configura, se usa y se recupera el segundo factor del admin.

### Modified Capabilities
- Ninguna.

## Impact

- **Código nuevo:** middleware, vistas, formularios y templates del 2FA en `orion.editor`;
  botón de reset en la lista de usuarios; chequeo `orion.W002`.
- **Código modificado:** ajustes base (apps de django-otp, middleware, `ORION_2FA_REQUIRED`),
  `pyproject.toml`, `Pipfile.lock`, pruebas del admin (que inician sesión ya verificadas),
  traducciones, README y CHANGELOG.
- **Dependencias nuevas:** `django-otp` (TOTP, códigos de respaldo, límite de intentos) y
  `segno` (código QR en SVG, Python puro). Ver design.
- **Migraciones:** las tablas de django-otp (`otp_totp`, `otp_static`). No tocan datos
  existentes. Al instalar, todos los usuarios del admin configuran el 2FA en su próximo
  ingreso.
