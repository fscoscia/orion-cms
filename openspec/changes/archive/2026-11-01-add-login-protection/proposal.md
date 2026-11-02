## Why

El login del admin acepta intentos sin límite: una contraseña débil se puede adivinar
probando. Recuperar la contraseña depende del email, que puede no estar configurado, y
cambiar el email de una cuenta no cierra las sesiones abiertas en otros equipos. La
especificación pide bloqueo temporal por usuario e IP después de 5 intentos (django-axes),
recuperación por email con enlace de un solo uso y cierre de las demás sesiones al cambiar
la contraseña o el email. Es el cambio 1 de la Fase 5.

## What Changes

- **Límite de intentos de login** con django-axes: después de 5 intentos fallidos con el
  mismo usuario desde la misma IP, ese usuario queda bloqueado desde esa IP por 15
  minutos (`ORION_LOGIN_FAILURE_LIMIT`, `ORION_LOGIN_LOCKOUT_MINUTES`). Un login correcto
  borra los intentos. La pantalla de bloqueo, en el estilo del admin y traducida, dice
  cuánto esperar. No se guarda un registro de cada login.
- **Desbloqueo** desde la línea de comandos con los comandos de django-axes
  (`axes_reset_username`, `axes_reset_ip`), documentados en el README.
- **IP real detrás de un proxy:** `ORION_TRUSTED_PROXIES` (cantidad de proxies propios
  delante del sitio, 0 por defecto) hace que la IP se lea de `X-Forwarded-For`. La usan el
  límite de login y el límite de envíos de formularios.
- **Recuperar contraseña** desde el login del admin, con el flujo de Wagtail (enlace de un
  solo uso que vence): solo aparece si hay servidor de email configurado (o en
  desarrollo). Después de recuperarla, el segundo factor sigue pidiéndose.
- **Cerrar las demás sesiones** al cambiar el email de una cuenta, como ya pasa con la
  contraseña: la sesión que hizo el cambio sigue abierta; si el cambio lo hace otro usuario
  (un superusuario), se cierran todas las de esa cuenta.

**Fuera del alcance:** pantalla del admin para ver o desbloquear cuentas bloqueadas (se
hace por comando); límite de pedidos de recuperación de contraseña; CAPTCHA en el login;
cambiar la política de contraseñas (ya valida largo mínimo, contraseñas comunes, solo
números y parecido con el usuario); vencimiento de sesiones por inactividad.

## Capabilities

### New Capabilities
- `account-security`: límite de intentos de login, desbloqueo, recuperación de
  contraseña y cierre de sesiones al cambiar las credenciales.

### Modified Capabilities
- `project-configuration`: la IP del visitante se lee detrás de los proxies que el
  proyecto declara.

## Impact

- **Dependencias nuevas:** `django-axes` 8.3.1 (la 9.0.0 tiene menos de dos semanas).
- **Código nuevo:** función de IP del visitante, middleware de sesiones por email,
  plantilla de bloqueo y traducciones.
- **Código modificado:** ajustes base (axes, backends de autenticación, middleware,
  recuperación de contraseña, `ORION_TRUSTED_PROXIES`), límite de envíos de formularios,
  `.env.example`, `pyproject.toml`, `Pipfile` (`sqlparse` fijada en 0.6.0), README y
  CHANGELOG.
- **Migraciones:** las tablas de django-axes. No tocan datos existentes.
- **Seguridad:** un atacante puede bloquear por 15 minutos a un usuario desde su propia
  IP, no desde la de la víctima; sin `ORION_TRUSTED_PROXIES` correcto detrás de un proxy,
  todas las visitas comparten IP y el bloqueo pasa a ser por usuario.
