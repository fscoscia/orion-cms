# taxonomies Specification

## Purpose
Define las categorías y las etiquetas que clasifican los artículos: su estructura, cómo se
traducen y quién las edita.

## Requirements

### Requirement: Categories have two levels
Las categorías SHALL editarse por separado del árbol de páginas y SHALL poder tener una
categoría superior. Una categoría con superior MUST NOT ser superior de otra.

#### Scenario: Third level
- **WHEN** un editor intenta poner "Prevención", que ya está dentro de "Salud", como
  superior de otra categoría
- **THEN** el admin lo rechaza

### Requirement: Categories and tags are translated once
Las categorías y las etiquetas SHALL traducirse con el flujo de traducción del sitio, una
vez cada una, y un artículo SHALL mostrar las suyas en el idioma de la visita cuando están
traducidas y en el idioma base cuando no.

#### Scenario: Translated category
- **WHEN** la categoría "Salud" está traducida como "Health" y se visita un artículo en
  `/en/`
- **THEN** el artículo muestra "Health" y su enlace filtra el listado en inglés

#### Scenario: Untranslated tag
- **WHEN** una etiqueta no está traducida al inglés
- **THEN** el artículo en `/en/` la muestra con su nombre en el idioma base

### Requirement: Articles keep the same classification in every language
Las categorías y etiquetas que el editor elige en el artículo original SHALL valer para
todas sus traducciones, y SHALL actualizarse en ellas al sincronizar la traducción.

#### Scenario: Category added to the original
- **WHEN** el editor suma una categoría al artículo original y se actualiza la traducción
- **THEN** la traducción también tiene esa categoría

### Requirement: Slugs are unique per language
Cada categoría y cada etiqueta SHALL tener un identificador para la URL del filtro, único
dentro de su idioma y formado solo por letras ASCII, números y guiones. Un identificador
vacío SHALL generarse a partir del nombre, sin tildes, y un nombre sin letras latinas SHALL
recibir igual un identificador válido.

#### Scenario: Repeated slug
- **WHEN** se intenta crear otra categoría en español con el identificador `salud`
- **THEN** el admin lo rechaza

#### Scenario: Slug from a name with accents
- **WHEN** se crea la etiqueta "Prevención" sin identificador
- **THEN** su identificador es `prevencion`

#### Scenario: Slug with accents typed by hand
- **WHEN** un editor escribe el identificador `salúd`
- **THEN** el admin lo rechaza

### Requirement: Editors manage categories and tags
Los grupos de editores y moderadores SHALL poder crear y modificar categorías y etiquetas.

#### Scenario: Editor creates a tag
- **WHEN** un usuario del grupo de editores crea una etiqueta
- **THEN** el admin la guarda
