# content-operations Specification

## Purpose
Define las operaciones de escritura de contenido de Orion, independientes del transporte:
con qué permisos se hacen, cómo se validan y cómo quedan registradas en las revisiones.

## Requirements

### Requirement: Operations are a layer apart from any transport
Las operaciones de contenido SHALL vivir en `orion.operations`, recibir el usuario que actúa
como argumento y no depender del MCP, de una petición HTTP ni de la entrada o salida estándar,
de modo que cualquier transporte las use.

#### Scenario: Called directly
- **WHEN** una prueba llama a una operación con un usuario, sin MCP ni petición
- **THEN** la operación se ejecuta y devuelve su resultado

### Requirement: A page can be created as a draft
Una operación SHALL crear una página de un tipo permitido bajo un padre dado, con los campos
indicados, como borrador no publicado, con una primera revisión a nombre del usuario. El tipo
MUST estar entre los permitidos para ese padre y el usuario MUST poder agregar subpáginas ahí.

#### Scenario: Draft under the home page
- **WHEN** un Editor crea una página libre bajo la portada
- **THEN** la página existe, no está publicada y su primera revisión es del Editor

#### Scenario: Type not allowed
- **WHEN** se pide un tipo que no puede ir bajo ese padre
- **THEN** la operación falla con un error de validación y no crea nada

### Requirement: A draft is updated against an expected revision
Una operación SHALL actualizar los campos de la última versión de una página guardándola como
una revisión nueva a nombre del usuario, sin publicarla. MUST exigir la revisión esperada (el
id de la última revisión) y fallar con un conflicto si la página tiene una más nueva.

#### Scenario: Update
- **WHEN** un Editor actualiza el título de una página con la revisión esperada vigente
- **THEN** se crea una revisión nueva y la versión publicada no cambia

#### Scenario: Someone else saved in between
- **WHEN** la revisión esperada ya no es la última
- **THEN** la operación falla con un conflicto y no guarda nada

### Requirement: Only editable content fields can be written
Una operación sobre una página SHALL aceptar solo el título, el slug, el título y la
descripción para buscadores y los campos de contenido del tipo de página. MUST rechazar los
campos internos del árbol, el estado de publicación, el dueño y cualquier campo desconocido.

#### Scenario: Internal field
- **WHEN** se intenta escribir `live` o `owner`
- **THEN** la operación falla con un error de validación

### Requirement: The body is validated as the editor would
El cuerpo de una página SHALL validarse con sus bloques y el texto enriquecido SHALL
normalizarse con el conversor de Wagtail, de modo que solo queden las funciones permitidas
por el bloque; un valor inválido MUST fallar con un error de validación.

#### Scenario: Unsafe markup
- **WHEN** el texto enriquecido de un bloque incluye una etiqueta `<script>`
- **THEN** lo guardado no la contiene

#### Scenario: Invalid block
- **WHEN** el cuerpo incluye un bloque que no existe
- **THEN** la operación falla con un error de validación

### Requirement: Permissions are the user's own and never raised
Cada operación SHALL comprobar los permisos del usuario con los de Wagtail y MUST fallar con
`PermissionDenied`, sin cambiar nada, si no los tiene. Un usuario inactivo MUST NOT poder
operar. Ninguna operación SHALL dar permisos ni saltar un bloqueo o un flujo de trabajo.

#### Scenario: Editor and redirects
- **WHEN** un Editor intenta crear una redirección
- **THEN** la operación falla con `PermissionDenied`, porque solo los Administradores las gestionan

#### Scenario: Locked page
- **WHEN** una página está bloqueada por otra persona
- **THEN** la operación de actualización falla con `PermissionDenied`

### Requirement: Redirects can be created and updated
Una operación SHALL crear una redirección (origen, destino y tipo) y otra SHALL actualizarla,
con los permisos de redirecciones de Wagtail, rechazando un origen repetido, un origen que
apunte a sí mismo y destinos que no sean una página o una URL http o https.

#### Scenario: Create
- **WHEN** un Administrador crea una redirección de `/viejo` a `https://example.com/nuevo/`
- **THEN** la redirección existe

#### Scenario: Self redirect
- **WHEN** el destino es el mismo que el origen
- **THEN** la operación falla con un error de validación

### Requirement: Site data and texts can be updated
Una operación SHALL actualizar los datos del sitio y otra los textos del sitio de un idioma,
validando cada campo con su modelo. Los datos del sitio MUST requerir el permiso de
modificarlos (los Administradores) y los textos el suyo (los Editores y los Administradores).

#### Scenario: Site texts
- **WHEN** un Editor actualiza los textos del sitio en español
- **THEN** los textos cambian

#### Scenario: Site data by an Editor
- **WHEN** un Editor intenta actualizar los datos del sitio
- **THEN** la operación falla con `PermissionDenied`

### Requirement: Operations never publish or delete
Ninguna operación SHALL publicar, despublicar, borrar ni mover páginas, ni borrar
redirecciones u otros datos, y MUST NOT dejar una página en vivo que no lo estuviera.

#### Scenario: Update of a published page
- **WHEN** se actualiza una página publicada
- **THEN** sigue publicada con su contenido anterior hasta que una persona publique la revisión nueva

### Requirement: Changes are attributed to the acting user
Cada cambio de una página SHALL quedar en una revisión y en el historial de Wagtail a nombre
del usuario que actúa.

#### Scenario: Revision author
- **WHEN** una operación actualiza una página
- **THEN** la revisión nueva y la entrada del historial son del usuario indicado
