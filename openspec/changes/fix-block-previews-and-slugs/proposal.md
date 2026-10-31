## Why

La spec `content-blocks` pide que cada bloque se muestre en el selector con una vista
previa, pero Imagen, Galería, Imagen y texto, Logos y Últimas novedades no tienen: Wagtail
solo la ofrece con un valor de ejemplo, y esos bloques necesitan imágenes o artículos que
un sitio nuevo no tiene. Además, las URLs con tildes (`/novedades/artículo-13/`) se ven
codificadas al compartirlas (`art%C3%ADculo-13`) y las traducciones de wagtail-localize ya
salen sin tildes, así que conviven dos estilos.

## What Changes

- **Imágenes de ejemplo de Orion** (creadas para Orion, sin licencias de terceros) para las
  vistas previas: los bloques con imágenes y Últimas novedades muestran su diseño con esas
  imágenes y con artículos de ejemplo, sin agregar nada a la biblioteca de imágenes ni a las
  páginas.
- **URLs sin tildes**: los slugs de páginas se generan en ASCII
  (`WAGTAIL_ALLOW_UNICODE_SLUGS = False` en los ajustes base) y los de categorías y
  etiquetas también, con un slug de respaldo para nombres en alfabetos no latinos.

**Fuera del alcance:** traducir los textos de ejemplo de las vistas previas que ya existen
(siguen en inglés); convertir slugs con tildes ya guardados (las bases conocidas no tienen;
un proyecto que los tenga los cambia a mano y Wagtail crea la redirección).

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `content-blocks`: la vista previa de los bloques que necesitan imágenes o artículos usa
  contenido de ejemplo de Orion.
- `site-routing`: las URLs de las páginas no llevan tildes ni caracteres fuera de ASCII.
- `taxonomies`: los slugs de categorías y etiquetas tampoco.

## Impact

- **Código nuevo:** imágenes de ejemplo en `orion/core/static/orion/samples/` y su
  generador; valores de vista previa de los bloques con imágenes y de Últimas novedades.
- **Código modificado:** templates de los bloques con imágenes y de la tarjeta de artículo
  (dibujan una imagen de ejemplo cuando la reciben), ajustes base, `TaxonomyMixin`,
  pruebas, README y CHANGELOG.
- **Dependencias:** ninguna.
- **Migraciones:** ninguna. No cambia contenido guardado.
