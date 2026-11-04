# site-security Specification

## Purpose
Define las protecciones del sitio frente al navegador y a los archivos subidos: HTTPS
forzado y HSTS, la política de seguridad de contenido del sitio público, los límites y el
tipo real de los documentos y el filtrado del HTML que escriben los editores.

## Requirements

### Requirement: Production forces HTTPS
Con el modo debug apagado, el sistema SHALL redirigir con 301 todo pedido HTTP a HTTPS,
salvo el chequeo de salud, y SHALL mandar HSTS por `ORION_HSTS_SECONDS` segundos (un año
por defecto), sin subdominios ni preload salvo que el proyecto los active. Con
`ORION_TRUSTED_PROXIES` mayor que 0 SHALL tomar el pedido como seguro cuando el proxy
manda `X-Forwarded-Proto: https`, y MUST NOT confiar en ese header sin proxies
declarados. `manage.py check --deploy` MUST NOT dar avisos con la configuración de
producción por defecto.

#### Scenario: Plain HTTP
- **WHEN** un visitante pide `http://sitio/servicios/` en producción
- **THEN** recibe una redirección 301 a `https://sitio/servicios/`

#### Scenario: HSTS
- **WHEN** un visitante pide una página por HTTPS en producción
- **THEN** la respuesta lleva `Strict-Transport-Security: max-age=31536000`

#### Scenario: Health check
- **WHEN** un monitor interno pide `http://127.0.0.1/health/`
- **THEN** recibe la respuesta del chequeo sin redirección

#### Scenario: Forged header
- **WHEN** sin proxies declarados un pedido HTTP trae `X-Forwarded-Proto: https`
- **THEN** igual se redirige a HTTPS

### Requirement: Public pages carry a strict content security policy
Toda respuesta del sitio público (páginas, búsqueda, errores, vista previa compartida)
SHALL llevar un header `Content-Security-Policy` con un nonce nuevo por respuesta, que
solo permita scripts con ese nonce (y los que ellos carguen), `object-src 'none'`,
`base-uri 'self'`, `form-action 'self'` y `frame-ancestors 'self'`; estilos propios y en
línea; e imágenes, fuentes, conexiones y marcos propios o por HTTPS. Los scripts de Orion
y los de la barra de Wagtail para editores SHALL llevar el nonce. Las respuestas del
admin, de los archivos estáticos y de los medios MUST NOT llevarla. Cada proyecto SHALL
poder cambiar cualquier directiva con `ORION_CSP`, y con `ORION_CSP_REPORT_ONLY=true` la
política SHALL mandarse como `Content-Security-Policy-Report-Only`.

#### Scenario: Injected script
- **WHEN** una página pública trae un `<script>` sin el nonce
- **THEN** el navegador no lo ejecuta

#### Scenario: Site scripts still run
- **WHEN** un visitante abre la portada con menús, mapas y formularios
- **THEN** todo funciona y la consola no muestra violaciones de la política

#### Scenario: Editor's user bar
- **WHEN** una editora con sesión abre una página pública
- **THEN** la barra de Wagtail aparece y funciona

#### Scenario: Admin untouched
- **WHEN** una editora abre el editor de páginas
- **THEN** la respuesta no lleva la política

### Requirement: Cached pages get a fresh nonce
Una página servida desde la caché de página SHALL llevar un nonce distinto en cada
respuesta, el mismo en el header y en el HTML, de modo que dos visitas nunca reciban el
mismo.

#### Scenario: Two visits
- **WHEN** dos visitantes abren la misma página en caché
- **THEN** cada uno recibe un nonce distinto y los scripts del sitio corren en ambos

### Requirement: Documents are limited
La biblioteca de documentos SHALL aceptar solo las extensiones de
`ORION_DOCUMENT_EXTENSIONS` (por defecto PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ODT, ODS,
ODP, TXT, CSV, MP4 y WebM) y hasta `ORION_DOCUMENT_MAX_UPLOAD_MB` (20 por defecto), o
hasta `ORION_VIDEO_MAX_UPLOAD_MB` (100 por defecto) para MP4 y WebM, con un mensaje
claro al rechazar. Los documentos ya subidos MUST NOT modificarse.

#### Scenario: Executable
- **WHEN** una editora sube `instalador.exe` como documento
- **THEN** el admin lo rechaza y explica qué tipos acepta

#### Scenario: Too large
- **WHEN** sube un PDF de 30 MB
- **THEN** el admin lo rechaza indicando el máximo

#### Scenario: Video within its limit
- **WHEN** sube un MP4 de 60 MB
- **THEN** el admin lo acepta

#### Scenario: Video too large
- **WHEN** sube un MP4 de 150 MB
- **THEN** el admin lo rechaza indicando el máximo para videos

### Requirement: Uploads must match their type
Un documento o un adjunto de formulario SHALL rechazarse cuando su contenido no
corresponde a su extensión: PDF, formatos de Office y OpenDocument, imágenes JPG y PNG,
y videos MP4 y WebM se reconocen por su firma; TXT y CSV MUST ser texto sin bytes nulos.

#### Scenario: Renamed executable
- **WHEN** una editora sube como documento un ejecutable renombrado a `informe.pdf`
- **THEN** el admin lo rechaza explicando que el contenido no corresponde al tipo PDF

#### Scenario: Real document
- **WHEN** sube un DOCX guardado por Word
- **THEN** se acepta

#### Scenario: Renamed video
- **WHEN** una editora sube un ejecutable renombrado a `clip.mp4`
- **THEN** el admin lo rechaza explicando que el contenido no corresponde al tipo MP4

### Requirement: HTML written by editors is filtered
El texto enriquecido que guardan los editores MUST NOT conservar scripts, atributos de
evento ni enlaces `javascript:`; solo SHALL conservar las etiquetas de las funciones
habilitadas en cada campo.

#### Scenario: Pasted script
- **WHEN** una editora pega `<script>alert(1)</script><p onclick="x()">Hola</p>` en un
  texto
- **THEN** la página publicada muestra "Hola" sin el script ni el atributo

### Requirement: The admin is recognised under a URL prefix
Cuando el sitio se sirve bajo un prefijo de URL, el sistema SHALL tratar el admin, los
estáticos y los medios igual que en la raíz del dominio: fuera de la política de seguridad
de contenido y de la caché de página.

#### Scenario: Admin page under a prefix
- **WHEN** se abre el admin de un sitio servido bajo `/sub`
- **THEN** la respuesta no lleva la política de seguridad de contenido del sitio público

#### Scenario: Admin request without a session under a prefix
- **WHEN** con la caché de página encendida, una visita sin sesión pide el login del admin
  de un sitio servido bajo `/sub`
- **THEN** la respuesta no se guarda en la caché de página

#### Scenario: Public page under a prefix
- **WHEN** se abre una página pública de un sitio servido bajo `/sub`
- **THEN** la respuesta lleva la política de seguridad de contenido
