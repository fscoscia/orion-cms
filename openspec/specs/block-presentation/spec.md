# block-presentation Specification

## Purpose
Define cómo ve y usa el visitante los bloques de contenido: estructura accesible,
imágenes livianas, interacción con teclado, comportamiento sin JavaScript y
compatibilidad con una política de seguridad de contenido estricta.

## Requirements

### Requirement: Blocks render with Orion's base design
Cada bloque SHALL mostrarse con el diseño base de Orion sin que el proyecto compile CSS, y
SHALL usar los colores y las fuentes definidos como variables CSS.

#### Scenario: Project without a build step
- **WHEN** un proyecto usa los bloques de Orion sin compilar CSS propio
- **THEN** cada bloque se ve con su diseño base

#### Scenario: Project fonts
- **WHEN** un proyecto carga una tipografía propia y redefine la fuente del texto y la de
  los títulos con variables CSS
- **THEN** el texto de los bloques, incluido el texto enriquecido, usa la fuente del texto
  y los títulos de los bloques y los subtítulos del texto enriquecido usan la de títulos

#### Scenario: Brand color
- **WHEN** un proyecto redefine el color principal y el de acento con variables CSS
- **THEN** los botones, los fondos de los bloques y los títulos resaltados usan los
  colores nuevos

### Requirement: Headings keep a valid outline
El título del Hero SHALL ser el encabezado principal de la página y los títulos de los
demás bloques SHALL ser encabezados de segundo nivel, de modo que la página mantenga una
jerarquía de encabezados válida.

#### Scenario: Page with a hero and cards
- **WHEN** una página tiene un Hero seguido de un bloque Tarjetas
- **THEN** el título del Hero es un `h1` y el de las Tarjetas un `h2`

### Requirement: Images are responsive and lightweight
Las imágenes de los bloques SHALL servirse en AVIF, con WebP de respaldo, en varias
medidas para que el navegador elija la adecuada, SHALL declarar ancho y alto y SHALL
cargarse en forma diferida, salvo la imagen del Hero, que se carga de inmediato con
prioridad alta. Cuando el primer bloque de una página es un Hero con imagen, la página
SHALL precargar esa imagen. Una imagen decorativa SHALL tener texto alternativo vacío.

#### Scenario: Gallery images
- **WHEN** una página tiene una Galería
- **THEN** cada imagen es un `<picture>` con una fuente AVIF con `srcset` y un `<img>` de
  respaldo con `srcset` en WebP, `width`, `height` y `loading="lazy"`

#### Scenario: Hero image
- **WHEN** una página empieza con un Hero con imagen
- **THEN** la imagen no es diferida, tiene `fetchpriority="high"` y el `<head>` la
  precarga en AVIF con las mismas medidas

#### Scenario: Decorative image
- **WHEN** una imagen está marcada como decorativa
- **THEN** su `alt` está vacío

### Requirement: The accordion works without JavaScript
Cada pregunta del acordeón SHALL abrirse y cerrarse con el mouse, el teclado y los
lectores de pantalla sin depender de JavaScript.

#### Scenario: Keyboard
- **WHEN** un visitante enfoca una pregunta con Tab y presiona Enter
- **THEN** la respuesta se muestra, y al presionar Enter de nuevo se oculta

### Requirement: Tabs are keyboard accessible and degrade to sections
Las pestañas SHALL seguir el patrón accesible de pestañas: una lista de pestañas con la
seleccionada marcada, flechas izquierda y derecha para moverse entre ellas y un solo panel
visible. Sin JavaScript, SHALL mostrarse todos los paneles uno debajo del otro con sus
títulos.

#### Scenario: Arrow keys
- **WHEN** el foco está en la primera pestaña y el visitante presiona la flecha derecha
- **THEN** se selecciona la segunda pestaña, se muestra su panel y recibe el foco

#### Scenario: Without JavaScript
- **WHEN** el navegador no ejecuta JavaScript
- **THEN** se ven los títulos y el contenido de todas las pestañas

### Requirement: Animated figures respect the visitor
Las cifras SHALL mostrar su número final sin JavaScript. Con JavaScript, SHALL contar
desde cero hasta el número final cuando el bloque aparece en pantalla, salvo que el
visitante haya pedido movimiento reducido, en cuyo caso se muestran sin animación. Los
lectores de pantalla SHALL leer solo el número final.

#### Scenario: Reduced motion
- **WHEN** el sistema del visitante pide movimiento reducido
- **THEN** las cifras aparecen con su número final, sin contar

#### Scenario: Without JavaScript
- **WHEN** el navegador no ejecuta JavaScript
- **THEN** cada cifra muestra su número final

### Requirement: Block scripts work under a strict Content Security Policy
Los comportamientos interactivos de los bloques MUST funcionar sin evaluar código en el
navegador ni usar scripts o estilos en línea, bajo una política que prohíba `unsafe-eval`,
`unsafe-inline` en scripts y estilos en línea.

#### Scenario: Strict policy
- **WHEN** una página con Pestañas, Acordeón y Cifras se sirve con esa política
- **THEN** los tres funcionan y el navegador no informa violaciones

### Requirement: External links in blocks open safely
Un botón o una tarjeta que abre un enlace en una pestaña nueva MUST incluir
`rel="noopener noreferrer"`, y un logo con enlace SHALL tener un nombre accesible.

#### Scenario: Partner logo
- **WHEN** un logo enlaza al sitio de un convenio
- **THEN** el enlace se anuncia con el nombre del convenio

### Requirement: Videos do not load until they are needed
Un video MUST NOT descargarse al abrir la página: SHALL mostrar su portada y empezar a
descargarse cuando el visitante lo inicia o, en modo ambiente, cuando entra en pantalla.
La portada SHALL declarar su ancho y su alto para que la página no salte.

#### Scenario: Video below the fold
- **WHEN** una página tiene un video fuera de la pantalla
- **THEN** el navegador no pide el archivo de video y la portada es diferida

### Requirement: Controlled videos are started by the visitor
Un video con controles SHALL mostrar su portada con un botón de reproducir e iniciarse
solo por acción del visitante, con sonido y con los controles nativos del navegador,
usables con el teclado. Sin JavaScript SHALL mostrar los controles nativos.

#### Scenario: Pressing play
- **WHEN** un visitante pulsa el botón de reproducir sobre la portada
- **THEN** el video se reproduce con sonido y puede pausarlo con el teclado

#### Scenario: Controlled video without JavaScript
- **WHEN** un visitante abre un video con controles sin JavaScript
- **THEN** puede iniciarlo con los controles nativos

### Requirement: Ambient videos respect the visitor
Un video ambiente SHALL reproducirse sin sonido y en bucle solo mientras esté en pantalla.
Con `prefers-reduced-motion` o sin JavaScript MUST NOT reproducirse: SHALL quedar la
portada.

#### Scenario: Leaving the screen
- **WHEN** un visitante desplaza la página hasta sacar un video ambiente de la pantalla
- **THEN** el video se pausa, y vuelve a reproducirse cuando regresa

#### Scenario: Reduced motion
- **WHEN** el visitante tiene activado `prefers-reduced-motion`
- **THEN** el video ambiente no se reproduce y se ve su portada

### Requirement: Visitors can pause ambient videos
Un video ambiente en reproducción SHALL ofrecer un botón de pausa usable con el teclado, y
lo que el visitante pausa MUST NOT reanudarse solo.

#### Scenario: Pausing
- **WHEN** un visitante pausa un video ambiente y vuelve a pasar por él
- **THEN** el video sigue pausado hasta que pulsa el botón otra vez

### Requirement: Carousels are operable by every input
El carrusel SHALL recorrerse con botones de anterior y siguiente, con puntos que indican
la posición, con las flechas del teclado y con gesto táctil. Los controles SHALL tener
nombre accesible y la posición actual SHALL anunciarse.

#### Scenario: Keyboard
- **WHEN** el foco está en el carrusel y el visitante pulsa la flecha derecha
- **THEN** el carrusel avanza a la siguiente diapositiva

#### Scenario: Last slide
- **WHEN** el carrusel está en la última diapositiva
- **THEN** el botón de siguiente queda deshabilitado

### Requirement: Carousels degrade to scrolling
Sin JavaScript todas las diapositivas SHALL ser accesibles con desplazamiento horizontal
y los botones y los puntos MUST NOT mostrarse.

#### Scenario: No JavaScript
- **WHEN** un visitante abre un carrusel sin JavaScript
- **THEN** recorre las diapositivas desplazándolas y no ve controles que no funcionan

### Requirement: Slides pause what leaves the screen
Una diapositiva que deja de verse MUST NOT seguir reproduciendo su video.

#### Scenario: Moving to another slide
- **WHEN** un visitante pasa a otra diapositiva con un video en reproducción
- **THEN** ese video se pausa

### Requirement: A leading carousel loads its first image first
Cuando el primer bloque visible de una página es un Carrusel a todo el ancho, la imagen
de su primera diapositiva MUST NOT ser diferida, SHALL tener prioridad alta y la página
SHALL precargarla, como la del Hero. Las demás imágenes SHALL ser diferidas.

#### Scenario: Page opening with a carousel
- **WHEN** una página empieza con un Carrusel a todo el ancho
- **THEN** la primera imagen tiene `fetchpriority="high"`, el `<head>` la precarga en AVIF
  y las demás tienen `loading="lazy"`

#### Scenario: Carousel further down
- **WHEN** un Carrusel no es el primer bloque de la página
- **THEN** todas sus imágenes son diferidas

### Requirement: Eyebrows sit above the title without changing the outline
El antetítulo SHALL mostrarse sobre el título, con el diseño base de Orion, y MUST NOT ser
un encabezado. Sobre fondos oscuros SHALL conservar el contraste.

#### Scenario: Hero with an eyebrow
- **WHEN** un Hero tiene antetítulo
- **THEN** el antetítulo es un párrafo antes del `h1` y la página conserva un solo `h1`

#### Scenario: Eyebrow without a title
- **WHEN** un bloque tiene antetítulo y su título opcional está vacío
- **THEN** la página muestra el antetítulo, sin un encabezado vacío

### Requirement: Anchors identify their block on the page
El ancla de un bloque visible SHALL ser el `id` de ese bloque en la página. Un bloque oculto
MUST NOT aparecer, con su ancla incluida.

#### Scenario: Link to a section
- **WHEN** un visitante abre `/#categorias` y un bloque visible tiene el ancla `categorias`
- **THEN** el navegador lleva al visitante a ese bloque

#### Scenario: Hidden block
- **WHEN** el bloque con el ancla `categorias` está oculto
- **THEN** la página no contiene ese `id`
