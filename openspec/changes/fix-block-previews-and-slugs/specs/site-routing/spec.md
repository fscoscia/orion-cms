# Spec Delta

## ADDED Requirements

### Requirement: Page URLs have no accents
Los slugs de las páginas SHALL generarse solo con letras ASCII, números y guiones: las
letras con tilde o diéresis SHALL pasar a su versión sin tilde, de modo que las URLs se
lean igual al compartirlas.

#### Scenario: Title with accents
- **WHEN** un editor crea una página con el título "Artículo de prueba"
- **THEN** su slug es `articulo-de-prueba`
