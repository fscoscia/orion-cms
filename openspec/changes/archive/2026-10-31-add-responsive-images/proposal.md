## Why

Las imágenes son la mayor parte del peso de una página, y la especificación pide servirlas
en AVIF con WebP de respaldo (ruweb solo usa WebP). Hoy Orion sirve WebP: cada plantilla
repite sus medidas, el Hero no se prioriza ni se precarga, los recortes se generan en la
primera visita (lenta) y la biblioteca acepta originales de cualquier tamaño, no acepta
SVG y no hay forma de ver qué imágenes sobran. Es el cambio 1 de la Fase 3.

## What Changes

- **Componente de imagen único** con medidas con nombre ("hero", "tarjeta", "galería",
  etc.): `<picture>` con fuentes AVIF y WebP en varias medidas, `<img>` de respaldo con
  `width` y `height`, `loading="lazy"` y `decoding="async"` salvo la imagen principal.
  Todas las plantillas de Orion lo usan y los proyectos pueden usarlo y sumar sus medidas.
- **Imagen principal priorizada**: la del Hero (y la de un artículo) lleva
  `fetchpriority="high"`, y la página la precarga desde el `<head>` cuando el primer
  bloque es un Hero con imagen.
- **Recortes al subir**: al subir o cambiar una imagen (o su punto focal) se generan en
  segundo plano las variantes de todas las medidas; un comando completa las que falten.
- **Límites de subida**: formatos permitidos y peso máximo configurables; un original de
  más de 2048 px de lado se reduce a 2048 px al subirlo.
- **SVG limpios**: la biblioteca acepta SVG y al subirlos elimina scripts, manejadores de
  eventos, enlaces `javascript:` y referencias externas; los SVG se sirven tal cual (sin
  convertir a AVIF).
- **Imágenes huérfanas**: un comando lista las imágenes que no se usan en ningún lado.

**Fuera del alcance:** videos y almacenamiento externo (a futuro); recortar o editar
imágenes en el admin (Wagtail ya ofrece punto focal); borrar huérfanas automáticamente
(el comando solo lista); reprocesar originales ya subidos de más de 2048 px (solo los
nuevos); caché HTTP de los archivos de medios (cambio 3, rendimiento).

## Capabilities

### New Capabilities
- `image-library`: qué acepta la biblioteca de imágenes (formatos, peso, tamaño, SVG
  limpios), recortes generados al subir, imágenes huérfanas y el componente de imagen
  para las plantillas de los proyectos.

### Modified Capabilities
- `block-presentation`: las imágenes pasan de WebP a AVIF con WebP de respaldo, y la del
  Hero se prioriza y se precarga.

## Impact

- **Código nuevo:** medidas y etiqueta de plantilla del componente de imagen en
  `orion.core`; señales de la biblioteca (reducción, limpieza de SVG, recortes); comandos
  `orion_generate_renditions` y `orion_unused_images`.
- **Código modificado:** plantillas de bloques, artículos, encabezado y pie;
  `orion/base.html` (precarga); ajustes base (`WAGTAILIMAGES_*`); README y CHANGELOG.
- **Dependencias nuevas:** ninguna (Pillow 13 codifica AVIF; `defusedxml`, que ya trae
  Willow, se declara porque Orion lo usa directamente para leer SVG).
- **Migraciones:** ninguna. Los recortes WebP existentes quedan; los AVIF se generan con
  el comando o en la primera visita.
