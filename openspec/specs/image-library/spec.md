# image-library Specification

## Purpose
Define qué acepta la biblioteca de imágenes, cómo se preparan las variantes de cada imagen
y cómo las plantillas de un proyecto muestran imágenes livianas y responsivas.

## Requirements

### Requirement: Templates show images through named sizes
Orion SHALL ofrecer a las plantillas un componente de imagen que recibe una imagen y el
nombre de una medida (por ejemplo "card") y muestra un `<picture>` con una fuente AVIF
en las anchuras de esa medida y el `sizes` de la medida, y un `<img>` de respaldo en WebP
con las mismas anchuras, `width`, `height`, `alt`, `loading="lazy"` y
`decoding="async"`. Marcada como principal, la imagen
MUST NOT ser diferida y SHALL llevar `fetchpriority="high"`. Un proyecto SHALL poder sumar
medidas propias o cambiar las de Orion desde los ajustes. Un nombre de medida inexistente
MUST fallar de forma visible al desarrollar, no en silencio.

#### Scenario: Card image
- **WHEN** una plantilla muestra una imagen con la medida "card"
- **THEN** el HTML tiene un `<source type="image/avif">` y un `<img>` diferido con
  `srcset` en WebP, ancho y alto

#### Scenario: Project size
- **WHEN** un proyecto define la medida "team" en sus ajustes
- **THEN** sus plantillas la usan como las de Orion y sus recortes también se generan al
  subir

#### Scenario: Unknown size
- **WHEN** una plantilla pide una medida que no existe
- **THEN** el desarrollo muestra un error que nombra la medida

### Requirement: Variants are generated when an image is uploaded
Al subir una imagen, cambiar su archivo o su punto focal, Orion SHALL generar en segundo
plano los recortes de todas las medidas, sin demorar la respuesta del admin. Un comando
SHALL generar los recortes que falten de todas las imágenes. Si un recorte falta igual al
mostrar la página, la página SHALL mostrarse generándolo en el momento.

#### Scenario: Upload
- **WHEN** un editor sube una foto
- **THEN** poco después existen sus recortes AVIF y WebP de todas las medidas

#### Scenario: Existing library
- **WHEN** el desarrollador corre el comando en un sitio con imágenes subidas antes
- **THEN** se generan los recortes faltantes y el comando informa cuántos creó

### Requirement: Uploads are limited and large originals are reduced
La biblioteca SHALL aceptar solo los formatos configurados (por defecto JPG, PNG, WebP,
AVIF, GIF y SVG) y hasta el peso máximo configurado (por defecto 10 MB), con un mensaje en
español al rechazar. Un original de mapa de bits de más de 2048 px de ancho o de alto SHALL
reducirse al subirlo para que su lado mayor mida 2048 px, conservando la proporción.

#### Scenario: Large photo
- **WHEN** un editor sube una foto de 6000 × 4000 px
- **THEN** la imagen guardada mide 2048 × 1365 px

#### Scenario: Not allowed
- **WHEN** un editor intenta subir un archivo de un formato no permitido o más pesado que
  el máximo
- **THEN** el admin lo rechaza con un mensaje claro y no se guarda nada

### Requirement: SVG images are cleaned
Al subir un SVG, la biblioteca SHALL quitar los elementos y atributos que no están en una
lista de permitidos, incluidos `<script>`, `<foreignObject>`, manejadores de eventos
(`on*`), enlaces `javascript:` y referencias a recursos externos. Un archivo que no es un
SVG válido MUST rechazarse. Los SVG MUST mostrarse como SVG, sin convertirse a otro
formato.

#### Scenario: SVG with a script
- **WHEN** un editor sube un logo SVG con un `<script>` y un atributo `onload`
- **THEN** el archivo guardado conserva el dibujo y no tiene ni el script ni el atributo

#### Scenario: SVG in a block
- **WHEN** un bloque muestra un logo SVG
- **THEN** la página lo sirve como SVG

### Requirement: Unused images can be listed
Un comando SHALL listar las imágenes que no se usan en ninguna página, fragmento ni ajuste
del sitio, con su título, fecha de subida y peso, y el total. MUST NOT borrar nada.

#### Scenario: Orphan image
- **WHEN** una imagen no se usa en ningún lado
- **THEN** el comando la lista

#### Scenario: Used image
- **WHEN** una imagen se usa en un bloque de una página
- **THEN** el comando no la lista
