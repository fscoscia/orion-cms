# e2e-tests Specification

## Purpose

Ejerce, con un navegador real, los flujos principales del admin de Wagtail y del sitio
público que las pruebas funcionales existentes no cubren (JavaScript, CSP, formularios
tal como los completa una persona), para dar confianza antes de construir el primer
sitio real sobre Orion.

## Requirements

### Requirement: An editor can log in, create a page and publish it end to end
Una suite de punta a punta SHALL abrir el admin de Wagtail con un navegador real, iniciar
sesión con credenciales válidas, crear una página hija bajo la página de inicio,
publicarla, y verificar que queda visible en el sitio público.

#### Scenario: Flujo completo de alta
- **WHEN** una persona editora inicia sesión en `/admin/`, crea una página y la publica
- **THEN** la página publicada se puede abrir desde el sitio público con su contenido

#### Scenario: Credenciales inválidas
- **WHEN** se intenta iniciar sesión en `/admin/` con una contraseña incorrecta
- **THEN** el admin muestra el error de credenciales sin iniciar sesión

### Requirement: A published page renders with its JavaScript and CSP intact
Una suite de punta a punta SHALL cargar una página publicada del sitio público en un
navegador real y verificar que su CSS y su JavaScript (Alpine.js, bajo la CSP estricta
con nonce) se aplican, y que la navegación a otra página publicada funciona.

#### Scenario: Alpine.js se inicializa bajo CSP
- **WHEN** se carga una página publicada que usa un componente de Alpine.js
- **THEN** el componente queda inicializado y funciona (sin que la CSP lo bloquee)

#### Scenario: Navegación entre páginas
- **WHEN** se hace clic en un enlace del menú hacia otra página publicada
- **THEN** el navegador llega a esa página

### Requirement: A form can be filled and submitted like a real visitor would
Una suite de punta a punta SHALL completar y enviar, con un navegador real, un
formulario armado con el bloque Formulario, y verificar que la persona visitante ve la
confirmación de envío.

#### Scenario: Envío exitoso
- **WHEN** se completan los campos requeridos de un formulario publicado y se envía
- **THEN** el navegador ve la página o el mensaje de agradecimiento configurado

### Requirement: The end-to-end suite runs on PostgreSQL and on MySQL
La suite de punta a punta SHALL poder correr contra cualquiera de las dos bases de datos
soportadas, de la misma forma que la suite funcional existente, aunque en una invocación
separada (no corre por defecto con la suite funcional, por su costo y su dependencia de
un navegador instalado).

#### Scenario: Corrida en cada motor
- **WHEN** se ejecuta `pipenv run test-e2e-postgres` o `pipenv run test-e2e-mysql`
- **THEN** la suite de punta a punta corre contra esa base de datos y reporta su
  resultado
