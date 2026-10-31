## Context

Ver proposal.md (Why). Wagtail decide si un bloque tiene vista previa por su
`preview_value` (o un `get_preview_value` propio) y la arma con el template del bloque.
Los bloques con imágenes usan `{% srcset_image %}`, que necesita una imagen guardada con
sus renditions; Últimas novedades consulta artículos publicados. La opción
`WAGTAIL_ALLOW_UNICODE_SLUGS` (por defecto verdadera) controla cómo el admin y
`Page.full_clean` arman los slugs.

## Goals / Non-Goals

**Goals:**
- Vistas previas que funcionen en un sitio vacío, sin efectos en la base.
- Un solo estilo de URL en todo el sitio.

**Non-Goals:**
- Transliterar alfabetos no latinos (cirílico, chino): reciben un slug de respaldo.

## Decisions

### Imágenes de ejemplo como archivos estáticos
Se generan con Pillow (ya instalado con Wagtail) unas pocas imágenes WebP livianas
(paisajes abstractos con los colores del tema, de 1600×900 y 800×800) y logos genéricos en
SVG, con un script versionado (`scripts/make_sample_images.py`) para poder regenerarlas.
Son obra propia de Orion, sin licencias de terceros. Alternativa: crear objetos `Image` en
la base al pedir una vista previa; ensuciaría la biblioteca del editor.

### Valor de vista previa sin la base de datos
`SampleImage` es un objeto liviano con `url`, `width`, `height`, `contextual_alt_text` e
`is_sample`. Los bloques con imágenes definen `get_preview_value` y arman su valor con
`StructValue` y `ListValue` directamente, sin `normalize` (que intentaría buscar la imagen
en la base). Los templates de imagen dibujan un `<img>` con la imagen de ejemplo cuando
`imagen.is_sample` y el `{% srcset_image %}` de siempre en otro caso. Últimas novedades
redefine `get_preview_context` y pasa artículos de ejemplo (título, fecha, resumen, imagen
de ejemplo y URL `#`); la tarjeta de artículo usa `article.url` en lugar de `{% pageurl %}`
para aceptar ambos.

### Slugs en ASCII
`WAGTAIL_ALLOW_UNICODE_SLUGS = False` en los ajustes base: el widget de slug del admin
convierte "Artículo" en `articulo` y `Page.full_clean` arma el slug automático igual. En
`TaxonomyMixin`, el slug vacío se arma con `slugify` sin Unicode y, si queda vacío (nombres
sin letras latinas), con `cautious_slugify` de Wagtail; un slug escrito a mano con
caracteres fuera de ASCII se rechaza mientras la opción esté apagada. El campo del modelo
no cambia, así que no hay migración.

## Risks / Trade-offs

- [Un proyecto que prefiera slugs Unicode] → redefine `WAGTAIL_ALLOW_UNICODE_SLUGS = True`
  en sus ajustes y Orion respeta esa opción también en categorías y etiquetas.
- [Los slugs con tildes ya guardados no cambian] → no hay en las bases conocidas; cambiar
  un slug publicado crea la redirección automática de Wagtail.
- [Las imágenes de ejemplo suman peso al paquete] → menos de 100 KB en total.

## Migration Plan

Sin migraciones. Revertir es quitar la opción de los ajustes y los valores de vista previa.
