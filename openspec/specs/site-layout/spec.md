# site-layout Specification

## Purpose
Define el encabezado y el pie que hereda toda página de un sitio Orion: qué muestran, cómo
se usan con teclado y en celular, y cómo un proyecto cambia su aspecto sin compilar código.

## Requirements

### Requirement: Every page has a header and a footer
Toda página que use la plantilla base de Orion SHALL mostrar un encabezado con el logo, el
menú del encabezado y el selector de idioma, y un pie con el logo del pie, el eslogan, los
datos de contacto, las redes sociales, el menú del pie y el texto legal.

#### Scenario: Page with all data loaded
- **WHEN** todos los datos del sitio y ambos menús están cargados
- **THEN** la página muestra cada uno en el encabezado o el pie

### Requirement: Keyboard users can skip to the content
La primera parte enfocable de cada página SHALL ser un enlace que lleva al contenido
principal, visible al recibir el foco.

#### Scenario: First tab
- **WHEN** un visitante presiona Tab al cargar la página
- **THEN** el foco llega al enlace "Saltar al contenido", que apunta a `#main-content`

### Requirement: The mobile menu is accessible
En pantallas angostas el menú del encabezado SHALL abrirse con un botón que informa su estado
con `aria-expanded`, y SHALL cerrarse con Escape devolviendo el foco al botón. Los submenús
SHALL abrirse con botones que informan su estado de la misma forma.

#### Scenario: Opening and closing
- **WHEN** un visitante abre el menú con el botón y presiona Escape
- **THEN** el menú se cierra, `aria-expanded` vuelve a `false` y el foco vuelve al botón

#### Scenario: Without JavaScript
- **WHEN** el navegador no ejecuta JavaScript
- **THEN** los ítems del menú siguen visibles y navegables

### Requirement: The site works without a CSS build
Un proyecto SHALL poder mostrar el encabezado, el pie y las páginas de Orion con estilos sin
instalar Node ni compilar CSS.

#### Scenario: Project without a build step
- **WHEN** un proyecto instala Orion y no compila CSS propio
- **THEN** las páginas cargan la hoja de estilos de Orion y se ven con su diseño base

### Requirement: Brand colors and fonts are CSS variables
Los colores y las fuentes del diseño base SHALL definirse como variables CSS que un proyecto
puede reemplazar con una hoja de estilos propia, sin recompilar el CSS de Orion.

#### Scenario: Changing the primary color
- **WHEN** un proyecto redefine la variable del color principal en su hoja de estilos
- **THEN** los botones y enlaces del encabezado y el pie usan el color nuevo

### Requirement: Interactive scripts are compatible with a strict Content Security Policy
Los scripts que Orion incluye MUST funcionar sin evaluar código en el navegador, para
admitir una política de seguridad de contenido que prohíba `unsafe-eval` y scripts en línea.

#### Scenario: Strict policy
- **WHEN** el sitio se sirve con una política que prohíbe `unsafe-eval` y scripts en línea
- **THEN** el menú en celular sigue funcionando
