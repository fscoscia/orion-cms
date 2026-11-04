## Context

Ver `proposal.md` ("Why") para la motivación y el hallazgo original. El código
relevante hoy, en `src/orion/settings/env.py`:

```python
def env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    raw_value = env_str(name)
    if not raw_value:
        return default
    ...


def env_int(name: str, default: int) -> int:
    raw_value = env_str(name)
    if not raw_value:
        return default
    ...


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw_value = env_str(name)
    if not raw_value:
        return list(default or [])
    ...
```

`env_bool`, `env_int` y `env_list` ya resuelven "ausente o vacía usa el default"
correctamente: llaman a `env_str(name)` (con su propio default vacío, que nunca entra
en juego) y después deciden el fallback ellas mismas con `if not raw_value: return
default`. Solo `env_str` carece de ese paso cuando se la llama directamente con un
`default` no vacío, porque devuelve lo que sale de `os.environ.get(name, default)` sin
revisar si el resultado quedó vacío.

## Goals / Non-Goals

**Goals:**
- Que `env_str("ORION_SEARCH_CONFIG", <default>)` (y cualquier otra llamada de
  `env_str` con un `default` no vacío) se comporte igual ante "variable ausente" y
  "variable presente y vacía".
- No tocar `env_bool`, `env_int` ni `env_list`: ya hacen lo correcto y no dependen del
  bug de `env_str`.

**Non-Goals:**
- No se revisa ni se documenta `ORION_SEARCH_CONFIG` en `docs/alta-de-cliente.md` ni en
  las guías de deploy: una vez corregido el fallback, no hace falta mencionarla ahí (ver
  "Fuera del alcance" en `proposal.md`).
- No se audita si existe algún otro helper de configuración con el mismo problema fuera
  de `src/orion/settings/env.py`; esta validación solo encontró el de `env_str`.

## Decisions

**Arreglar en `env_str`, no en cada llamador:** las siete variables afectadas
(`LANGUAGE_CODE`, `TIME_ZONE`, `DEFAULT_FROM_EMAIL`, `WAGTAIL_SITE_NAME`,
`WAGTAILADMIN_BASE_URL`, `ORION_ADMIN_PATH`, `ORION_SEARCH_CONFIG`) comparten el mismo
patrón (`env_str(nombre, default_no_vacío)`); corregir la función una vez evita repetir
la misma condición siete veces y previene que una variable nueva con este patrón caiga
en el mismo bug. Alternativa descartada: envolver solo la asignación de
`ORION_SEARCH_CONFIG` en `settings/base.py` con un `or` — resuelve el síntoma que
encontró la validación pero deja el bug de fondo en `env_str` para la próxima variable
que lo use.

**Mismo criterio que `env_bool`/`env_int`/`env_list`:** en vez de inventar un mecanismo
nuevo, `env_str` adopta el `if not raw_value: return default` que las otras tres ya
usan. Mantiene un solo patrón de "ausente o vacía" en todo el módulo.

```python
def env_str(name: str, default: str = "") -> str:
    """Return the variable stripped of surrounding whitespace, or ``default`` when
    absent or empty."""
    raw_value = os.environ.get(name, "").strip()
    return raw_value or default
```

## Risks / Trade-offs

- [Riesgo] Alguien podría depender hoy de que `env_str` devuelva `""` para una variable
  presente y vacía con un `default` no vacío (en vez del default). → Mitigación: ese
  comportamiento nunca estuvo documentado ni era el que `.env.example` prometía; es
  justamente el bug que este cambio corrige. Las pruebas de `project-configuration`
  cubren el caso con `ORION_SEARCH_CONFIG` como ejemplo concreto.
- [Riesgo] `env_str` se usa también con `default=""` (p. ej. `SECRET_KEY`,
  `DATABASE_URL`, `EMAIL_HOST`); con el default vacío, `raw_value or default` sigue
  devolviendo `""` en ausencia o vacío, igual que antes. → Sin cambio de comportamiento
  en esos casos; se verifica con una prueba que cubra ambos (default vacío y no vacío).

## Migration Plan

Cambio de una función interna, sin estado persistente ni migración de datos. Se
despliega como cualquier otro cambio de Orion (nueva versión del paquete); no requiere
pasos de migración en los proyectos que lo instalen. No hay rollback especial: revertir
el commit alcanza.
