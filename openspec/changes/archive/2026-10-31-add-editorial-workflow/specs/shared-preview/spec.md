# Spec Delta

## Purpose

Define los enlaces temporales que permiten a alguien sin cuenta en el admin ver el
borrador de una página: quién los crea, qué muestran, cuánto duran y cómo se revocan.

## ADDED Requirements

### Requirement: Editors create temporary preview links
Quien puede editar una página SHALL poder crear, desde la página en el admin, un enlace de
vista previa que vence en 1, 7 o 30 días (7 por defecto), copiarlo y ver los enlaces
vigentes de esa página con su autor y su vencimiento. Quien no puede editar la página
MUST NOT crear ni ver sus enlaces.

#### Scenario: Creating a link
- **WHEN** un editor crea un enlace de 7 días para "Nosotros"
- **THEN** ve el enlace listo para copiar y su fecha de vencimiento

#### Scenario: Without permission
- **WHEN** un usuario que no puede editar "Nosotros" intenta crear un enlace para ella
- **THEN** el admin lo rechaza y no se crea ningún enlace

### Requirement: A link shows the latest draft without an account
Al abrir un enlace vigente, cualquier persona, sin iniciar sesión, SHALL ver la página
tal como está en su borrador más reciente en ese momento, con el diseño del sitio. La
respuesta MUST NOT indexarse ni guardarse en caché compartida, y los enlaces de la página
mostrada MUST NOT navegar fuera de la vista previa.

#### Scenario: Viewing a draft
- **WHEN** una clienta sin cuenta abre el enlace de "Nosotros"
- **THEN** ve el borrador, aunque lo publicado sea distinto

#### Scenario: Later edits
- **WHEN** el editor guarda otro cambio y la clienta recarga el enlace
- **THEN** ve el cambio nuevo

#### Scenario: Not indexed
- **WHEN** un buscador pide el enlace
- **THEN** la respuesta indica que no se indexe y no se guarde en caché

### Requirement: Links expire and can be revoked
Un enlace vencido, revocado, inexistente o de una página borrada SHALL responder 404, sin
revelar si existió. Quien puede editar la página SHALL poder revocar cualquiera de sus
enlaces antes del vencimiento. Los enlaces MUST ser imposibles de adivinar.

#### Scenario: Expired
- **WHEN** alguien abre un enlace cuyo vencimiento pasó
- **THEN** recibe 404

#### Scenario: Revoked
- **WHEN** el editor revoca el enlace y la clienta lo recarga
- **THEN** recibe 404

#### Scenario: Guessing
- **WHEN** alguien prueba un enlace con otro código
- **THEN** recibe 404
