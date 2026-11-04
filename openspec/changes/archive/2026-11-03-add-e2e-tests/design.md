## Context

Ver proposal.md - Why. La suite actual corre con `pytest` + `pytest-django` contra el
proyecto de ejemplo (`example/`), con `DATABASE_URL` seleccionando PostgreSQL o MySQL
(`pipenv run test-postgres` / `pipenv run test-mysql`). `example/example/settings.py`
fija `DEBUG=true` por defecto, así que en los tests `STORAGES["staticfiles"]` usa
`StaticFilesStorage` (no la variante de WhiteNoise con manifest) y no corre
`collectstatic`. El middleware de CSP (`orion.core.csp.ContentSecurityPolicyMiddleware`)
está siempre activo, con o sin `DEBUG`, así que una prueba de punta a punta encuentra la
misma CSP estricta con nonce que en producción. `tests/conftest.py` ya tiene
`_page_cache_off` (cachea en memoria, caché de página apagada salvo que se marque el
test) y `_without_second_factor`; ambos fixtures son `autouse` y se aplican igual a las
pruebas nuevas, porque conviven en el mismo árbol de `pytest` y la misma configuración
(`pyproject.toml`, `[tool.pytest.ini_options]`).

## Goals / Non-Goals

**Goals:**
- Un navegador real (Chromium) ejerciendo los flujos de alta de página, publicación y
  envío de formulario, de punta a punta.
- Que la suite nueva corra con los mismos dos comandos que ya usa el resto de la suite
  (`pipenv run test-postgres`, `pipenv run test-mysql`), sin un tercer flujo de CI
  paralelo.
- Aislar las pruebas de punta a punta (lentas, con navegador) de la suite funcional
  rápida, para no pagar su costo en cada corrida de `pipenv run test`.

**Non-Goals:**
- Integración continua: a futuro, según `docs/especificacion.md`.
- Cobertura de más de un navegador o de pruebas visuales/de accesibilidad automatizadas.
- Presupuesto de Lighthouse: ya resuelto como deferred en `add-deploy-guides`.
- Reemplazar ninguna prueba funcional existente; esto se suma, no sustituye.

## Decisions

### 1. `pytest-playwright`, con Chromium, como única dependencia nueva

Playwright es lo que pide `docs/especificacion.md` explícitamente. `pytest-playwright`
es el plugin oficial del proyecto Playwright para integrarlo con `pytest`: agrega los
fixtures `page`, `browser`, `context`, etc., y la opción `--browser` para elegir el
motor; sin él habría que escribir a mano el manejo del ciclo de vida del navegador que
el plugin ya resuelve. Se usa solo Chromium (el navegador por defecto del plugin): cubre
el caso real (Alpine.js y CSS modernos no tienen diferencias de compatibilidad
relevantes acá) sin multiplicar el tiempo de corrida por tres motores.

El navegador de Playwright (Chromium) no es un paquete de Python: se instala aparte con
`playwright install chromium` después de `pipenv install --dev`, igual que
`django-tailwind-cli` descarga su binario de Tailwind aparte del paquete de Python. Se
documenta en el README como un paso extra de instalación, igual que esa dependencia.

Alternativa descartada: Selenium. Más vieja y con una API más verbosa para esperar a que
el DOM esté listo; Playwright espera automáticamente a que los elementos sean
interactuables, lo que simplifica las pruebas de un sitio con JavaScript (Alpine.js).

### 2. Pruebas de punta a punta en `tests/e2e/`, excluidas por defecto con un marcador

Las pruebas de punta a punta son mucho más lentas que la suite funcional (arrancan un
servidor real y un navegador) y requieren el navegador de Playwright instalado aparte.
Se agrupan bajo `tests/e2e/` (siguen dentro de `testpaths = ["tests"]`, ya configurado) y
se marcan con `pytest.mark.e2e` (vía `pytestmark` a nivel de módulo). `addopts` suma
`-m "not e2e"`, así que `pipenv run test`, `pipenv run test-postgres` y
`pipenv run test-mysql` no las corren. Dos scripts nuevos en el `Pipfile`,
`test-e2e-postgres` y `test-e2e-mysql`, corren `pytest -m e2e` contra cada base de datos
(mismas variables `POSTGRES_TEST_URL` / `MYSQL_TEST_URL` que los scripts existentes).

Alternativa descartada: sumarlas a la suite existente sin marcador, para que
`pipenv run test-postgres` las incluya directo. Se descarta porque la mayoría de las
corridas durante el desarrollo son rápidas y no necesitan un navegador; obligarlas a
instalar y correr Chromium en cada corrida sería un costo nuevo impuesto a todo el
flujo de trabajo existente, no solo a quien corre las pruebas de punta a punta a
propósito.

### 3. `live_server` de `pytest-django`, sin tocar `STORAGES` ni `collectstatic`

`pytest-django` usa automáticamente
`django.contrib.staticfiles.testing.StaticLiveServerTestCase` para el fixture
`live_server` cuando `django.contrib.staticfiles` está en `INSTALLED_APPS` (que ya lo
está): el servidor de pruebas sirve los estáticos desde los *finders* (las carpetas
`static/` de cada app), no desde la storage configurada, así que no hace falta correr
`collectstatic` ni cambiar `STORAGES` para que el CSS y el JS lleguen al navegador.

### 4. Fixture propio de sesión de Playwright, sobre los fixtures que ya trae el plugin

`pytest-playwright` ya resuelve el ciclo de vida del navegador; se agrega un fixture
`live_server_page` (en `tests/e2e/conftest.py`) que combina `page` (del plugin) con
`live_server` (de `pytest-django`) para navegar con una URL base ya armada
(`live_server.url`), evitando repetir esa concatenación en cada prueba.

### 5. `DJANGO_ALLOW_ASYNC_UNSAFE=1` para las corridas de punta a punta

Al implementar: con el navegador de Playwright ya iniciado (API sincrónica, que
mantiene un *event loop* de `asyncio` corriendo por debajo con `greenlet`), la
creación de la base de datos de pruebas (`_nodb_cursor`, un chequeo interno de Django
marcado `@async_unsafe`) ve ese *event loop* y asume que se la está llamando desde
código asincrónico, así que falla con `SynchronousOnlyOperation` aunque nada async
esté pasando de verdad: es un falso positivo del chequeo de Django ante la forma en
que Playwright implementa su API sincrónica, no un problema real de concurrencia.
Django ya trae la salida oficial para este caso (ver su documentación de
`async_unsafe`): la variable de entorno `DJANGO_ALLOW_ASYNC_UNSAFE`, que desactiva ese
chequeo. Se agrega a los dos scripts nuevos del `Pipfile`
(`test-e2e-postgres`/`test-e2e-mysql`), no a `test`/`test-postgres`/`test-mysql`, que
no usan Playwright y no la necesitan.

### Dependencias

Nueva: `pytest-playwright` (dependencia de desarrollo). Su navegador (Chromium) se
instala aparte, fuera de `pip`/`pipenv`.

### Migraciones

Ninguna.

## Risks / Trade-offs

- [Un paso de instalación extra (`playwright install chromium`), fuera de
  `pipenv install --dev`] → Se documenta en el README junto al resto de los comandos de
  desarrollo; quien no corre las pruebas de punta a punta no lo necesita.
- [La suite de punta a punta es más lenta y no corre con `pipenv run test`] → A propósito
  (ver Decisión 2); se documenta en el README para que no parezca que falta cobertura.
- [Sin integración continua todavía] → Las pruebas de punta a punta quedan a cargo de
  quien implementa un cambio, igual que el resto de la suite hoy; CI es un punto
  separado, a futuro, en `docs/especificacion.md`.
- [Solo Chromium] → No cubre diferencias específicas de Firefox o Safari; aceptado para
  no multiplicar el tiempo de corrida (ver Decisión 1).
- [`DJANGO_ALLOW_ASYNC_UNSAFE=1` desactiva un chequeo de seguridad de Django] → Solo se
  activa en los dos scripts de punta a punta (ver Decisión 5), donde el chequeo da un
  falso positivo por cómo Playwright implementa su API sincrónica; el resto de la suite
  (sin Playwright) sigue con el chequeo activo.
- [El editor del admin de Wagtail tiene su propia carrera entre JS y la prueba] → Al
  implementar la prueba de alta y publicación de una página (`test_admin_page_lifecycle.py`):
  el campo `slug` vive en la pestaña "Promocionar" (colapsada, no interactuable sin
  cambiar de pestaña) y se completa con JS a partir del título; en vez de competir con
  ese JS o cambiar de pestaña, la prueba fija su valor directamente
  (`locator.evaluate(...)`, disparando el evento `input` que el controlador de Wagtail
  espera). "Publicar" resulta ser una acción secundaria (este proyecto tiene moderación
  habilitada), colapsada en el menú desplegable del pie de página detrás de "Guardar
  borrador": la prueba abre ese menú y espera a que Tippy.js termine de mostrarlo
  (`.tippy-box[data-state="visible"]`) antes de hacer clic en "Publicar". Y la URL del
  formulario de alta ya calza con el patrón `**/admin/pages/**` que se usaba para
  esperar la redirección tras publicar, así que esa espera no esperaba nada realmente;
  se cambió a esperar que la URL deje de contener `/pages/add/`.
