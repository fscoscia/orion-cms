# Spec Delta

## ADDED Requirements

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
