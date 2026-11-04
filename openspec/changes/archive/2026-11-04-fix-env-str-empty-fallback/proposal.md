## Why

La validación de la Fase 7 (cambio `validate-intervita-site`, ver su `design.md`,
hallazgo 1) encontró que `orion_install` falla en cualquier instalación real que siga
`.env.example` al pie de la letra: `env_str()` solo aplica su `default` cuando la
variable no existe en el entorno, pero `pipenv` carga una variable presente y vacía
(`ORION_SEARCH_CONFIG=`, exactamente como la distribuye `.env.example`) como `""` en
`os.environ`, así que el default documentado ("vacío usa el idioma base") nunca se
aplica. El síntoma es un `psycopg.errors.InvalidName` al crear los formularios de
ejemplo, porque PostgreSQL recibe una configuración de texto vacía.

## What Changes

- Corregir `env_str()` en `src/orion/settings/env.py` para que una variable presente y
  vacía caiga al `default` igual que una variable ausente, en vez de devolver la cadena
  vacía. `env_bool`, `env_int` y `env_list` ya resuelven esto correctamente (llaman a
  `env_str(name)` con default vacío y aplican su propio `if not raw_value: return
  default`); el cambio lleva ese mismo criterio a `env_str` para que sus propios
  llamadores con un `default` no vacío (`LANGUAGE_CODE`, `TIME_ZONE`,
  `DEFAULT_FROM_EMAIL`, `WAGTAIL_SITE_NAME`, `WAGTAILADMIN_BASE_URL`,
  `ORION_ADMIN_PATH`, `ORION_SEARCH_CONFIG`) dejen de depender de que la variable esté
  completamente ausente.
- Ninguna variable cambia su valor por defecto ni su nombre: solo se corrige cuándo se
  aplica ese default.

**Fuera del alcance:** cualquier otro hallazgo de `validate-intervita-site` (el
`.gitignore` faltante en `project-template` es un cambio aparte); agregar
`ORION_SEARCH_CONFIG` o cualquier otra variable a `docs/alta-de-cliente.md` o a las
guías de deploy del README (una vez corregido el fallback, no hace falta mencionarlas
ahí: el comportamiento documentado — "vacío usa X" — simplemente empieza a cumplirse).

## Capabilities

### Modified Capabilities
- `project-configuration`: una variable de entorno de tipo texto con un valor por
  defecto no vacío debe caer a ese default tanto cuando está ausente como cuando está
  presente pero vacía.

## Impact

- **Código:** `src/orion/settings/env.py` (`env_str`), un cambio de una función. No
  afecta `env_bool`, `env_int` ni `env_list`: su comportamiento ya era correcto y no
  cambia.
- **Configuración:** ninguna variable nueva ni renombrada; `.env.example` no necesita
  cambios (el comentario "vacío usa X" ya era la intención, ahora se cumple).
- **Dependencias nuevas:** ninguna.
- **Migraciones:** ninguna.
- **Compatibilidad:** un sitio que hoy define alguna de esas variables con un valor
  explícito no se ve afectado. Uno que la deja presente y vacía pasa de recibir `""` a
  recibir el default documentado — el comportamiento que `.env.example` siempre
  prometió y que hasta ahora nunca se cumplía (y, en el caso de `ORION_SEARCH_CONFIG`,
  rompía la instalación en lugar de degradar en silencio).
