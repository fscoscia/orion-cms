## Why

La validación de la Fase 7 (cambio `validate-intervita-site`, ver su `design.md`,
hallazgo 2) encontró que `orion-start` deja un proyecto nuevo sin ningún `.gitignore`.
El primer `git add` de cualquier sitio de cliente arriesga commitear `.env` (con
`SECRET_KEY` y otros secretos), `media/`, `static/` o una base SQLite local — justo lo
que un `.gitignore` existe para evitar, y exactamente los archivos que
`src/orion/project_template/.env.example` advierte "nunca commitear".

## What Changes

- Agregar un `.gitignore` a `src/orion/project_template/` para que `orion-start` lo
  copie a todo proyecto nuevo, con al menos: `.env`, `.venv/`, `__pycache__/`,
  `*.py[cod]`, `media/`, `static/`, `*.sqlite3`, y entradas de editor/SO (`.idea/`,
  `.vscode/`, `.DS_Store`) — el mismo conjunto que ya protege a este propio repositorio
  (`.gitignore` en la raíz de Orion), adaptado a un proyecto de cliente (sin las
  entradas específicas de Orion como paquete: `*.egg-info/`, `build/`, `dist/`,
  `.ruff_cache/`, `example/...`).
- Agregar un requisito a la especificación de `project-template` que confirme que el
  proyecto generado incluye un `.gitignore`.

**Fuera del alcance:** cualquier otro hallazgo de `validate-intervita-site` (el bug de
`env_str`, ya corregido en `fix-env-str-empty-fallback`, es un cambio aparte); agregar
el `.gitignore` manualmente a `/Users/fscoscia/Proyectos/intervita` no es necesario —
ya lo tiene, creado a mano durante esa validación.

## Capabilities

### Modified Capabilities
- `project-template`: el proyecto generado por `orion-start` ahora incluye un
  `.gitignore` listo para su primer commit.

## Impact

- **Código:** `src/orion/project_template/.gitignore` (archivo nuevo); sin cambios en
  `src/orion/bin.py` (la copia la hace Django `startproject` igual que con cualquier
  otro archivo de la plantilla).
- **Dependencias nuevas:** ninguna.
- **Migraciones:** ninguna.
- **Compatibilidad:** ningún proyecto existente se ve afectado — `orion-start` solo
  cambia para instalaciones nuevas a partir de esta versión de Orion.
