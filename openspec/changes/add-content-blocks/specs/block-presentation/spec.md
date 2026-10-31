# Spec Delta

## Purpose

Define cómo ve y usa el visitante los bloques de contenido: estructura accesible,
imágenes livianas, interacción con teclado, comportamiento sin JavaScript y
compatibilidad con una política de seguridad de contenido estricta.

## ADDED Requirements

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
Las imágenes de los bloques SHALL servirse en WebP con varias medidas para que el
navegador elija la adecuada, SHALL declarar ancho y alto y SHALL cargarse en forma
diferida, salvo la imagen del Hero, que se carga de inmediato. Una imagen decorativa SHALL
tener texto alternativo vacío.

#### Scenario: Gallery images
- **WHEN** una página tiene una Galería
- **THEN** cada imagen tiene `srcset` en WebP, `width`, `height` y `loading="lazy"`

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
