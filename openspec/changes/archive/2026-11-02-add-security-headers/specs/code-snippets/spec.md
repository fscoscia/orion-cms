## MODIFIED Requirements

### Requirement: Snippets are inserted where chosen
Un fragmento activo SHALL insertarse tal cual en la ubicación elegida: dentro de
`<head>`, al inicio de `<body>` o al final de `<body>`, en el orden en que se crearon. Un
fragmento desactivado MUST NOT insertarse y SHALL conservarse. Cada `<script>` y
`<style>` del fragmento SHALL recibir el nonce de la política de seguridad de la
respuesta, de modo que corra con la política estricta; los scripts que el fragmento carga
SHALL poder correr. Los atributos de evento (`onclick=`) y los enlaces `javascript:` del
fragmento MUST NOT ejecutarse.

#### Scenario: Analytics in the head
- **WHEN** un superusuario crea un fragmento "Google Analytics" en `<head>` y lo activa
- **THEN** todas las páginas públicas incluyen ese código dentro de `<head>`, con el nonce
  de la respuesta, y el script de Google que carga también corre

#### Scenario: Turned off
- **WHEN** lo desactiva
- **THEN** ninguna página lo incluye y el fragmento sigue en el admin

#### Scenario: Event attribute
- **WHEN** un fragmento trae `<button onclick="abrir()">`
- **THEN** el botón aparece pero el navegador no ejecuta ese atributo
