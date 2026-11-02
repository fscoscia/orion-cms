# Tasks

## 1. IP del visitante

- [x] 1.1 `orion.core.client_ip.get_client_ip` con `ORION_TRUSTED_PROXIES`, usada por el límite de envíos de formularios; verificar con `pytest tests/test_account_security.py tests/test_forms.py` (sin proxy ignora el header, con 1 toma la última, header inventado a la izquierda ignorado, header corto, límite de formularios por IP real)

## 2. Límite de intentos

- [x] 2.1 django-axes 8.3.1 en `pyproject.toml` y `Pipfile`; ajustes (backend, middleware, parámetros, límites desde el entorno, sin registro de accesos, IP de Orion), plantilla de bloqueo traducida, migraciones; verificar con `pytest tests/test_account_security.py tests/test_two_factor.py` (bloqueo al quinto, 429 con la pantalla, contraseña correcta rechazada durante el bloqueo, otra IP y otro usuario pasan, vencimiento, éxito borra intentos, comando de desbloqueo, sin registro de accesos, 2FA sin cambios) y `makemigrations --check`

## 3. Recuperación y sesiones

- [x] 3.1 `WAGTAIL_PASSWORD_RESET_ENABLED` según el email; verificar con `pytest tests/test_account_security.py` (enlace en el login con SMTP y en desarrollo, ausente en producción sin SMTP, email recibido, enlace de un solo uso, email desconocido sin email, segundo factor pedido después)
- [x] 3.2 `CredentialsSessionMiddleware`; verificar con `pytest tests/test_account_security.py` (cambio de email propio mantiene la sesión y cierra la otra, cambio por superusuario cierra todas las de la cuenta, cambio de contraseña, sesión previa sin hash no se cierra, público sin efecto)

## 4. Navegador y cierre

- [x] 4.1 Verificar en el navegador: bloqueo después de 5 intentos con la pantalla traducida, desbloqueo por comando, recuperación de contraseña de punta a punta con el SMTP local y segundo factor después, cambio de email que cierra la otra sesión, en escritorio y celular
- [x] 4.2 Traducir los textos nuevos; README (bloqueo, desbloqueo, `ORION_TRUSTED_PROXIES`, recuperación, `force_login` en pruebas), `.env.example`, CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-11-01)

- `pytest tests/test_account_security.py` 25 passed (IP: sin proxy, uno, dos, IP
  inventada a la izquierda, header corto o ausente; bloqueo: al quinto aun con la
  contraseña correcta, 429 con la pantalla traducida, cuatro no bloquean, éxito borra los
  intentos, otra IP, otro usuario, vencimiento, desbloqueo por comando, límite desde los
  ajustes, IP real detrás de un proxy, sin registro de ingresos; recuperación: enlace en el
  login, oculto si está apagada, recuperación y enlace de un solo uso, email desconocido
  sin email, segundo factor después; sesiones: cambio de email propio, cambio por otro,
  cambio de contraseña, sesiones previas conservadas). `tests/test_settings_base.py` suma
  5 (recuperación según el email y límites desde el entorno) y `tests/test_forms.py` 1
  (límite de envíos detrás de un proxy).
- Navegador (dos Chrome headless con perfiles separados, 1280 px y 390 px, servidor SMTP
  local), 25/25 en cuatro etapas: bloqueo al sexto intento con la contraseña correcta,
  pantalla en celular sin desborde, otro usuario desde la misma IP entra;
  `axes_reset_username ana` y ana entra; recuperación de punta a punta (enlace en el
  login, email recibido, contraseña cambiada, enlace usado inválido, con 2FA obligatorio
  el ingreso pasa a configurar el segundo factor); dos sesiones de ana, el cambio de email
  desde una deja esa adentro y manda la otra al login.
- Traducciones: 0 sin traducir ni dudosas en `orion.editor`.
- `pipenv run test-postgres` 639 passed; `pipenv run test-mysql` 638 passed, 1 skipped.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó las
  migraciones de `axes` en PostgreSQL y MySQL (`.env` restaurado).
