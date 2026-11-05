## ADDED Requirements

### Requirement: Blocks can appear as they enter the screen
Un proyecto SHALL poder activar con el ajuste `ORION_BLOCK_REVEAL`, apagado por defecto, que
los bloques aparezcan con un fundido y un desplazamiento corto al entrar en pantalla. Con el
ajuste apagado, las páginas MUST NOT cambiar. El primer bloque visible de la página MUST
mostrarse siempre desde el primer momento.

#### Scenario: Setting off
- **WHEN** el proyecto no activa el ajuste
- **THEN** ningún bloque lleva el atributo de aparición ni cambia su aspecto

#### Scenario: Setting on
- **WHEN** el proyecto activa el ajuste y un visitante baja por la página
- **THEN** cada bloque, salvo el primero, aparece al entrar en pantalla

#### Scenario: Leading block
- **WHEN** el proyecto activa el ajuste y el primer bloque es un Hero
- **THEN** el Hero se muestra completo desde que carga la página, sin fundido

### Requirement: Revealing never hides content from the visitor
Un bloque con aparición al entrar en pantalla SHALL mostrarse completo y sin animación sin
JavaScript, con movimiento reducido, en la vista previa del editor y al imprimir. Si el
observador de intersección no está disponible o no responde, el contenido SHALL mostrarse a
los pocos segundos. La aparición MUST animar solo `transform` y `opacity`.

#### Scenario: Reduced motion
- **WHEN** el sistema del visitante pide movimiento reducido
- **THEN** todos los bloques se muestran completos desde el principio

#### Scenario: Without JavaScript
- **WHEN** la página se abre sin JavaScript
- **THEN** todos los bloques se muestran completos

#### Scenario: Editor preview
- **WHEN** un editor abre la vista previa de una página
- **THEN** todos los bloques se muestran completos, sin animación

#### Scenario: Observer does not respond
- **WHEN** el navegador no entrega las intersecciones, por ejemplo con la pestaña en segundo plano
- **THEN** pasados unos segundos todos los bloques se muestran

#### Scenario: Printing
- **WHEN** el visitante imprime la página
- **THEN** todos los bloques se imprimen visibles
