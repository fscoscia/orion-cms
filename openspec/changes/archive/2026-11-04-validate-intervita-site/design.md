## Context

Ver `proposal.md` ("Why") para la motivación. Puntos de partida relevantes:

- `orion-start` (entry point de consola, generado desde `src/orion/project_template/`)
  crea un proyecto nuevo conectado a Orion; `orion_install` (comando de gestión en
  `src/orion/core/management/commands/orion_install.py`) migra, crea el administrador,
  confirma el idioma base y carga el contenido de ejemplo. Ambos están construidos y
  archivados (Fase 5), pero nunca se ejecutaron contra un proyecto fuera de este repo.
- Orion no tiene remoto en GitHub ni tags todavía: `pip install git+https://...@vX` (la
  forma que documenta el README) no es posible hoy. Se decidió con el usuario instalar
  con un path local para esta validación; publicar y taguear queda para cuando el sitio
  esté listo para desplegarse, y requiere su autorización antes de hacer `push` o crear
  el tag.
- `example/` ya prueba Orion, pero vive dentro de este repositorio y nunca se despliega
  (CLAUDE.md); no sirve como validación de una instalación externa real.

## Goals / Non-Goals

**Goals:**
- Confirmar que un proyecto externo, en su propio repositorio, puede instalar Orion,
  correr `orion-start` + `orion_install` y quedar funcionando (admin, vista previa,
  caché, búsqueda, controles de seguridad) sin pasos no documentados.
- Confirmar que `docs/alta-de-cliente.md` y las guías de `docs/guias/` alcanzan para
  seguir construyendo sobre ese proyecto.
- Dejar una lista concreta de fricciones o fallos encontrados en Orion, con suficiente
  detalle para abrir un cambio de OpenSpec propio por cada uno que lo justifique.

**Non-Goals:**
- No se construyen las páginas, bloques ni contenido reales de Intervita en este cambio
  (ver "Fuera del alcance" en `proposal.md`).
- No se publica Orion en GitHub ni se crea ningún tag en este cambio.
- No se corrige ningún hallazgo dentro de este mismo cambio: cada fix es un cambio de
  OpenSpec aparte, con su propio diseño y pruebas.

## Decisions

**Ubicación del proyecto:** `/Users/fscoscia/Proyectos/intervita`, hermano de `orion/` y
de `../orion-prototipos/`, con su propio repositorio git. Mismo nivel que el repo de
Orion, nunca dentro de él, para no mezclar contenido de cliente con el paquete base
(regla explícita de `CLAUDE.md`).

**Cómo instala Orion:** con un path local editable:
```
pipenv install -e /Users/fscoscia/Proyectos/orion
```
en lugar de la forma `git+https://...@vX` del README. Alternativa descartada: publicar y
taguear Orion ahora — se descartó porque hacer `push` a un remoto y crear un tag son
acciones visibles y difíciles de revertir que el usuario pidió posponer hasta que el
sitio esté más avanzado.

**Base de datos:** PostgreSQL local (Docker Compose que ya trae Orion, u otra instancia
local), igual que la base principal de producción, para que la validación cubra el mismo
motor que se usará al desplegar. MySQL no se valida en Intervita: ya lo cubre la suite de
Orion (`pipenv run test-mysql`).

**Qué se verifica, no solo que arranque:** además de que el sitio levante, se recorren a
mano los puntos de `docs/alta-de-cliente.md` (como ensayo, sin cuentas reales) y se
prueban: admin en español, vista previa en vivo, 2FA, límite de intentos de login, caché
de página completa, buscador, formularios de ejemplo y `manage.py check --deploy`. Es la
única forma de encontrar fricciones que un simple "el servidor arrancó" no revela.

**Cómo se registran los hallazgos:** una lista en este `design.md` (sección que se
completa durante la ejecución de las tareas), no un documento nuevo. Cada hallazgo que
implique cambiar código o comportamiento de Orion se propone después como su propio
cambio de OpenSpec (siguiendo el patrón ya usado por `fix-skeleton-qa-findings` y
`fix-block-previews-and-slugs`), con su propia spec delta y pruebas; este cambio no se
reabre para incluirlos.

## Risks / Trade-offs

- [Riesgo] Validar con un path local en vez de `git+https://...@vX` no prueba el flujo de
  instalación real que usará cada cliente (clonar, fijar driver con el extra `[postgres]`
  o `[mysql]`, resolver la etiqueta). → Mitigación: queda explícitamente anotado como
  pendiente en los hallazgos; se valida ese flujo específico en un cambio posterior,
  cuando Orion se publique en GitHub.
- [Riesgo] El proyecto Intervita, al vivir fuera de este repositorio, no tiene ningún
  cambio de OpenSpec que lo gobierne ni pruebas automatizadas compartidas con Orion. →
  Mitigación: no es necesario para esta validación puntual; si Intervita crece a un
  proyecto real con su propio flujo de trabajo, define sus propias convenciones en su
  repositorio.
- [Riesgo] Encontrar muchos hallazgos puede tentar a corregirlos todos dentro de este
  mismo cambio, mezclando validación con implementación. → Mitigación: los `Non-Goals` ya
  lo excluyen; `tasks.md` solo pide documentar, no corregir.

## Hallazgos de la validación

### 1. `ORION_SEARCH_CONFIG=` vacío en `.env` rompe `orion_install` (bug, amerita un cambio)

**Qué se esperaba:** según `.env.example` y el README, dejar `ORION_SEARCH_CONFIG` vacío
hace que Orion use la configuración de texto de PostgreSQL del idioma base (`spanish`
para `es`).

**Qué pasó:** `orion_install` falló al crear los formularios de ejemplo con
`psycopg.errors.InvalidName: invalid name syntax` sobre
`to_tsvector(''::regconfig, ...)`. La causa es `env_str()` en
`src/orion/settings/env.py:15-17`: usa `os.environ.get(name, default)`, que solo aplica
`default` cuando la variable **no existe** en el entorno. Pero `pipenv` carga
`ORION_SEARCH_CONFIG=` (presente y vacía) en `os.environ` como `""`, así que
`ORION_SEARCH_CONFIG` en `settings/base.py:436-439` queda en `""` en vez de caer al mapa
`POSTGRES_SEARCH_CONFIGS`. Afecta a cualquier `.env` que mantenga la línea vacía como
documenta `.env.example` — es decir, el uso normal y documentado, no un error del
usuario.

**Alcance:** de las variables que usan `env_str` con un default no vacío
(`LANGUAGE_CODE`, `TIME_ZONE`, `DEFAULT_FROM_EMAIL`, `WAGTAIL_SITE_NAME`,
`WAGTAILADMIN_BASE_URL`, `ORION_ADMIN_PATH`, `ORION_SEARCH_CONFIG`), solo
`ORION_SEARCH_CONFIG` se distribuye vacía en `.env.example`; las demás ya traen un valor
no vacío por defecto, así que no se manifiesta en la práctica — pero cualquier variable
nueva que siga el mismo patrón ("vacío usa X") heredaría el mismo bug.

**Agravante:** ni `docs/alta-de-cliente.md` ni las guías de deploy del README
(VPS y cPanel) mencionan `ORION_SEARCH_CONFIG`, y ambas corren `orion_install` como paso
de rutina. Un cliente real que siga esos documentos al pie de la letra se topa con este
mismo fallo al instalar.

**Workaround aplicado en Intervita (no en Orion):** `ORION_SEARCH_CONFIG=spanish`
explícito en su `.env`.

**Amerita un cambio de OpenSpec propio:** sí — corregir `env_str` (o el sitio que la
llama para `ORION_SEARCH_CONFIG`) para que "presente y vacía" caiga al default igual que
"ausente", con una prueba que cubra `orion_install` sobre un `.env` que mantenga la
línea vacía como la distribuye `.env.example`.

### 2. `project-template` no genera un `.gitignore` (gap, amerita un cambio)

**Qué se esperaba:** `orion-start` deja un proyecto listo para su primer commit, como
dice el README.

**Qué pasó:** el proyecto generado no incluye ningún `.gitignore`. Sin uno, el primer
`git add` de cualquier proyecto nuevo arriesga commitear `.env` (secretos), `media/`,
`static/` o `*.sqlite3`. Se creó uno a mano para Intervita, basado en el `.gitignore` de
este mismo repositorio.

**Amerita un cambio de OpenSpec propio:** sí, pequeño — agregar un `.gitignore` a
`src/orion/project_template/` (`.env`, `.venv/`, `__pycache__/`, `media/`, `static/`,
`*.sqlite3`, editores y OS), con una prueba en el requisito de `project-template` que
confirme que el proyecto generado lo incluye.

### 3. Comportamiento de UI con JavaScript no verificado con un navegador real (límite de esta sesión, no es un bug)

**Qué se esperaba (tareas 3.1 y 4.3):** confirmar visualmente que la vista previa en
vivo está abierta por defecto, y que un bloque nuevo aparece en el selector del editor
con su ícono, descripción y vista previa.

**Qué pasó:** esta sesión no tiene una herramienta de navegador real (solo acceso a
shell, HTTP y al ORM de Django). Se verificó todo lo que no depende de JavaScript en el
navegador: el admin responde en español con la marca de Intervita, exige 2FA, permite
crear y publicar páginas y bloques propios, y estos se sirven correctamente en el sitio
público. Lo que sí es JS-dependiente (panel de vista previa abierto por defecto, StreamField
como editor interactivo, selector de bloques) no se confirmó visualmente.

**Amerita un cambio de OpenSpec propio:** no. No es un hallazgo sobre Orion: es una
verificación pendiente para quien continúe el sitio de Intervita con un navegador a
mano, o para una futura validación con herramientas de navegador disponibles.
