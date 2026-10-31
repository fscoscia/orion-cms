# content-blocks Specification

## Purpose
Define la biblioteca de bloques con la que los editores arman el contenido de las páginas:
qué bloques hay, qué carga el editor en cada uno, cómo se ocultan, cómo se resaltan los
títulos y cómo se traducen.

## Requirements

### Requirement: The block library offers the base blocks
Orion SHALL ofrecer los bloques Hero, Texto, Imagen, Galería, Imagen + texto, Tarjetas,
Cifras animadas, Pestañas, Acordeón, Llamada a la acción, Logos, Datos de contacto y Botón,
y un cuerpo de página que los reúne a todos para que un tipo de página lo use sin
declararlos uno por uno.

#### Scenario: Adding a block
- **WHEN** un editor agrega un bloque en un campo que usa el cuerpo de página de Orion
- **THEN** el selector ofrece los trece bloques

#### Scenario: Project with a subset
- **WHEN** un proyecto arma su propio cuerpo de página con algunos bloques de Orion y uno
  propio
- **THEN** el selector ofrece solo esos bloques y cada uno se muestra con su diseño

### Requirement: Blocks explain themselves in the editor
Cada bloque SHALL mostrarse en el selector con un nombre en el idioma del admin, un ícono,
una descripción de para qué sirve y una vista previa con contenido de ejemplo y los
estilos del sitio.

#### Scenario: Choosing a block
- **WHEN** un editor abre el selector de bloques
- **THEN** cada bloque muestra su nombre, su descripción y una vista previa

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
