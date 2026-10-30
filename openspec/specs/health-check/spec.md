# health-check Specification

## Purpose
Permite que un monitor externo o el servidor de despliegue sepa si la aplicación responde y
puede comunicarse con su base de datos, sin exponer información interna.

## Requirements

### Requirement: Health endpoint reports status
El sistema SHALL exponer `/health/` respondiendo `200` con un cuerpo JSON que indica estado
correcto cuando la aplicación y la base de datos responden.

#### Scenario: Everything works
- **WHEN** un cliente pide `GET /health/` y la base de datos responde
- **THEN** la respuesta es `200` con `{"status": "ok"}`

### Requirement: Database failure is reported as unavailable
El sistema SHALL responder `503` con estado de error cuando la base de datos no responde.

#### Scenario: Database down
- **WHEN** un cliente pide `GET /health/` y la consulta a la base de datos falla
- **THEN** la respuesta es `503` con `{"status": "error"}`

### Requirement: Health responses expose no internals and are not cached
Las respuestas de salud MUST NOT incluir mensajes de error, versiones ni datos de
configuración, y MUST indicar que no deben guardarse en caché.

#### Scenario: Failure detail hidden
- **WHEN** la base de datos falla con un mensaje técnico
- **THEN** la respuesta no contiene ese mensaje

#### Scenario: No caching
- **WHEN** se pide `/health/`
- **THEN** la respuesta incluye `Cache-Control: no-store`

### Requirement: Health endpoint only accepts read methods
El endpoint SHALL aceptar solo `GET` y `HEAD`.

#### Scenario: Write method
- **WHEN** un cliente envía `POST /health/`
- **THEN** la respuesta es `405`
