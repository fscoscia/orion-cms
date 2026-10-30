# localized-routing Specification

## Purpose
Define cómo la URL determina el idioma de una página, qué ve un visitante cuando pide un
idioma no público o una traducción que no existe, y cómo las páginas enlazan a sus
traducciones para personas y buscadores.

## Requirements

### Requirement: The base language has no URL prefix
Las páginas del idioma base SHALL servirse sin prefijo de idioma y las de los demás idiomas
con el código del idioma como primer segmento.

#### Scenario: Base language page
- **WHEN** el idioma base es `es` y existe la página publicada `servicios`
- **THEN** se sirve en `/servicios/` en español

#### Scenario: Secondary language page
- **WHEN** `en` es público y la traducción publicada de esa página tiene slug `services`
- **THEN** se sirve en `/en/services/` en inglés

### Requirement: Non-public languages redirect to the base language
Una URL con el prefijo de un idioma que no es público SHALL redirigir con `302` al inicio
del idioma base.

#### Scenario: Language added but not public
- **WHEN** `en` existe pero no es público y un visitante pide `/en/services/`
- **THEN** la respuesta es `302` hacia `/`

### Requirement: Missing translations redirect to a language home
Una URL de un idioma público que no corresponde a una página publicada SHALL redirigir con
`302` al inicio de ese idioma si está publicado, o al inicio del idioma base si no lo está.

#### Scenario: Untranslated page
- **WHEN** `en` es público, su inicio está publicado y no existe `/en/servicios/`
- **THEN** la respuesta es `302` hacia `/en/`

#### Scenario: Language home not published
- **WHEN** `en` es público pero su inicio no está publicado
- **THEN** cualquier URL con prefijo `/en/` redirige con `302` hacia `/`

### Requirement: Language switcher lists public languages
El selector de idioma SHALL listar los idiomas públicos, marcar el actual y enlazar a la
traducción publicada de la página actual o, si no existe, al inicio de ese idioma.

#### Scenario: Translation exists
- **WHEN** una página tiene traducción publicada en `en`
- **THEN** el selector enlaza a esa traducción

#### Scenario: Translation missing
- **WHEN** una página no tiene traducción publicada en `en`
- **THEN** el selector enlaza al inicio de `en`

#### Scenario: Non-public language
- **WHEN** `fr` existe pero no es público
- **THEN** el selector no muestra `fr`

### Requirement: Pages declare their translations for search engines
Cada página SHALL declarar con `hreflang` sus traducciones publicadas en idiomas públicos,
más una entrada `x-default` que apunta a la versión del idioma base.

#### Scenario: Page translated to English
- **WHEN** una página en `es` tiene traducción publicada en `en`, y `en` es público
- **THEN** ambas versiones declaran `hreflang="es"`, `hreflang="en"` y `x-default` con URLs
  absolutas

#### Scenario: Translation in a non-public language
- **WHEN** la única traducción está en un idioma no público
- **THEN** la página no declara esa traducción
