# Proposal

## Why

Al seguir `docs/guias/empezar.md` y el README de punta a punta (8 y 9 de noviembre de 2026)
aparecieron fallas que las guías no anticipan: el comando de instalación del README no
funciona con pipenv, `orion-start` solo corre desde la carpeta donde se instaló Orion, la
plantilla pide una etiqueta de versión que todavía no existe, `createdb` no se explica, un
proyecto creado antes de que existiera `AGENTS.md` no sabe cómo recibirlo y las guías no
viajan con el paquete. Además, las guías no cubren dos situaciones reales: el sitio con
contenido pero sin diseño, y la identidad y el SEO del sitio (favicon, imagen social,
`robots.txt`, Search Console), que Orion ya resuelve desde el admin pero nadie documenta.

## What Changes

- Nueva guía `docs/guias/identidad-y-seo.md`: qué se carga desde el admin (Datos del sitio,
  pestañas Identidad y SEO; descripción del sitio por idioma; pestaña Promocionar de cada
  página), qué prepara o redacta la IA (favicon cuadrado, imagen social de 1200 × 630,
  títulos y descripciones SEO) y cómo comprobar el resultado en el navegador.
- `empezar.md` y README: instalación con `pipenv --python 3.12 install git+<url>` (sin
  `#egg`, sin comillas ni extras), `orion-start` desde la carpeta temporal `orion-tools`,
  versión fijada por etiqueta o, mientras no exista ninguna, por el hash de un commit; qué
  hace `createdb` y su equivalente en MySQL; cómo dar `AGENTS.md` y `CLAUDE.md` a un
  proyecto creado antes; y que las guías no viajan con el paquete.
- `estilos-y-diseno.md`: camino para cuando hay contenido pero no diseño.
- `trabajar-con-ia.md`: fase de estructura previa a la dirección visual, y la experiencia de
  un proyecto real donde taste se usó solo para la dirección de arte.
- `trabajar-con-ia.md`: cómo se resuelven los formularios (desde el admin, sin código; el
  asistente propone campos y textos, una persona los carga y se comprueba un envío real).
- Fuera de alcance: la presentación (no está en el repositorio), cualquier código de Orion y
  la publicación de la primera etiqueta de versión.

## Capabilities

### New Capabilities

### Modified Capabilities
- `ai-assisted-development`: se agrega la guía de identidad y SEO y se ajustan los
  requisitos de instalación, de estilos y diseño, de skills por fase y de enlaces entre guías.

## Impact

- Documentación: `docs/guias/identidad-y-seo.md` (nueva), `docs/guias/empezar.md`,
  `docs/guias/estilos-y-diseno.md`, `docs/guias/trabajar-con-ia.md` y `README.md`.
- Sin cambios de código, migraciones ni dependencias.
- Riesgo: los comandos de instalación se comprobaron a mano contra GitHub; los de skills no
  probados siguen marcados como tales.
