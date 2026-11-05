## ADDED Requirements

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
