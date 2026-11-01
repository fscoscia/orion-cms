# Tasks

## 1. Registro de envíos

- [x] 1.1 App `orion.integrations` con `EmailStatus` (una fila), backend SMTP que registra éxitos y errores en `open()` y `send_messages()`, ajustes base que lo usan con `EMAIL_HOST`, migración; verificar con `pytest tests/test_integrations.py` (éxito, error al conectar, error al mandar, `fail_silently`, error recortado, el envío no falla si el registro falla, nada de destinatarios ni contenido guardado) y `makemigrations --check`

## 2. Avisos de formularios

- [x] 2.1 `email_notice` en `FormSubmission` (migración con `""`), `build_notice` desde los datos guardados, estado `sent`/`pending` al enviar y comando `orion_retry_form_emails` con `ORION_FORMS_EMAIL_RETRY_DAYS`; verificar con `pytest tests/test_forms.py tests/test_integrations.py` (pruebas actuales del aviso intactas, pendiente si el servidor falla, reintento que lo manda y lo marca, más viejos sin reenviar, formulario sin destinatarios ignorado, corte si la conexión falla)

## 3. Pantalla y panel

- [x] 3.1 Vista Integraciones (estado, configuración sin contraseña, último éxito y error, mapas, guía), prueba por POST con dirección validada, menú en Configuración solo para administradores, `EmailWarningPanel`; verificar con `pytest tests/test_integrations.py` (cada estado, contraseña nunca en el HTML, editora sin acceso ni menú, prueba que sale y que falla, dirección inválida, GET no manda, aviso con cada condición y sin ellas, editora sin aviso)

## 4. Documentación, navegador y cierre

- [x] 4.1 `docs/alta-de-cliente.md`; README (Integraciones, cron del reintento, enlace al checklist), `.env.example`, CHANGELOG; especificación (Fase 4 hecha) y estado en CLAUDE.md
- [x] 4.2 Verificar en el navegador: Integraciones con el email apagado, configurado contra un SMTP local (prueba que sale) y caído (prueba que falla, aviso en el panel, envío pendiente y reintento), editora sin acceso, en escritorio y celular
- [x] 4.3 Traducir los textos nuevos; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-11-01)

- `pytest tests/test_integrations.py` 31 passed (registro: éxito, error al conectar, al
  iniciar sesión y al mandar, `fail_silently`, conexión abierta antes, recuperación con el
  último error visible, error recortado, nada de destinatarios, contenido ni contraseña
  guardados, el envío sale aunque falle el registro; pantalla: cada estado, configuración
  sin contraseña, servidor sin usuario, datos incompletos, backend propio, mapas, menú y
  acceso; prueba: sale, falla, dirección por defecto e inválida, GET no manda, editora no
  manda; panel: sin SMTP en producción, error con pendientes, sin problemas, desarrollo y
  editora). `tests/test_forms.py` suma 7 (aviso enviado, sin destinatarios, pendiente si
  el servidor falla, reintento con los mismos datos, sin reenvío doble, más viejos sin
  reenviar, formulario sin destinatarios, servidor todavía caído, corte a mitad).
- Navegador (Chrome headless, 1280 px y 390 px, servidor SMTP local), 23/23 en cuatro
  etapas: apagado (estado, nota de desarrollo, guía abierta, mapas, celular sin desborde,
  editora sin menú ni acceso); activo (sin probar, prueba recibida por el servidor,
  activo); caído (error de la prueba, con errores, último error, un visitante envía el
  formulario y ve el agradecimiento, aviso en el panel con 1 pendiente, celular sin
  desborde, editora sin aviso); con el servidor de vuelta, `orion_retry_form_emails`
  mandó el aviso (destinatario, respuesta y datos correctos), una segunda corrida no
  reenvió nada y el aviso del panel desapareció. Hallado y corregido: un servidor sin
  usuario mostraba "Contraseña: Falta" (ahora un guion) y la guía no mostraba el
  triángulo de desplegable.
- Hallado y corregido en las pruebas: "Active" y el error de la prueba tomaban
  traducciones de otros catálogos; los estados llevan contexto y el error usa la
  traducción existente ("No se pudo enviar").
- Traducciones: 0 sin traducir ni dudosas en `orion.integrations` y `orion.forms`.
- `pipenv run test-postgres` 608 passed; `pipenv run test-mysql` 607 passed, 1 skipped.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó
  `orion_forms.0003_email_notice` y `orion_integrations.0001_initial` en PostgreSQL y
  MySQL (`.env` restaurado).
