# mcp-server Specification

## Purpose
Define el servidor MCP local de solo lectura con el que un asistente de IA consulta un sitio
construido sobre Orion: cómo se lanza, qué herramientas ofrece y qué garantías mantiene.

## Requirements

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

### Requirement: The server answers the MCP lifecycle
El servidor SHALL responder `initialize` (con su nombre, la versión de Orion y la
capacidad de herramientas), `tools/list`, `tools/call` y `ping`, y MUST NOT responder a las
notificaciones. Un método desconocido SHALL dar el error JSON-RPC `-32601` y parámetros
inválidos el `-32602`.

#### Scenario: Initialize
- **WHEN** el cliente envía `initialize`
- **THEN** la respuesta incluye la versión del protocolo, `serverInfo` con la versión de Orion
  y la capacidad `tools`

#### Scenario: Notification
- **WHEN** el cliente envía `notifications/initialized`
- **THEN** el servidor no escribe ninguna respuesta

#### Scenario: Unknown method
- **WHEN** el cliente envía un método que el servidor no conoce
- **THEN** la respuesta es un error `-32601`

### Requirement: Tools are defined apart from the transport
Cada herramienta SHALL declararse en un registro con su nombre, su descripción, su esquema de
entrada y la función que la ejecuta, sin depender de la entrada ni de la salida estándar, de
modo que otro transporte pueda reutilizar el registro.

#### Scenario: Registry without stdio
- **WHEN** una prueba llama a una herramienta por el registro, sin lanzar el comando
- **THEN** obtiene su resultado sin abrir ningún flujo de entrada o salida

### Requirement: Tools only read unless writing is allowed
Cada herramienta SHALL declarar un nivel de acceso (`read`, `draft` o `settings`). Sin
`--allow-writes` en el modo local, y con una clave `read-only` en el remoto, ninguna
herramienta SHALL crear, modificar ni borrar datos, y las que no son de lectura MUST NOT
existir ni listarse. Una herramienta que no existe SHALL dar un error de herramienta
desconocida.

#### Scenario: No writes
- **WHEN** se ejecutan todas las herramientas del modo por defecto contra un sitio con contenido
- **THEN** no se ejecuta ninguna sentencia de escritura sobre la base de datos

#### Scenario: Write tool without the flag
- **WHEN** el cliente llama a `page_update_draft` sin que se haya lanzado con `--allow-writes`
- **THEN** recibe un error de herramienta desconocida

#### Scenario: Unclassified tool
- **WHEN** una herramienta no declara su nivel de acceso
- **THEN** una clave restringida no puede listarla ni llamarla

### Requirement: Results are bounded
Las herramientas que listan SHALL aceptar `page` y `per_page`, con un máximo de 100 por página
y un valor por defecto, e indicar el total y si hay más páginas.

#### Scenario: Limit exceeded
- **WHEN** el cliente pide `per_page` de 500
- **THEN** la herramienta responde con un error de parámetros

### Requirement: Tool errors are answers
Un error dentro de una herramienta SHALL volver como un resultado con `isError: true` y un
mensaje que explique la causa, y MUST NOT terminar el proceso.

#### Scenario: Page not found
- **WHEN** el cliente pide una página con un id que no existe
- **THEN** recibe un resultado con `isError: true` y el proceso sigue atendiendo mensajes

### Requirement: The site overview tool describes the site
La herramienta de resumen SHALL devolver el nombre del sitio, el idioma base, los idiomas
agregados y cuáles son públicos, y la versión de Orion.

#### Scenario: Languages
- **WHEN** el sitio tiene español como base y el inglés agregado sin publicar
- **THEN** el resumen lista ambos y marca el inglés como no público

### Requirement: The schema tool describes page types and blocks
La herramienta de esquema SHALL listar los tipos de página del sitio con sus campos y, para
los campos de cuerpo, los bloques disponibles con su nombre, tipo y etiqueta. Con el nombre de
un bloque SHALL devolver sus campos completos, de modo que un asistente sepa qué puede
construir sin leer el código y sin recibir de una vez la descripción de todos los bloques.

#### Scenario: Project page type
- **WHEN** el proyecto define un tipo de página propio con un bloque propio
- **THEN** el esquema los incluye junto a los de Orion

#### Scenario: One block in full
- **WHEN** el cliente pide el esquema del bloque `hero`
- **THEN** recibe sus campos, con tipo, etiqueta y opciones

#### Scenario: Unknown block
- **WHEN** el cliente pide un bloque que no existe
- **THEN** recibe un resultado con `isError: true`

### Requirement: Page tools expose the tree and a page
La herramienta de árbol SHALL devolver las páginas con su id, título, tipo, URL, estado de
publicación e idioma, en páginas acotadas. La herramienta de página SHALL devolver una página
con sus campos, incluido el cuerpo en el formato guardado.

#### Scenario: Page tree
- **WHEN** el sitio tiene una portada con dos páginas hijas
- **THEN** el árbol las lista con su jerarquía y su estado

### Requirement: Site settings are readable
Una herramienta SHALL devolver los datos del sitio (identidad, contacto, redes y los ajustes
de SEO) y los textos del sitio por idioma, sin incluir valores secretos.

#### Scenario: Settings
- **WHEN** el cliente pide los ajustes del sitio
- **THEN** recibe los datos cargados y no recibe claves ni variables de entorno

### Requirement: Redirects and recorded 404s are readable
Las herramientas SHALL listar las redirecciones (origen, destino y tipo) y las rutas que
dieron 404 con su cantidad de visitas, en páginas acotadas.

#### Scenario: 404 list
- **WHEN** el sitio registró tres rutas con 404
- **THEN** la herramienta las devuelve ordenadas por visitas

### Requirement: Forms are listed without their submissions
La herramienta de formularios SHALL listar cada formulario con su título, URL, campos y
destinatario de avisos, y MUST NOT incluir envíos, adjuntos ni datos de quienes los enviaron.

#### Scenario: Form with submissions
- **WHEN** un formulario tiene envíos guardados
- **THEN** la herramienta devuelve el formulario sin ningún dato de esos envíos

### Requirement: Project checks are available as tools
El servidor SHALL ofrecer herramientas para el chequeo de convenciones, las imágenes sin uso
(sin borrar nada) y el estado de salud de la base, con el mismo resultado que sus comandos.

#### Scenario: Unused images
- **WHEN** hay dos imágenes que ninguna página usa
- **THEN** la herramienta las lista y no borra ninguna

### Requirement: No personal data of users is exposed
Ninguna herramienta SHALL devolver datos de cuentas de usuario (nombres, emails, contraseñas
ni dispositivos de verificación) ni envíos de formularios.

#### Scenario: User accounts
- **WHEN** se recorren los resultados de todas las herramientas
- **THEN** no aparece el email ni el nombre de ninguna cuenta del admin

### Requirement: A guide explains how to connect an assistant
El repositorio SHALL incluir la guía `docs/guias/usar-el-mcp.md`, en español, con el comando
para lanzar el servidor, un ejemplo de configuración para Claude Code, la lista de
herramientas, lo que no expone, la advertencia sobre datos personales y contenido ajeno, y
cómo activar la escritura local con la cuenta técnica. MUST enlazar la guía del endpoint
remoto. El `AGENTS.md` de la plantilla MUST enlazarla.

#### Scenario: Configuration example
- **WHEN** se lee la guía
- **THEN** incluye un ejemplo de `.mcp.json` con `pipenv run manage orion_mcp`

#### Scenario: Writing is documented
- **WHEN** se lee la sección de escritura
- **THEN** explica `--allow-writes`, la cuenta técnica y que nada se publica solo

#### Scenario: Remote guide
- **WHEN** se lee la guía
- **THEN** enlaza `mcp-en-produccion.md`

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

### Requirement: Pages expose the revision to expect
La herramienta de página SHALL devolver `latest_revision_id`, el id de la última revisión, para
usarlo como revisión esperada.

#### Scenario: Revision id
- **WHEN** el cliente pide una página con revisiones
- **THEN** la respuesta incluye el id de su última revisión

### Requirement: The HTTP endpoint is off by default
El sitio SHALL servir el MCP en `POST /_mcp/` solo si `ORION_MCP_ENDPOINT` está activado. Con
el ajuste apagado, que es el valor por defecto, la ruta MUST responder 404. La ruta SHALL
quedar fuera del caché de páginas y del registro de 404.

#### Scenario: Off
- **WHEN** el ajuste está apagado y llega un POST con una clave válida
- **THEN** la respuesta es 404

#### Scenario: Not a public page
- **WHEN** el endpoint está encendido y recibe peticiones
- **THEN** ninguna entra al caché de páginas ni al registro de rutas 404

### Requirement: The endpoint takes one JSON-RPC message per POST
El endpoint SHALL leer un mensaje JSON-RPC por petición POST con `Authorization: Bearer`, usar
el mismo manejo de mensajes del modo local y responder `application/json`. Las notificaciones
SHALL recibir 202 sin cuerpo. GET y DELETE MUST recibir 405. Las respuestas MUST llevar
`Cache-Control: no-store` y la ruta MUST NOT exigir sesión ni CSRF.

#### Scenario: Request
- **WHEN** llega un `initialize` con una clave válida
- **THEN** la respuesta es JSON con la versión del protocolo

#### Scenario: Notification
- **WHEN** llega `notifications/initialized`
- **THEN** la respuesta es 202 sin cuerpo

#### Scenario: GET
- **WHEN** llega un GET
- **THEN** la respuesta es 405

### Requirement: The endpoint refuses what is not a plain API call
El endpoint SHALL rechazar con 403 una petición con cabecera `Origin` que no figure en
`ORION_MCP_ALLOWED_ORIGINS` (vacía por defecto), con 400 una `MCP-Protocol-Version`
desconocida y con 413 un cuerpo mayor que `ORION_MCP_MAX_BODY` (1 MB por defecto).

#### Scenario: Browser origin
- **WHEN** llega una petición con `Origin: https://otro.example`
- **THEN** la respuesta es 403

#### Scenario: Body too large
- **WHEN** el cuerpo supera el máximo
- **THEN** la respuesta es 413

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

### Requirement: A key acts as its user
Las herramientas de escritura llamadas con una clave SHALL actuar como el usuario de la clave,
con sus permisos de Wagtail recortados por el alcance, y las revisiones y el historial MUST
quedar a su nombre.

#### Scenario: Attribution
- **WHEN** una clave `draft-only` crea un borrador
- **THEN** la revisión es del usuario de la clave

#### Scenario: Permissions still apply
- **WHEN** el usuario de la clave no puede agregar subpáginas bajo ese padre
- **THEN** recibe un error de herramienta de permiso

### Requirement: Operation keys make retries safe
Las herramientas de escritura llamadas con una clave SHALL aceptar `operation_key` (hasta 100
caracteres de `A-Za-z0-9_.:-`). Repetirla con los mismos argumentos MUST devolver el resultado
guardado sin ejecutar la operación de nuevo; con otros argumentos MUST dar un error de
conflicto. Los recibos MUST ser de cada clave.

#### Scenario: Exact retry
- **WHEN** se repite `page_create_draft` con la misma `operation_key` y los mismos argumentos
- **THEN** la respuesta es la misma y existe una sola página

#### Scenario: Same key, other arguments
- **WHEN** se repite la `operation_key` con otro título
- **THEN** recibe un error de conflicto y no se crea nada

### Requirement: Old receipts are purged without a scheduled task
Los recibos con más de 30 días SHALL borrarse de forma oportunista al registrar uno nuevo,
como mucho una vez por hora, sin una tarea programada.

#### Scenario: Expired
- **WHEN** se registra un recibo y hay otros de hace 31 días
- **THEN** los antiguos se borran

### Requirement: Use is limited
El endpoint SHALL limitar los intentos de autenticación fallidos por IP y las peticiones por
clave por minuto (`ORION_MCP_RATE_LIMIT`), respondiendo 429 con `Retry-After`. La IP SHALL ser
la del visitante según `ORION_TRUSTED_PROXIES`.

#### Scenario: Failed attempts
- **WHEN** una IP supera los intentos fallidos permitidos
- **THEN** recibe 429 incluso con una clave válida mientras dure el bloqueo

### Requirement: Each call is logged without secrets
Cada llamada autenticada SHALL escribir un registro con el prefijo de la clave, la herramienta
y el resultado (ok o error), y MUST NOT incluir el token ni los argumentos.

#### Scenario: Log line
- **WHEN** una clave llama a `page_get`
- **THEN** el registro tiene su prefijo y la herramienta, y no su token

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
