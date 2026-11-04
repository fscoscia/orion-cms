# Spec Delta

## ADDED Requirements

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
