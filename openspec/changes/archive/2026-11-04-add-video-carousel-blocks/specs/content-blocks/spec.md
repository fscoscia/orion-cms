# Spec Delta

## MODIFIED Requirements

### Requirement: The block library offers the base blocks
Orion SHALL ofrecer los bloques Hero, Texto, Imagen, Galería, Imagen + texto, Tarjetas,
Cifras animadas, Pestañas, Acordeón, Llamada a la acción, Logos, Datos de contacto, Botón,
Últimas novedades, Mapa, Video y Carrusel, y un cuerpo de página que los reúne a todos
para que un tipo de página lo use sin declararlos uno por uno.

#### Scenario: Adding a block
- **WHEN** un editor agrega un bloque en un campo que usa el cuerpo de página de Orion
- **THEN** el selector ofrece los diecisiete bloques

#### Scenario: Project with a subset
- **WHEN** un proyecto arma su propio cuerpo de página con algunos bloques de Orion y uno
  propio
- **THEN** el selector ofrece solo esos bloques y cada uno se muestra con su diseño

## ADDED Requirements

### Requirement: The video block shows a library video with a cover
El bloque Video SHALL pedir un video de la biblioteca de documentos y una imagen de
portada, y SHALL ofrecer un título y un pie opcionales. Un documento que no sea MP4 ni
WebM MUST rechazarse con un mensaje claro.

#### Scenario: Video with its cover
- **WHEN** un editor elige un MP4 y una portada, y publica
- **THEN** la página muestra el video con esa portada

#### Scenario: Document that is not a video
- **WHEN** un editor elige un PDF en el campo de video
- **THEN** el admin rechaza el bloque y explica que debe ser un MP4 o un WebM

#### Scenario: Missing cover
- **WHEN** un editor guarda el bloque sin portada
- **THEN** el admin pide la imagen

### Requirement: The video block offers a playback mode and a format
El editor SHALL elegir el modo del video, con controles o ambiente, y su formato,
horizontal o vertical. Por defecto SHALL ser con controles y horizontal.

#### Scenario: Vertical ambient video
- **WHEN** un editor elige el modo ambiente y el formato vertical
- **THEN** el video se muestra en proporción 9:16 y sin controles

### Requirement: The carousel block holds slides
El bloque Carrusel SHALL contener de 2 a 12 diapositivas y un título opcional. Cada
diapositiva SHALL pedir una imagen y SHALL ofrecer un video, un título, un texto y un
enlace, todos opcionales. Cuando tiene video, la imagen SHALL ser su portada y el video
SHALL reproducirse en modo ambiente.

#### Scenario: Slides with text and link
- **WHEN** un editor carga tres diapositivas con título, texto y enlace
- **THEN** la página las muestra en ese orden

#### Scenario: Single slide
- **WHEN** un editor guarda un carrusel con una sola diapositiva
- **THEN** el admin pide al menos dos

#### Scenario: Document that is not a video in a slide
- **WHEN** un editor elige un PDF como video de una diapositiva
- **THEN** el admin rechaza la diapositiva y explica que debe ser un MP4 o un WebM

### Requirement: The carousel block offers two layouts
El editor SHALL elegir la disposición del carrusel: una diapositiva a todo el ancho o
varias tarjetas visibles a la vez. Por defecto SHALL ser a todo el ancho.

#### Scenario: Full-width layout
- **WHEN** un carrusel usa la disposición a todo el ancho
- **THEN** se ve una diapositiva por vez, ocupando todo el ancho de la página

#### Scenario: Cards layout
- **WHEN** un carrusel usa la disposición de tarjetas en una pantalla de escritorio
- **THEN** se ven varias diapositivas a la vez y el resto queda a un desplazamiento

### Requirement: Existing content survives the new blocks
Sumar los bloques Video y Carrusel MUST NOT modificar el contenido de las páginas
existentes, y su migración SHALL limitarse a la definición de los bloques.

#### Scenario: Migrating a site with content
- **WHEN** un sitio con páginas publicadas aplica la migración
- **THEN** el cuerpo de cada página queda igual y se muestra como antes
