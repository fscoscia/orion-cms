# content-blocks Specification

## Purpose
Define la biblioteca de bloques con la que los editores arman el contenido de las páginas:
qué bloques hay, qué carga el editor en cada uno, cómo se ocultan, cómo se resaltan los
títulos y cómo se traducen.

## Requirements

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

### Requirement: Blocks explain themselves in the editor
Cada bloque SHALL mostrarse en el selector con un nombre en el idioma del admin, un ícono,
una descripción de para qué sirve y una vista previa con contenido de ejemplo y los
estilos del sitio. Los bloques que muestran imágenes o artículos SHALL usar en su vista
previa imágenes y artículos de ejemplo que trae Orion, y la vista previa MUST NOT agregar
imágenes a la biblioteca ni crear páginas.

#### Scenario: Choosing a block
- **WHEN** un editor abre el selector de bloques
- **THEN** cada bloque muestra su nombre, su descripción y una vista previa

#### Scenario: Gallery preview on a new site
- **WHEN** un editor de un sitio sin imágenes cargadas mira la vista previa de la Galería
- **THEN** ve la galería con las imágenes de ejemplo de Orion y la biblioteca de imágenes
  sigue vacía

### Requirement: Blocks can be hidden without deleting them
Cada bloque SHALL tener un interruptor "Visible", activado por defecto. Un bloque oculto
MUST NOT mostrarse a los visitantes y SHALL conservar su contenido en el admin.

#### Scenario: Hiding a block
- **WHEN** un editor desactiva "Visible" en un bloque y publica
- **THEN** la página publicada no muestra ese bloque y el editor lo sigue viendo con su
  contenido

### Requirement: Projects define block styles
Cada bloque SHALL tener un campo "Estilo" cuyas opciones declara el proyecto en sus
ajustes, con un estilo por defecto que Orion provee. El valor elegido SHALL llegar al
template del bloque. Con una sola opción disponible, el campo MUST NOT mostrarse al editor.
Cambiar las opciones MUST NOT requerir migraciones, y un bloque cuyo estilo ya no existe
SHALL mostrarse con el estilo por defecto.

#### Scenario: Project with hero variants
- **WHEN** un proyecto declara los estilos "Estándar" e "Imagen al costado" para el Hero y
  un editor elige "Imagen al costado"
- **THEN** el template del Hero recibe ese estilo y la página lo muestra con esa variante

#### Scenario: Project without styles
- **WHEN** un proyecto no declara estilos
- **THEN** el editor no ve el campo "Estilo" y los bloques usan el estilo por defecto

#### Scenario: Style removed from settings
- **WHEN** un proyecto quita un estilo que un bloque publicado tenía elegido
- **THEN** la página muestra ese bloque con el estilo por defecto, sin error

### Requirement: Bold words in titles are highlighted
Los títulos de los bloques SHALL admitir solo negrita como formato, y las palabras en
negrita SHALL mostrarse con el color de acento del sitio. Un título MUST NOT admitir
otros formatos, enlaces ni varios párrafos.

#### Scenario: Highlighted word
- **WHEN** un editor escribe el título "Cuidamos **tu salud**"
- **THEN** la página muestra el título con "tu salud" en el color de acento, dentro de un
  único encabezado

### Requirement: Body text is limited to editorial formats
El bloque Texto y los paneles de Pestañas y Acordeón SHALL admitir solo negrita, itálica,
enlaces, listas y subtítulos.

#### Scenario: Text formats
- **WHEN** un editor escribe en un bloque Texto
- **THEN** la barra ofrece negrita, itálica, enlaces, listas y subtítulos, y ningún otro
  formato

### Requirement: Buttons use semantic destinations
Los botones de los bloques SHALL elegir su destino como cualquier enlace de contenido: una
página interna, una URL externa, un email o un teléfono, con las mismas validaciones. Un
botón sin destino visible MUST NOT mostrarse.

#### Scenario: Button to an unpublished page
- **WHEN** el botón de un Hero enlaza a una página que se despublica
- **THEN** el Hero se muestra sin ese botón

### Requirement: Images require alternative text or a decorative mark
Cada imagen de un bloque SHALL tener texto alternativo o estar marcada como decorativa.
El admin MUST rechazar una imagen sin ninguna de las dos cosas.

#### Scenario: Image without alt text
- **WHEN** un editor elige una imagen en un bloque Imagen sin escribir el texto
  alternativo ni marcarla como decorativa
- **THEN** el admin rechaza el bloque y pide una de las dos cosas

### Requirement: Contact block combines site data and extra items
El bloque Datos de contacto SHALL mostrar los datos del sitio que el editor elija entre
teléfono, WhatsApp, email y dirección, tomados de los datos del sitio, y SHALL admitir
datos extra cargados en el bloque, cada uno con etiqueta y texto. Un dato del sitio
elegido pero no cargado MUST NOT mostrarse.

#### Scenario: Site phone and opening hours
- **WHEN** el bloque muestra el teléfono del sitio y un dato extra "Horario: lunes a
  viernes de 7 a 19"
- **THEN** la página muestra el teléfono de los datos del sitio y el horario

#### Scenario: Phone changes in site data
- **WHEN** un administrador cambia el teléfono en los datos del sitio
- **THEN** todos los bloques Datos de contacto que lo muestran pasan a mostrar el nuevo

### Requirement: Tabs and accordion panels hold rich text
Cada pestaña y cada pregunta del acordeón SHALL tener un título y un texto enriquecido, y
MUST NOT admitir otros bloques adentro.

#### Scenario: Frequently asked questions
- **WHEN** un editor carga tres preguntas con sus respuestas en un Acordeón
- **THEN** la página muestra las tres preguntas con sus respuestas plegadas

### Requirement: Block content is translatable
El texto de los bloques SHALL traducirse con el flujo de traducción del sitio, y las
páginas y los datos elegidos en los bloques SHALL mostrarse en el idioma de la visita
cuando estén traducidos.

#### Scenario: Translated hero
- **WHEN** una página con un Hero se traduce a `en`
- **THEN** wagtail-localize ofrece el título, el texto y la etiqueta del botón para
  traducir, y `/en/` los muestra traducidos

### Requirement: The hero only opens a page body
En el cuerpo de página de Orion, el Hero SHALL admitirse solo como primer bloque. El admin
MUST rechazar un cuerpo con un Hero en otra posición o con más de un Hero.

#### Scenario: Hero in the middle
- **WHEN** un editor pone un Hero después de un bloque Texto y guarda
- **THEN** el admin rechaza el cuerpo e indica que el Hero va primero

### Requirement: Projects add blocks to Orion's pages
Un proyecto SHALL poder sumar bloques propios al cuerpo de las páginas de Orion declarándolos
en sus ajustes, sin crear tipos de página propios. Los bloques de Orion MUST seguir
disponibles.

#### Scenario: Block declared by the project
- **WHEN** el proyecto declara un bloque propio en sus ajustes
- **THEN** ese bloque se ofrece en el cuerpo de una página de contenido, junto a los de Orion

#### Scenario: No project blocks
- **WHEN** el proyecto no declara ningún bloque
- **THEN** el cuerpo ofrece solo los bloques de Orion

### Requirement: Project blocks stay out of Orion's migrations
Declarar bloques propios MUST NOT generar migraciones en las apps de Orion.

#### Scenario: Migration check with project blocks
- **WHEN** un proyecto con bloques propios corre `makemigrations --check`
- **THEN** no se detectan cambios en las apps de Orion

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

### Requirement: Blocks with a title offer an eyebrow
Los bloques con título SHALL ofrecer un antetítulo opcional de hasta 80 caracteres. Un
bloque sin antetítulo MUST mostrarse como hasta ahora.

#### Scenario: Cards with an eyebrow
- **WHEN** un editor escribe "Beneficios" como antetítulo de un bloque Tarjetas
- **THEN** la página muestra "Beneficios" sobre el título

#### Scenario: Block without a title field
- **WHEN** un editor agrega un bloque Texto
- **THEN** el bloque no ofrece antetítulo

### Requirement: Content blocks offer an anchor
Todos los bloques de contenido SHALL ofrecer un ancla opcional en sus ajustes. El ancla
MUST usar solo minúsculas, números y guiones, sin guiones al inicio o al final.

#### Scenario: Valid anchor
- **WHEN** un editor escribe `categorias` como ancla
- **THEN** el admin la acepta

#### Scenario: Invalid anchor
- **WHEN** un editor escribe `#Mis Categorías`
- **THEN** el admin la rechaza y explica el formato

#### Scenario: Project block
- **WHEN** un bloque de un proyecto hereda del bloque base de Orion
- **THEN** ofrece el ancla sin declararla

### Requirement: Anchors are unique within a page
El admin MUST rechazar un ancla repetida en el cuerpo de una página, y las anclas que usa
el propio sitio (`main-content` y `site-nav-panel`), señalando el bloque afectado.

#### Scenario: Repeated anchor
- **WHEN** dos bloques de una página usan el ancla `requisitos`
- **THEN** el admin rechaza la página y marca el segundo bloque

#### Scenario: Reserved anchor
- **WHEN** un bloque usa el ancla `main-content`
- **THEN** el admin la rechaza

### Requirement: Eyebrows are translated and anchors are kept
El antetítulo SHALL traducirse con el flujo de traducción del sitio. El ancla MUST NOT
ofrecerse para traducir y SHALL conservarse en cada idioma.

#### Scenario: Translated page
- **WHEN** una página con antetítulo y ancla se traduce a `en`
- **THEN** wagtail-localize ofrece el antetítulo y la traducción conserva el ancla

### Requirement: Existing content survives the new fields
Sumar el antetítulo y el ancla MUST NOT modificar el contenido existente, y sus migraciones
SHALL limitarse a la definición de los bloques.

#### Scenario: Migrating a site with content
- **WHEN** un sitio con páginas y menús aplica las migraciones
- **THEN** cada página y cada menú se muestran como antes

### Requirement: Cards can carry a tag and fit their image
Cada tarjeta SHALL ofrecer una etiqueta opcional de hasta 40 caracteres, que se muestra sobre
su título. El bloque Tarjetas SHALL ofrecer un ajuste de imagen con dos opciones: recortada
para llenar el espacio, por defecto, o completa dentro del espacio. Una tarjeta sin etiqueta
y un bloque con el ajuste por defecto MUST mostrarse como hasta ahora.

#### Scenario: Card with a tag
- **WHEN** un editor escribe "Categoría 1" como etiqueta de una tarjeta
- **THEN** la página muestra "Categoría 1" sobre el título de esa tarjeta

#### Scenario: Card without a tag
- **WHEN** un editor deja la etiqueta vacía
- **THEN** la tarjeta se muestra sin etiqueta y sin espacio reservado

#### Scenario: Tag too long
- **WHEN** un editor escribe una etiqueta de más de 40 caracteres
- **THEN** el admin rechaza la tarjeta

#### Scenario: Whole image
- **WHEN** un editor elige mostrar la imagen completa en un bloque de tarjetas con ilustraciones
- **THEN** la imagen de cada tarjeta se ve entera, sin recortes

#### Scenario: Existing cards
- **WHEN** un sitio con tarjetas publicadas aplica la migración
- **THEN** las tarjetas se ven igual que antes: sin etiqueta y con la imagen recortada
