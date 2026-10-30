## ADDED Requirements

### Requirement: Page language does not depend on the visitor's browser
El sistema SHALL mostrar las páginas públicas en el idioma configurado del sitio, sin
importar el idioma que pida el navegador del visitante.

#### Scenario: Browser asks for another language
- **WHEN** el idioma del sitio es `es` y un visitante pide una página con
  `Accept-Language: fr`
- **THEN** el documento HTML declara `lang="es"`

#### Scenario: Browser asks for no language
- **WHEN** el idioma del sitio es `es` y un visitante pide una página sin
  `Accept-Language`
- **THEN** el documento HTML declara `lang="es"`
