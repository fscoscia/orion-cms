# Spec Delta

## ADDED Requirements

### Requirement: Links to a page can point to one of its sections
Un enlace a una página interna SHALL poder sumar un ancla, que se agrega a la dirección de
la página, también en la versión traducida. El admin MUST rechazar un ancla sin página o con
un formato inválido, y MUST NOT exigir que exista en la página.

#### Scenario: Section of the home page
- **WHEN** un enlace apunta a la página de inicio con el ancla `categorias`
- **THEN** el enlace es `/#categorias`

#### Scenario: Translated page
- **WHEN** un enlace apunta a "Servicios" con el ancla `precios` y se visita `/en/`
- **THEN** el enlace es `/en/services/#precios`

#### Scenario: Anchor without a page
- **WHEN** un editor escribe un ancla y elige una URL externa, o ninguna página
- **THEN** el admin rechaza el enlace e indica elegir una página

#### Scenario: Unpublished page
- **WHEN** la página del enlace no está publicada
- **THEN** el enlace no se muestra, con o sin ancla

#### Scenario: Existing link
- **WHEN** un enlace guardado antes de este cambio no tiene ancla
- **THEN** lleva a la misma dirección que antes
