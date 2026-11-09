## ADDED Requirements

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
