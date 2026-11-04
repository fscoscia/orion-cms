## ADDED Requirements

### Requirement: The admin is recognised under a URL prefix
Cuando el sitio se sirve bajo un prefijo de URL, el sistema SHALL tratar el admin, los
estáticos y los medios igual que en la raíz del dominio: fuera de la política de seguridad
de contenido y de la caché de página.

#### Scenario: Admin page under a prefix
- **WHEN** se abre el admin de un sitio servido bajo `/sub`
- **THEN** la respuesta no lleva la política de seguridad de contenido del sitio público

#### Scenario: Admin request without a session under a prefix
- **WHEN** con la caché de página encendida, una visita sin sesión pide el login del admin
  de un sitio servido bajo `/sub`
- **THEN** la respuesta no se guarda en la caché de página

#### Scenario: Public page under a prefix
- **WHEN** se abre una página pública de un sitio servido bajo `/sub`
- **THEN** la respuesta lleva la política de seguridad de contenido
