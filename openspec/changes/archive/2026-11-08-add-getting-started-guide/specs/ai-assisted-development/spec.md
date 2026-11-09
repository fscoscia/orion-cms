## ADDED Requirements

### Requirement: A getting-started guide takes a developer from an empty machine to a running project
El repositorio SHALL incluir la guía `docs/guias/empezar.md`, en español, para quien construye
un sitio sobre Orion con un asistente de IA. La guía MUST cubrir, en este orden: preparar la
máquina, instalar `orion-start` fuera de un proyecto, crear el proyecto, configurar `.env` y
la base de datos, dejar el sitio funcionando, abrir el proyecto con el asistente y hacer una
primera tarea guiada.

#### Scenario: The guide covers the whole path
- **WHEN** se abre `docs/guias/empezar.md`
- **THEN** tiene una sección por cada paso anterior, en ese orden

#### Scenario: Prerequisites can be checked
- **WHEN** se lee la sección de preparación de la máquina
- **THEN** cada herramienta requerida trae el comando que comprueba que está instalada

### Requirement: The getting-started guide installs Orion from its public repository
La guía MUST indicar cómo instalar `orion-start` desde el repositorio público de Orion sin
tener todavía un proyecto, con la URL real del repositorio y una etiqueta de versión, y MUST
explicar que el `Pipfile` del proyecto generado fija esa misma versión.

#### Scenario: Installation commands use the real repository
- **WHEN** se leen los comandos de instalación de la guía
- **THEN** la URL es la del repositorio publicado y no contiene marcadores como `<organization>`

#### Scenario: The version is explicit
- **WHEN** se lee el comando de instalación
- **THEN** fija una etiqueta de versión, no una rama

### Requirement: The getting-started guide brings the site up with Orion's install command
La guía MUST usar `orion_install` para migrar, crear el administrador y cargar los formularios
de ejemplo, e indicar cómo comprobar que el sitio responde (el admin y `/health/`).

#### Scenario: The site is verified
- **WHEN** se lee el paso de puesta en marcha
- **THEN** termina con la comprobación del admin y del chequeo de salud

### Requirement: The getting-started guide verifies that the assistant loaded the project rules
La guía MUST incluir un primer pedido para el asistente, ya redactado, cuya respuesta
demuestra que cargó el `AGENTS.md`: qué no puede editar y cómo decide entre un bloque de
Orion y uno propio. MUST decir qué hacer si la respuesta no refleja las reglas.

#### Scenario: A prompt confirms the rules were loaded
- **WHEN** se lee el paso de abrir el proyecto con el asistente
- **THEN** hay un pedido listo para copiar y se describe qué debe mencionar la respuesta

#### Scenario: The assistant did not load the file
- **WHEN** la respuesta no refleja las reglas
- **THEN** la guía indica cómo indicarle el `AGENTS.md` al asistente

### Requirement: The getting-started guide states what it was checked against
La guía MUST declarar la versión de Orion y la fecha con las que se comprobó cada comando, y
MUST distinguir lo que no pudo comprobarse.

#### Scenario: Version and date are declared
- **WHEN** se abre la guía
- **THEN** nombra la versión de Orion y la fecha de la comprobación

### Requirement: A styles-and-design guide explains where and how the project styles live
El repositorio SHALL incluir la guía `docs/guias/estilos-y-diseno.md`, que MUST explicar dónde
vive el CSS propio del proyecto y cómo se compila, por qué el CSS propio va fuera de
`@layer`, cómo definir estilos de bloque, cómo declarar tamaños de imagen y regenerar los
recortes, y cómo sobrescribir un template de Orion por nombre.

#### Scenario: Each topic is covered
- **WHEN** se abre `docs/guias/estilos-y-diseno.md`
- **THEN** tiene una sección por cada tema anterior

#### Scenario: Commands exist in the project
- **WHEN** la guía nombra un comando o una variable de configuración
- **THEN** existe en Orion o en el proyecto generado

### Requirement: The guides link to each other
`trabajar-con-ia.md` MUST enlazar la guía de arranque y la de estilos y diseño, y el README
MUST enlazarlas desde la sección que explica cómo usar Orion en un proyecto.

#### Scenario: Entry points reach the guides
- **WHEN** se lee el README y `trabajar-con-ia.md`
- **THEN** ambos enlazan `empezar.md` y `estilos-y-diseno.md`
