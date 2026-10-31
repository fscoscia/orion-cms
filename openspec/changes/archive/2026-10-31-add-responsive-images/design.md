## Context

Ver proposal.md (Why). Hoy las plantillas de Orion (Hero, Imagen, Imagen y texto,
Galería, Tarjetas, Logos, tarjeta y página de artículo, encabezado y pie) llaman cada una a
`{% srcset_image ... format-webp <medidas> %}` con sus propias medidas, y las vistas
previas de bloques usan `SampleImage` (`is_sample`) con un `<img>` simple. Wagtail 7.4
tiene `{% picture %}` y `Image.get_renditions(*filters)` (crea varias variantes en una sola
pasada), el directivo `preserve-svg`, `Filter.expand_spec`, los ajustes
`WAGTAILIMAGES_EXTENSIONS` y `WAGTAILIMAGES_MAX_UPLOAD_SIZE`, y el índice de referencias
("Uso" de cada imagen). Pillow 13 codifica AVIF. `defusedxml` 0.7 ya está instalado (lo
requiere Willow).

## Goals / Non-Goals

**Goals:**
- Un único lugar con las medidas de las imágenes, usado por las plantillas y por la
  generación de recortes.
- Sin dependencias nuevas.

**Non-Goals:**
- Cambiar el modelo de imagen (`WAGTAILIMAGES_IMAGE_MODEL`): cambiarlo después de tener
  datos es una migración difícil para cada proyecto.
- Una cola de tareas.

## Decisions

### Medidas con nombre
`orion.core.images.IMAGE_SIZES`: diccionario `nombre → {"filters", "sizes"}`, por ejemplo
`"card": {"filters": "fill-{480x300,800x500}", "sizes": "(min-width: 64rem) 33vw, ..."}`,
con las medidas que hoy tienen las plantillas (hero, image, image_text, gallery, card,
logo, article, article_card, site_logo). `ORION_IMAGE_SIZES` en los ajustes del proyecto
se combina encima (agrega o reemplaza por nombre). `get_image_size(name)` lanza
`ImproperlyConfigured` con el nombre si no existe. Los formatos son fijos: AVIF y WebP
(`format-{avif,webp}`), calidad por defecto de Wagtail (`WAGTAILIMAGES_AVIF_QUALITY`,
`WAGTAILIMAGES_WEBP_QUALITY`, ajustables por el proyecto).

### Etiqueta `{% responsive_image %}`
En `orion_core`: `{% responsive_image image "card" alt=... class=... is_main=False %}`.
- Imagen vacía → nada.
- `SampleImage` → el `<img>` simple de hoy (incluye la plantilla actual).
- SVG (`image.is_svg()`) → un `<img>` de la variante `original` (con `preserve-svg`, sigue
  siendo SVG), con su ancho y alto, sin `<picture>`.
- Resto → `image.get_renditions(*filtros)` con las medidas × formatos y
  `wagtail.images.models.Picture(renditions, attrs).__html__()`, el mismo HTML que
  `{% picture %}`: AVIF como `<source>` y WebP en el `srcset` del `<img>` de respaldo
  (un `<source>` WebP sería redundante). Atributos: `alt`, `class`, `sizes`; `loading="lazy"` y
  `decoding="async"` salvo `is_main`, que pone `fetchpriority="high"`.
Las plantillas de Orion pasan a usarla; el texto alternativo sigue saliendo de
`contextual_alt_text` / `image_alt_text` (vacío si es decorativa).

### Precarga de la imagen principal
`{% main_image_preload page %}` en el `<head>` de `orion/base.html`: si la página tiene un
StreamField `body` cuyo primer bloque es un Hero con imagen (no SVG ni de ejemplo), emite
`<link rel="preload" as="image" type="image/avif" imagesrcset="..." imagesizes="..."
fetchpriority="high">` con las variantes AVIF de la medida "hero" (las mismas que usa el
bloque, así el navegador no descarga dos veces). Los proyectos con otra plantilla base
pueden usar la etiqueta igual.

### Recortes al subir
Señal `post_save` de la imagen (cualquier guardado: subida, archivo nuevo o punto focal;
Wagtail guarda una variante distinta por punto focal). Programa con
`transaction.on_commit` la generación de todas las medidas × formatos con
`get_renditions` (solo crea las que faltan) en un hilo aparte (`threading.Thread`,
`daemon=True`), así la subida no espera. Errores se registran en el log, nunca rompen la
subida. `ORION_IMAGE_RENDITIONS_IN_BACKGROUND` (verdadero por defecto) permite generarlas
en el mismo hilo; las pruebas lo apagan. `manage.py orion_generate_renditions` recorre
todas las imágenes y genera lo que falte (para bibliotecas existentes o si se reinició el
proceso a mitad de una generación). Si una variante falta igual, `get_renditions` la crea
al mostrar la página (comportamiento actual de Wagtail).

### Límites y reducción
`WAGTAILIMAGES_EXTENSIONS = ["avif", "gif", "jpg", "jpeg", "png", "svg", "webp"]` y
`WAGTAILIMAGES_MAX_UPLOAD_SIZE` desde `ORION_IMAGE_MAX_UPLOAD_MB` (10 por defecto), en los
ajustes base; Wagtail valida y traduce los mensajes. Reducción: señal `pre_save` de la
imagen; si el archivo es nuevo (`file._committed` falso), no es SVG ni GIF animado y su
lado mayor supera `ORION_IMAGE_MAX_DIMENSION` (2048), se redimensiona con Willow
conservando el formato y se recalculan ancho, alto, peso y hash
(`_set_image_file_metadata`).

### SVG limpios
En la misma señal `pre_save`, un SVG nuevo se lee con `defusedxml.ElementTree` (acepta el
`DOCTYPE` que agregan las herramientas de diseño y rechaza entidades y referencias
externas; un archivo inválido produce `ValidationError` en el formulario
mediante un validador del campo) y se reescribe dejando solo elementos y atributos de una
lista de permitidos (formas, trazos, gradientes, `text`, `g`, `defs`, `use` con `href`
interno `#...`, estilos de presentación, `style` y `<style>` sin `@import`, `url()`
externos ni `javascript:`, que usan los SVG exportados para dar color). Se quitan
`script`, `foreignObject`, cualquier `on*`, `href`/`xlink:href` que no empiece con `#` y valores con
`url(` externos. El validador va en el formulario de imágenes
(`WAGTAILIMAGES_IMAGE_FORM_BASE = "orion.core.image_forms.ImageForm"`, en un módulo
propio porque `orion.core.forms` se importa antes de que carguen los modelos; el campo de
Wagtail ya rechaza la mayoría de los archivos rotos antes), así el
editor ve el error en el admin; la limpieza en `pre_save` cubre también las subidas por
código.

### Imágenes huérfanas
`manage.py orion_unused_images`: imágenes sin referencias en `ReferenceIndex`
(`ReferenceIndex.get_references_to(image)` vacío), con título, fecha y peso, y el total.
Los ajustes del sitio no están en el índice por defecto: `orion.site_data` registra
`SiteSettings` con `ReferenceIndex.register_model` (además, el admin muestra el uso de
los logos); una prueba lo confirma. Recomienda correr `rebuild_references_index` si el índice está
desactualizado. Solo lista.

### Recortes repetidos
Varias medidas comparten filtros ("image" y "article"); se generan una vez. Para saber
qué falta se compara el filtro ya resuelto por Wagtail (`clean_filter_for_svg`) y la
clave del punto focal, igual que guarda Wagtail.

### Dependencias de desarrollo
Al bloquear, `filelock`, `nodeenv` y `platformdirs` (de pre-commit) subían a versiones de
días; se fijan en `Pipfile` (4.2.0, 1.11.0 y 4.13.3) junto a `python-discovery`.

## Risks / Trade-offs

- [Hilo en segundo plano: si el proceso se recicla a mitad, faltan variantes] → se crean
  en la primera visita o con el comando; se documenta correrlo después de importar.
- [AVIF tarda más en codificar] → por eso se genera al subir y no en la visita.
- [`_set_image_file_metadata` es interno de Wagtail] → una prueba cubre la reducción; si
  Wagtail lo cambia, falla la prueba al actualizar.
- [La limpieza de SVG puede quitar algo legítimo poco común] → lista de permitidos amplia
  para SVG de logos e íconos; se documenta.
- [Las variantes WebP viejas quedan en disco] → no molestan; `wagtail` no las borra solas.

## Migration Plan

Sin migraciones. Después de actualizar, correr `manage.py orion_generate_renditions` para
crear las variantes AVIF de las imágenes existentes. Revertir: volver a la versión
anterior; las variantes AVIF quedan sin uso.
