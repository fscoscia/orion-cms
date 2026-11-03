## Purpose

Genera, con un solo comando, la estructura de un proyecto Django nuevo ya conectado a
Orion: lo que hoy hay que copiar a mano siguiendo el README.

## ADDED Requirements

### Requirement: A console command scaffolds a new project connected to Orion
Instalar el paquete SHALL agregar un comando de consola que, dado un nombre de proyecto,
cree un directorio con `manage.py`, los ajustes del proyecto (importando los ajustes base
de Orion y fijando `ROOT_URLCONF`, `WSGI_APPLICATION`, `STATIC_ROOT`, `MEDIA_ROOT` y el
directorio de templates propios), las rutas y el WSGI, una app propia vacía para el diseño
y los bloques del cliente, un directorio de templates para sobrescribir los de Orion por
nombre, un `.env.example` con las variables de los ajustes base, y un `Pipfile` que fija la
versión de Orion instalada.

#### Scenario: New project
- **WHEN** se corre el comando con un nombre de proyecto en un directorio vacío
- **THEN** el directorio resultante tiene `manage.py`, los ajustes, las rutas, el WSGI, la
  app propia, el directorio de templates, `.env.example` y `Pipfile`

#### Scenario: Settings already import Orion's base
- **WHEN** se abren los ajustes generados
- **THEN** importan los ajustes base de Orion y fijan `ROOT_URLCONF`, `WSGI_APPLICATION`,
  `STATIC_ROOT`, `MEDIA_ROOT` y el directorio de templates con el nombre del proyecto

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
