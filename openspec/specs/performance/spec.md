# performance Specification

## Purpose
Define cómo un sitio Orion responde rápido y liviano: qué se guarda en caché y cuándo se
vacía, cómo revalida el navegador, cuántas consultas puede hacer cada página y cómo se
entregan los archivos estáticos y las fuentes.

## Requirements

### Requirement: Public pages are served from a full-page cache
Con la caché de página activa, una respuesta 200 a un GET o HEAD de un visitante sin
sesión SHALL guardarse y servirse a las visitas siguientes a la misma dirección (con su
consulta) sin volver a armarse. MUST NOT guardarse ni servirse desde la caché: visitas
con sesión iniciada, respuestas que agregan cookies o llevan un token CSRF (formularios), vistas previas (del editor y compartidas), el admin, respuestas que no son 200 o
que piden no guardarse. La caché SHALL activarse por defecto fuera de `DEBUG` y poder
apagarse con `ORION_PAGE_CACHE`.

#### Scenario: Second visit
- **WHEN** dos visitantes sin sesión abren `/servicios/`
- **THEN** la segunda respuesta sale de la caché, idéntica a la primera

#### Scenario: Editor signed in
- **WHEN** una editora con sesión abre `/servicios/`
- **THEN** la página se arma para ella (con la barra de Wagtail) y no se guarda

#### Scenario: Page with a form
- **WHEN** una página incluye un formulario con token CSRF
- **THEN** su respuesta no se guarda

### Requirement: The page cache empties when content changes
La caché de página SHALL vaciarse entera al publicar, despublicar, mover o borrar una
página, al confirmarse una publicación programada y al guardar o borrar menús, datos del
sitio, textos del sitio, idiomas, categorías, etiquetas, imágenes, sitios o
redirecciones. Un comando SHALL vaciarla a mano. Vaciarla MUST NOT borrar otros datos de
la caché compartida (sesiones, límites de intentos, recortes).

#### Scenario: Publish
- **WHEN** un editor publica un cambio en "Servicios"
- **THEN** la próxima visita a cualquier página muestra el contenido nuevo

#### Scenario: Menu edited
- **WHEN** una Administradora agrega un ítem al menú del encabezado
- **THEN** todas las páginas muestran el ítem nuevo en su próxima visita

### Requirement: Browsers revalidate pages instead of downloading them again
Las páginas públicas SHALL incluir `ETag` y `Last-Modified`, y una petición con
`If-None-Match` o `If-Modified-Since` que coincide SHALL responder 304 sin cuerpo.

#### Scenario: Revalidation
- **WHEN** el navegador vuelve a pedir `/servicios/` con el `ETag` recibido
- **THEN** la respuesta es 304

### Requirement: The cache backend is configured by environment
`CACHE_URL` SHALL elegir la caché: `file:///ruta`, `redis://…` (o `rediss://`),
`locmem://` o `dummy://`. Vacía, SHALL usar archivos en una carpeta temporal del
sistema. Cada proyecto SHALL usar un prefijo de claves propio, para que dos sitios en el
mismo servidor no compartan datos. Un esquema desconocido MUST impedir el arranque con
un mensaje claro.

#### Scenario: Redis
- **WHEN** el `.env` tiene `CACHE_URL=redis://127.0.0.1:6379/1`
- **THEN** la caché usa ese Redis

#### Scenario: Unknown scheme
- **WHEN** el `.env` tiene `CACHE_URL=memcached://x`
- **THEN** el proyecto no arranca y el error nombra los esquemas válidos

### Requirement: Menus are computed once per language
Los ítems de cada menú SHALL calcularse una vez por ubicación e idioma y reutilizarse en
las visitas siguientes hasta que la caché se vacíe; marcar el ítem actual SHALL seguir
funcionando en cada página.

#### Scenario: Second page
- **WHEN** después de una primera visita se abre otra página sin caché de página
- **THEN** el encabezado y el pie no consultan la base para armar los menús, y el ítem
  de la página actual sigue marcado

### Requirement: Pages stay within a query budget
Sin caché de página, la portada, una página con bloques, un listado de artículos y un
artículo SHALL armarse con una cantidad acotada de consultas que no crece con la
cantidad de bloques, imágenes o artículos mostrados. Las pruebas MUST fallar si se supera.

#### Scenario: Listing with many articles
- **WHEN** un listado muestra 12 artículos con imagen
- **THEN** usa las mismas consultas que con 2

### Requirement: Static files are compressed and cached forever
Fuera de `DEBUG`, los archivos estáticos SHALL servirse desde la aplicación con nombres
con hash, comprimidos con Brotli o gzip según el navegador, y con un
`Cache-Control` de larga duración (diez años, el de WhiteNoise) e `immutable`.

#### Scenario: Stylesheet
- **WHEN** un navegador que acepta Brotli pide la hoja de estilos de Orion
- **THEN** la recibe comprimida con Brotli y con `immutable`

### Requirement: Project fonts can be preloaded
`ORION_FONT_PRELOAD` SHALL aceptar rutas de archivos estáticos woff2 y la plantilla base
SHALL precargarlas con `<link rel="preload" as="font" type="font/woff2" crossorigin>`.
Sin el ajuste, MUST NOT agregarse nada.

#### Scenario: Brand font
- **WHEN** un proyecto define `ORION_FONT_PRELOAD = ["mi_sitio/fonts/marca.woff2"]`
- **THEN** cada página precarga esa fuente desde su URL de estáticos con hash
