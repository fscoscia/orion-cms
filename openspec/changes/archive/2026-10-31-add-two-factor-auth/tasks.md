# Tasks

## 1. Base

- [x] 1.1 Agregar `django-otp` y `segno` a `pyproject.toml`, instalar y bloquear; apps de django-otp, middleware y `ORION_2FA_REQUIRED` en los ajustes base, chequeo `orion.W002`, fixture que lo desactiva en las pruebas existentes; verificar con `pipenv run manage check`, `makemigrations --check` y la suite

## 2. Flujo

- [x] 2.1 Middleware y vistas de verificar y configurar con sus templates; verificar con `pytest tests/test_two_factor.py` (sin dispositivo va a configurar, QR y clave, confirmación con TOTP, 10 códigos mostrados una vez, con dispositivo va a verificar, código incorrecto, TOTP correcto, código de respaldo de un solo uso, límite de intentos, sitio público sin pedir código, rutas libres)
- [x] 2.2 "Mi doble factor" en la cuenta (regenerar códigos, configurar otro teléfono) y reset desde la lista de usuarios con sus permisos; verificar con `pytest tests/test_two_factor.py`

## 3. Navegador y cierre

- [x] 3.1 Verificar en el navegador: primer ingreso con alta y QR, códigos de respaldo, nuevo ingreso con código, ingreso con código de respaldo, reset por una Administradora y nueva alta, en escritorio y celular
  - Resultado (Chrome headless, códigos TOTP calculados desde la clave mostrada): 15/15 comprobaciones. Encontrado y corregido: el diseño del login de Wagtail ocultaba el error de un código incorrecto (ahora se muestra como mensaje, con prueba); la clave se cortaba dentro de un grupo y el botón "Ya los guardé" no estaba centrado (CSS).
- [x] 3.2 Traducir los textos nuevos, actualizar README (2FA obligatorio, recuperación, `ORION_2FA_REQUIRED` en desarrollo) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados
  - Resultado (2026-10-31): sin textos sin traducir ni dudosos; suite 323 passed en PostgreSQL y 323 passed en MySQL; `ruff check` y `ruff format --check` limpios; pre-commit pasa; `manage.py check` sin problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó las migraciones de `otp_static` y `otp_totp` en PostgreSQL y MySQL (`.env` restaurado).

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-two-factor-auth` cuando esté aprobado.
