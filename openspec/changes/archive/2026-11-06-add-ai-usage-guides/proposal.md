# Proposal

## Why

Quien construye un sitio sobre Orion lo hace cada vez más con un asistente de IA. Sin
instrucciones del proyecto, el agente tiende a dos extremos: usar solo los bloques de Orion
(y entregar diseños planos) o crear bloques propios sin criterio. La validación con tres
versiones del sitio de Bolt Emprende (con y sin Figma, con y sin bloques propios) mostró
además fallas silenciosas que una guía evita: una clave de bloque propia que tapa a una de
Orion, contenido descartado al quitar un bloque, componentes de Alpine con el mismo nombre,
CSS que pierde contra las utilidades de Tailwind, imágenes recortadas por la rendición
`card` y una portada propia que Orion no reconoce. Hoy nada de esto está escrito, y
`orion-start` no entrega ninguna instrucción para agentes.

## What Changes

- `orion-start` entrega en la raíz del proyecto un `AGENTS.md` con el nombre del proyecto
  insertado y un `CLAUDE.md` mínimo que apunta a ese archivo.
- Nueva guía `docs/guias/trabajar-con-ia.md`: reparto de trabajo entre Orion y el proyecto,
  criterio de bloques de Orion o propios, uso de las skills por fase, choques entre skills,
  qué revisar siempre a mano y problemas típicos de los bloques propios.
- El `AGENTS.md` del proyecto resume las reglas que el agente debe seguir sin leer la guía
  completa: qué se toca y qué no, el criterio de bloques, CSS y diseño, contenido existente,
  actualización de Orion y verificación al terminar una tarea.
- El README enlaza la guía y menciona los dos archivos que entrega `orion-start`; el
  CHANGELOG lo registra.
- No hay migraciones ni dependencias nuevas.

**Fuera del alcance:**
- Cambios en los bloques o en el CSS de Orion que surgieron de la validación (separador de
  miles en estadísticas, elegir cuál bloque es la portada, margen superior del pie, fondo
  de la `<section>` interna): cada uno merece su propio cambio.
- Instalar, vendorizar o fijar skills de terceros en los proyectos; la guía solo las
  describe.
- Un servidor MCP o una API para agentes (sigue a futuro, ver `docs/especificacion.md`).
- Modificar el `AGENTS.md` y el `CLAUDE.md` del repositorio de Orion, que guían el trabajo
  sobre el paquete.
- Pruebas de rendimiento o de integración continua para los proyectos de cliente.

## Capabilities

### New Capabilities
- `ai-assisted-development`: documentación para construir un sitio sobre Orion con un
  asistente de IA (la guía `trabajar-con-ia.md` y su contenido obligatorio).

### Modified Capabilities
- `project-template`: el proyecto generado incluye `AGENTS.md` y `CLAUDE.md`.

## Impact

- `src/orion/project_template/`: dos archivos nuevos con marcadores de posición.
- `src/orion/bin.py`: reemplaza el nombre del proyecto en esos archivos, igual que ya hace
  con la versión de Orion en el `Pipfile`.
- `docs/guias/trabajar-con-ia.md`, `README.md`, `CHANGELOG.md` y `docs/especificacion.md`.
- `tests/test_project_template.py`: pruebas de los archivos entregados.
- Riesgo: la guía nombra skills y comandos de terceros (impeccable, taste, Emil) que cambian
  por su cuenta; queda como descripción de lo probado, con la fecha y la versión.
