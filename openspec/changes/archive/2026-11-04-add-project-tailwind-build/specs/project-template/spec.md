## MODIFIED Requirements

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

## ADDED Requirements

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
