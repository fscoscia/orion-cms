## Why

Al construir una página de prueba sobre Intervita durante la Fase 7 (validación,
`validate-intervita-site`), el texto se vio sin ningún estilo. La causa: Orion versiona
y sirve su propio CSS compilado (`/static/orion/css/orion.css`), pero ese archivo solo
contiene las clases de los templates **de Orion** (bloques, header, footer). El README
dice "las clases de Tailwind que use un template propio las compila el proyecto con su
propio CSS" (sección "Bloques de contenido"), pero `project-template` nunca dejó armado
ningún mecanismo para hacerlo: el `Pipfile` generado no incluye `django-tailwind-cli`,
los ajustes generados no lo configuran, y no hay comando ni guía para correrlo. Todo
proyecto de cliente queda así, desde el día uno, sin forma de estilizar sus propios
tipos de página y bloques.

De paso, se encontró que `docs/guias/crear-un-tipo-de-pagina.md` usa en su ejemplo la
clase `orion-lead`, que no existe en ningún lado de `orion.css` ni es una utilidad de
Tailwind — un detalle menor encontrado en el camino, parte del mismo problema (estilos
de proyecto que no están resueltos).

## What Changes

- `project-template` agrega al proyecto generado:
  - `django-tailwind-cli` en el `Pipfile` (misma versión que usa Orion internamente).
  - Un archivo fuente de Tailwind propio del proyecto (`<project_name>/static_src/<project_name>.css`)
    que importa el `@theme` y los componentes de Orion (`orion.css`, vía el paquete
    instalado) y declara `@source` sobre los templates propios del proyecto (`home/`,
    `templates/`), para que sus propias clases (de Tailwind o de bloques propios) se
    compilen sin tocar el CSS que Orion ya trae.
  - Los ajustes de `django_tailwind_cli` (`INSTALLED_APPS`, `TAILWIND_CLI_VERSION`,
    `TAILWIND_CLI_SRC_CSS`, `TAILWIND_CLI_DIST_CSS`, `TAILWIND_CLI_PATH`) apuntando a
    ese archivo propio, con una salida separada del CSS de Orion (nunca sobrescribe
    `orion/css/orion.css`).
  - Scripts de `Pipfile` (`css-build`, `css-watch`) iguales en nombre a los que ya usa
    este mismo repositorio para compilar el CSS de Orion, pero corriendo sobre el CSS
    del proyecto.
  - El `.gitignore` de la plantilla (agregado en `add-project-template-gitignore`) ya
    cubre el binario descargado de Tailwind si se guarda en una carpeta como `.tailwind/`;
    se confirma que el nombre usado coincide.
- Un override de `orion/base.html` en los templates generados (`templates/orion/base.html`)
  que agrega el `<link>` del CSS propio del proyecto vía `{% block extra_css %}`, como ya
  documenta el README para hojas de estilo propias.
- `docs/guias/crear-un-tipo-de-pagina.md`: quitar `orion-lead` del ejemplo (no es una
  clase real) y dejar el párrafo de bajada sin clase, o con una nota de que el
  proyecto define su propio estilo.

**Fuera del alcance:** inventar o agregar una clase `.orion-lead` (u otro componente
visual nuevo) a `orion.css` — es una decisión de diseño visual, no de infraestructura;
automatizar la compilación en CI o en el deploy (las guías de deploy del README ya
mencionan `collectstatic`; sumar el paso de `tailwind build` ahí queda para cuando se
revisen esas guías, si hace falta); cualquier otro hallazgo de `validate-intervita-site`
ya resuelto en los cambios anteriores.

## Capabilities

### Modified Capabilities
- `project-template`: el proyecto generado por `orion-start` ahora incluye su propio
  mecanismo de compilación de Tailwind (dependencia, ajustes y fuente CSS propia),
  separado del CSS que Orion ya trae compilado.

## Impact

- **Código:** `src/orion/project_template/` (Pipfile, settings.py-tpl, un archivo CSS
  fuente nuevo, un override de `orion/base.html`); `docs/guias/crear-un-tipo-de-pagina.md`
  (un ejemplo corregido).
- **Dependencias nuevas:** `django-tailwind-cli`, pero solo en el `Pipfile` **generado**
  para cada proyecto cliente — no se agrega a las dependencias de Orion. Orion ya la usa
  como dependencia de desarrollo para compilar su propio CSS (`Pipfile` de este repo);
  se reutiliza la misma versión fijada ahí.
- **Migraciones:** ninguna.
- **Compatibilidad:** ningún proyecto existente se ve afectado — `orion-start` solo
  cambia para instalaciones nuevas a partir de esta versión de Orion.
