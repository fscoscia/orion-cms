## 1. Agregar el `.gitignore` a la plantilla

- [x] 1.1 Crear `src/orion/project_template/.gitignore` con el contenido de
  `design.md` ("Decisions"); verificar con `ls` que queda junto a `.env.example` y
  `Pipfile` en la raíz de la plantilla.

## 2. Pruebas

- [x] 2.1 En `tests/test_project_template.py::TestOrionStart`, extender
  `test_scaffolds_a_new_project` con
  `assert (destination / ".gitignore").is_file()`; verificar con
  `pipenv run test -k test_project_template`.
- [x] 2.2 Agregar un caso que confirme que el `.gitignore` generado excluye `.env`
  (por ejemplo, `assert ".env" in (destination / ".gitignore").read_text().splitlines()`);
  verificar con `pipenv run test -k test_project_template`. Los 6 casos de
  `test_project_template.py` pasan.
- [x] 2.3 Correr la suite completa en PostgreSQL (`pipenv run test-postgres`) y en
  MySQL (`pipenv run test-mysql`), y verificar que ambas terminan en verde. PostgreSQL:
  739 passed, 5 deselected. MySQL: 738 passed, 1 skipped, 5 deselected.
- [x] 2.4 Correr `pipenv run lint` y verificar que no reporta hallazgos. "All checks
  passed!"
