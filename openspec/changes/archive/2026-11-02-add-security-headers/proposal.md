## Why

El sitio en producción todavía acepta HTTP, no pide HTTPS al navegador para las próximas
visitas (HSTS) y no tiene una política de seguridad de contenido (CSP): si alguien logra
inyectar un script en una página, el navegador lo ejecuta. Además, los documentos aceptan
cualquier extensión y los adjuntos de formularios se aceptan por la extensión, sin mirar
el contenido. La especificación pide headers de seguridad, HTTPS forzado y subidas
validadas por su tipo real; se decidió una CSP estricta con nonce que también cubra los
fragmentos de código. Es el cambio 2 de la Fase 5.

## What Changes

- **HTTPS forzado** fuera de debug: redirección de HTTP a HTTPS (salvo `/health/`, para
  monitores internos) y HSTS de un año (`ORION_HSTS_SECONDS`), sin subdominios ni
  preload por defecto. Detrás de proxies propios (`ORION_TRUSTED_PROXIES`) se confía en
  `X-Forwarded-Proto`. `manage.py check --deploy` queda sin avisos.
- **CSP en el sitio público**, con un nonce nuevo por respuesta:
  - scripts solo con el nonce (`'strict-dynamic'`: lo que cargan esos scripts también
    corre); `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`,
    `frame-ancestors 'self'`;
  - estilos propios y en línea; imágenes, conexiones y marcos del propio sitio y de
    cualquier origen HTTPS (lo que piden Analytics, Pixel o un chat); las teselas del mapa
    entran por ser HTTPS;
  - los proyectos ajustan cada directiva con `ORION_CSP` y `ORION_CSP_REPORT_ONLY=true` la
    manda en modo informe (no bloquea) para diagnosticar.
- **Nonce en todo lo propio:** los scripts de la plantilla base, los de la barra de
  Wagtail para editores y los `<script>` y `<style>` de los fragmentos de código. Las
  páginas servidas desde la caché reciben un nonce nuevo en cada visita.
- **Documentos limitados:** solo extensiones de documentos (`ORION_DOCUMENT_EXTENSIONS`:
  PDF, Word, Excel, PowerPoint, OpenDocument, TXT y CSV) y hasta
  `ORION_DOCUMENT_MAX_UPLOAD_MB` (20).
- **Tipo real de los archivos:** documentos y adjuntos de formularios se rechazan si el
  contenido no corresponde a la extensión (por ejemplo, un ejecutable renombrado a
  `.pdf`).
- **HTML de los editores filtrado:** queda cubierto por Wagtail (el texto enriquecido solo
  guarda las etiquetas de sus funciones); una prueba lo fija.

**Fuera del alcance:** CSP en el admin (Wagtail usa scripts en línea en paneles y
widgets; el admin ya exige login y segundo factor); reportes de CSP a un servicio
(`report-uri`); `Permissions-Policy`; HSTS con subdominios o preload (lo decide cada
cliente con su dominio); inspección de archivos con antivirus.

## Capabilities

### New Capabilities
- `site-security`: HTTPS forzado y HSTS, CSP del sitio público con nonce, límites y tipo
  real de los documentos, y filtrado del HTML de los editores.

### Modified Capabilities
- `code-snippets`: los fragmentos se insertan con el nonce de la CSP.
- `forms`: los adjuntos se validan por su contenido, no solo por la extensión.
- `project-configuration`: los valores seguros fuera de debug suman HTTPS forzado y HSTS.

## Impact

- **Código nuevo:** middleware de CSP, verificación del tipo de archivo, formulario base
  de documentos, plantilla de la barra de Wagtail con nonce, pruebas.
- **Código modificado:** ajustes base, caché de página (nonce nuevo en cada visita),
  plantilla base, etiqueta de fragmentos, constructor de formularios, `.env.example`,
  README y CHANGELOG.
- **Dependencias nuevas:** ninguna (CSP propia en lugar de django-csp; ver diseño).
- **Migraciones:** ninguna.
- **Compatibilidad:** un fragmento con atributos de evento (`onclick=`, `onload=`) o
  `javascript:` deja de correr; un proyecto con scripts propios en línea en sus plantillas
  necesita el nonce (`{{ request.csp_nonce }}`); los documentos ya subidos no se tocan.
- **Seguridad:** HSTS hace que el navegador recuerde por un año usar HTTPS: el sitio no
  puede volver a HTTP sin esperar ese plazo.
