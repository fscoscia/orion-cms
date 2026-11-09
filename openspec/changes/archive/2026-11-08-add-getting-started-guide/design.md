# Design

## Context

Observado al preparar el cambio:

- `orion-start` es un comando del paquete (`src/orion/bin.py`); no existe hasta instalar
  Orion, y el `Pipfile` del proyecto generado trae la dependencia de Orion con
  `git = "https://github.com/<organization>/orion.git"` y `ref = "v__ORION_VERSION__"`.
- El remoto del repositorio es `git@github.com:fscoscia/orion-cms.git`, no `…/orion.git`.
- `git tag` está vacío y la versión es `0.1.0.dev0`: la etiqueta que fija el `Pipfile`
  generado no existe.
- Una consulta anónima por HTTPS (`git ls-remote https://github.com/fscoscia/orion-cms.git`)
  respondió "Repository not found". Se pidió que el repositorio fuera público; hay que
  confirmar su visibilidad y su nombre antes de escribir la URL en nada (tarea 1.1).
- `orion_install` ya migra, crea el administrador y carga los formularios de ejemplo; el
  README lo documenta, pero no forma parte de ningún recorrido.
- `docs/guias/` no viaja con el paquete (se instala desde Git), así que el `AGENTS.md` solo
  puede apuntar a las guías por URL.

Ver `proposal.md` para el motivo.

## Goals / Non-Goals

**Goals:**
- Un único documento lineal que lleve de una máquina preparada a un sitio funcionando con el
  asistente ya cargado con las reglas.
- Que cada comando de la guía se haya ejecutado al escribirla, o quede marcado como no
  comprobado.
- Que la guía de estilos explique solo lo que Orion y la plantilla ya hacen.

**Non-Goals:**
- Resolver la publicación de versiones (etiquetas, `__version__`, PyPI).
- Documentar despliegue, copias de seguridad ni operación (viven en `README.md` y
  `docs/alta-de-cliente.md`).

## Decisions

### 1. Un solo documento de arranque, lineal; las demás guías quedan como consulta
`empezar.md` se lee de corrido (30 a 40 minutos) y termina enlazando las guías por tarea.
Cada paso tiene un comando y una comprobación visible.

*Alternativa descartada:* sumar los pasos al README. El README ya es largo y habla a quien
mantiene Orion; separar al lector evita mezclar comandos de ambos públicos.

### 2. `orion-start` se obtiene en un entorno virtual descartable
Para correr `orion-start` antes de tener proyecto, la guía crea un entorno virtual temporal
con `python3.12 -m venv`, instala Orion desde Git con `pip` y corre `orion-start`. El
proyecto generado usa después su propio `pipenv install`. Solo se usa lo que ya exigen los
requisitos (Python y pip).

*Alternativas descartadas:* `pipx` o `uvx`, que agregan una herramienta más para instalar y
que no están entre los requisitos del proyecto. Si al comprobarlo el comando de `venv` no
funciona, se documenta el que sí.

### 3. La URL del repositorio se escribe literal y se confirma antes
El `Pipfile` generado reemplaza `<organization>/orion.git` por la URL real. Un agente que
encuentra un marcador tiende a inventar el valor; escribir la URL elimina un paso manual y
una fuente de errores. La misma URL se usa en el README y en el `AGENTS.md`.

*Alternativas descartadas:* dejar el marcador (mantiene el problema) y leer la URL de una
constante o de los metadatos del paquete (sobreingeniería para un valor que cambia raras
veces).

Esta decisión queda **condicionada** a la tarea 1.1: si el nombre o la visibilidad del
repositorio no son los esperados, se ajusta antes de escribir nada.

### 4. La etiqueta publicada es requisito previo, no parte de este cambio
Con la plantilla actual el `Pipfile` fija `v<versión instalada>`. La guía instala Orion con
una etiqueta publicada y explica que debe coincidir con la que fija el `Pipfile`. Publicar
la primera etiqueta es una decisión del propietario del repositorio (fuera del alcance); la
comprobación completa por Git queda para cuando exista. Mientras tanto, el recorrido se
comprueba instalando Orion desde la copia local (`pip install <ruta>`), y la guía lo declara.

### 5. `orion_install` reemplaza los pasos sueltos de migrar y crear el administrador
La guía usa `manage orion_install` (verifica la base, migra, crea el administrador, informa
el idioma y carga los formularios de ejemplo) porque es el camino que Orion documenta y es
idempotente.

### 6. El primer pedido al asistente comprueba el `AGENTS.md`
El pedido listo para copiar pregunta qué archivos no puede editar y cómo decide entre un
bloque de Orion y uno propio; la respuesta correcta depende del `AGENTS.md`. Si falla, se le
indica el archivo. Se redacta sin asumir un asistente concreto: `AGENTS.md` es la convención
común y `CLAUDE.md` remite a él.

### 7. La guía de estilos se limita a lo que ya existe
Se documenta lo que la plantilla y Orion ya entregan: `static_src/project.css` y
`pipenv run css-build` / `css-watch`, CSS fuera de `@layer`, `ORION_BLOCK_STYLES` y el
atributo `data-block-style`, `ORION_IMAGE_SIZES` con `orion_generate_renditions`, y la
sobrescritura de templates por nombre. Los nombres se verifican contra el código y el
README antes de escribirlos.

### 8. Instalar una skill va en `trabajar-con-ia.md`, no en la guía de arranque
La guía de arranque no obliga a usar skills. La instalación en el proyecto (con los
cuidados ya descritos: verificar el binario, apagar la telemetría, no instalarla en Orion)
se suma a la sección de skills de la guía de IA.

## Risks / Trade-offs

- [La URL aparece en tres lugares (`Pipfile`, `AGENTS.md`, README)] → una prueba comprueba
  que el `Pipfile` generado no conserva marcadores; el CHANGELOG registra el cambio y, si el
  repositorio se mueve, se actualizan juntos.
- [El repositorio no es público o no tiene etiqueta] → la guía no funciona de punta a punta;
  se declara en la propia guía y en el resultado de este cambio como no comprobado.
- [Los comandos de herramientas de terceros cambian] → la guía declara la versión de Orion y
  la fecha de comprobación y evita fijar versiones de terceros.
- [`docs/guias/` fuera del paquete] → el `AGENTS.md` enlaza por URL; si no hay red el
  asistente no las lee. Se acepta: empaquetarlas es otro cambio.
- No hay migraciones ni dependencias nuevas; el contenido existente no se toca.

## Open Questions

- Fecha de la primera etiqueta de versión: no cambia las especificaciones ni las tareas, solo
  cuándo se puede comprobar la instalación por Git.
