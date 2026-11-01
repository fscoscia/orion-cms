# Spec Delta

## Purpose

Define los fragmentos de código de terceros que se cargan desde el admin en las páginas
públicas: quién los gestiona, dónde y en qué páginas se insertan, cómo se apagan y cómo se
recupera una versión anterior.

## ADDED Requirements

### Requirement: Snippets are inserted where chosen
Un fragmento activo SHALL insertarse tal cual en la ubicación elegida: dentro de
`<head>`, al inicio de `<body>` o al final de `<body>`, en el orden en que se crearon. Un
fragmento desactivado MUST NOT insertarse y SHALL conservarse.

#### Scenario: Analytics in the head
- **WHEN** un superusuario crea un fragmento "Google Analytics" en `<head>` y lo activa
- **THEN** todas las páginas públicas incluyen ese código dentro de `<head>`

#### Scenario: Turned off
- **WHEN** lo desactiva
- **THEN** ninguna página lo incluye y el fragmento sigue en el admin

### Requirement: Snippets have a scope
Un fragmento SHALL poder aplicarse a todo el sitio, a páginas elegidas (con o sin sus
subpáginas) o a tipos de página elegidos, y opcionalmente solo a ciertos idiomas; sin
idiomas elegidos SHALL aplicarse a todos. En vistas que no son páginas (como los
resultados de búsqueda) solo SHALL aplicarse los de todo el sitio.

#### Scenario: One section
- **WHEN** un fragmento se aplica a "Novedades" con sus subpáginas
- **THEN** está en "Novedades" y sus artículos, y no en "Servicios"

#### Scenario: Page type
- **WHEN** un fragmento se aplica al tipo Artículo
- **THEN** está en todos los artículos y en ninguna otra página

#### Scenario: Language
- **WHEN** un fragmento se aplica solo al inglés
- **THEN** está en las páginas en inglés y no en las en español

### Requirement: Only authorized users manage snippets
Ver, crear, editar, activar o borrar fragmentos SHALL requerir los permisos del modelo de
fragmentos, que MUST NOT darse a ningún grupo por defecto (solo los superusuarios los
gestionan hasta que se asignen). Quien no tiene el permiso MUST NOT ver los fragmentos en
el menú ni acceder a sus pantallas.

#### Scenario: Administrator without the permission
- **WHEN** una Administradora abre el admin
- **THEN** no ve los fragmentos de código ni puede abrir su pantalla

#### Scenario: Permission granted
- **WHEN** un superusuario da el permiso a un grupo "Marketing"
- **THEN** sus miembros gestionan los fragmentos

### Requirement: An emergency switch turns every snippet off
Con `ORION_SCRIPTS_DISABLED` verdadero, ninguna página SHALL incluir fragmentos, sin
importar su estado, y el admin SHALL mostrar un aviso en la pantalla de fragmentos.

#### Scenario: Broken site
- **WHEN** un fragmento rompe el sitio y se pone `ORION_SCRIPTS_DISABLED=true`
- **THEN** después de reiniciar, ninguna página incluye fragmentos

### Requirement: Snippets keep their history
Cada guardado de un fragmento SHALL quedar como versión con autor y fecha, y SHALL poder
compararse y restaurarse una versión anterior desde el admin.

#### Scenario: Restore
- **WHEN** alguien cambió el código de un fragmento y rompió algo
- **THEN** desde el historial se ve quién lo cambió y se restaura la versión anterior

### Requirement: Snippets never run in the admin or in previews
Los fragmentos MUST NOT incluirse en las pantallas del admin, en la vista previa del
editor ni en la vista previa compartida.

#### Scenario: Preview
- **WHEN** un editor abre la vista previa de una página con un fragmento activo
- **THEN** la vista previa no incluye el fragmento

### Requirement: Saving a snippet refreshes cached pages
Guardar o borrar un fragmento SHALL vaciar la caché de página, para que el cambio se vea
en la próxima visita.

#### Scenario: New snippet
- **WHEN** se activa un fragmento con páginas en caché
- **THEN** la próxima visita a esas páginas lo incluye
