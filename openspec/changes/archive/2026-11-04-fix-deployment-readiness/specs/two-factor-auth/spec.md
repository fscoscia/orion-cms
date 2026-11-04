## ADDED Requirements

### Requirement: The second factor is required under a URL prefix
El sistema MUST exigir el segundo factor en el admin también cuando el sitio se sirve bajo
un prefijo de URL, como una subruta de cPanel.

#### Scenario: Admin under a prefix without verifying
- **WHEN** un usuario con acceso al admin, sin el segundo factor verificado, abre el admin
  de un sitio servido bajo `/sub`
- **THEN** es redirigido a configurar o verificar el segundo factor

#### Scenario: Public page under a prefix
- **WHEN** ese mismo usuario abre una página pública del sitio servido bajo `/sub`
- **THEN** la página responde sin pedir el segundo factor
