# site-data Specification

## Purpose
Define los datos de identidad y contacto que muestra todo sitio, separa los que son iguales
en todos los idiomas de los que se traducen, y establece quién puede editarlos.

## Requirements

### Requirement: Fixed site data has a single place
El logo, el logo del pie, el teléfono, el WhatsApp, el email, la dirección y las redes
sociales SHALL editarse en un único lugar del admin y valer para todos los idiomas.

#### Scenario: Phone shown in every language
- **WHEN** se carga el teléfono y se visita el sitio en `es` y en `en`
- **THEN** ambas versiones muestran el mismo teléfono

### Requirement: Social networks come from a known list
Cada red social SHALL elegirse de una lista de redes conocidas con su URL, para mostrarse
con su ícono y su nombre accesible.

#### Scenario: Adding Instagram
- **WHEN** un administrador agrega Instagram con su URL
- **THEN** el pie muestra un enlace a esa URL con el ícono de Instagram y el nombre
  "Instagram" para lectores de pantalla

#### Scenario: Invalid URL
- **WHEN** se carga una red social con un texto que no es una URL
- **THEN** el admin rechaza el valor

### Requirement: Site texts are translated per language
El eslogan y el texto legal del pie SHALL tener una versión por idioma, traducible con el
flujo de traducción del sitio, y SHALL existir como máximo una versión por idioma.

#### Scenario: Translated legal text
- **WHEN** existen los textos del sitio en `es` y su traducción en `en`
- **THEN** el pie en `/en/` muestra el texto legal en inglés

#### Scenario: Missing translation
- **WHEN** un idioma público no tiene su versión de los textos del sitio
- **THEN** el pie muestra los textos del idioma base

#### Scenario: Second version in the same language
- **WHEN** se intenta crear otra versión de los textos del sitio en un idioma que ya tiene
  una
- **THEN** el admin lo rechaza

### Requirement: Editing rights are split by kind of data
Los datos fijos MUST editarse solo con el permiso de ajustes del sitio; los textos del sitio
SHALL poder editarlos los grupos de editores y moderadores.

#### Scenario: Editor edits the legal text
- **WHEN** un usuario del grupo de editores abre los textos del sitio
- **THEN** puede modificarlos

#### Scenario: Editor tries to change the logo
- **WHEN** un usuario del grupo de editores intenta abrir los datos fijos del sitio
- **THEN** el admin se lo impide

### Requirement: Missing data renders nothing
El encabezado y el pie SHALL omitir cada dato que no esté cargado, sin dejar marcadores
vacíos, y mostrar el nombre del sitio cuando no hay logo.

#### Scenario: No logo
- **WHEN** no hay logo cargado
- **THEN** el encabezado muestra el nombre del sitio como enlace al inicio
