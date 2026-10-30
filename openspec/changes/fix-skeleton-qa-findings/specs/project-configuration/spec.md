## ADDED Requirements

### Requirement: Email uses TLS unless SSL is chosen
El sistema SHALL usar TLS para el email cuando ninguna variable de entorno elige otro
modo, y MUST dejar de usar TLS cuando se activa SSL sin indicar TLS.

#### Scenario: Neither variable defined
- **WHEN** `EMAIL_USE_TLS` y `EMAIL_USE_SSL` no están definidas
- **THEN** el email usa TLS y no usa SSL

#### Scenario: Only SSL enabled
- **WHEN** `EMAIL_USE_SSL` vale `true` y `EMAIL_USE_TLS` no está definida
- **THEN** el email usa SSL, no usa TLS y la verificación de arranque no informa errores
  de email

#### Scenario: TLS explicitly disabled
- **WHEN** `EMAIL_USE_TLS` vale `false` y `EMAIL_USE_SSL` no está definida
- **THEN** el email no usa TLS ni SSL
