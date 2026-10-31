# content-links Specification

## Purpose
Define los destinos de enlace que los editores eligen en menús y bloques, cómo se validan
y cómo se convierten en el enlace que ve el visitante.

## Requirements

### Requirement: A link has exactly one destination
Un enlace SHALL apuntar a uno solo de estos destinos: una página interna, una URL externa,
un email o un teléfono. El admin MUST rechazar un enlace con más de un destino.

#### Scenario: Two destinations
- **WHEN** un editor elige una página y además escribe una URL en el mismo enlace
- **THEN** el admin rechaza el enlace e indica dejar uno solo

### Requirement: Internal pages follow the visitor's language
Un enlace a una página interna SHALL llevar a la versión publicada de esa página en el idioma
de la visita cuando existe, y a la página elegida en caso contrario.

#### Scenario: Translated page
- **WHEN** un enlace apunta a "Servicios" y se visita el sitio en `/en/`, donde "Services"
  está publicada
- **THEN** el enlace lleva a `/en/services/`

### Requirement: Absolute URLs of the own site are rejected
El admin MUST rechazar como URL externa una dirección cuyo dominio es el del propio sitio,
e indicar que se elija la página interna.

#### Scenario: Pasting an own URL
- **WHEN** un editor escribe `https://<dominio del sitio>/servicios/` como URL externa
- **THEN** el admin rechaza el valor y sugiere elegir la página

### Requirement: Email and phone links are normalized
Un email SHALL convertirse en un enlace `mailto:` y un teléfono en un enlace `tel:` con solo
dígitos y un `+` inicial opcional, conservando el texto como lo escribió el editor.

#### Scenario: Phone with spaces
- **WHEN** un editor escribe el teléfono `+595 21 729 1444`
- **THEN** el enlace es `tel:+595217291444` y el texto visible conserva los espacios

### Requirement: External links can open in a new tab safely
Un enlace externo SHALL poder abrirse en una pestaña nueva; en ese caso MUST incluir
`rel="noopener noreferrer"`.

#### Scenario: New tab
- **WHEN** un editor marca "abrir en pestaña nueva" en una URL externa
- **THEN** el enlace tiene `target="_blank"` y `rel="noopener noreferrer"`
