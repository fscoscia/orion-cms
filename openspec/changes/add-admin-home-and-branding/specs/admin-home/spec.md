# Spec Delta

## Purpose

Define lo que ve un editor al entrar al admin y los atajos que lo llevan a las tareas más
comunes, desde el admin y desde el sitio.

## ADDED Requirements

### Requirement: The admin home greets and offers the common tasks
El panel de inicio SHALL saludar al usuario por su nombre y ofrecer como acciones grandes
crear una página, escribir un artículo, editar la portada, subir imágenes, editar los menús
y editar los datos del sitio. Cada acción SHALL mostrarse solo si el usuario tiene permiso
para hacerla y si lo que necesita existe.

#### Scenario: Editor without settings permission
- **WHEN** un usuario del grupo de editores entra al admin
- **THEN** ve las acciones de páginas, artículos, imágenes y menús, y no la de datos del
  sitio

#### Scenario: Site without article listings
- **WHEN** el sitio no tiene ningún listado de artículos
- **THEN** el panel no ofrece escribir un artículo

### Requirement: Writing an article starts in the right listing
La acción y el atajo "Nuevo artículo" SHALL abrir el formulario de un artículo nuevo dentro
del único listado de artículos, o pedir elegir el listado cuando hay varios.

#### Scenario: One listing
- **WHEN** hay un solo listado y el editor elige "Nuevo artículo"
- **THEN** se abre el formulario de un artículo dentro de ese listado

#### Scenario: Several listings
- **WHEN** hay dos listados
- **THEN** el admin muestra los dos para elegir dónde crear el artículo

### Requirement: The admin home lists unpublished changes
El panel de inicio SHALL listar las páginas con cambios sin publicar que el usuario puede
editar, de la más reciente a la más antigua, con su tipo y hace cuánto se cambiaron, y
enlace para editarlas.

#### Scenario: Draft change
- **WHEN** un editor guarda un borrador de una página publicada
- **THEN** la página aparece en "Cambios sin publicar" del panel

### Requirement: The admin menu shows shortcuts and hides what an editor does not use
El menú lateral SHALL ofrecer "Ver el sitio", que abre el sitio en otra pestaña, y "Nuevo
artículo" cuando el usuario puede crear artículos. Los informes y la ayuda de Wagtail SHALL
mostrarse solo a los administradores.

#### Scenario: Editor's menu
- **WHEN** un usuario que no es administrador abre el menú lateral
- **THEN** ve "Nuevo artículo" y "Ver el sitio" y no ve Informes ni Ayuda

### Requirement: The site bar reaches the header and the footer
La barra flotante que Wagtail muestra en el sitio a los usuarios con sesión SHALL ofrecer
accesos para editar el menú del encabezado, el menú del pie y los textos del pie del idioma
de la página que se está mirando, según los permisos del usuario.

#### Scenario: Editing the footer from the site
- **WHEN** un editor mira `/en/` y abre la barra flotante
- **THEN** el acceso "Pie" lo lleva a editar el menú del pie en inglés
