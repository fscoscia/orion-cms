## RENAMED Requirements

- FROM: `### Requirement: Every tool only reads`
- TO: `### Requirement: Tools only read unless writing is allowed`

## MODIFIED Requirements

### Requirement: A command starts a local MCP server over stdio
`manage.py orion_mcp` SHALL iniciar un servidor MCP que lee mensajes JSON-RPC 2.0, uno por
línea, de la entrada estándar y escribe las respuestas, una por línea, en la salida estándar.
La salida estándar MUST llevar solo mensajes del protocolo; los registros y avisos SHALL ir a
la salida de errores. El servidor MUST terminar cuando se cierra la entrada. Acepta la
bandera `--allow-writes`, que MUST estar apagada por defecto.

#### Scenario: Protocol on stdout only
- **WHEN** el servidor recibe cualquier mensaje y una herramienta escribe con `print`
- **THEN** la salida estándar contiene solo respuestas JSON-RPC válidas

#### Scenario: Input closed
- **WHEN** el cliente cierra la entrada
- **THEN** el proceso termina sin error

#### Scenario: Default mode
- **WHEN** el comando se lanza sin banderas
- **THEN** el servidor es de solo lectura

### Requirement: Tools only read unless writing is allowed
Sin `--allow-writes`, ninguna herramienta SHALL crear, modificar ni borrar datos, archivos ni
configuración, y las herramientas de escritura MUST NOT existir ni listarse. Una herramienta
que no existe SHALL dar un error de herramienta desconocida.

#### Scenario: No writes
- **WHEN** se ejecutan todas las herramientas del modo por defecto contra un sitio con contenido
- **THEN** no se ejecuta ninguna sentencia de escritura sobre la base de datos

#### Scenario: Write tool without the flag
- **WHEN** el cliente llama a `page_update_draft` sin que se haya lanzado con `--allow-writes`
- **THEN** recibe un error de herramienta desconocida

### Requirement: A guide explains how to connect an assistant
El repositorio SHALL incluir la guía `docs/guias/usar-el-mcp.md`, en español, con el comando
para lanzar el servidor, un ejemplo de configuración para Claude Code, la lista de
herramientas, lo que no expone y la advertencia sobre datos personales y contenido ajeno.
Tras agregarse la escritura MUST explicar cómo activarla, qué cuenta usa y cómo crearla y
darle permisos, qué herramientas agrega, por qué el modo local no tiene una URL a la que
alguien pueda llegar, que el límite real frente al asistente es qué comandos puede ejecutar, y
que el asistente solo escribe borradores y que una persona los revisa y publica. El `AGENTS.md` de la plantilla MUST
enlazarla.

#### Scenario: Configuration example
- **WHEN** se lee la guía
- **THEN** incluye un ejemplo de `.mcp.json` con `pipenv run manage orion_mcp`

#### Scenario: Writing is documented
- **WHEN** se lee la sección de escritura
- **THEN** explica `--allow-writes`, la cuenta técnica y que nada se publica solo

## ADDED Requirements

### Requirement: Writing uses a dedicated technical account
Con `--allow-writes` el servidor SHALL actuar siempre como la cuenta de usuario `orion-agent`,
sin que nadie la elija. Las revisiones y el historial SHALL quedar a nombre de la cuenta y los
permisos que cuentan MUST ser los suyos. Sin `--allow-writes` el servidor MUST NOT exigir ni
tocar la cuenta.

#### Scenario: Editor permissions
- **WHEN** la cuenta está solo en Editores y el asistente intenta crear una redirección
- **THEN** recibe un error de herramienta que dice que no tiene permiso

#### Scenario: Account in Administrators
- **WHEN** el equipo agregó la cuenta al grupo Administradores y el asistente crea una redirección
- **THEN** la redirección se crea y no se publica ni borra nada

#### Scenario: Read-only mode
- **WHEN** el comando se lanza sin `--allow-writes` y la cuenta no existe
- **THEN** arranca de solo lectura sin ningún error

### Requirement: The server checks the account before writing
Antes de aceptar mensajes, `orion_mcp --allow-writes` MUST terminar con un error claro si la
cuenta no existe (nombrando `orion_create_agent_user`), está inactiva o es superusuaria, y
SHALL avisar por la salida de errores con qué cuenta y qué grupos escribe.

#### Scenario: Account missing
- **WHEN** se lanza con `--allow-writes` y la cuenta no existe
- **THEN** el comando termina con un error que nombra `orion_create_agent_user`

#### Scenario: Inactive account
- **WHEN** la cuenta `orion-agent` está inactiva
- **THEN** el comando termina con un error

#### Scenario: Superuser account
- **WHEN** la cuenta `orion-agent` es superusuaria
- **THEN** el comando termina con un error y no acepta mensajes

#### Scenario: Warning of the groups
- **WHEN** el servidor arranca con la cuenta en el grupo Editores
- **THEN** la salida de errores dice que escribe como `orion-agent` y con qué grupos

### Requirement: A command creates the technical account
`manage.py orion_create_agent_user` SHALL crear la cuenta `orion-agent` si no existe, activa,
sin email, con contraseña inutilizable, sin ser superusuaria y en el grupo Editores. Ejecutarlo
de nuevo MUST NOT modificar una cuenta existente, solo informarla, y MUST terminar con un error
si esa cuenta es superusuaria. `orion_install` MUST NOT crearla.

#### Scenario: First run
- **WHEN** se ejecuta en un sitio sin la cuenta
- **THEN** la cuenta existe, está activa, está en Editores y no se puede entrar al admin con ella

#### Scenario: Second run
- **WHEN** se ejecuta otra vez
- **THEN** no cambia la cuenta ni sus grupos y lo informa

#### Scenario: Existing superuser
- **WHEN** la cuenta `orion-agent` ya existe como superusuaria
- **THEN** el comando termina con un error y no la modifica

#### Scenario: The installer does not create it
- **WHEN** se ejecuta `orion_install` en un sitio nuevo
- **THEN** la cuenta `orion-agent` no existe

### Requirement: Write tools create drafts and edit settings
Con la escritura permitida el servidor SHALL ofrecer `page_create_draft`, `page_update_draft`,
`redirect_create`, `redirect_update`, `site_settings_update` y `site_texts_update`, que usan
las operaciones de contenido. Ninguna SHALL publicar, despublicar ni borrar. Un fallo de
permiso, de validación o de conflicto MUST volver como un error de herramienta con la causa.

#### Scenario: Draft through the tool
- **WHEN** el asistente crea una página con `page_create_draft`
- **THEN** la página queda como borrador y la respuesta indica su id y su revisión

#### Scenario: Conflict
- **WHEN** `page_update_draft` recibe una revisión esperada que ya no es la última
- **THEN** recibe un error de herramienta que pide leer la página otra vez

### Requirement: Pages expose the revision to expect
La herramienta de página SHALL devolver `latest_revision_id`, el id de la última revisión, para
usarlo como revisión esperada.

#### Scenario: Revision id
- **WHEN** el cliente pide una página con revisiones
- **THEN** la respuesta incluye el id de su última revisión
