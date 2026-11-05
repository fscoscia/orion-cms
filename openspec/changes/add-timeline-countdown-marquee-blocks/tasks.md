# Tasks

## 1. Bloque Pasos

- [x] 1.1 Crear `StepBlock` y `StepsBlock` (antetítulo, título, 2 a 12 pasos con título, texto e imagen opcional), registrarlo en `ContentStreamBlock` con ayuda y vista previa, y verificarlo con tests de validación (un solo paso, texto largo).
- [x] 1.2 Crear `orion/blocks/steps.html` con `<ol>`, numeración automática y títulos de nivel correcto, y verificar con tests el HTML, la numeración tras reordenar y los niveles de encabezado.

## 2. Bloque Cuenta regresiva

- [x] 2.1 Crear `CountdownBlock` (antetítulo, título, fecha y hora límite, mensaje de cierre, botón opcional), registrarlo con ayuda y vista previa, y verificarlo con tests de validación.
- [x] 2.2 Crear `orion/blocks/countdown.html` con la fecha legible, el instante en `data-*` y `role="timer"`, y verificar con tests el HTML y que no anuncia segundos (`aria-live`).
- [x] 2.3 Agregar el componente Alpine `countdown` a `orion.js` y verificar en e2e: cuenta que avanza, fecha pasada con y sin mensaje, sin JavaScript, y que no hay errores de CSP.

## 3. Bloque Cinta

- [x] 3.1 Crear `MarqueeBlock` (frases, logos, velocidad), reutilizando `LogoBlock`, registrarlo con ayuda y vista previa, y verificarlo con tests de validación y de vista previa sin logos.
- [x] 3.2 Crear `orion/blocks/marquee.html` quieto por defecto, con el grupo duplicado oculto a lectores de pantalla, y verificar con tests el HTML.
- [x] 3.3 Agregar el componente Alpine `marquee` a `orion.js` (activa el movimiento, botón de pausa, pausa por foco y puntero) y verificar en e2e: desliza, pausa y reanuda, movimiento reducido emulado (quieta y sin botón), sin JavaScript, y sin errores de CSP.

## 4. Estilos

- [x] 4.1 Sumar los estilos base de los tres bloques a `core/static_src/orion.css`, compilar con `pipenv run css-build` y comprobar en el navegador escritorio y móvil, y con `ORION_BLOCK_STYLES`.

## 5. Migración, textos y documentación

- [x] 5.1 Generar la migración de `orion.pages` y la del proyecto de ejemplo, revisar que solo cambie la definición y verificar con un test que una página existente conserva su cuerpo.
- [x] 5.2 Traducir los textos nuevos al español y verificar con `compilemessages` y una prueba del admin en español; comprobar con una prueba que wagtail-localize ofrece los textos de los tres bloques.
- [x] 5.3 Actualizar README ("veinte bloques"), `docs/guias/crear-un-bloque.md`, CHANGELOG y `docs/especificacion.md`, y comprobar que no queda "diecisiete bloques".

## 6. Verificación integral

- [x] 6.1 Ejecutar `pipenv run lint`, `makemigrations --check`, la suite y e2e en PostgreSQL y MySQL, y documentar los resultados.
- [ ] 6.2 Comprobar en Intervita que `makemigrations` genera solo una migración de definición y que los tres bloques se cargan y publican desde el admin.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
