# site-languages Specification

## Purpose
Define qué idiomas puede tener un sitio construido sobre Orion, cuál es el idioma base, y
cómo se decide qué idiomas se editan en el admin y cuáles se muestran a los visitantes.

## Requirements

### Requirement: Languages come from a catalog defined in code
El sistema SHALL ofrecer para agregar solo los idiomas de un catálogo definido en la
configuración del proyecto.

#### Scenario: Adding a catalog language
- **WHEN** un administrador agrega un idioma desde el admin
- **THEN** solo puede elegirlo entre los idiomas del catálogo

### Requirement: The base language must belong to the catalog
El sistema MUST negarse a arrancar si el idioma base configurado no está en el catálogo.

#### Scenario: Base language outside the catalog
- **WHEN** `LANGUAGE_CODE` vale un idioma que el catálogo no incluye
- **THEN** el arranque falla con un mensaje que nombra el idioma y el catálogo

### Requirement: A new site starts with only the base language
Un sitio recién instalado SHALL tener un único idioma, el idioma base, con su página de
inicio.

#### Scenario: Fresh installation
- **WHEN** se migra una base de datos vacía con `LANGUAGE_CODE` igual a `es`
- **THEN** el único idioma existente es `es`

### Requirement: Added languages are editable, public ones are visible
Un idioma agregado SHALL poder editarse en el admin desde ese momento, pero SHALL mostrarse
a los visitantes solo cuando un administrador lo marca como público.

#### Scenario: Language added but not public
- **WHEN** se agrega el idioma `en` sin marcarlo como público
- **THEN** los editores pueden crear contenido en `en` y los visitantes no lo ven

#### Scenario: Language made public
- **WHEN** un administrador marca `en` como público
- **THEN** los visitantes pueden ver el contenido publicado en `en`

### Requirement: The base language is always public
El idioma base MUST ser siempre público, aunque no figure entre los marcados como públicos.

#### Scenario: Base language not marked
- **WHEN** la lista de idiomas públicos no incluye al idioma base
- **THEN** el contenido del idioma base sigue visible para los visitantes

### Requirement: Only administrators manage languages
Agregar idiomas y decidir cuáles son públicos MUST estar restringido a usuarios con permiso
para administrar idiomas y ajustes del sitio.

#### Scenario: Editor without permission
- **WHEN** un editor sin esos permisos intenta cambiar los idiomas públicos
- **THEN** el admin no le muestra la opción y rechaza el cambio
