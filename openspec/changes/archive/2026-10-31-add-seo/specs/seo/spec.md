# Spec Delta

## Purpose

Define los metadatos que cada página ofrece a buscadores y redes sociales, los archivos
del sitio para buscadores (sitemap, robots.txt, favicon) y dónde los edita cada rol.

## ADDED Requirements

### Requirement: Every page has a title and a description with fallbacks
El `<title>` de una página SHALL ser su título SEO si lo tiene; si no, su título seguido de
" | " y el nombre del sitio (sin repetir el nombre si el título ya es igual a él). La
descripción SHALL ser la de la página (en un artículo sin descripción, su resumen) o, si
falta, la descripción del sitio en el idioma de la página; sin ninguna, la página MUST NOT
tener etiqueta de descripción.

#### Scenario: Page without SEO fields
- **WHEN** la página "Servicios" de "Clínica Ejemplo" no tiene título ni descripción SEO
- **THEN** su título es "Servicios | Clínica Ejemplo" y su descripción es la del sitio en
  español

#### Scenario: Page with an SEO title
- **WHEN** el editor carga el título SEO "Turnos online en Asunción"
- **THEN** el `<title>` es exactamente ese texto

### Requirement: Pages are ready to be shared on social networks
Cada página SHALL incluir etiquetas Open Graph (título, descripción, URL canónica, tipo,
idioma, nombre del sitio e imagen) y de Twitter Card (`summary_large_image` con imagen,
`summary` sin ella). La imagen SHALL ser, en orden, la imagen social de la página, la
imagen del artículo, la imagen del Hero que abre la página o la imagen social por defecto
del sitio, recortada a 1200 × 630 en un formato que lean las redes (JPEG).

#### Scenario: Article
- **WHEN** se comparte un artículo con imagen y sin imagen social propia
- **THEN** `og:type` es `article` y `og:image` es la imagen del artículo en 1200 × 630

#### Scenario: Page without images
- **WHEN** una página no tiene imágenes y el sitio tiene imagen social por defecto
- **THEN** `og:image` es la del sitio

### Requirement: Every page declares its canonical URL
Cada página SHALL tener `<link rel="canonical">` con su URL absoluta, armada en la visita
con el dominio del sitio y sin parámetros de consulta, salvo el número de página de un
listado a partir de la segunda.

#### Scenario: Tracking parameters
- **WHEN** alguien abre `/servicios/?utm_source=x`
- **THEN** la canónica es la URL de `/servicios/` sin parámetros

#### Scenario: Listing page
- **WHEN** alguien abre la página 2 de Novedades
- **THEN** la canónica incluye `?page=2`

### Requirement: Editors can keep a page out of search engines
Cada página de Orion SHALL tener, en la pestaña Promocionar, "No indexar" y "No seguir los
enlaces". Marcadas, la página SHALL incluir la etiqueta `robots` correspondiente y, si no
se indexa, MUST NOT figurar en el sitemap. Los proyectos SHALL poder sumar lo mismo a sus
tipos de página.

#### Scenario: Page not indexed
- **WHEN** el editor marca "No indexar" en "Gracias por tu consulta"
- **THEN** la página tiene `<meta name="robots" content="noindex">` y no está en el sitemap

### Requirement: The sitemap lists every public page in every public language
`/sitemap.xml` SHALL listar, con su fecha de última publicación, las páginas publicadas y
públicas del sitio en todos los idiomas públicos, y MUST NOT incluir páginas privadas, sin
publicar, marcadas para no indexar o de idiomas que no son públicos.

#### Scenario: Translated page
- **WHEN** "Servicios" está publicada en español y en inglés, y el inglés es público
- **THEN** el sitemap lista `/servicios/` y `/en/services/`

#### Scenario: Language not public
- **WHEN** el francés está agregado pero no es público
- **THEN** el sitemap no lista páginas en francés

### Requirement: robots.txt is editable
`/robots.txt` SHALL servir el texto cargado en Datos del sitio o, si está vacío, uno que
permite todo salvo el admin. Siempre SHALL anunciar el sitemap del sitio.

#### Scenario: Default
- **WHEN** nadie editó el robots.txt
- **THEN** `/robots.txt` permite todo, bloquea la ruta del admin e incluye la línea
  `Sitemap:` con la URL absoluta del sitemap

#### Scenario: Custom text
- **WHEN** una Administradora carga un texto propio sin línea `Sitemap:`
- **THEN** `/robots.txt` sirve ese texto con la línea `Sitemap:` agregada al final

### Requirement: The site has a favicon
Con un favicon cargado en Datos del sitio, cada página SHALL enlazar el ícono en 32 px y
192 px y el de Apple en 180 px (y el SVG tal cual, si es SVG), y `/favicon.ico` SHALL
llevar al ícono de 32 px. Sin favicon, `/favicon.ico` SHALL responder 404.

#### Scenario: Favicon loaded
- **WHEN** una Administradora sube un PNG cuadrado como favicon
- **THEN** las páginas enlazan sus versiones de 32, 180 y 192 px

### Requirement: Pages describe the site and the content with structured data
Cada página SHALL incluir JSON-LD con el sitio web (nombre, URL, idioma) y la organización
(nombre, URL, logo, teléfono, email, dirección y redes de Datos del sitio, solo los
cargados), y las migas de pan desde la portada cuando la página no es la portada. Un
artículo SHALL incluir además un `Article` con título, descripción, imagen, fechas de
publicación y modificación y la organización como editora. El JSON MUST escaparse para que
un texto del editor no pueda cerrar la etiqueta `<script>`.

#### Scenario: Article
- **WHEN** un buscador lee un artículo
- **THEN** encuentra `WebSite`, `Organization`, `BreadcrumbList` (Inicio › Novedades ›
  artículo) y `Article` con su fecha

#### Scenario: Text with markup
- **WHEN** el título de un artículo contiene `</script>`
- **THEN** el JSON-LD sigue siendo válido y no cierra la etiqueta

### Requirement: Site-wide SEO settings live in the site data
Datos del sitio SHALL tener una pestaña SEO con el favicon, la imagen social por defecto,
el robots.txt y el código de verificación de Search Console, editables por quien edita los
datos del sitio. La descripción del sitio SHALL estar en Textos del sitio, una por idioma.
El código de verificación SHALL generar `<meta name="google-site-verification">` y MUST
aceptar solo letras, números, guiones y guiones bajos.

#### Scenario: Search Console
- **WHEN** una Administradora pega el código de verificación
- **THEN** todas las páginas tienen la etiqueta meta con ese código

#### Scenario: Pasted HTML
- **WHEN** pega la etiqueta completa en lugar del código
- **THEN** el admin la rechaza con un mensaje que explica qué pegar
