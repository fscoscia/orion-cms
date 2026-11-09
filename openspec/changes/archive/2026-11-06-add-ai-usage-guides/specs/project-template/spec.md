# Spec Delta

## ADDED Requirements

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
