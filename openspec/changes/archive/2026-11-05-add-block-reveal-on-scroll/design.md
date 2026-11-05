## Context

Ver `proposal.md` para el motivo. Lo que condiciona el enfoque, comprobado en el código:

- `ContentStreamBlock.render_basic` ya envuelve cada bloque visible en
  `<div class="block-{tipo}">` y conoce su posición (`is_leading_block` para el primero).
- `orion.js` carga con `defer` y registra los componentes Alpine; ya hay un observador de
  intersección en `counter` (Cifras) que respeta el movimiento reducido.
- La política de seguridad es estricta (CSP con nonce): sin estilos ni scripts en línea.
- Las páginas se sirven con caché de página completa: el atributo lo decide el ajuste del
  proyecto, no la petición, salvo la vista previa del editor, que no se cachea.
- En Bolt Emprende, esta misma animación dejó elementos con `opacity: 0` cuando el observador
  no respondía. Las verificaciones de taste lo marcaron como defecto real (`hidden-content`).

## Goals / Non-Goals

**Goals:**
- Una aparición al scroll que nunca deje contenido oculto y que no cueste LCP ni CLS.
- Cero cambios para quien no active el ajuste.

**Non-Goals:**
- Un sistema de animación general, escalonados o efectos ligados al scroll.

## Decisions

### El ocultamiento es CSS condicionado; JavaScript solo revela
Los estilos que ocultan (`opacity: 0` y un `translateY` corto) viven dentro de
`@media (scripting: enabled) and (prefers-reduced-motion: no-preference)` y solo para
`[data-reveal]:not(.is-revealed)`. Sin JavaScript, con movimiento reducido o en un navegador
sin `scripting` (se muestra todo, sin animación) el contenido nunca se oculta. Es la garantía
principal: no depende de que un script corra a tiempo. `@media print` lo muestra todo.
Alternativa descartada: ocultar con una clase que agrega JavaScript, porque deja contenido
invisible si el script falla.

### JavaScript: observador con respaldo temporal
`orion.js` observa los `[data-reveal]` y agrega `is-revealed` al entrar en pantalla. Si el
observador no entregó ninguna respuesta tras 3 segundos, se revela todo; si ya respondió, el
temporizador no hace nada, para no revelar de golpe bloques lejanos que el visitante aún no
vio. También se revela todo si `IntersectionObserver` no existe. La transición se limita a
`transform` y `opacity`.

### El atributo lo agrega `render_basic`, no el template de cada bloque
`render_basic` añade `data-reveal` a la envoltura de los bloques visibles cuando
`ORION_BLOCK_REVEAL` está encendido, excepto el primero (`position == 0`) y excepto en la
vista previa del editor. Un solo lugar cubre todos los bloques, incluidos los del proyecto.
Cómo detecta la vista previa en `render_basic` (contexto o `request.is_preview`) se confirma
al implementar, con una prueba.

### Ajuste global, no por bloque
Es un ajuste del proyecto porque la aparición es parte del estilo del sitio, no del contenido
de una página. El editor no lo ve ni lo configura.

## Risks / Trade-offs

- [Bloques por encima del pliegue que no son el primero se ocultan un instante] → El
  observador los revela en cuanto carga el script; el respaldo temporal cubre el peor caso.
- [El CLS puede subir si el bloque se desplaza al aparecer] → Solo `transform` y `opacity`,
  sin cambiar el espacio ocupado; se mide con las pruebas e2e.
- [Navegadores sin `@media (scripting)`] → Se muestra todo sin animación: se pierde el
  efecto, no el contenido.

## Migration Plan

Sin migraciones. Un proyecto que lo quiera pone `ORION_BLOCK_REVEAL = True` en sus ajustes.
