## Why

Al armar dos versiones del Home de Bolt Emprende sobre Orion, el proyecto tuvo que escribir
a mano tres bloques que cualquier landing necesita: una **línea de tiempo** de pasos
numerados, una **cuenta regresiva** hasta una fecha límite y una **cinta** de frases y logos
que se desliza. Cada uno costó una clase, un template, estilos y JavaScript propios, sin
pruebas ni traducciones, y habría que repetirlo en el sitio de cualquier otro cliente.

## What Changes

- Un bloque **Pasos** (línea de tiempo): título, antetítulo y entre 2 y 12 pasos numerados
  automáticamente, cada uno con título, texto e imagen opcional.
- Un bloque **Cuenta regresiva**: título, antetítulo, fecha y hora límite, botón opcional y
  un mensaje opcional que reemplaza al reloj cuando la fecha ya pasó.
- Un bloque **Cinta**: frases y logos que se deslizan en bucle, con velocidad elegible, botón
  de pausa y alternativa quieta sin JavaScript o con movimiento reducido.
- Los tres heredan de `BaseContentBlock` (estilo, ancla y visibilidad), con ayuda y vista
  previa en el admin, textos traducibles y estilos base sin compilar CSS.
- La biblioteca pasa de diecisiete a veinte bloques. Los artículos los reciben también.
- Sin dependencias nuevas. Es un cambio de definición de StreamField: genera una migración
  en `orion.pages` y los proyectos con tipos de página propios corren `makemigrations`.

### Fuera del alcance

- Efectos de scroll sobre estos bloques (línea que se llena al bajar, vehículo que recorre la
  línea, parallax): son decisión de diseño de cada proyecto, sobre el marcado que Orion ya
  entrega.
- Una cuenta regresiva que repita, o que consulte la hora del servidor.
- Reemplazar los bloques propios de Bolt Emprende: es un paso posterior en ese proyecto.

## Capabilities

### New Capabilities

Ninguna: los bloques pertenecen a la biblioteca existente.

### Modified Capabilities

- `content-blocks`: la biblioteca suma los bloques Pasos, Cuenta regresiva y Cinta, con sus
  validaciones, su comportamiento sin JavaScript y con movimiento reducido.

## Impact

- **Código:** `orion/core/blocks/content.py` y `__init__.py`; templates
  `orion/blocks/steps.html`, `countdown.html`, `marquee.html`; componentes Alpine `countdown`
  y `marquee` en `orion.js`; estilos en `core/static_src/orion.css` y el CSS compilado;
  traducciones al español.
- **Migraciones:** `orion.pages` (definición del cuerpo de página) y la del proyecto de
  ejemplo; ningún dato cambia.
- **Documentación:** README ("veinte bloques"), `docs/guias/crear-un-bloque.md`, CHANGELOG y
  `docs/especificacion.md`.
- **Riesgo:** bajo para el contenido existente; los proyectos con tipos de página propios
  necesitan una migración de definición.
