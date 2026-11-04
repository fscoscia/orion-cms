## ADDED Requirements

### Requirement: Projects add blocks to Orion's pages
Un proyecto SHALL poder sumar bloques propios al cuerpo de las páginas de Orion declarándolos
en sus ajustes, sin crear tipos de página propios. Los bloques de Orion MUST seguir
disponibles.

#### Scenario: Block declared by the project
- **WHEN** el proyecto declara un bloque propio en sus ajustes
- **THEN** ese bloque se ofrece en el cuerpo de una página de contenido, junto a los de Orion

#### Scenario: No project blocks
- **WHEN** el proyecto no declara ningún bloque
- **THEN** el cuerpo ofrece solo los bloques de Orion

### Requirement: Project blocks stay out of Orion's migrations
Declarar bloques propios MUST NOT generar migraciones en las apps de Orion.

#### Scenario: Migration check with project blocks
- **WHEN** un proyecto con bloques propios corre `makemigrations --check`
- **THEN** no se detectan cambios en las apps de Orion
