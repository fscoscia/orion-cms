# Design

## Context

`orion-start` envuelve `startproject` de Django con la plantilla `src/orion/project_template/`
y después reemplaza marcadores en dos archivos (`__ORION_VERSION__` en el `Pipfile` y
`__ORION_STATIC_SRC__` en `static_src/project.css`). La plantilla ya trae `home/`,
`templates/`, `static_src/`, `.env.example`, `.gitignore` y un `Pipfile` sin dependencias de
desarrollo (por eso un proyecto generado no tiene `pytest`). Las guías por tarea viven en
`docs/guias/` del repositorio de Orion, que no se instala con el paquete.

El contenido a documentar sale de validar Orion con tres versiones de un sitio real
(Bolt Emprende: con Figma y con bloques propios, sin Figma y solo con bloques de Orion, y
una tercera con bloques propios guiada por impeccable). Los hallazgos están en la
conversación que originó este cambio; aquí se fijan como requisitos de documentación.

## Goals / Non-Goals

**Goals:**
- Que un proyecto recién generado diga al agente qué puede tocar y cómo decidir entre
  bloques de Orion y bloques propios, sin leer la guía completa.
- Una guía que explique el reparto de trabajo, las skills por fase y las fallas silenciosas
  conocidas.
- No introducir dependencias ni migraciones.

**Non-Goals:**
- Corregir en Orion lo que la validación reveló (ver "Fuera del alcance" del proposal).
- Instalar skills o fijar sus versiones en los proyectos.
- Mantener sincronizadas las skills de terceros: la guía describe lo probado y su fecha.

## Decisions

### 1. El nombre del proyecto se inserta con el patrón de marcadores que ya existe
`bin.py` reemplaza `__PROJECT_NAME__` en `AGENTS.md` y `CLAUDE.md` después de `startproject`,
igual que hace con `__ORION_VERSION__` en el `Pipfile`.

*Alternativa descartada:* pasar `--extension=md` a `startproject` para que Django renderice
los `.md`. Django 5.2 solo reescribe el sufijo `.py-tpl`, por lo que habría que nombrar los
archivos con otra convención, y además renderizaría `templates/README.md` y todo `{% ... %}`
y `{{ ... }}` del propio `AGENTS.md` (que documenta etiquetas de templates y las
interpretaría como código). Un reemplazo de texto es más simple y no tiene ese riesgo.

### 2. `AGENTS.md` es un resumen autosuficiente; la guía es el detalle
El archivo del proyecto repite lo esencial (qué se toca, el criterio de bloques, CSS, contenido
existente, actualización, verificación) porque es lo único que el agente carga siempre. La
guía `trabajar-con-ia.md` amplía con las skills, los choques entre ellas y los problemas
típicos. Se acepta una duplicación pequeña y deliberada del criterio de bloques; se evita
duplicar las listas largas.

### 3. Las guías por tarea se referencian por nombre; no se copian al proyecto
`docs/guias/` no viaja con el paquete (se instala desde Git). El `AGENTS.md` las nombra y
dice que están en `docs/guias/` del repositorio de Orion. No se copian porque quedarían
desactualizadas en cada proyecto, y empaquetar documentación en el paquete es otro cambio.
Es una limitación conocida (ver Riesgos).

### 4. Comando de pruebas: `manage test`
Un proyecto generado no instala `pytest` (su `Pipfile` no tiene dependencias de desarrollo y
agregarlo exigiría justificar una dependencia). El `AGENTS.md` indica `pipenv run manage test`.
Orion sigue usando `pytest` para su propio repositorio.

### 5. Idioma y tono
Los archivos para el proyecto y la guía van en español, como el resto de `docs/` y el
README. Los fragmentos de código y los identificadores quedan como son. El `AGENTS.md`
usa un tono imperativo y breve; la guía explica el porqué.

### 6. Las skills de terceros se describen por lo probado
La guía separa lo que se probó con Orion de lo que no, indica las versiones observadas
(impeccable 4.8.0 con su motor 0.1.18, taste `design-taste-frontend`, las skills de Emil) y
la fecha, y advierte que el instalador de impeccable descarga un binario y envía telemetría:
verificar el hash contra el que publica el paquete y apagarla (`DO_NOT_TRACK=1`,
`IMPECCABLE_NO_TELEMETRY=1`) antes de usarla.

## Risks / Trade-offs

- **Skills que cambian:** lo que la guía dice de impeccable, taste y Emil puede quedar viejo.
  Mitigación: fecha y versión visibles, y la sección "probado / no probado".
- **Guías no incluidas en el paquete:** un agente en un proyecto sin acceso al repositorio de
  Orion no puede leerlas. Mitigación: el `AGENTS.md` lleva lo esencial; empaquetar las guías
  queda como seguimiento posible.
- **Marcador sin reemplazar:** si `bin.py` no encuentra el archivo, quedaría `__PROJECT_NAME__`
  en el proyecto. Mitigación: la prueba de `orion-start` verifica que no quede ningún marcador.
- **Criterio de bloques demasiado laxo o estricto:** la validación mostró que prohibir los
  bloques propios produce diseños planos y que permitirlos sin justificar produce deuda. La
  línea de justificación por bloque es el contrapeso; el criterio se revisará con proyectos
  reales (Fase 7).

## Migraciones e impacto en contenido existente

Ninguno: solo documentación y dos archivos de plantilla. No hay migraciones, ni cambios en
bloques ni en StreamField, ni dependencias nuevas.
