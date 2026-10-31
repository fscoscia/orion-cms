# Spec Delta

## Purpose

Define cómo el admin muestra la identidad del cliente (logo, nombre y colores) en lugar de
la de Wagtail.

## ADDED Requirements

### Requirement: The admin shows the client's logo and name
El admin SHALL mostrar el logo del pie de Datos del sitio en el menú lateral y el logo en
la página de login, y el nombre del sitio en el título del login, en el panel de inicio y en
el título de las pestañas del navegador. Sin logo cargado, SHALL mantener el de Wagtail.

#### Scenario: Login page
- **WHEN** el sitio "Clínica Ejemplo" tiene logo y alguien abre el login del admin
- **THEN** ve el logo y el título "Ingresar a Clínica Ejemplo"

### Requirement: The project sets the admin colors
Los colores principal y de acento del admin SHALL definirse en los ajustes del proyecto
como colores hexadecimales. Sin ajuste, el admin SHALL conservar los colores de Wagtail. Un
color inválido MUST impedir que el proyecto arranque, y un color sobre el que el texto
blanco no alcanza un contraste de 4.5:1 SHALL generar un aviso de los chequeos del sistema.

#### Scenario: Brand colors
- **WHEN** el proyecto define el color principal `#1d4ed8`
- **THEN** el menú lateral y los botones del admin usan ese color

#### Scenario: Low contrast color
- **WHEN** el proyecto define el color de acento `#facc15`
- **THEN** `manage.py check` avisa que el texto blanco no se lee bien sobre ese color
