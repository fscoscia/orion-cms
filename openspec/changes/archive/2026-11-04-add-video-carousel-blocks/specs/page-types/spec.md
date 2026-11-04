# Spec Delta

## MODIFIED Requirements

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
