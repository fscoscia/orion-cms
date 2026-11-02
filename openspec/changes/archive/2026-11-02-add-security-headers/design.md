## Context

Fuera de debug, los ajustes base ya marcan las cookies como seguras, mandan
`X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` y
`X-Frame-Options: SAMEORIGIN` (la vista previa del admin usa un iframe del mismo sitio).
No hay redirección a HTTPS, HSTS ni CSP. El sitio público solo carga scripts externos
propios (`orion.js`, Alpine en su variante CSP, `preview.js` en vistas previas) con
`defer`, sin scripts ni estilos en línea; el JSON-LD es un `<script>` de datos que el
navegador no ejecuta. Los fragmentos de código se insertan tal cual con
`{% code_snippets %}`. La barra de Wagtail para editores (`{% wagtailuserbar %}`) carga
`vendor.js`, `userbar.js` y el `media.js` de sus ítems desde
`wagtailadmin/userbar/base.html`, en un `{% block js %}`. El admin de Wagtail tiene
scripts en línea (paneles en línea, widgets de fecha, resultados destacados). La caché de
página (`PageCacheMiddleware`, antes de todo salvo seguridad y WhiteNoise) guarda el HTML y
los headers y los devuelve tal cual. Los documentos aceptan cualquier extensión (Wagtail
valida `WAGTAILDOCS_EXTENSIONS` solo si está definida) y los adjuntos de formularios se
validan por extensión y peso en `validate_attachment`.

## Goals / Non-Goals

**Goals:**
- HTTPS obligatorio en producción, también detrás de Nginx.
- Que un script inyectado en una página pública no corra.
- Que nada propio (sitio, barra de Wagtail, fragmentos) se rompa con la política.
- Rechazar archivos disfrazados.

**Non-Goals:**
- CSP en el admin, reportes de violaciones, `Permissions-Policy`, HSTS con subdominios o
  preload, antivirus.

## Decisions

### 1. HTTPS con los ajustes de Django

`SECURE_SSL_REDIRECT = env_bool("ORION_SSL_REDIRECT", not DEBUG)`,
`SECURE_REDIRECT_EXEMPT = [r"^health/$"]`,
`SECURE_HSTS_SECONDS = env_int("ORION_HSTS_SECONDS", 0 if DEBUG else 31536000)`,
`SECURE_HSTS_INCLUDE_SUBDOMAINS` y `SECURE_HSTS_PRELOAD` en `False` (variables de entorno
para activarlos). `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` solo
si `ORION_TRUSTED_PROXIES > 0`: sin proxy, el visitante podría mandar el header y Django
creería que el pedido es seguro. Un año de HSTS es lo que pide `check --deploy`
(`security.W004`); una prueba corre `check --deploy` con los ajustes de producción.
Tres avisos de `check --deploy` corresponden a decisiones tomadas y se silencian en
`SILENCED_SYSTEM_CHECKS`, con el motivo al lado: HSTS sin subdominios (`W005`) y sin
preload (`W021`), que decide cada cliente según su dominio, y `X-Frame-Options:
SAMEORIGIN` (`W019`), que necesita la vista previa del admin.

### 2. CSP propia en lugar de django-csp

Django 5.2 no trae CSP (llega en 6.0). django-csp 4.0 resolvería el header y el nonce,
pero hay que adaptarlo igual en tres puntos propios de Orion: solo para el sitio público,
nonce nuevo en las páginas de la caché y nonce para los fragmentos y la barra de Wagtail.
El header y el nonce son unas 40 líneas; con middleware propio no se suma una dependencia
y el día que Orion pase a Django 6 se cambia por la CSP nativa. Alternativa descartada:
django-csp, por lo anterior.

`orion.core.csp`:
- `ContentSecurityPolicyMiddleware`, adentro de `PageCacheMiddleware` y de
  `ConditionalGetMiddleware` (hallado al implementar: con un nonce nuevo por respuesta el
  ETag cambiaba siempre y se perdían los 304; el middleware pone un ETag calculado sin el
  nonce, que `ConditionalGetMiddleware` respeta):
  en cada pedido que no sea del admin, estáticos ni medios, pone `request.csp_nonce`
  (`secrets.token_urlsafe(16)`) y en la respuesta agrega el header (o el de solo informe
  con `ORION_CSP_REPORT_ONLY`). No pisa un header que la vista ya haya puesto.
- La política por defecto, en `ORION_CSP` (dict directiva → lista; el proyecto reemplaza
  o agrega directivas):
  - `default-src 'self'`
  - `script-src 'nonce-…' 'strict-dynamic' 'self'` (`'self'` solo sirve a navegadores sin
    `strict-dynamic`)
  - `style-src 'self' 'unsafe-inline'`: los estilos en línea son un riesgo menor y los
    usan Leaflet, la barra de Wagtail y muchos fragmentos de terceros
  - `img-src 'self' data: https:`, `font-src 'self' data: https:`, `connect-src 'self'
    https:`, `frame-src 'self' https:`, `media-src 'self' https:`: lo que Analytics,
    Pixel, chats y las teselas del mapa necesitan, sin listar dominios
  - `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`,
    `frame-ancestors 'self'`
- El valor `"'nonce'"` en una directiva se reemplaza por el nonce de la respuesta.

### 3. Nonce en la caché

La caché guarda la respuesta con el nonce con el que se armó. Al servirla,
`PageCacheMiddleware` genera un nonce nuevo y reemplaza el viejo en el contenido y en el
header de la política (el nonce es aleatorio de 22 caracteres: no aparece por casualidad
en el HTML). El nonce viejo se guarda en la entrada de caché. Así una página cacheada
nunca repite nonce, y el costo es un reemplazo de texto por visita.

### 4. Nonce en lo propio

- `orion/base.html`: `nonce="{{ request.csp_nonce }}"` en cada `<script>`. La vista
  previa de bloques se sirve desde el admin, sin política, y no cambia.
- `wagtailadmin/userbar/base.html` de Orion extiende la de Wagtail y reescribe
  `{% block js %}` con los mismos scripts y el filtro `with_nonce` sobre `media.js`.
- `{% code_snippets %}` pasa el código por `add_nonce(code, nonce)`, que agrega el
  atributo a cada `<script` y `<style` de apertura que no lo tenga. Solo se aplica a
  contenido de confianza (fragmentos creados con el permiso dedicado y HTML de Wagtail):
  nunca a contenido de visitantes. Los fragmentos ya se cachean por generación; el nonce
  se agrega al insertar, no se guarda.

### 5. Documentos y tipo real

- `WAGTAILDOCS_EXTENSIONS` desde `ORION_DOCUMENT_EXTENSIONS` (validación de Wagtail).
- `orion.core.uploads.matches_extension(file, extension)` lee los primeros 8 bytes:
  `%PDF` para PDF; `PK\x03\x04` para DOCX, XLSX, PPTX, ODT, ODS y ODP; la firma OLE
  `D0 CF 11 E0 A1 B1 1A E1` para DOC, XLS y PPT; `FF D8 FF` para JPG; `\x89PNG` para PNG;
  TXT y CSV, primeros 8 KB sin bytes nulos. Extensiones sin firma conocida (un proyecto
  que agrega otras) se aceptan por extensión. Sin `python-magic`: necesitaría `libmagic`
  en el servidor, que en cPanel no siempre está.
- `orion.core.document_forms.DocumentForm` (`WAGTAILDOCS_DOCUMENT_FORM_BASE`) valida peso
  (`ORION_DOCUMENT_MAX_UPLOAD_MB`) y tipo real. Subir varios documentos usa el mismo
  formulario.
- `validate_attachment` de los formularios suma `matches_extension` con el mismo mensaje
  que un tipo no permitido.

### 6. HTML de los editores

El texto enriquecido de Wagtail ya pasa por su filtro de etiquetas permitidas al guardar;
Orion no tiene bloques de HTML crudo. Se agrega una prueba que pega script, atributos de
evento y `javascript:` y verifica la página publicada.

### Dependencias

Ninguna.

### Migraciones

Ninguna.

## Risks / Trade-offs

- [HSTS por un año] → El sitio no puede volver a HTTP sin esperar; se puede bajar con
  `ORION_HSTS_SECONDS` antes del primer deploy. Sin subdominios para no afectar otros
  servicios del dominio del cliente.
- [Un fragmento con `onclick=` o `javascript:` deja de andar] → El README lo advierte y
  `ORION_CSP_REPORT_ONLY` permite diagnosticar; los códigos estándar (Analytics, Tag
  Manager, Pixel) usan solo `<script>`.
- [`img-src`, `connect-src` y `frame-src` aceptan cualquier origen HTTPS] → La protección
  principal (scripts) es estricta; un proyecto puede cerrar esas directivas con
  `ORION_CSP`.
- [El admin sigue sin CSP] → Requiere login y segundo factor; Wagtail no es compatible con
  una CSP estricta.
- [Plantillas de proyectos con scripts en línea] → Necesitan `nonce="{{
  request.csp_nonce }}"`; el CHANGELOG lo marca.
- [Reemplazar el nonce en la caché] → Si el HTML contuviera por azar el texto del nonce
  viejo, también se reemplaza; con 22 caracteres aleatorios es despreciable.
