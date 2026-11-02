## MODIFIED Requirements

### Requirement: Secure defaults outside debug
Con el modo debug apagado, el sistema SHALL enviar las cookies de sesión y de CSRF solo por
HTTPS, marcar la cookie de sesión como no accesible desde JavaScript, prohibir que otros
sitios muestren el sitio dentro de un marco, redirigir HTTP a HTTPS y mandar HSTS.

#### Scenario: Production cookies
- **WHEN** el modo debug está apagado
- **THEN** las cookies de sesión y CSRF se marcan como seguras y la de sesión como HttpOnly

#### Scenario: Production HTTPS
- **WHEN** el modo debug está apagado
- **THEN** la redirección a HTTPS está activa y HSTS dura un año

#### Scenario: Development
- **WHEN** el modo debug está encendido
- **THEN** no hay redirección a HTTPS ni HSTS
