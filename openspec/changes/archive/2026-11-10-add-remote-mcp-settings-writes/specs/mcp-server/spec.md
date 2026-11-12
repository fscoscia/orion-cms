## MODIFIED Requirements

### Requirement: A key's scope limits the tools it can use
Una clave `read-only` SHALL poder listar y llamar solo herramientas de nivel `read`. Una
`draft-only` SHALL además poder usar `page_create_draft` y `page_update_draft`. Una `full`
SHALL además poder usar `redirect_create`, `redirect_update`, `site_settings_update`,
`site_texts_update` y `settings_revert`. Ninguna clave `read-only` ni `draft-only` SHALL poder
usar herramientas de nivel `settings`, y ninguna clave SHALL poder publicar, despublicar ni
borrar.

#### Scenario: Read-only key
- **WHEN** una clave `read-only` llama a `page_create_draft`
- **THEN** recibe un error de herramienta desconocida

#### Scenario: Draft-only key and redirects
- **WHEN** una clave `draft-only` ligada a un Administrador llama a `redirect_create`
- **THEN** recibe un error de herramienta desconocida

#### Scenario: Full key
- **WHEN** una clave `full` ligada a un Administrador de Wagtail llama a `redirect_create`
- **THEN** la redirección se crea a nombre del usuario de la clave

#### Scenario: Full key without the user's permission
- **WHEN** una clave `full` ligada a un Editor llama a `redirect_create`
- **THEN** recibe un error de herramienta de permiso y no se crea nada

### Requirement: Write tools create drafts and edit settings
Con la escritura permitida el servidor SHALL ofrecer `page_create_draft`, `page_update_draft`,
`redirect_create`, `redirect_update`, `site_settings_update`, `site_texts_update` y
`settings_revert`, que usan las operaciones de contenido. Ninguna SHALL publicar, despublicar
ni borrar. Un fallo de permiso, de validación o de conflicto MUST volver como un error de
herramienta con la causa.

#### Scenario: Draft through the tool
- **WHEN** el asistente crea una página con `page_create_draft`
- **THEN** la página queda como borrador y la respuesta indica su id y su revisión

#### Scenario: Conflict
- **WHEN** `page_update_draft` recibe una revisión esperada que ya no es la última
- **THEN** recibe un error de herramienta que pide leer la página otra vez

### Requirement: A guide explains the remote endpoint
El repositorio SHALL incluir la guía `docs/guias/mcp-en-produccion.md`, en español, que
explique cómo activar el endpoint, que exige HTTPS, cómo crear y revocar claves, los
alcances (incluido que `full` solo lo crea un superusuario y qué puede cambiar), cómo
deshacer una escritura con `settings_revert` y hasta cuándo, cómo conectar un cliente, los
límites, la rotación y los riesgos. El `AGENTS.md` de la plantilla y `docs/alta-de-cliente.md`
MUST enlazarla.

#### Scenario: Risks
- **WHEN** se lee la guía
- **THEN** dice qué permite una clave filtrada y cómo revocarla

#### Scenario: Full keys
- **WHEN** se lee la guía
- **THEN** explica que una clave `full` cambia redirecciones, datos y textos al instante, quién
  puede crearla y que `settings_revert` no deshace redirecciones creadas

## ADDED Requirements

### Requirement: Settings writes keep the previous values
Cada escritura de ajustes hecha con una clave (`redirect_create`, `redirect_update`,
`site_settings_update`, `site_texts_update`) SHALL guardar un recibo con los valores previos de
los campos que cambió y SHALL devolver su `operation_key`; si el cliente no la manda, el
servidor MUST generar una. Los valores previos MUST NOT incluir secretos ni datos personales
de usuarios.

#### Scenario: Server-generated key
- **WHEN** una clave `full` llama a `site_settings_update` sin `operation_key`
- **THEN** la respuesta incluye una `operation_key` y existe un recibo con los valores previos

#### Scenario: Only changed fields
- **WHEN** `site_texts_update` cambia un texto de varios
- **THEN** el recibo guarda el valor previo solo de ese texto

### Requirement: A settings write can be reverted
`settings_revert` SHALL recibir una `operation_key` y restaurar los valores previos de esa
operación solo si cada campo sigue valiendo lo que la operación escribió. Si alguno cambió
después, MUST dar un error de conflicto y no modificar nada. Sobre una operación de
`redirect_create` MUST dar un error que remita al admin y no SHALL borrar nada.

#### Scenario: Revert
- **WHEN** se revierte una operación de `site_settings_update` sin cambios posteriores
- **THEN** los campos recuperan su valor previo, a nombre del usuario de la clave

#### Scenario: Changed afterwards
- **WHEN** alguien editó ese campo en el admin después de la operación y se intenta revertir
- **THEN** recibe un error de conflicto y el campo conserva su valor actual

#### Scenario: Already reverted
- **WHEN** se revierte dos veces la misma operación
- **THEN** la segunda respuesta indica que ya estaba revertida y no escribe

#### Scenario: Created redirect
- **WHEN** se intenta revertir una operación de `redirect_create`
- **THEN** recibe un error que indica corregirla en el admin y la redirección sigue existiendo

#### Scenario: Receipt too old
- **WHEN** se intenta revertir una operación cuyo recibo ya fue purgado
- **THEN** recibe un error que dice que no se puede revertir
