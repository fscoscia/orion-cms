# Spec Delta

## Purpose

Define cómo un editor crea la traducción de una página a otro idioma del sitio y cómo se
entera de que una traducción quedó desactualizada respecto de su original.

## ADDED Requirements

### Requirement: Editors translate pages from the original
Un usuario con el permiso de traducir, que por defecto tienen los grupos de editores y
moderadores, SHALL poder crear la traducción de una página a cualquier idioma agregado al
sitio desde la propia página original.

#### Scenario: Create a translation
- **WHEN** un editor pide traducir una página en `es` al idioma `en`
- **THEN** se crea la versión en `en` como borrador, vinculada a la original

#### Scenario: No translation permission
- **WHEN** un usuario del admin sin el permiso de traducir intenta traducir una página
- **THEN** la acción se rechaza y no se crea ninguna traducción

### Requirement: Translations are edited field by field
La traducción SHALL presentar los textos de la original para traducirlos uno por uno,
conservando la estructura de la página.

#### Scenario: Translating texts
- **WHEN** un editor abre una traducción nueva
- **THEN** ve cada texto de la original con su campo para la traducción

### Requirement: Outdated translations are flagged
Cuando el original cambia después de traducirse, el sistema SHALL marcar en la traducción
los textos nuevos o modificados como pendientes, sin publicar cambios en la traducción por
su cuenta.

#### Scenario: Original edited after translation
- **WHEN** se publica un cambio de texto en la página original y se sincronizan sus
  traducciones
- **THEN** la traducción muestra ese texto como pendiente y su versión publicada no cambia
