# ai-assisted-development Specification

## Purpose
Documenta cómo construir un sitio sobre Orion con un asistente de IA: cómo repartir el
trabajo entre Orion y el proyecto, qué skills usar en cada fase y qué revisar a mano, para
que el agente no se limite ni se descontrole y no cause pérdidas silenciosas de contenido.

## Requirements

### Requirement: A guide explains how to build a site on Orion with an AI assistant
El repositorio SHALL incluir la guía `docs/guias/trabajar-con-ia.md`, en español, para quien
construye un sitio sobre Orion con un asistente de IA. La guía MUST cubrir: el reparto de
trabajo entre Orion y el proyecto, el criterio de bloques de Orion o propios, el uso de las
skills por fase, los choques entre skills, qué revisar siempre a mano, los problemas típicos
de los bloques propios, cómo pedir bien y qué no delegar sin revisión.

#### Scenario: The guide exists and covers its sections
- **WHEN** se abre `docs/guias/trabajar-con-ia.md`
- **THEN** tiene una sección para cada uno de los temas anteriores

### Requirement: The guide gives a criterion for Orion's blocks or the project's own
La guía MUST ofrecer un criterio, no una prohibición, para elegir entre los bloques de Orion
y los bloques propios, con ejemplos genéricos que no nombren un cliente ni un diseño
concreto.

#### Scenario: Orion's block fits
- **WHEN** el contenido tiene la forma de un bloque de Orion y el aspecto se logra con CSS,
  un estilo de bloque o un template propio
- **THEN** el criterio indica usar el bloque de Orion

#### Scenario: Three situations favour an own block
- **WHEN** se lee el criterio
- **THEN** enumera como motivos válidos para un bloque propio los datos que el bloque no
  tiene, el comportamiento propio y la composición que Orion no ofrece

#### Scenario: Examples do not name a client
- **WHEN** se buscan en la guía los nombres de un cliente o de un diseño concreto
- **THEN** no aparecen en los ejemplos del criterio

### Requirement: The guide asks to justify each own block
La guía MUST pedir que cada bloque propio lleve una línea que diga qué necesita que Orion no
ofrece, y que un patrón repetido en varios proyectos se proponga para Orion.

#### Scenario: Each own block is justified
- **WHEN** se lee la regla sobre bloques propios
- **THEN** pide esa línea de justificación en cada uno

### Requirement: The guide assigns the skills by phase without letting two decide the same thing
La guía MUST describir las skills de IA en fases (dirección, construcción, refinado,
movimiento y verificación), indicar que una sola skill decide la dirección visual, y
distinguir lo que se probó con Orion de lo que no. MUST nombrar los choques conocidos entre
skills y cómo resolverlos, y MUST advertir que el instalador de una skill puede descargar un
binario y enviar telemetría, pidiendo revisarlo antes de usarla.

#### Scenario: One skill decides the direction
- **WHEN** se lee la fase de dirección
- **THEN** indica que se elige una skill para decidirla y que la otra solo verifica

#### Scenario: Tested and untested are distinguished
- **WHEN** se lee la descripción de cada skill
- **THEN** separa lo que se probó con Orion de lo que no se probó

#### Scenario: Third-party installers are flagged
- **WHEN** se lee la advertencia sobre skills de terceros
- **THEN** pide verificar lo que se descarga y apagar la telemetría antes de usarla

### Requirement: The guide requires checking the result in a browser by walking the whole page
La guía MUST exigir que un cambio visual se revise en un navegador a un ancho de teléfono y a
uno de escritorio, recorriendo la página entera para que carguen las imágenes con carga
perezosa, y MUST listar qué comprobar: accesibilidad, rendimiento, contenido editable,
formato de las cifras en el idioma del sitio y textos de relleno.

#### Scenario: The whole page is walked
- **WHEN** se lee la sección de revisión manual
- **THEN** pide recorrer la página entera antes de dar el resultado por bueno

### Requirement: The guide lists the typical failures of own blocks
La guía MUST listar las fallas silenciosas conocidas de los bloques propios y cómo
evitarlas: una clave de bloque que tapa a la de Orion, quitar un bloque con contenido, un
componente de Alpine con el nombre de uno de Orion, CSS dentro de `@layer` que pierde contra
las utilidades de Tailwind, imágenes recortadas por la rendición `card`, una portada propia
sin la clave `hero` y anclas duplicadas.

#### Scenario: Each known failure is listed with its remedy
- **WHEN** se lee la sección de problemas típicos
- **THEN** aparece cada falla de la lista con cómo evitarla

### Requirement: The guide explains how to update Orion in a project with own blocks
La guía MUST explicar los pasos de una actualización de Orion en un proyecto con bloques
propios: leer el CHANGELOG, comprobar que ninguna clave nueva choque con las propias,
correr `makemigrations --check` y `migrate` (los bloques nuevos de Orion traen migraciones de
definición del campo `body` que no tocan el contenido) y revisar la portada.

#### Scenario: Update steps
- **WHEN** se lee la sección de actualización
- **THEN** incluye revisar el CHANGELOG, comparar claves, aplicar las migraciones y revisar
  la portada

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
