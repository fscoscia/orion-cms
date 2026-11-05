# Tasks

## 1. Ajuste y atributo

- [x] 1.1 Agregar `ORION_BLOCK_REVEAL = False` a `settings/base.py` y verificar con un test que no cambia el HTML de ningún bloque con el ajuste apagado.
- [x] 1.2 Agregar `data-reveal` a la envoltura en `ContentStreamBlock.render_basic` con el ajuste encendido, excepto el primer bloque visible y la vista previa del editor, y verificar con tests de HTML: con el ajuste encendido, con un primer bloque oculto y en la vista previa.

## 2. Estilos y script

- [x] 2.1 Agregar los estilos de aparición a `core/static_src/orion.css` dentro de `@media (scripting: enabled) and (prefers-reduced-motion: no-preference)`, con `@media print` visible, y compilar con `pipenv run css-build`.
- [x] 2.2 Agregar el observador a `orion.js` con el respaldo de pocos segundos y la revelación total sin `IntersectionObserver`, y verificar en e2e: aparece al bajar, el primer bloque no se oculta, movimiento reducido emulado, sin JavaScript y con un observador que nunca responde.
- [x] 2.3 Medir en e2e que el CLS no sube y que no hay errores de CSP.

## 3. Documentación

- [x] 3.1 Documentar `ORION_BLOCK_REVEAL` en el README y en `docs/guias/crear-un-bloque.md`, y actualizar el CHANGELOG.

## 4. Verificación integral

- [x] 4.1 Ejecutar `pipenv run lint`, la suite y e2e en PostgreSQL y MySQL, y documentar los resultados.
- [x] 4.2 Comprobar en Intervita con el ajuste apagado que las páginas no cambian, y con el ajuste encendido que ningún bloque queda oculto.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
