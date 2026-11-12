## MODIFIED Requirements

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

## ADDED Requirements

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
`draft-only` SHALL además poder usar `page_create_draft` y `page_update_draft`. Ninguna clave
remota SHALL poder usar `redirect_create`, `redirect_update`, `site_settings_update` ni
`site_texts_update`.

#### Scenario: Read-only key
- **WHEN** una clave `read-only` llama a `page_create_draft`
- **THEN** recibe un error de herramienta desconocida

#### Scenario: Draft-only key and redirects
- **WHEN** una clave `draft-only` ligada a un Administrador llama a `redirect_create`
- **THEN** recibe un error de herramienta desconocida

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
alcances, cómo conectar un cliente, los límites, la rotación y los riesgos. El `AGENTS.md` de
la plantilla y `docs/alta-de-cliente.md` MUST enlazarla.

#### Scenario: Risks
- **WHEN** se lee la guía
- **THEN** dice qué permite una clave filtrada y cómo revocarla
