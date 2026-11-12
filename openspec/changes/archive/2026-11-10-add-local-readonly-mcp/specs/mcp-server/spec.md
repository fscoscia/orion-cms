## Purpose
Define el servidor MCP local de solo lectura con el que un asistente de IA consulta un sitio
construido sobre Orion: cómo se lanza, qué herramientas ofrece y qué garantías mantiene.

## ADDED Requirements

### Requirement: A command starts a local MCP server over stdio
`manage.py orion_mcp` SHALL iniciar un servidor MCP que lee mensajes JSON-RPC 2.0, uno por
línea, de la entrada estándar y escribe las respuestas, una por línea, en la salida estándar.
La salida estándar MUST llevar solo mensajes del protocolo; los registros y avisos SHALL ir a
la salida de errores. El servidor MUST terminar cuando se cierra la entrada.

#### Scenario: Protocol on stdout only
- **WHEN** el servidor recibe cualquier mensaje y una herramienta escribe con `print`
- **THEN** la salida estándar contiene solo respuestas JSON-RPC válidas

#### Scenario: Input closed
- **WHEN** el cliente cierra la entrada
- **THEN** el proceso termina sin error

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

### Requirement: Every tool only reads
Ninguna herramienta SHALL crear, modificar ni borrar datos, archivos ni configuración. Una
herramienta que no existe SHALL dar un error de herramienta desconocida.

#### Scenario: No writes
- **WHEN** se ejecutan todas las herramientas contra un sitio con contenido
- **THEN** no se ejecuta ninguna sentencia de escritura sobre la base de datos

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
herramientas, lo que no expone y la advertencia sobre datos personales y contenido ajeno. El
`AGENTS.md` de la plantilla MUST enlazarla.

#### Scenario: Configuration example
- **WHEN** se lee la guía
- **THEN** incluye un ejemplo de `.mcp.json` con `pipenv run manage orion_mcp`
