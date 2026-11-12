# Proposal

## Why

Los equipos construyen sitios sobre Orion con un asistente de IA, que hoy solo puede leer
archivos y pedirle a una persona que mire el admin. Un servidor MCP le da al asistente
herramientas para consultar el sitio real (qué tipos de página y bloques existen, qué páginas
hay, qué 404 se registraron) en lugar de adivinarlo. Es el primer paso de un camino que
termina en un MCP usable en producción; empezar por lectura y en local no toca datos ni
expone una puerta nueva al sitio, y deja probadas las herramientas antes de abrirlas.

## What Changes

- Comando `manage.py orion_mcp`: servidor MCP por stdio, solo lectura, para el desarrollador
  que lo lanza. Habla JSON-RPC 2.0 escrito a mano (`initialize`, `tools/list`, `tools/call`,
  `ping`), sin dependencias nuevas.
- App nueva `orion.mcp`, con las herramientas definidas aparte del transporte para poder
  reutilizarlas en un endpoint HTTP futuro.
- Herramientas de lectura: resumen del sitio, esquema (tipos de página y bloques con sus
  campos), árbol de páginas, una página, ajustes del sitio, redirecciones, 404 registrados,
  formularios (sin envíos), chequeo de convenciones, imágenes sin uso y salud.
- No expone envíos de formularios ni datos de usuarios, y ninguna herramienta escribe.
- Documentación: guía `docs/guias/usar-el-mcp.md`, mención en el `AGENTS.md` de la
  plantilla, ejemplo de configuración para Claude Code y `CHANGELOG`.
- El `design.md` deja escrita la hoja de ruta de cuatro cambios hacia producción.
- Fuera de alcance: escritura de cualquier tipo, endpoint HTTP, claves de API, y entregar un
  `.mcp.json` dentro de la plantilla del proyecto.

## Capabilities

### New Capabilities
- `mcp-server`: servidor MCP local de solo lectura, sus herramientas y sus garantías.

### Modified Capabilities

## Impact

- Código: paquete nuevo `src/orion/mcp/` (protocolo, registro de herramientas, comando),
  `orion.mcp` en `INSTALLED_APPS` de los ajustes base (lo reciben todos los proyectos).
- Dos extracciones pequeñas sin cambio de comportamiento: la lógica de `orion_unused_images`
  y el chequeo de base de `/health/`, para que las herramientas las reutilicen.
- Documentación: `docs/guias/usar-el-mcp.md` (nueva), `AGENTS.md` de la plantilla, README,
  `CHANGELOG.md`.
- Sin migraciones, sin dependencias nuevas.
- Riesgos: instrucciones ajenas dentro del contenido leído, datos personales si se carga una
  copia de producción en local y cambios del protocolo; ver `design.md`.
