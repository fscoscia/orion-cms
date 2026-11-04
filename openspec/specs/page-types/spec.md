# page-types Specification

## Purpose
Define los tipos de página con los que se arma un sitio Orion, dónde puede ir cada uno,
cómo se crea la portada inicial y cómo cada página mantiene un encabezado principal único.

## Requirements

### Requirement: Orion provides the base page types
Orion SHALL ofrecer los tipos de página Portada, Página libre, Página de contacto, Listado
de artículos y Artículo, creables desde el admin, y SHALL seguir mostrando con su diseño
las páginas de tipos que un proyecto agregue.

#### Scenario: Creating a page
- **WHEN** un editor crea una página debajo de la Portada
- **THEN** puede elegir Página libre, Página de contacto o Listado de artículos

### Requirement: Each page type has allowed places
La Portada SHALL ir solo en la raíz del sitio, con una por idioma. Las Páginas libres, las
de contacto y los Listados de artículos SHALL ir debajo de la Portada o de una Página
libre. Los Artículos SHALL ir solo dentro de un Listado de artículos, y un Listado de
artículos MUST NOT admitir otro tipo de página como hija.

#### Scenario: Article outside a listing
- **WHEN** un editor intenta crear un Artículo debajo de una Página libre
- **THEN** el admin no ofrece el tipo Artículo en ese lugar

#### Scenario: Second home page in a language
- **WHEN** ya existe la Portada en español y se intenta crear otra Portada en español
- **THEN** el admin no lo permite

### Requirement: The initial home page replaces Wagtail's welcome page
Al instalar Orion, la raíz del sitio SHALL pasar a ser una Portada en el idioma base, en
reemplazo de la página de bienvenida que crea Wagtail, solo si esa página sigue intacta:
sin cambios, sin páginas hijas y sin traducciones. Si fue modificada, la instalación MUST
NOT tocar el árbol de páginas.

#### Scenario: Fresh install
- **WHEN** se migra una base nueva
- **THEN** la raíz del sitio es una Portada y la página de bienvenida de Wagtail no existe

#### Scenario: Site already in use
- **WHEN** la página de bienvenida ya tiene páginas hijas
- **THEN** la migración no modifica ninguna página

### Requirement: Every page has exactly one main heading
Cada página SHALL tener un único encabezado `h1`: el título del Hero cuando el cuerpo
empieza con un Hero visible, o el título de la página en caso contrario. Cuando el cuerpo
empieza con un Carrusel a todo el ancho visible, el título de la página SHALL seguir
siendo el `h1`, visible solo para lectores de pantalla.

#### Scenario: Page without a hero
- **WHEN** una Página libre empieza con un bloque Texto
- **THEN** la página muestra su título como `h1` antes del cuerpo

#### Scenario: Page with a hero
- **WHEN** una Página libre empieza con un Hero
- **THEN** el título del Hero es el único `h1` de la página

#### Scenario: Page opening with a full-width carousel
- **WHEN** una Página libre empieza con un Carrusel a todo el ancho
- **THEN** el título de la página es el único `h1`, no ocupa lugar en pantalla y los
  títulos de las diapositivas no son `h1`

#### Scenario: Page opening with a cards carousel
- **WHEN** una Página libre empieza con un Carrusel de tarjetas
- **THEN** la página muestra su título como `h1` antes del cuerpo

### Requirement: The contact page always shows the site contact data
La Página de contacto SHALL mostrar los datos de contacto cargados en Datos del sitio
(teléfono, WhatsApp, email y dirección) y, si la ubicación está cargada, un mapa de esa
ubicación, además de su cuerpo de bloques, sin que el editor los cargue en la página.

#### Scenario: Phone changed in site data
- **WHEN** un administrador cambia el teléfono en Datos del sitio
- **THEN** la Página de contacto muestra el teléfono nuevo

#### Scenario: Location loaded
- **WHEN** la ubicación del sitio está cargada
- **THEN** la Página de contacto muestra el mapa de esa ubicación

#### Scenario: No location
- **WHEN** la ubicación del sitio no está cargada
- **THEN** la Página de contacto no muestra ningún mapa
