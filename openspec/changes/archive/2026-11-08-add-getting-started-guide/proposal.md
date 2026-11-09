# Proposal

## Why

Quien construye un sitio sobre Orion con un asistente de IA hoy no tiene un camino de
arranque. El README está escrito para quien desarrolla el paquete (pruebas, MySQL y
PostgreSQL locales, OpenSpec), no para quien lo instala en un proyecto de cliente. Además:

- `orion-start` viene dentro del paquete, pero nada explica cómo obtenerlo antes de tener un
  proyecto.
- El `Pipfile` generado y el README apuntan a `<organization>/orion.git` y
  `<organizacion>/orion.git`, que no coinciden con el repositorio real
  (`fscoscia/orion-cms`), y fijan una etiqueta (`v0.1.0.dev0`) que no está publicada.
- El comando que deja el sitio funcionando (`orion_install`) no figura en ningún recorrido.
- El `AGENTS.md` ya remite a guías por tarea, pero ninguna cubre estilos y diseño, y no hay
  forma de comprobar que el asistente cargó las reglas.

## What Changes

- Nueva guía `docs/guias/empezar.md`, para leer de corrido: preparar la máquina (con una
  comprobación por herramienta), instalar `orion-start` fuera de un proyecto, crear el
  proyecto, `.env` y base de datos, `orion_install`, levantar el sitio y entrar al admin,
  abrir el proyecto con el asistente con un primer pedido que comprueba que cargó el
  `AGENTS.md`, y una primera tarea guiada.
- Nueva guía `docs/guias/estilos-y-diseno.md`: dónde vive el CSS del proyecto, cómo se
  compila, qué va fuera de `@layer`, estilos de bloque, tamaños de imagen y cómo sobrescribir
  templates de Orion.
- `docs/guias/trabajar-con-ia.md` enlaza ambas e incorpora cómo instalar una skill en el
  proyecto.
- La plantilla del proyecto: el `Pipfile` apunta al repositorio real (sin el marcador
  `<organization>`) y el `AGENTS.md` enlaza `empezar.md` y las guías por tarea.
- El README corrige las dos URLs de instalación y enlaza las guías; el CHANGELOG y
  `docs/especificacion.md` lo registran.
- No hay migraciones ni dependencias nuevas.

**Fuera del alcance:**
- Publicar la primera etiqueta de versión o cambiar la versión del paquete: es una decisión
  de publicación del propietario del repositorio.
- Hacer público el repositorio, si no lo estuviera.
- Una guía propia para actualizar Orion: sigue en la sección 7 de `trabajar-con-ia.md` y en
  el `AGENTS.md`.
- Una guía de despliegue o de servidor; el alta de un cliente sigue en
  `docs/alta-de-cliente.md`.
- Empaquetar `docs/guias/` dentro del paquete, o cualquier cambio en los bloques, el CSS o
  el código de Orion.
- Videos, cursos o material fuera del repositorio.

## Capabilities

### New Capabilities
<!-- Ninguna: la documentación para desarrolladores con IA ya tiene su capacidad. -->

### Modified Capabilities
- `ai-assisted-development`: se agregan la guía de arranque y la guía de estilos y diseño,
  con su contenido obligatorio y los enlaces desde las demás guías.
- `project-template`: el `Pipfile` generado apunta al repositorio de Orion sin marcadores
  y el `AGENTS.md` generado enlaza la guía de arranque y las guías por tarea.

## Impact

- `docs/guias/empezar.md` y `docs/guias/estilos-y-diseno.md` (nuevos);
  `docs/guias/trabajar-con-ia.md`, `README.md`, `CHANGELOG.md` y `docs/especificacion.md`.
- `src/orion/project_template/Pipfile` y `src/orion/project_template/AGENTS.md`;
  `tests/test_project_template.py`.
- Riesgos: la URL del repositorio queda escrita en tres lugares (`Pipfile`, `AGENTS.md`,
  README); el repositorio debe ser público y tener una etiqueta publicada para que el
  recorrido funcione de punta a punta (ver `design.md`).
