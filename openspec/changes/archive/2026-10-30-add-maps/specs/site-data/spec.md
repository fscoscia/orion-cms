# Spec Delta

## MODIFIED Requirements

### Requirement: Fixed site data has a single place
El logo, el logo del pie, el teléfono, el WhatsApp, el email, la dirección, la ubicación en
el mapa y las redes sociales SHALL editarse en un único lugar del admin y valer para todos
los idiomas.

#### Scenario: Phone shown in every language
- **WHEN** se carga el teléfono y se visita el sitio en `es` y en `en`
- **THEN** ambas versiones muestran el mismo teléfono

#### Scenario: Location shown in every language
- **WHEN** se elige la ubicación del sitio y se visita la página de contacto en `es` y en
  `en`
- **THEN** ambas versiones muestran el mapa en la misma ubicación
