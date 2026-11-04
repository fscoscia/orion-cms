# Orion

CMS base reutilizable sobre Wagtail 7.4 LTS y Django 5.2 LTS (Python 3.12). Es un paquete
(`src/orion/`) que cada proyecto de cliente instala; no contiene contenido ni diseño de
ningún cliente. `example/` es un proyecto local para desarrollar y probar; nunca se despliega.

## Comandos

```bash
pipenv install --dev            # entorno
pipenv run test                 # pruebas (base de DATABASE_URL)
pipenv run test-postgres        # pruebas en PostgreSQL
pipenv run test-mysql           # pruebas en MySQL
pipenv run lint                 # ruff check
pipenv run format               # ruff format
pipenv run manage <comando>     # manage.py del proyecto de ejemplo
```

## Alcance y plan

- `docs/especificacion.md`: especificación funcional completa (qué entra en la v1, qué
  queda a futuro, integraciones, decisiones tomadas) y el plan de fases. Leerla antes de
  proponer una fase o una funcionalidad nueva.
- Estado: Fases 0 (esqueleto), 1 (contenido y multi-idioma), 2 (experiencia del editor),
  3 (medios, rendimiento y SEO), 4 (formularios, buscador, scripts e integraciones), 5
  (seguridad y operación) y 6 (calidad y documentación) hechas; la siguiente es la Fase 7
  (validación: construir el sitio de Intervita).
- Prototipos de referencia en `../orion-prototipos/`, fuera del repositorio. La opción 1
  (`opcion1-wagtail`) tiene bloques, hooks del admin y templates para reescribir dentro de
  Orion; no se copia tal cual.
- `docs/guias/`: guías paso a paso por tarea para construir un sitio sobre Orion
  (crear un bloque, un tipo de página, un formulario). Consultarlas antes de estas
  tareas en el sitio de Intervita (Fase 7) o en cualquier otro proyecto.

## Flujo de trabajo

Todo cambio pasa por OpenSpec (`openspec/`): proponer (`/opsx:propose`), implementar
(`/opsx:apply`) y archivar (`/opsx:archive`) cuando esté aprobado. El contexto del proyecto,
las decisiones tomadas y las convenciones están en `openspec/config.yaml`; los
comportamientos vigentes, en `openspec/specs/`.

## Reglas

1. Inspeccionar el proyecto y sus versiones antes de modificar código.
2. Priorizar lo nativo de Django y Wagtail; la solución más simple y mantenible.
3. No agregar dependencias sin justificarlas en el `design.md` del cambio.
4. No eliminar datos ni generar migraciones destructivas sin autorización.
5. Conservar la compatibilidad de StreamField y del contenido existente.
6. Validaciones, permisos y seguridad en todo cambio; nunca exponer secretos.
7. Pruebas proporcionales al cambio y ejecutadas en PostgreSQL y MySQL.
8. Nunca afirmar pruebas no ejecutadas.
9. Ante ambigüedad importante, consultar antes de implementar.
10. Sin sobreingeniería ni refactorizaciones no pedidas.

## Convenciones

Ruff (línea de 88, comillas dobles). Python en snake_case, clases en PascalCase, constantes
en UPPER_SNAKE_CASE, booleanos con `is_`/`has_`/`can_`. Sufijos de Wagtail: `Page`,
`IndexPage`, `Block`, `Form`, `Service`, `Mixin`. Templates `snake_case.html`; CSS e IDs en
kebab-case; URLs en kebab-case; variables de entorno en UPPER_SNAKE_CASE. Código y
comentarios en inglés; textos visibles con gettext y traducción al español. La lista
completa está en `openspec/config.yaml`.

## Checklist por tarea

- [ ] Respeta la arquitectura y las convenciones.
- [ ] Usa componentes nativos de Django/Wagtail cuando corresponde.
- [ ] Se administra correctamente desde Wagtail.
- [ ] No afecta contenido editorial existente.
- [ ] Permisos, validaciones y seguridad revisados.
- [ ] Migraciones revisadas y seguras.
- [ ] Pruebas ejecutadas y resultados documentados.
- [ ] Sin dependencias ni cambios innecesarios.
- [ ] Archivos modificados y riesgos pendientes documentados.
