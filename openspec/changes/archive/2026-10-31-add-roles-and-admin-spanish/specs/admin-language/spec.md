# Spec Delta

## Purpose

Define que el admin de un sitio Orion se muestre completo en el idioma del usuario, sin
frases de Wagtail que queden en inglés.

## ADDED Requirements

### Requirement: The admin has no English phrases in Spanish
Con el admin en español, todas las frases de Wagtail y de wagtail-localize SHALL mostrarse
en español, incluidas las de las pantallas que arma JavaScript y las etiquetas del login.

#### Scenario: Login page
- **WHEN** alguien abre el login del admin en español
- **THEN** los campos dicen "Nombre de usuario" y "Contraseña"

#### Scenario: Searching pages
- **WHEN** un editor mira el panel de inicio
- **THEN** el buscador dice "Buscar en todas las páginas…"

### Requirement: New untranslated phrases are detected
Una actualización de Wagtail que agregue frases sin traducir al español SHALL hacer fallar
una prueba que las lista.

#### Scenario: Wagtail upgrade
- **WHEN** una versión nueva de Wagtail trae una frase sin traducción al español
- **THEN** la prueba de traducciones falla y nombra esa frase
