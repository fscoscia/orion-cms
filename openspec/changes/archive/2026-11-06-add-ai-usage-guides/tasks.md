# Tasks

## 1. Plantilla del proyecto

- [x] 1.1 Crear `src/orion/project_template/AGENTS.md` con el resumen de reglas del proyecto y el marcador `__PROJECT_NAME__` (verificable: la prueba 1.4 lee el archivo generado).
- [x] 1.2 Crear `src/orion/project_template/CLAUDE.md` mínimo que remite a `AGENTS.md`.
- [x] 1.3 En `src/orion/bin.py`, reemplazar `__PROJECT_NAME__` por el nombre del proyecto en esos dos archivos (verificable: `pipenv run test tests/test_project_template.py`).
- [x] 1.4 Pruebas en `tests/test_project_template.py`: ambos archivos existen; el nombre del proyecto aparece y no queda ningún `__PROJECT_NAME__`; `CLAUDE.md` remite a `AGENTS.md`; el comando de pruebas es `manage test` y no aparece `pytest`; el `.gitignore` no los ignora.

## 2. Guía

- [x] 2.1 Escribir `docs/guias/trabajar-con-ia.md` con las secciones del spec `ai-assisted-development` (reparto de trabajo, criterio de bloques, skills por fase, choques, revisión manual, problemas típicos, actualización de Orion, cómo pedir, qué no delegar).
- [x] 2.2 Comprobar que los ejemplos del criterio de bloques son genéricos (verificable: `grep -in "bolt" docs/guias/trabajar-con-ia.md` no devuelve nada en el criterio).

## 3. Documentación del repositorio

- [x] 3.1 Enlazar la guía y mencionar `AGENTS.md`/`CLAUDE.md` en `README.md` (sección "Usar Orion en un proyecto" y lista de guías) y en `docs/especificacion.md` (fila "Documentación para desarrolladores y agentes").
- [x] 3.2 Registrar el cambio en `CHANGELOG.md`.

## 4. Verificación

- [x] 4.1 Correr `pipenv run test` en PostgreSQL y en MySQL (`pipenv run test-postgres` y `pipenv run test-mysql`) y documentar los resultados.
- [x] 4.2 `pipenv run lint` y `pipenv run format` sin cambios pendientes.
- [x] 4.3 Generar un proyecto con `orion-start` en una carpeta temporal y leer su `AGENTS.md` y `CLAUDE.md` (verificable: `cat` de ambos archivos).
- [x] 4.4 `openspec validate add-ai-usage-guides --strict` sin avisos.
