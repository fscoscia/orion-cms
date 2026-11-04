## ADDED Requirements

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
