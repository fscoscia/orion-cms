## Why

Hoy un proyecto que instala Orion no puede crear ninguna página: el único tipo existente es
el `Page` base de Wagtail, que no se crea desde el admin, y la raíz del sitio es la página
de bienvenida genérica de Wagtail. Los bloques del cambio 3 necesitan páginas donde usarse,
y todo sitio institucional necesita una portada, páginas libres, una página de contacto y
una sección de novedades (cambio 4 de la Fase 1, ver `docs/especificacion.md`).

## What Changes

- **Tipos de página** con reglas de dónde puede ir cada uno:
  - **Portada**: la raíz del sitio, una por idioma, con el cuerpo de bloques.
  - **Página libre**: cuerpo de bloques, debajo de la Portada o de otra Página libre.
  - **Página de contacto**: muestra siempre los datos de contacto de Datos del sitio y un
    cuerpo de bloques; el formulario (Fase 4) y el mapa (cambio 5) se suman después.
  - **Listado de artículos**: lista paginada de sus artículos, filtrable por categoría y
    etiqueta, con su feed RSS.
  - **Artículo**: fecha, resumen, imagen, categorías, etiquetas y cuerpo de bloques; solo
    dentro de un Listado de artículos.
- **Encabezado principal de cada página**: si el cuerpo empieza con un Hero, su título es
  el `h1`; si no, la página muestra su título como `h1`. El Hero solo puede ser el primer
  bloque del cuerpo.
- **Categorías jerárquicas** (dos niveles) y **etiquetas**, ambas como fragmentos
  traducibles: se traducen una vez y cada idioma las muestra y filtra en su idioma.
- **Bloque "Últimas novedades"**: los artículos más recientes del idioma de la visita, de
  todos los listados o de uno elegido.
- **RSS** por listado y por idioma.
- **Portada inicial**: una migración reemplaza la página de bienvenida de Wagtail por una
  Portada, solo si la raíz sigue siendo esa página intacta (sin hijas ni traducciones). Si
  alguien ya la modificó, la migración no toca nada.
- Permisos de los grupos de editores y moderadores para categorías y etiquetas.

**Fuera del alcance:** campos y metadatos de SEO, Open Graph, JSON-LD y sitemap (Fase 3);
caché de página completa (Fase 3); buscador (Fase 4); formulario de contacto (Fase 4); mapa
(cambio 5); calendario de publicaciones y vista previa compartible (Fase 2); autor del
artículo; artículos relacionados; páginas de categoría o etiqueta con URL propia (el
filtro es un parámetro del listado); contenido de ejemplo al instalar (Fase 5).

## Capabilities

### New Capabilities
- `page-types`: tipos de página de Orion, dónde puede ir cada uno, la Portada inicial, el
  encabezado principal de cada página y la página de contacto.
- `articles`: artículos y sus listados: campos, orden, paginación, filtros, RSS y el
  bloque de últimas novedades.
- `taxonomies`: categorías y etiquetas de los artículos, su traducción y quién las edita.

### Modified Capabilities
- `content-blocks`: el catálogo suma el bloque "Últimas novedades" y el Hero solo se
  admite como primer bloque del cuerpo.

## Impact

- **Código nuevo:** app `orion.pages` (modelos de página, fragmentos de categorías y
  etiquetas, templates, feed RSS, migraciones); bloque de últimas novedades en
  `orion.core.blocks`.
- **Código modificado:** `ContentStreamBlock` (nuevo bloque y validación del Hero),
  ajustes base (`INSTALLED_APPS` con `orion.pages` y `wagtail.contrib.routable_page`),
  `orion.css` compilado, migración de la app `demo` del ejemplo, traducciones, README y
  CHANGELOG.
- **Dependencias:** ninguna nueva (`wagtail.contrib.routable_page` viene con Wagtail).
- **Migraciones:** tablas nuevas de `orion.pages`; una migración de datos que reemplaza la
  página de bienvenida de Wagtail por una Portada solo cuando es la original sin tocar (la
  borra: autorizado al planificar); permisos para los grupos de editores. La migración de
  `demo` cambia por el bloque nuevo (el ejemplo nunca se despliega).
