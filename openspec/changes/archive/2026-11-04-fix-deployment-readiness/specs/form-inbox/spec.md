## ADDED Requirements

### Requirement: CSV exports do not run visitors' formulas
La exportación CSV MUST neutralizar todo valor escrito por un visitante que una planilla
interpretaría como fórmula, conservando su texto legible. Los números y teléfonos MUST
exportarse sin cambios.

#### Scenario: Value that starts a formula
- **WHEN** un envío tiene `=HYPERLINK("http://example.test","x")` en un campo y se exporta
  a CSV
- **THEN** la celda empieza con un apóstrofo seguido del texto original

#### Scenario: Other formula prefixes
- **WHEN** un valor empieza con `@`, con una tabulación, con `+` o `-` seguidos de letras
  o de un salto de línea, y se exporta a CSV
- **THEN** la celda empieza con un apóstrofo seguido del texto original

#### Scenario: Phone number
- **WHEN** un envío tiene `+595 21 729 1444` en un campo y se exporta a CSV
- **THEN** la celda tiene ese mismo valor, sin apóstrofo

#### Scenario: Excel export
- **WHEN** ese mismo envío con la fórmula se exporta a Excel
- **THEN** la celda es de texto y no una fórmula
