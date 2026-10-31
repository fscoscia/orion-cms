# Spec Delta

## MODIFIED Requirements

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
