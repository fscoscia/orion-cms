## 1. Bloques del proyecto

- [x] 1.1 Agregar `ORION_PROJECT_BLOCKS`, `SiteStreamBlock` y `BodyStreamField`, usarlos en
  `BodyPage`, y probar en `tests/test_content_blocks.py` que el bloque se ofrece y que
  `deconstruct` no lo incluye.
- [x] 1.2 Documentar el ajuste en el README, en `docs/guias/crear-un-bloque.md` y en el
  CHANGELOG, y verificar que la guía indica no importar modelos de Orion en los bloques.

## 2. Integración

- [x] 2.1 Declarar bloques en Intervita y correr `makemigrations --check`: sin cambios en las
  apps de Orion. Registrar aquí el resultado. "No changes detected" con
  `quick_links` y `unit_tabs` declarados, y el selector del admin los ofrece.
- [x] 2.2 Correr lint, `makemigrations --check` en Orion, y las pruebas en PostgreSQL, MySQL y
  de punta a punta. Registrar aquí los resultados. PostgreSQL: 785 passed, 5 deselected.
  MySQL: 784 passed, 1 skipped, 5 deselected. Punta a punta: 5 passed en cada base. Lint y
  migraciones limpios.

## Workflow follow-up

- Archivar el cambio cuando esté aprobado.
