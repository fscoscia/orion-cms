# Spec Delta

## MODIFIED Requirements

### Requirement: Page language does not depend on the visitor's browser
El sistema SHALL mostrar cada página pública en el idioma que indica su URL (el idioma base
sin prefijo, los demás con su prefijo), sin importar el idioma que pida el navegador del
visitante.

#### Scenario: Browser asks for another language
- **WHEN** el idioma del sitio es `es` y un visitante pide una página con
  `Accept-Language: fr`
- **THEN** el documento HTML declara `lang="es"`

#### Scenario: Browser asks for no language
- **WHEN** el idioma del sitio es `es` y un visitante pide una página sin
  `Accept-Language`
- **THEN** el documento HTML declara `lang="es"`

#### Scenario: Prefixed URL with a different browser language
- **WHEN** `en` es público y un visitante pide `/en/` con `Accept-Language: es`
- **THEN** el documento HTML declara `lang="en"`
