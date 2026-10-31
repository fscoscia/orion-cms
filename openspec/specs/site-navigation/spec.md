# site-navigation Specification

## Purpose
Define los menús del encabezado y del pie: cómo se estructuran, cómo se traducen y qué
ítems ve un visitante.

## Requirements

### Requirement: Header and footer each have one menu per language
El sitio SHALL tener un menú para el encabezado y otro para el pie, como máximo uno de cada
ubicación por idioma, editables por separado del árbol de páginas.

#### Scenario: Second header menu in the same language
- **WHEN** se intenta crear otro menú del encabezado en un idioma que ya tiene uno
- **THEN** el admin lo rechaza

### Requirement: Menus have two levels
Cada ítem del menú SHALL poder tener una lista de subítems, y los subítems MUST NOT tener
subítems propios.

#### Scenario: Item with a submenu
- **WHEN** un ítem "Servicios" tiene los subítems "Consultorios" e "Internación"
- **THEN** el menú muestra "Servicios" con un submenú de esos dos enlaces

### Requirement: Menus are translated per language
Los menús SHALL traducirse con el flujo de traducción del sitio. Un idioma sin su versión
del menú SHALL mostrar el menú del idioma base con sus páginas en el idioma de la visita
cuando estén traducidas.

#### Scenario: Translated menu
- **WHEN** el menú del encabezado tiene su traducción en `en`
- **THEN** `/en/` muestra las etiquetas en inglés

#### Scenario: Menu not translated yet
- **WHEN** `en` es público, no tiene menú propio y la página enlazada tiene traducción
  publicada en `en`
- **THEN** `/en/` muestra el menú del idioma base enlazando a la versión en inglés

### Requirement: Only reachable destinations are shown
Un ítem que enlaza a una página no publicada, o un ítem sin destino, MUST NOT mostrarse a
los visitantes. Un ítem con subítems y sin destino propio SHALL mostrarse si tiene al menos
un subítem visible.

#### Scenario: Unpublished page
- **WHEN** un ítem enlaza a una página despublicada
- **THEN** el menú público no muestra ese ítem

#### Scenario: Group label
- **WHEN** un ítem "Institucional" no tiene destino y tiene subítems publicados
- **THEN** se muestra como título del grupo con sus subítems

### Requirement: Current page is marked
El ítem que corresponde a la página que se está viendo, o a una de sus páginas superiores,
SHALL marcarse como actual de forma accesible.

#### Scenario: Visiting a child page
- **WHEN** se visita una subpágina de "Servicios"
- **THEN** el ítem "Servicios" se marca con `aria-current`
