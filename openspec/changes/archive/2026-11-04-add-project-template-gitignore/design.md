## Context

Ver `proposal.md` ("Why") para la motivación. `orion-start` (en `src/orion/bin.py`) es
una envoltura de `django-admin startproject --template=<project_template>`; Django
copia todo archivo de la plantilla salvo que esté dentro de un directorio oculto o
`__pycache__`, o tenga extensión `.pyo`/`.pyc`/`.py.class`
(`django/core/management/templates.py`, método `handle_template`). No filtra archivos
por nombre, así que un archivo llamado `.gitignore` en la raíz de la plantilla se copia
igual que ya se copia `.env.example` hoy.

## Goals / Non-Goals

**Goals:**
- Que todo proyecto nuevo generado por `orion-start` incluya un `.gitignore` que
  excluya al menos `.env` y los demás artefactos de desarrollo que no deben
  commitearse.

**Non-Goals:**
- No se revisa si `src/orion/project_template/.env.example` o cualquier otro archivo de
  la plantilla necesita cambios; solo se agrega el `.gitignore` faltante.
- No se agrega un `.gitignore` al propio repositorio de Orion: ya tiene uno.

## Decisions

**Contenido del `.gitignore` generado:** el mismo criterio que el `.gitignore` de este
repositorio, recortado a lo que un proyecto de cliente necesita (sin las entradas
propias de un paquete Python como `*.egg-info/`, `build/`, `dist/`, `.ruff_cache/`, ni
las específicas de `example/`):

```gitignore
# Python
__pycache__/
*.py[cod]
.pytest_cache/

# Environment and secrets
.env
.venv/

# Runtime files
media/
static/
*.sqlite3

# Editors and OS
.idea/
.vscode/
.DS_Store
```

Es, de hecho, el mismo archivo que se creó a mano para Intervita durante
`validate-intervita-site` (ver su `design.md`, hallazgo 2); este cambio lo deja en la
plantilla para que no haga falta repetirlo a mano en el próximo proyecto.

**Dónde va en la plantilla:** `src/orion/project_template/.gitignore`, junto a
`.env.example` y `Pipfile` (la raíz de la plantilla, no dentro de `project_name/` ni de
`home/`), para que quede en la raíz de cada proyecto generado.

## Risks / Trade-offs

- [Riesgo] Un proyecto que ya corrió `orion-start` antes de este cambio no recibe el
  `.gitignore` retroactivamente. → Mitigación: ningún cambio de Orion puede tocar
  proyectos de cliente ya generados; queda como un paso manual (como se hizo para
  Intervita) o se resuelve la próxima vez que ese proyecto actualice su copia de la
  plantilla, si alguna vez la vuelve a generar.
