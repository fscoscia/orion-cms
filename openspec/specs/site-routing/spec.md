# site-routing Specification

## Purpose
Define las rutas que Orion expone a cada proyecto (admin, documentos y páginas de Wagtail)
y cómo se presenta una página que todavía no tiene una plantilla propia.

## Requirements

### Requirement: Admin path is configurable
El sistema SHALL servir el admin de Wagtail en la ruta indicada por una variable de entorno,
con `admin/` como valor por defecto.

#### Scenario: Default path
- **WHEN** la variable no está definida
- **THEN** la pantalla de inicio de sesión del admin responde en `/admin/login/`

#### Scenario: Custom path
- **WHEN** la variable vale `panel/`
- **THEN** el admin responde en `/panel/` y no en `/admin/`

### Requirement: Invalid admin paths are rejected
El sistema MUST rechazar al arrancar una ruta de admin vacía, que empiece con `/`, que no
termine en `/` o que contenga caracteres fuera de letras minúsculas, números, guiones y
barras.

#### Scenario: Leading slash
- **WHEN** la variable vale `/panel/`
- **THEN** el arranque falla con un mensaje que explica el formato esperado

### Requirement: Pages are served at the site root
El sistema SHALL servir las páginas publicadas de Wagtail a partir de `/`, después de toda
ruta explícita del proyecto.

#### Scenario: Root page
- **WHEN** existe una página raíz publicada y se pide `/`
- **THEN** la respuesta es `200` y muestra el título de la página

### Requirement: Pages without a template still render
Una página sin plantilla propia SHALL mostrarse con una plantilla mínima de Orion que
incluye el título, el idioma del sitio y la barra de edición para usuarios autenticados.

#### Scenario: Generic page
- **WHEN** se pide una página cuyo tipo no define plantilla
- **THEN** la respuesta es `200` con un documento HTML que declara el idioma y el título

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

### Requirement: Page URLs have no accents
Los slugs de las páginas SHALL generarse solo con letras ASCII, números y guiones: las
letras con tilde o diéresis SHALL pasar a su versión sin tilde, de modo que las URLs se
lean igual al compartirlas.

#### Scenario: Title with accents
- **WHEN** un editor crea una página con el título "Artículo de prueba"
- **THEN** su slug es `articulo-de-prueba`
