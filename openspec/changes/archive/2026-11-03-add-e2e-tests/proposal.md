## Why

La suite actual (`pytest` + `pytest-django`) cubre modelos, vistas y comandos, pero no
ejerce un navegador real: no hay pruebas que carguen una página publicada y verifiquen
que Alpine.js se inicializa bajo la CSP estricta, que un formulario se puede completar y
enviar como lo haría una persona, o que un editor puede iniciar sesión en el admin de
Wagtail, crear una página y publicarla de punta a punta. `docs/especificacion.md` (Fase
6, punto 2) pide justamente eso: pruebas de punta a punta con Playwright para el admin y
el sitio, corriendo en PostgreSQL y en MySQL, antes de construir el primer sitio real
(Fase 7, Intervita) sobre esas pruebas.

## What Changes

- Nueva dependencia de desarrollo: `pytest-playwright` (y el navegador Chromium que
  instala, vía `playwright install chromium`), justificada en design.md.
- Una suite de pruebas de punta a punta, separada de la suite funcional existente, que
  levanta el sitio de ejemplo con un servidor real (`live_server` de `pytest-django`) y
  lo recorre con un navegador Chromium headless.
- Casos del admin: iniciar sesión, crear una página hija y publicarla, ver el error de
  credenciales inválidas.
- Casos del sitio público: una página publicada carga con su CSS y JS (CSP con nonce
  respetada, Alpine.js inicializado), la navegación entre páginas funciona, un formulario
  del bloque Formulario se completa y envía con el navegador.
- Correr la suite nueva en PostgreSQL y en MySQL, igual que la suite existente
  (`pipenv run test-postgres` / `pipenv run test-mysql`).
- README: cómo instalar el navegador de Playwright y correr la suite de punta a punta.

## Capabilities

### New Capabilities
- `e2e-tests`: pruebas de punta a punta con un navegador real para los flujos
  principales del admin de Wagtail y del sitio público, corriendo en PostgreSQL y en
  MySQL.

### Modified Capabilities
(ninguna: no cambia el comportamiento de ninguna capacidad existente, solo se agregan
pruebas)

## Impact

- `pyproject.toml` / `Pipfile`: nueva dependencia de desarrollo (`pytest-playwright`) y
  su navegador descargado aparte (no es un paquete de Python, no se declara como
  dependencia pip).
- Nuevo directorio de pruebas (p. ej. `tests/e2e/`), separado de `tests/` para no
  correr los navegadores en cada ejecución rápida de la suite funcional.
- `pytest.ini_options` / configuración de pytest: un marcador o directorio aparte para
  poder excluir las pruebas de punta a punta de una corrida rápida.
- README y CHANGELOG.
- Fuera de alcance: integración continua (a futuro, según
  `docs/especificacion.md`), pruebas visuales o de accesibilidad automatizadas,
  navegadores además de Chromium, y el presupuesto de Lighthouse (ya resuelto como
  deferred en `add-deploy-guides`).
