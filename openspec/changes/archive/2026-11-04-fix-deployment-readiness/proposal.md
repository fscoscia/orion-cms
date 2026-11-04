## Why

La verificación posterior a la Fase 6 instaló el paquete real en un entorno limpio y
encontró cinco problemas que las pruebas no detectan, porque todas corren bajo `pipenv`,
en la raíz del dominio y sin mirar los logs. Dos impiden operar un sitio real: siguiendo
las guías de deploy el sitio no arranca, y los errores 500 no quedan registrados en
ningún lado. Hay que resolverlos antes de desplegar Intervita (Fase 7).

## What Changes

- Los proyectos generados leen su `.env` sin depender de `pipenv`, tanto en `manage.py`
  como en Gunicorn y Passenger. Una variable ya definida en el entorno real tiene
  prioridad sobre el archivo.
- Fuera de debug, los errores del servidor y los avisos de la aplicación se escriben en la
  salida de errores del proceso. Los 404 no se registran ahí: ya los cuenta el monitor
  del admin.
- El `.gitignore` de la plantilla ignora solo las carpetas de la raíz del proyecto
  (`/static/`, `/media/`), para no perder los estáticos de las apps propias, y agrega
  `/private/`, donde están los adjuntos de formularios.
- El CSS compilado del proyecto se versiona, igual que el de Orion, y la plantilla trae uno
  inicial. Sin ese archivo, fuera de debug todas las páginas públicas responden 500.
- La exigencia del 2FA, la CSP y las exclusiones de la caché de página reconocen el admin
  aunque el sitio corra bajo una subruta (`SCRIPT_NAME`). Hoy el admin queda sin 2FA en
  ese caso.
- La exportación CSV de envíos neutraliza los valores que una planilla interpretaría como
  fórmula. La exportación a Excel ya los guarda como texto (Wagtail) y no cambia.
- Las guías de deploy (VPS y cPanel) y el checklist de alta se corrigen para que funcionen
  de punta a punta, incluyendo la dependencia `django-tailwind-cli` que agregó
  `add-project-tailwind-build`.

**Fuera del alcance:**

- Declarar soporte completo para subrutas: este cambio solo evita que las protecciones
  fallen abiertas. Quedan como están las redirecciones de idioma a `/` de
  `orion.localization`.
- Los demás hallazgos de la verificación (`brotli`, permisos del backup mientras se
  escribe, carpeta y límite de la caché en archivos, CHANGELOG atrasado, specs con
  requisitos largos).
- Escribir en el repositorio de Intervita: se documenta qué debe cambiar ahí.
- Volver portable la ruta del `@import` de `project.css`, que apunta al paquete instalado en
  la máquina donde se generó el proyecto, y dejar `django-tailwind-cli` solo para
  desarrollo. Compilar en otra máquina sigue requiriendo corregir esa ruta.
- Configurar un servicio externo de monitoreo de errores.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `project-configuration`: el `.env` se lee sin `pipenv` y los errores se registran fuera
  de debug.
- `project-template`: el proyecto generado carga su `.env`, su `.gitignore` protege lo que
  corresponde y su CSS compilado se versiona.
- `two-factor-auth`: el segundo factor se exige también bajo una subruta.
- `site-security`: la CSP y la caché de página reconocen el admin bajo una subruta.
- `form-inbox`: el CSV exportado no ejecuta fórmulas escritas por visitantes.

## Impact

- **Código:** `orion.settings` (`env.py`, `base.py`), plantilla de proyecto
  (`settings.py-tpl`, `.gitignore`), `orion.core.csp`, `orion.core.cache.middleware`,
  `orion.seo.middleware`, `orion.editor.middleware` y `orion.forms.submissions`.
- **Dependencias:** una nueva, `python-dotenv` (justificada en `design.md`).
- **Migraciones:** ninguna. No afecta contenido ni datos existentes.
- **Proyectos existentes:** Intervita debe agregar la carga del `.env` a sus ajustes y
  corregir su `.gitignore` a mano; queda explicado en el CHANGELOG.
- **Orden:** se aplica después de archivar `add-project-tailwind-build`, que está completo
  y toca los mismos archivos de la plantilla.
- **Documentación:** README (deploy, registro de errores), `docs/alta-de-cliente.md` y
  CHANGELOG.
