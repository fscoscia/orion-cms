# project-template Specification

## Purpose

Genera, con un solo comando, la estructura de un proyecto Django nuevo ya conectado a
Orion: lo que hoy hay que copiar a mano siguiendo el README.

## Requirements

### Requirement: A console command scaffolds a new project connected to Orion
Instalar el paquete SHALL agregar un comando de consola que, dado un nombre de proyecto,
cree un directorio con `manage.py`, los ajustes del proyecto (importando los ajustes base
de Orion y fijando `ROOT_URLCONF`, `WSGI_APPLICATION`, `STATIC_ROOT`, `MEDIA_ROOT`, el
directorio de templates propios y la compilación de Tailwind del proyecto), las rutas y
el WSGI, una app propia vacía para el diseño y los bloques del cliente, un directorio de
templates para sobrescribir los de Orion por nombre (incluido un override de
`orion/base.html` que carga el CSS propio del proyecto), un archivo fuente de Tailwind
propio del proyecto, un `.env.example` con las variables de los ajustes base, un
`.gitignore` que excluye al menos `.env` y los demás archivos que no deben llegar a un
commit, y un `Pipfile` que fija la versión de Orion instalada y agrega
`django-tailwind-cli` para compilar el CSS propio.

#### Scenario: New project
- **WHEN** se corre el comando con un nombre de proyecto en un directorio vacío
- **THEN** el directorio resultante tiene `manage.py`, los ajustes, las rutas, el WSGI, la
  app propia, el directorio de templates, el archivo fuente de Tailwind propio,
  `.env.example`, `.gitignore` y `Pipfile`

#### Scenario: Settings already import Orion's base
- **WHEN** se abren los ajustes generados
- **THEN** importan los ajustes base de Orion y fijan `ROOT_URLCONF`, `WSGI_APPLICATION`,
  `STATIC_ROOT`, `MEDIA_ROOT` y el directorio de templates con el nombre del proyecto

#### Scenario: Secrets are excluded from version control
- **WHEN** se abre el `.gitignore` generado
- **THEN** excluye `.env`

#### Scenario: Tailwind is configured to build the project's own stylesheet
- **WHEN** se abren los ajustes generados
- **THEN** `django_tailwind_cli` está instalado, apunta al archivo fuente propio del
  proyecto y su salida es un archivo distinto al que ya trae Orion compilado

### Requirement: The command refuses to overwrite an existing project
El comando MUST negarse a escribir sobre un directorio que ya tiene contenido, en lugar de
mezclar o sobrescribir archivos.

#### Scenario: Destination already exists
- **WHEN** se corre el comando con un nombre que ya existe como directorio con archivos
- **THEN** el comando falla sin modificar ese directorio

### Requirement: The project's version pin is explicit
El `Pipfile` generado SHALL fijar una versión de Orion (la instalada al correr el comando),
para que quien lo usa confirme o ajuste la etiqueta antes de instalar.

#### Scenario: Pipfile references a version
- **WHEN** se abre el `Pipfile` generado
- **THEN** la dependencia de Orion nombra una versión, no una referencia sin fijar

### Requirement: The project's own templates compile to their own stylesheet
El proyecto generado SHALL poder compilar, con el mismo mecanismo que usa Orion
internamente (`django-tailwind-cli`, sin Node), las clases de Tailwind que usan sus
propios templates y bloques, en un archivo separado del CSS que Orion ya trae
compilado, sin modificarlo ni sobrescribirlo.

#### Scenario: Project classes compile without touching Orion's CSS
- **WHEN** se corre el comando de compilación de Tailwind sobre el proyecto generado,
  con un template propio que usa una clase de Tailwind
- **THEN** esa clase aparece en el CSS compilado del proyecto, y el CSS que Orion trae
  compilado (`orion/css/orion.css`) no cambia

#### Scenario: The project's stylesheet loads alongside Orion's
- **WHEN** se visita una página del sitio generado
- **THEN** el HTML carga tanto el CSS de Orion como el CSS propio del proyecto

### Requirement: A generated project loads its env file
Los ajustes de un proyecto generado SHALL cargar el `.env` de la raíz del proyecto antes
de importar los ajustes de Orion, de modo que `manage.py`, Gunicorn y Passenger reciban
la misma configuración sin pasos adicionales.

#### Scenario: Command without pipenv
- **WHEN** se corre `python manage.py check` en un proyecto generado con el `.env`
  completo y sin esas variables en el entorno
- **THEN** el comando termina sin errores de configuración

#### Scenario: WSGI application without pipenv
- **WHEN** un servidor importa la aplicación WSGI del proyecto con el `.env` completo y
  sin esas variables en el entorno
- **THEN** la aplicación se carga sin errores de configuración

### Requirement: The generated gitignore keeps the project's own static files
El `.gitignore` generado MUST ignorar las carpetas de estáticos y medios solo en la raíz
del proyecto, nunca dentro de las apps.

#### Scenario: Static files of an app
- **WHEN** el proyecto tiene `home/static/home/css/site.css`
- **THEN** git no ignora ese archivo

#### Scenario: Collected static files
- **WHEN** `collectstatic` escribe en `static/` en la raíz del proyecto
- **THEN** git ignora esa carpeta

### Requirement: The generated gitignore excludes form attachments
El `.gitignore` generado MUST excluir la carpeta `private/` de la raíz del proyecto, que
por defecto guarda los adjuntos de los formularios.

#### Scenario: Attachment in the default folder
- **WHEN** existe `private/forms/1/abc/cv.pdf`
- **THEN** git ignora ese archivo

### Requirement: The project's compiled stylesheet is versioned
El proyecto generado SHALL incluir su hoja de estilos compilada inicial, y su `.gitignore`
MUST NOT ignorarla, de modo que un deploy no necesite compilar CSS.

#### Scenario: Compiled stylesheet in version control
- **WHEN** existe `assets/project/css/project.css` en un proyecto generado
- **THEN** git no ignora ese archivo

### Requirement: A new project serves pages before compiling its stylesheet
Un proyecto recién generado MUST responder sus páginas públicas fuera de debug sin haber
corrido nunca la compilación de CSS.

#### Scenario: First deploy without compiling
- **WHEN** en un proyecto recién generado se corre `collectstatic` con `DEBUG` apagado y se
  pide la portada
- **THEN** la respuesta es 200

### Requirement: A generated project includes instructions for AI assistants
El proyecto generado SHALL incluir en su raíz un `AGENTS.md` con las reglas para quien
construye el sitio con un asistente de IA, y un `CLAUDE.md` mínimo que apunte a ese archivo.
Ninguno MUST conservar marcadores de posición sin reemplazar, y el nombre del proyecto MUST
aparecer donde corresponda. El `.gitignore` generado MUST NOT ignorarlos.

#### Scenario: Both files are delivered
- **WHEN** se corre el comando con un nombre de proyecto
- **THEN** la raíz del proyecto tiene `AGENTS.md` y `CLAUDE.md`

#### Scenario: The project name is inserted
- **WHEN** se abre el `AGENTS.md` generado para el proyecto `mysite`
- **THEN** nombra `mysite` y no contiene marcadores de posición sin reemplazar

#### Scenario: CLAUDE.md points to AGENTS.md
- **WHEN** se abre el `CLAUDE.md` generado
- **THEN** remite al `AGENTS.md` de la raíz

#### Scenario: The files are versioned
- **WHEN** existen `AGENTS.md` y `CLAUDE.md` en un proyecto generado
- **THEN** git no los ignora

### Requirement: The generated AGENTS.md states the working rules of the project
El `AGENTS.md` generado MUST decir qué se toca y qué no (el paquete de Orion instalado no
se edita), el criterio de bloques de Orion o propios, los comandos del proyecto incluido el
de pruebas (`manage test`, porque el proyecto no instala `pytest`), las guías por tarea, las
reglas de CSS y de contenido existente, los pasos para actualizar Orion y cómo verificar una
tarea al terminar.

#### Scenario: The test command matches what the project installs
- **WHEN** se abre el `AGENTS.md` generado
- **THEN** el comando de pruebas es `manage test` y no menciona `pytest`

#### Scenario: Existing content is protected
- **WHEN** se lee la sección de contenido existente
- **THEN** advierte que quitar un bloque con contenido o renombrar una clave exige migrar
  los datos antes

#### Scenario: Update steps are present
- **WHEN** se lee la sección de actualización de Orion
- **THEN** incluye revisar el CHANGELOG, comparar claves de bloques y aplicar las migraciones

### Requirement: The generated Pipfile points to Orion's repository without placeholders
El `Pipfile` generado MUST apuntar a la URL del repositorio de Orion sin marcadores de
posición, de modo que instalar el proyecto no exija editar el archivo.

#### Scenario: No placeholder remains
- **WHEN** se abre el `Pipfile` generado
- **THEN** la URL de Orion no contiene `<organization>` ni otro marcador por completar

### Requirement: The generated AGENTS.md points to the getting-started and task guides
El `AGENTS.md` generado MUST enlazar la guía de arranque y las guías por tarea con una URL
que se pueda abrir, porque `docs/guias/` no viaja con el paquete.

#### Scenario: Guides are reachable
- **WHEN** se abre el `AGENTS.md` generado
- **THEN** nombra `empezar.md` y las guías por tarea con su enlace
