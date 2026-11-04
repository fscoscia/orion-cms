## Context

Ver `proposal.md` ("Why"). Piezas relevantes de cómo Orion compila su propio CSS hoy
(`src/orion/core/static_src/orion.css`, el `TAILWIND_CLI_*` de `example/example/settings.py`):

```css
/* orion.css, fuente que Orion versiona compilada */
@import "tailwindcss" source(none);
@plugin "@tailwindcss/typography";
@source "../templates";
@source "../../localization/templates";
/* …el resto de las apps de Orion… */
@theme static { /* --color-primary-*, --color-accent-*, --font-sans, --font-display… */ }
@layer base { /* reset */ }
@layer components { /* .orion-richtext, .orion-title, .orion-button… */ }
```

`source(none)` apaga la detección automática de Tailwind (no serviría: compilaría desde
dentro del paquete instalado, sin ver los templates del proyecto); los `@source`
explícitos apuntan, a mano, a cada app de Orion. `example/` reconfigura
`TAILWIND_CLI_DIST_CSS` para que la salida sobrescriba ese mismo archivo dentro del
paquete (`STATICFILES_DIRS` apunta directo a `src/orion/core/static`) — es el mecanismo
con el que Orion recompila su **propio** CSS, no algo para que un proyecto cliente lo
reutilice tal cual: un proyecto nunca debe escribir dentro del paquete instalado.

`orion/base.html` ya trae `{% block extra_css %}` (vacío) antes de `</head>`, y el
README ya lo usa para sumar una hoja de estilo propia (ejemplo `brand.css`, con
overrides de las variables del `@theme`) — pero ese ejemplo es CSS sin Tailwind, sin
build. No hay ningún ejemplo de cómo un proyecto compila **sus propias clases**.

## Goals / Non-Goals

**Goals:**
- Que el proyecto generado por `orion-start` pueda compilar las clases de Tailwind de
  sus propios templates y bloques, sin tocar ni sobrescribir el CSS que Orion ya trae.
- Reusar los tokens del tema (colores, fuentes) y las clases de componentes de Orion
  (`.orion-title`, `.orion-richtext`, etc.) en los templates propios del proyecto, para
  que una página de un tipo propio se vea consistente con el resto del sitio.
- Mismo mecanismo que ya usa Orion (`django-tailwind-cli`, sin Node): nada nuevo que
  aprender para quien ya construyó sobre Orion.

**Non-Goals:**
- No se agrega ninguna clase de diseño nueva a `orion.css` (ver "Fuera del alcance" en
  `proposal.md`); el único cambio ahí es el ejemplo de la guía que usaba una clase
  inexistente.
- No se automatiza la compilación en el deploy ni en CI.
- No se cambia cómo Orion compila su propio CSS (`pipenv run css-build` sigue igual).

## Decisions

**Un archivo fuente propio del proyecto que importa el de Orion, no una copia.** El
archivo generado en `static_src/project.css` (junto a `home/` y `templates/`, no dentro
del paquete de ajustes del proyecto, para no depender de la sustitución de
`{{ project_name }}` que Django aplica solo a ese directorio) hace:

```css
@import "tailwindcss" source(none);
@import "__ORION_STATIC_SRC__/orion.css";

@source "../home";
@source "../templates";
```

`__ORION_STATIC_SRC__` se resuelve a la ruta absoluta de
`orion.core.static_src` del paquete instalado, igual que `bin.py` ya resuelve
`__ORION_VERSION__` en el `Pipfile` generado (mismo mecanismo, un placeholder más).
Importar el archivo de Orion (no copiar su contenido) trae sus tokens de `@theme`, el
plugin de tipografía y sus clases de `@layer components`, disponibles para las clases
que usen los templates propios; los `@source` del proyecto solo agregan sus propios
directorios (`home/`, `templates/`), sin repetir los de Orion (ya los trae el import).
Alternativa descartada: que el proyecto reconfigure `TAILWIND_CLI_SRC_CSS` apuntando
directo al `orion.css` del paquete y agregue sus propios `@source` ahí — se descartó
porque implicaría escribir (o parchear en memoria) un archivo dentro del paquete
instalado, lo mismo que se evita para `example/`.

**Salida separada, cargada con `extra_css`.** Se agrega `STATICFILES_DIRS = [BASE_DIR /
"assets"]` a los ajustes generados (un directorio fuente nuevo; no puede ser `static/`,
que ya es `STATIC_ROOT`, el destino de `collectstatic` — Django no permite que coincidan)
y `TAILWIND_CLI_DIST_CSS = "project/css/project.css"`, resuelto dentro de ese directorio
— mismo patrón de namespacing que usa Orion con `orion/css/orion.css`, para que no
choque con ningún otro estático. El override generado de `templates/orion/base.html`
agrega:

```django
{% extends "orion/base.html" %}
{% load static %}
{% block extra_css %}<link rel="stylesheet" href="{% static 'project/css/project.css' %}">{% endblock %}
```

Así el HTML sirve los dos archivos: el de Orion (con sus propios bloques y templates ya
compilados) y el del proyecto (con lo propio), sin que compilar uno afecte al otro.

**`TAILWIND_CLI_PATH` y el binario descargado.** Mismo patrón que `example/`:
`TAILWIND_CLI_PATH = BASE_DIR / ".tailwind"`. El `.gitignore` de la plantilla
(`add-project-template-gitignore`) ya ignora `.venv/`; se agrega `.tailwind/` a esa
misma lista en este cambio, igual que lo ignora el `.gitignore` de este propio
repositorio.

**Versión de `django-tailwind-cli`.** La misma que fija el `Pipfile` de este repositorio
(`==4.8.1`), para no manejar dos versiones distintas del mismo binario de Tailwind
(4.3.3) entre Orion y sus proyectos.

## Risks / Trade-offs

- [Riesgo] El `@import` de un archivo dentro del paquete instalado (`site-packages` en
  una instalación real, o `src/orion` en una editable) podría no resolver si
  `django-tailwind-cli` ejecuta el binario de Tailwind desde un directorio de trabajo
  que no ve esa ruta. → Mitigación: se usa una ruta absoluta resuelta en Python al
  generar el proyecto (no relativa), igual que ya funciona para `example/`, que importa
  rutas fuera de su propio árbol sin problema.
- [Riesgo] Si alguna vez cambia la estructura interna de `orion.css` (por ejemplo, se
  mueve de carpeta), todo proyecto generado antes del cambio tiene una ruta de `@import`
  vieja. → Mitigación: la ruta se resuelve una vez, al generar el proyecto (como la
  versión del `Pipfile`); actualizarla es un paso manual de migración documentado si
  llega a hacer falta, igual que cualquier otro cambio de versión mayor de Orion.
- [Riesgo] Un proyecto que olvida correr `tailwind build` antes de su primer commit o
  deploy sirve un CSS propio vacío (sin romper nada: el archivo simplemente no tiene las
  clases propias todavía). → Mitigación: igual que con `collectstatic`, es un paso de
  build conocido; se documenta en el `README.md` del proyecto generado
  (`templates/README.md` de la plantilla) y, si hace falta, en las guías de deploy en
  un cambio futuro (fuera de alcance de este).

## Migration Plan

Cambio de la plantilla de un comando de scaffolding; no migra nada. No afecta ningún
proyecto ya generado (ver "Impact" en `proposal.md`). Sin rollback especial: revertir el
commit alcanza.
