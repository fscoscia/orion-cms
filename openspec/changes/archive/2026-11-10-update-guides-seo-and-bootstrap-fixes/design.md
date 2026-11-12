# Design

## Context

Las guías de `docs/guias/` y el README son la única forma de aprender a usar Orion, y no
viajan con el paquete (ni con `orion-start`). El 9 de noviembre de 2026 se siguió el flujo
real contra GitHub y se observó: `pipenv run orion-start` falla con `command not found`
fuera de la carpeta donde se instaló; `pipenv install` falla con `v0.1.0.dev0` porque el
repositorio no tiene etiquetas; y un proyecto creado con una plantilla anterior conserva el
`Pipfile` con `<organization>` y no tiene `AGENTS.md`. Datos del sitio ya tiene las
pestañas Identidad y SEO (favicon, imagen social, `robots.txt`, código de Search Console) y
`openspec/specs/seo/spec.md` describe su comportamiento; falta una guía que lo explique.

## Goals / Non-Goals

**Goals:**
- Que quien siga las guías llegue al sitio funcionando sin tropezar con las fallas ya vistas.
- Documentar identidad y SEO con el reparto admin / asistente.

**Non-Goals:**
- Publicar la primera etiqueta o decidir la política de versiones (cambio aparte).
- Que `orion-start` copie las guías al proyecto (cambio de código aparte).
- Reescribir la presentación, que no está en el repositorio.

## Decisions

- **Guía propia `identidad-y-seo.md`** y no una sección de `empezar.md`: `empezar.md` se lee
  de corrido el primer día y ya tiene unas 160 líneas; la identidad y el SEO se cargan cuando
  hay logo, textos e imágenes. `empezar.md` la enlaza al final.
- **Los ajustes del sitio se cargan desde el admin, no se le piden al asistente.** Son datos
  únicos guardados en la base, requieren permisos de Administradora y el admin valida (por
  ejemplo, rechaza la etiqueta completa de Search Console). El asistente redacta, prepara
  archivos y revisa. Alternativa descartada: un script de carga; duplicaría la validación y
  escribiría en la base sin pasar por permisos.
- **Fijar la versión por etiqueta y, sin etiquetas, por hash de commit.** Una rama se mueve y
  rompe la reproducibilidad. `main` solo se menciona como lo que no conviene.
- **Instalación con `pipenv --python 3.12 install git+<url>`:** es la forma que se comprobó;
  `"paquete[extra] @ git+…"` falla en pipenv ("looks like a path"). `--python 3.12` evita que
  pipenv elija una versión mayor y falle al bloquear.
- **Sin diseño, la estructura va primero.** Permite revisar el orden de la información con el
  aspecto por defecto antes de fijar colores; la dirección visual mínima la aprueba una
  persona para no dejar la estética a una skill.
- **La carpeta temporal `orion-tools` se mantiene** (descrita y con la advertencia de
  ejecutar desde ella). Alternativa: `pipx`, sin carpeta temporal, que no se probó; queda como
  pregunta abierta.

## Risks / Trade-offs

- Los comandos pueden volverse obsoletos con una nueva versión de pipenv → la guía declara
  versión y fecha con las que se comprobó (requisito ya vigente).
- Los comandos de skills que no se probaron podrían citarse como verificados → se mantiene la
  separación «se probó / no se probó» y no se agregan comandos nuevos de skills.
- La guía de SEO depende de los nombres de pestañas del admin → verificarlos en el admin
  en español antes de escribirlos.

## Open Questions

- ¿`pipx` en lugar de la carpeta temporal? No cambia las especificaciones si se decide
  después, solo los comandos del paso de instalación.
