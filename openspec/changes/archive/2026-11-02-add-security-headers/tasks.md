# Tasks

## 1. HTTPS

- [x] 1.1 Redirección, excepción de `/health/`, HSTS y header del proxy en los ajustes base, con variables en `.env.example`; verificar con `pytest tests/test_site_security.py tests/test_settings_base.py` (301 a HTTPS, HSTS de un año, `/health/` sin redirección, header falso sin proxy, header válido con proxy, desarrollo sin redirección, `check --deploy` sin avisos con producción)

## 2. CSP

- [x] 2.1 `orion.core.csp` (middleware, política por defecto, `ORION_CSP`, `ORION_CSP_REPORT_ONLY`), nonce en `orion/base.html` y la barra de Wagtail, nonce nuevo en la caché; verificar con `pytest tests/test_site_security.py tests/test_performance.py tests/test_site_layout.py` (header en páginas, búsqueda, 404 y vista previa compartida; sin header en admin, estáticos y medios; nonce igual en header y scripts; nonce distinto por respuesta y en hits de caché; directiva cambiada por el proyecto; modo informe; barra de Wagtail con nonce)
- [x] 2.2 Nonce en `{% code_snippets %}`; verificar con `pytest tests/test_code_snippets.py tests/test_site_security.py` (script y style con el nonce, nonce existente respetado, sin cambios en el texto fuera de las etiquetas)

## 3. Subidas

- [x] 3.1 `orion.core.uploads`, formulario base de documentos con extensiones y peso, tipo real en adjuntos de formularios; verificar con `pytest tests/test_site_security.py tests/test_forms.py` (cada firma aceptada, ejecutable renombrado rechazado en documentos y adjuntos, extensión no permitida, peso, TXT con bytes nulos, extensión sin firma conocida aceptada)
- [x] 3.2 Prueba del filtrado de texto enriquecido (script, `onclick`, `javascript:`)

## 4. Navegador y cierre

- [x] 4.1 Verificar en el navegador con los ajustes de producción (CSP activa, caché encendida): portada, página con mapa, formulario enviado, búsqueda, menú en celular, barra de Wagtail con sesión, fragmento de Analytics de prueba que carga un script externo, sin violaciones en la consola; un script inyectado sin nonce no corre; subida de un ejecutable renombrado rechazada en el admin
- [x] 4.2 Traducir los textos nuevos; README (HTTPS, HSTS, CSP, nonce para plantillas, fragmentos con `onclick`, documentos), `.env.example`, CHANGELOG; ejecutar la suite en PostgreSQL y MySQL, `ruff`, pre-commit, `manage.py check` (y `--deploy` con producción), `makemigrations --check`; registrar los resultados

## Resultados de verificación (2026-11-02)

- `pytest tests/test_site_security.py` 40 passed (HTTPS: 301, HSTS, `/health/` exenta,
  header falso sin proxy, header válido con proxy, `check --deploy` limpio con
  producción; CSP: directivas, nonce en los scripts del sitio, búsqueda y 404, vista
  previa compartida, sin política en admin y estáticos, nonce distinto por respuesta y en
  hits de caché, directivas del proyecto, modo informe, barra de Wagtail; `add_nonce`;
  firmas aceptadas y rechazadas; documentos: PDF, extensión no permitida, ejecutable
  renombrado con un solo mensaje, peso; texto enriquecido sin script, `onclick` ni
  `javascript:`). Suman `tests/test_settings_base.py` 3 (HTTPS en producción y
  desarrollo, header del proxy), `tests/test_code_snippets.py` 1 (nonce en script y
  style) y `tests/test_forms.py` 1 (CV disfrazado).
- Hallado y corregido al implementar: con un nonce por respuesta el ETag cambiaba siempre
  y se perdían los 304 (el middleware de CSP pone un ETag sin el nonce, adentro de
  `ConditionalGetMiddleware`); `check --deploy` avisaba por decisiones tomadas (HSTS sin
  subdominios ni preload, `SAMEORIGIN`), silenciadas con el motivo; un documento
  disfrazado mostraba además un error de extensión vacía de Wagtail (se omite la
  validación del modelo cuando el archivo ya fue rechazado).
- Navegador (Chrome headless, ajustes de producción con CSP y caché de página, 1280 px y
  390 px), 19/19: política en la página, hit de caché con nonce nuevo en cada respuesta,
  mapa de OpenStreetMap con teselas, fragmento en línea y el script externo que carga
  (`strict-dynamic`), menú del celular con Alpine, búsqueda, formulario enviado, barra de
  Wagtail de una editora, sin violaciones en ninguna; un script inyectado en la respuesta
  sin nonce no corrió y el navegador lo reportó; un ejecutable renombrado a PDF rechazado
  en el admin.
- Traducciones: 0 sin traducir ni dudosas en `orion.core` y `orion.forms`.
- `pipenv run test-postgres` 684 passed; `pipenv run test-mysql` 683 passed, 1 skipped.
- `ruff check`, `ruff format --check` y pre-commit sin errores; `manage.py check` sin
  problemas; `check --deploy` con un entorno de producción: "no issues (3 silenced)";
  `makemigrations --check` sin cambios (el cambio no tiene migraciones).
