# editor-preview Specification

## Purpose
Define cómo ve el editor el resultado de lo que edita: cuándo se abre la vista previa, en
qué tamaño, cómo se usa en celular y qué pasa con los enlaces dentro de ella.

## Requirements

### Requirement: The preview opens by default on wide screens
La primera vez que alguien edita una página en una pantalla de al menos 1200 px de ancho,
la vista previa SHALL abrirse sola ocupando la mitad de la ventana. Si el editor la cierra o
cambia su ancho, SHALL respetarse su elección en las siguientes ediciones.

#### Scenario: First edit
- **WHEN** un editor abre por primera vez el formulario de una página en una pantalla de
  1280 px
- **THEN** la vista previa está abierta y ocupa unos 640 px

#### Scenario: Preview closed by the editor
- **WHEN** el editor cierra la vista previa y abre otra página
- **THEN** la vista previa sigue cerrada

### Requirement: Orion pages preview at desktop size
Las páginas de Orion SHALL mostrarse en la vista previa en tamaño escritorio por defecto, y
SHALL poder verse también en tamaño celular y tablet.

#### Scenario: Preview size
- **WHEN** un editor abre la vista previa de una Página libre
- **THEN** está seleccionado el tamaño escritorio y se ofrecen celular y tablet

### Requirement: The preview button has a visible name
El botón que abre la vista previa SHALL mostrar el texto "Vista previa" además de su ícono.

#### Scenario: Finding the preview
- **WHEN** un editor abre el formulario de una página
- **THEN** ve un botón con el texto "Vista previa"

### Requirement: Links do not navigate inside the preview
Dentro de la vista previa, los enlaces y los formularios de la página MUST NOT navegar ni
enviarse. El editor SHALL ofrecer un enlace a la página publicada que la abre en otra
pestaña.

#### Scenario: Clicking a menu link in the preview
- **WHEN** el editor hace clic en un enlace del menú dentro de la vista previa
- **THEN** la vista previa sigue mostrando la página que se edita

#### Scenario: Viewing the published page
- **WHEN** el editor usa el enlace "En vivo" de una página publicada
- **THEN** la página publicada se abre en otra pestaña

### Requirement: Phones switch between editing and previewing
En pantallas de menos de 800 px de ancho la vista previa MUST NOT abrirse sola; al abrirla
SHALL ocupar la pantalla en tamaño celular, y un botón "Editar" visible SHALL volver al
formulario.

#### Scenario: Previewing on a phone
- **WHEN** un editor en un celular presiona "Vista previa" y después "Editar"
- **THEN** primero ve la vista previa a pantalla completa en tamaño celular y después el
  formulario
