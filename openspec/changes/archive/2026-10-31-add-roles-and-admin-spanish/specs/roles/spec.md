# Spec Delta

## Purpose

Define los roles del admin de un sitio Orion, qué puede hacer cada uno y cómo se aprueba el
contenido que prepara un Editor.

## ADDED Requirements

### Requirement: Sites have Editors and Administrators
Todo sitio SHALL tener los grupos "Editores" y "Administradores". Un Editor SHALL poder
crear y modificar páginas, imágenes, documentos, menús, textos del sitio, categorías y
etiquetas, y MUST NOT poder publicar páginas. Un Administrador SHALL poder además publicar,
borrar y bloquear páginas, borrar fragmentos, editar los datos y los idiomas del sitio y
administrar usuarios.

#### Scenario: Editor publishes
- **WHEN** un Editor abre una página que modificó
- **THEN** puede enviarla a aprobación y no puede publicarla

#### Scenario: Administrator edits site data
- **WHEN** un Administrador abre Datos del sitio
- **THEN** puede modificarlos

### Requirement: Administrators do not reach technical settings
Un Administrador MUST NOT poder modificar sitios, colecciones, flujos de trabajo ni grupos;
eso queda para los superusuarios.

#### Scenario: Administrator opens sites
- **WHEN** un Administrador intenta abrir la lista de sitios
- **THEN** el admin se lo impide

### Requirement: Administrators approve what Editors submit
Las páginas que un Editor envía a revisión SHALL quedar esperando la aprobación de un
Administrador, que SHALL poder aprobarlas, rechazarlas o pedir cambios.

#### Scenario: Approval
- **WHEN** un Editor envía una página a revisión y un Administrador la aprueba
- **THEN** la página queda publicada

### Requirement: Existing permissions survive the renaming
Al instalar el cambio, los grupos de Wagtail SHALL renombrarse conservando los permisos y los
usuarios que ya tenían, y la instalación MUST NOT quitar permisos ni usuarios de ningún
grupo.

#### Scenario: Existing editor
- **WHEN** un usuario del grupo "Editors" existe antes de migrar
- **THEN** después de migrar pertenece a "Editores" con los mismos permisos

### Requirement: A group can be limited to a section
Un superusuario SHALL poder crear un grupo cuyos permisos de páginas valgan solo para una
sección del árbol.

#### Scenario: Group for the news section
- **WHEN** un grupo tiene permisos de páginas solo sobre "Novedades"
- **THEN** sus usuarios pueden editar páginas dentro de "Novedades" y no fuera
