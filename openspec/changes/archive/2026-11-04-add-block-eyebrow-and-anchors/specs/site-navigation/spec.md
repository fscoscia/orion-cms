# Spec Delta

## MODIFIED Requirements

### Requirement: Current page is marked
El ítem que corresponde a la página que se está viendo, o a una de sus páginas superiores,
SHALL marcarse como actual de forma accesible.
Un enlace con ancla MUST NOT marcar su página como la actual.

#### Scenario: Visiting a child page
- **WHEN** se visita una subpágina de "Servicios"
- **THEN** el ítem "Servicios" se marca con `aria-current`

#### Scenario: Link to a section
- **WHEN** un visitante está en el inicio y un ítem apunta a `/#categorias`
- **THEN** ese ítem no se marca como página actual
