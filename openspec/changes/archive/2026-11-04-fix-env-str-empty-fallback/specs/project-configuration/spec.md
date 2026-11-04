## ADDED Requirements

### Requirement: A text variable with a default falls back when present but empty
Cuando una variable de entorno de texto tiene un valor por defecto no vacío, el sistema
SHALL usar ese default tanto si la variable está ausente como si está presente pero
vacía (o solo espacios).

#### Scenario: Variable absent
- **WHEN** `ORION_SEARCH_CONFIG` no está definida y `LANGUAGE_CODE` vale `es`
- **THEN** la configuración de búsqueda de PostgreSQL es `spanish`

#### Scenario: Variable present and empty
- **WHEN** `ORION_SEARCH_CONFIG` está definida como cadena vacía y `LANGUAGE_CODE` vale
  `es`
- **THEN** la configuración de búsqueda de PostgreSQL es `spanish`, igual que si la
  variable estuviera ausente

#### Scenario: Variable present with an explicit value
- **WHEN** `ORION_SEARCH_CONFIG` vale `simple`
- **THEN** la configuración de búsqueda de PostgreSQL es `simple`
