## Context

El admin usa el `LoginView` de Wagtail (vista de Django) con el `LoginForm` de Orion, y el
`TwoFactorMiddleware` pide el segundo factor después; los códigos incorrectos ya se frenan
con el throttling de django-otp. `AUTHENTICATION_BACKENDS` es el de Django por defecto.
Recuperar la contraseña es el flujo de Wagtail (`/admin/password_reset/`), activo por
defecto (`WAGTAIL_PASSWORD_RESET_ENABLED` sigue a `WAGTAIL_PASSWORD_MANAGEMENT_ENABLED`),
aunque en producción sin `EMAIL_HOST` el backend `dummy` descarta el email. Django ya
cierra las sesiones de una cuenta al cambiar su contraseña (el hash de sesión sale de la
contraseña) y la vista de Wagtail mantiene la sesión que hizo el cambio con
`update_session_auth_hash`; con el email no pasa nada. La IP del visitante se lee de
`REMOTE_ADDR` en el límite de envíos de formularios. Ninguna prueba usa `client.login`.

## Goals / Non-Goals

**Goals:**
- Frenar la adivinación de contraseñas sin bloquear a un usuario desde todas partes.
- Recuperación de contraseña que solo aparece cuando puede funcionar.
- Cambiar el email de una cuenta la protege igual que cambiar la contraseña.
- La IP correcta detrás de Nginx.

**Non-Goals:**
- Pantalla de cuentas bloqueadas, CAPTCHA, límite de pedidos de recuperación, cambios a
  la política de contraseñas, vencimiento de sesiones.

## Decisions

### 1. django-axes 8.3.1

La especificación ya eligió django-axes: es el paquete estándar de Django para esto,
mantenido, compatible con Django 5.2, y se engancha a las señales de autenticación, así
que funciona con el login de Wagtail sin tocar la vista. La 9.0.0 tiene dos días; se fija
`django-axes>=8.3.1,<9` en `pyproject.toml`, que el lock resuelve a 8.3.1. Al regenerar
el lock, `sqlparse` (dependencia de Django) subía a 0.6.1, publicada el mismo día: queda
fijada en 0.6.0 en el `Pipfile`. Sin el extra
`ipware`: la IP la da Orion (decisión 3).

Configuración en los ajustes base:
- `AxesStandaloneBackend` primero en `AUTHENTICATION_BACKENDS` y `AxesMiddleware` al final
  de `MIDDLEWARE`, como pide axes.
- `AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]`: el bloqueo es la combinación,
  así un atacante no bloquea a la víctima desde todas las IP ni a toda una oficina.
- `AXES_FAILURE_LIMIT` y `AXES_COOLOFF_TIME` desde `ORION_LOGIN_FAILURE_LIMIT` (5) y
  `ORION_LOGIN_LOCKOUT_MINUTES` (15), variables de entorno.
- `AXES_RESET_ON_SUCCESS = True`, `AXES_DISABLE_ACCESS_LOG = True` y
  `AXES_ENABLE_ACCESS_FAILURE_LOG = False`: no se guarda un registro de cada login (dato
  personal sin uso en el admin).
- `AXES_LOCKOUT_TEMPLATE` con una plantilla de Orion que extiende la de login de Wagtail,
  y `AXES_CLIENT_IP_CALLABLE` con la función de la decisión 3.
- Handler por defecto de base de datos: el bloqueo sobrevive a reinicios y es el mismo
  para todos los procesos; axes borra los intentos vencidos al registrar uno nuevo.

Las pruebas siguen sin `client.login` (axes exige el `request`); las de axes hacen POST al
login real.

Alternativa descartada: un límite propio con la caché, como el de formularios. Es poco
código, pero con caché `locmem` cada proceso cuenta por su lado y se pierde lo que axes ya
resuelve (desbloqueo, limpieza, señales).

### 2. Desbloqueo por comando

`axes_reset_username <usuario>` y `axes_reset_ip <ip>` vienen con axes; el README los
documenta. Una pantalla para administradores queda fuera: es raro y el bloqueo vence solo.

### 3. `orion.core.client_ip.get_client_ip`

Con `ORION_TRUSTED_PROXIES = 0` devuelve `REMOTE_ADDR`. Con N > 0 parte
`X-Forwarded-For` por comas y toma la N-ésima desde la derecha: cada proxy propio agrega
una al final, y lo que está a la izquierda lo puede escribir el visitante. Con menos
direcciones de las esperadas toma la primera. La usan axes y `is_rate_limited` de los
formularios. La guía de deploy (cambio 5) indica el valor para Nginx (1) y cPanel
(Passenger ya pone la IP real en `REMOTE_ADDR`: 0).

### 4. Recuperación de contraseña según el email

`WAGTAIL_PASSWORD_RESET_ENABLED = bool(EMAIL_HOST) or DEBUG`, sobrescribible por el
proyecto. El resto es el flujo de Wagtail y Django: el token deja de valer al cambiar la
contraseña (un solo uso) y vence a los `PASSWORD_RESET_TIMEOUT` segundos (3 días por
defecto de Django); la confirmación es la misma exista o no la cuenta. Hay que verificar
que el `TwoFactorMiddleware` deja pasar las URL de recuperación sin sesión (lo hace: solo
actúa con un usuario autenticado) y que, al terminar, el login sigue pidiendo el segundo
factor.

### 5. Sesiones atadas al email

`orion.editor.middleware.CredentialsSessionMiddleware`, después de
`AuthenticationMiddleware`:
- Guarda en la sesión un hash (`salted_hmac` con `SECRET_KEY`) del email del usuario.
- En cada pedido, si la sesión tiene un hash distinto del email actual, cierra la sesión
  (`logout`) y sigue como anónimo; si no tiene hash (sesiones previas), lo guarda.
- Al terminar el pedido, si el usuario de esta sesión cambió su propio email durante el
  pedido, guarda el hash nuevo: la sesión que hizo el cambio sigue abierta.

Alternativa descartada: recorrer y borrar las sesiones de la base al cambiar el email; las
sesiones no están indexadas por usuario y hay que decodificar cada una. Otra descartada:
un modelo de usuario propio que sume el email al hash de sesión de Django; cambiar el
modelo de usuario en proyectos ya creados es una migración muy riesgosa.

### Dependencias

`django-axes` 8.3.1 (justificada en la decisión 1). Ninguna otra.

### Migraciones

Las de `axes` (tablas de intentos). No tocan datos existentes.

## Risks / Trade-offs

- [Detrás de un proxy sin `ORION_TRUSTED_PROXIES`, todas las visitas tienen la IP del
  proxy] → El bloqueo pasa a ser por usuario: alguien puede bloquear a "ana" por 15
  minutos. La guía de deploy lo indica y el límite de formularios mejora con el mismo
  ajuste.
- [Con un valor de `ORION_TRUSTED_PROXIES` mayor que los proxies reales, el visitante
  elige su IP] → El ajuste se documenta como "cantidad de proxies propios" con ejemplos.
- [axes rompe `client.login` en pruebas de proyectos] → El README dice usar
  `force_login`.
- [La sesión que cambia el email la mantiene el middleware al final del pedido; si el
  cambio ocurre en un pedido que termina con error, esa sesión también se cierra] →
  Aceptable: vuelve a ingresar.
