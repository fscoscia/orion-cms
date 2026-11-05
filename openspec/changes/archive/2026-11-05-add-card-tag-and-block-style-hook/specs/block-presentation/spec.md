## ADDED Requirements

### Requirement: The block wrapper exposes its style
La envoltura de cada bloque visible SHALL exponer el estilo elegido por el editor con un
atributo `data-block-style`, de modo que un proyecto pueda pintar la banda del bloque de
borde a borde. El estilo por defecto MUST NOT agregar el atributo, y las clases actuales de
la envoltura y de la sección interna MUST NOT cambiar.

#### Scenario: Style from the project
- **WHEN** un proyecto declara el estilo "oscuro" para un bloque y un editor lo elige
- **THEN** la envoltura del bloque lleva `data-block-style="oscuro"`

#### Scenario: Default style
- **WHEN** un editor deja el estilo por defecto
- **THEN** la envoltura no lleva el atributo `data-block-style`

#### Scenario: Existing selectors keep working
- **WHEN** un proyecto estiliza un bloque con `.block-cards--oscuro`
- **THEN** ese selector sigue aplicándose solo a la sección interna, como antes
