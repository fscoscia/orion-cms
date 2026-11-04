## ADDED Requirements

### Requirement: A project's env file is read without pipenv
El sistema SHALL ofrecer a los proyectos una forma de cargar las variables de un archivo
`.env` antes de leer los ajustes, sin depender de cómo se lance el proceso. Una variable
ya definida en el entorno MUST conservar su valor, y la ausencia del archivo MUST NOT ser
un error.

#### Scenario: Variable only in the file
- **WHEN** `SECRET_KEY` está en el `.env` y no en el entorno
- **THEN** los ajustes usan el valor del archivo

#### Scenario: Variable in both places
- **WHEN** `DEBUG` vale `false` en el entorno y `true` en el `.env`
- **THEN** los ajustes usan `false`

#### Scenario: No file
- **WHEN** el proyecto no tiene `.env` y las variables están en el entorno
- **THEN** los ajustes se cargan sin error

#### Scenario: Values with special characters
- **WHEN** `SECRET_KEY` en el `.env` contiene `#`, `$`, `(` o `=`
- **THEN** los ajustes reciben el valor completo y sin cambios

### Requirement: Server errors are logged outside debug
Fuera de debug, el sistema SHALL escribir en la salida de errores del proceso cada error
del servidor, con su traza, y los avisos de la aplicación, sin depender de que haya
destinatarios de email configurados.

#### Scenario: Unhandled error in a request
- **WHEN** una vista lanza una excepción no controlada con `DEBUG` apagado
- **THEN** la respuesta es 500 y la traza de la excepción aparece en la salida de errores

#### Scenario: Error logged by Orion
- **WHEN** falla el envío del aviso de un formulario con `DEBUG` apagado
- **THEN** el error aparece en la salida de errores

### Requirement: Not-found requests stay out of the error log
El sistema MUST NOT escribir en la salida de errores las respuestas 404 ni otras
respuestas 4xx, para que el tráfico de bots no tape los errores reales.

#### Scenario: Missing page
- **WHEN** una visita pide una ruta inexistente con `DEBUG` apagado
- **THEN** la salida de errores no registra esa petición
