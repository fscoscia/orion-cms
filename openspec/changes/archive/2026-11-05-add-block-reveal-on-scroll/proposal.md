## Why

Los dos Home de Bolt Emprende hacen aparecer las secciones al bajar (un fundido con un
desplazamiento corto), y el proyecto lo escribió por su cuenta. Esa primera versión tenía un
defecto real, que las verificaciones de taste detectaron: si el observador de intersección no
responde (por ejemplo, con la pestaña en segundo plano), decenas de elementos quedaban
invisibles con `opacity: 0` y el contenido no se podía leer. Es el tipo de comportamiento que
conviene resolver una vez, bien, en Orion, y no en cada proyecto.

## What Changes

- Un ajuste opcional del proyecto, `ORION_BLOCK_REVEAL`, **apagado por defecto**, hace que
  los bloques aparezcan con un fundido y un desplazamiento corto al entrar en pantalla.
- El primer bloque visible de la página nunca se oculta, para no retrasar el LCP.
- Seguridad frente a fallos: sin JavaScript, con movimiento reducido, en la vista previa del
  editor y al imprimir el contenido se muestra completo y sin animación; si el observador no
  responde, todo se muestra a los pocos segundos.
- Solo `transform` y `opacity`; sin dependencias nuevas.
- Un sitio que no activa el ajuste no cambia nada.

### Fuera del alcance

- Escalonado entre elementos, parallax, contadores ligados al desplazamiento y cualquier otro
  efecto de scroll: siguen siendo del proyecto.
- Una opción por bloque o por estilo en el admin.
- Animar el contenido interno de cada bloque (tarjetas, pasos) por separado.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `block-presentation`: los bloques pueden aparecer al entrar en pantalla, con las
  salvaguardas de accesibilidad y de fallo.

## Impact

- **Código:** `ContentStreamBlock.render_basic` (atributo `data-reveal` en la envoltura),
  `orion.js` (observador con respaldo), `orion.css` y su compilado, `settings/base.py`
  (`ORION_BLOCK_REVEAL`), README y CHANGELOG.
- **Migraciones:** ninguna.
- **Pruebas:** HTML con el ajuste apagado y encendido, el primer bloque, la vista previa; e2e
  en PostgreSQL y MySQL con movimiento reducido emulado, sin JavaScript y con un observador
  que no responde.
- **Riesgo:** bajo; apagado por defecto, y el contenido siempre termina visible.
