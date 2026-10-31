# Spec Delta

## MODIFIED Requirements

### Requirement: The block library offers the base blocks
Orion SHALL ofrecer los bloques Hero, Texto, Imagen, Galería, Imagen + texto, Tarjetas,
Cifras animadas, Pestañas, Acordeón, Llamada a la acción, Logos, Datos de contacto, Botón y
Últimas novedades, y un cuerpo de página que los reúne a todos para que un tipo de página
lo use sin declararlos uno por uno.

#### Scenario: Adding a block
- **WHEN** un editor agrega un bloque en un campo que usa el cuerpo de página de Orion
- **THEN** el selector ofrece los catorce bloques

#### Scenario: Project with a subset
- **WHEN** un proyecto arma su propio cuerpo de página con algunos bloques de Orion y uno
  propio
- **THEN** el selector ofrece solo esos bloques y cada uno se muestra con su diseño

## ADDED Requirements

### Requirement: The hero only opens a page body
En el cuerpo de página de Orion, el Hero SHALL admitirse solo como primer bloque. El admin
MUST rechazar un cuerpo con un Hero en otra posición o con más de un Hero.

#### Scenario: Hero in the middle
- **WHEN** un editor pone un Hero después de un bloque Texto y guarda
- **THEN** el admin rechaza el cuerpo e indica que el Hero va primero
