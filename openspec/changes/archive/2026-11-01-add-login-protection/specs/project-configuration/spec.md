## ADDED Requirements

### Requirement: The visitor's address is read behind trusted proxies
El sistema SHALL tomar la IP del visitante de `REMOTE_ADDR` cuando
`ORION_TRUSTED_PROXIES` vale 0 (por defecto). Con un valor N mayor que 0 SHALL tomarla de
`X-Forwarded-For`, contando N direcciones desde la derecha, y MUST ignorar las que el
visitante agregue a la izquierda. Si el header tiene menos direcciones que N, SHALL usar
la primera. El límite de intentos de login y el de envíos de formularios SHALL usar esa
IP.

#### Scenario: Directly exposed
- **WHEN** `ORION_TRUSTED_PROXIES` vale 0 y llega `X-Forwarded-For: 1.2.3.4`
- **THEN** la IP es la de `REMOTE_ADDR` y el header se ignora

#### Scenario: Behind Nginx
- **WHEN** `ORION_TRUSTED_PROXIES` vale 1 y llega `X-Forwarded-For: 9.9.9.9, 1.2.3.4`
- **THEN** la IP es `1.2.3.4`, la que agregó Nginx, aunque el visitante haya inventado
  `9.9.9.9`
