# Tasks

## 1. Página Formulario

- [x] 1.1 App `orion.forms` con `FormPage`, `FormField` (teléfono y archivo) y `FormSubmission`, plantillas de la página, del formulario y de agradecimiento, y `SiteSettings.privacy_page`, con migraciones; verificar con `pytest tests/test_forms.py` (campos de cada tipo, validación del servidor, teléfono con `type="tel"`, agradecimiento y redirección) y `makemigrations --check`
- [x] 1.2 Adjuntos privados (almacenamiento, validadores, vista de descarga, enlace en los envíos, chequeo `orion.E005`); verificar con `pytest tests/test_forms.py` (PDF guardado fuera de medios, `.exe` y archivo pesado rechazados, descarga con permiso sí y sin permiso no)

## 2. Defensas y consentimiento

- [x] 2.1 Campo trampa, tiempo mínimo, límite por IP y consentimiento con enlace a la política; verificar con `pytest tests/test_forms.py` (trampa y envío rápido no se guardan ni avisan, sexto envío rechazado, sin consentimiento rechazado, `consent_at` guardado, enlace en el idioma de la visita, sin CSRF rechazado)
- [x] 2.2 Límites al editor; verificar con `pytest tests/test_forms.py` (31 campos rechazado, tipo no permitido rechazado)

## 3. Email, bloque y ejemplos

- [x] 3.1 Aviso por email (remitente con nombre, `reply_to`, adjuntos como enlace, error de envío sin perder el envío) y prueba desde el admin; verificar con `pytest tests/test_forms.py`
- [x] 3.2 Bloque Formulario y comando `orion_create_example_forms`; verificar con `pytest tests/test_forms.py tests/test_content_blocks.py` (envío desde la portada llega al formulario, formulario sin publicar no se muestra, comando idempotente)

## 4. Navegador y cierre

- [x] 4.1 `pipenv run css-build`; verificar en el navegador: armar un formulario en el admin, enviarlo con un adjunto, ver el agradecimiento, descargar el adjunto, email de prueba, bloque en la portada, rechazo por tiempo mínimo, en escritorio y celular
- [x] 4.2 Traducir los textos nuevos; actualizar README (formularios, adjuntos privados y su carpeta, ajustes `ORION_FORMS_*`, ejemplos) y CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check`, `makemigrations --check` y `migrate` en ambas bases; registrar los resultados

## Resultados de verificación (2026-10-31)

- `pytest tests/test_forms.py` 29 passed (campos y validación, teléfono `tel`,
  agradecimiento y redirección 303, adjuntos privados, rechazados por tipo y peso,
  descarga con y sin permiso, `orion.E005`, trampa, tiempo mínimo, firma de otro
  formulario, límite por IP, CSRF, consentimiento, límites del editor, aviso por email con
  `reply_to` y remitente, adjunto como enlace, error de SMTP sin perder el envío, email de
  prueba, bloque, comando idempotente).
- Navegador (Chrome headless, 1280 px y 390 px), 16/16: envío de "Trabajá con nosotros"
  con un PDF y agradecimiento; envío inmediato rechazado con el mensaje genérico; bloque
  en "Consultas" que envía a "Contacto"; error de consentimiento junto a la casilla; en el
  admin, enlace al CV en los envíos, descarga como adjunto (200) y sin sesión
  redirección al login; email de prueba confirmado (y visible en la consola del
  servidor); pestañas Contenido, Después de enviar, Email y Promocionar, y tipos con
  Teléfono y Archivo. No se armó un formulario campo por campo desde la interfaz (lo
  cubren las pruebas y el comando). Hallado y corregido: la traducción de "Settings"
  pisaba "Propiedades" en todo el admin.
- `pipenv run css-build` con los estilos `.orion-form`.
- Traducciones de `forms`, `core` y `site_data`: 0 sin traducir.
- `pipenv run test-postgres` 505 passed; `pipenv run test-mysql` 505 passed.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas y `makemigrations --check` sin cambios en ambas bases; `migrate` aplicó
  `orion_forms.0001`, `orion_pages.0006_form_block`, `orion_site_data.0005_privacy_page`,
  `demo.0004_form_block` y `wagtailforms` 0001–0005 en PostgreSQL y MySQL (`.env`
  restaurado). `example/private/` agregado a `.gitignore`.

## Workflow follow-up

- Revisar la propuesta y la implementación.
- Archivar el cambio con `openspec archive add-forms` cuando esté aprobado.
