# Spec Delta

## MODIFIED Requirements

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
