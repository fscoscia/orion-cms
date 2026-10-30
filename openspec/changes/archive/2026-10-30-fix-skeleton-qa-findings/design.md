## Context

Ver proposal.md (Why). Hechos verificados durante la revisión:

- **pipenv 2026.0.3 carga `.env` con `load_dotenv(..., override=True)`**, y no ofrece un
  modo que respete el shell. Solo existe `PIPENV_DONT_LOAD_ENV=1`, que no carga nada.
  - `POSTGRES_TEST_URL=… pipenv run test-postgres` corrió contra la base local.
  - Con `PIPENV_DONT_LOAD_ENV=1 ORION_ADMIN_PATH=panel/` fallan 2 pruebas.
- **Orden de desmontaje en `tests/test_routing.py`:** el fixture `reload_urls` se desmonta
  antes que el fixture `settings`, así que recarga las URLs con `ORION_ADMIN_PATH` todavía
  en `panel/`. Ejecutar la prueba de ruta propia antes que la de ruta por defecto hace
  fallar a esta última.
- **Idioma según el navegador:** con `LocaleMiddleware` y la lista `LANGUAGES` de Django
  (99 idiomas), `Accept-Language: fr` produce `<html lang="fr">`.
- **Wagtail no depende de `LocaleMiddleware`:** solo aparece en sus ajustes de prueba. El
  admin aplica el idioma preferido de cada usuario por su cuenta.

## Goals / Non-Goals

**Goals:**
- Que la suite dé el mismo resultado en cualquier orden y con cualquier `.env` válido.
- Que lo documentado para cambiar la base de pruebas funcione tal como está escrito.

**Non-Goals:**
- Dejar de usar `.env` o cambiar de herramienta de entorno.
- Diseñar el modelo multi-idioma (Fase 1).

## Decisions

### `.env` se documenta en vez de evitarse
La forma de cambiar un valor bajo `pipenv run` pasa a ser editar `.env`. Se documenta en:
- el README;
- la cabecera de `.env.example`;
- el comentario de `docker-compose.yml`, que deja las URLs de Docker como líneas para
  copiar a `.env`.

Para ejecuciones puntuales se documenta `PIPENV_DONT_LOAD_ENV=1`.

Alternativas descartadas:
- **Que el proyecto de ejemplo lea `.env` sin pisar el entorno:** requiere `python-dotenv`
  como dependencia y deja dos cargadores compitiendo.
- **Scripts de pipenv aparte para Docker:** duplican comandos para un caso opcional.

### Restauración de ajustes y URLs en un solo fixture
El fixture de rutas aplica la ruta del admin con `override_settings` dentro de un `with`,
recarga las URLs y, al salir del `with` (ajuste ya restaurado), las recarga otra vez. Así el
orden queda garantizado por el código del fixture y no por el orden de desmontaje de pytest.

Además, la prueba de "ruta por defecto" fija explícitamente `admin/` con el mismo fixture,
porque los ajustes del proyecto de ejemplo se leen del entorno al arrancar la suite. Que
`admin/` sea el valor por defecto ya lo prueba `test_settings_base.py`, recargando el módulo
sin la variable.

Alternativa descartada: pedir el fixture `settings` y llamar a su `finalize()` a mano; se
apoya en un detalle interno de pytest-django.

### Pruebas de ajustes con entorno limpio
`load_settings` borra todas las variables que lee `orion.settings.base`, no solo cuatro. La
lista se obtiene del código fuente del módulo (llamadas `env_*("NOMBRE"…)`), y la misma
lista alimenta la prueba de cobertura de `.env.example`. Una sola fuente evita que la lista
de las pruebas quede desactualizada cuando se agregue una variable.

Alternativa descartada: una tupla escrita a mano en las pruebas; es lo que hoy quedó
incompleto.

### Quitar `LocaleMiddleware` en vez de restringir `LANGUAGES`
Hoy no hay idiomas por URL ni selector, así que el middleware solo sirve para que el
navegador cambie el idioma. Quitarlo deja el sitio en `LANGUAGE_CODE` con una línea menos.

Alternativa considerada: `LANGUAGES = [(LANGUAGE_CODE, …)]`. Logra el mismo efecto, pero
fija ahora una forma de `LANGUAGES` que la Fase 1 va a redefinir con wagtail-localize. La
Fase 1 vuelve a agregar el middleware junto con `i18n_patterns`. Con
`prefix_default_language=False`, Django usa `LANGUAGE_CODE` para las URLs sin prefijo, así
que el problema no reaparece.

### TLS por defecto derivado de SSL
`EMAIL_USE_TLS` toma por defecto `not EMAIL_USE_SSL`:
- Sin variables: TLS, que coincide con el puerto 587 por defecto.
- Con solo SSL: TLS apagado, sin disparar `orion.E001`.
- Con las dos explícitas en `true`: `orion.E001` sigue rechazándolo.

Alternativa descartada: cambiar `.env.example` a `EMAIL_USE_TLS=false`. Alinea el ejemplo
con el código, pero deja el default inseguro: credenciales SMTP sin cifrar.

## Risks / Trade-offs

- **[Un proyecto con `EMAIL_HOST` y un servidor SMTP sin STARTTLS deja de enviar email]** →
  Se avisa en el CHANGELOG. Se resuelve poniendo `EMAIL_USE_TLS=false`.
- **[El login del admin deja de seguir el idioma del navegador]** → Se muestra en
  `LANGUAGE_CODE` (`es` por defecto). Ya dentro del admin, cada usuario sigue viendo su
  idioma preferido.
- **[Leer la lista de variables del código fuente depende del patrón `env_*("…")`]** → Si
  alguien lee una variable de otra forma, la prueba de cobertura no la ve. Se acepta: es la
  convención del módulo.

## Migration Plan

Sin migraciones de base de datos. Orden recomendado:
1. Archivar `add-project-skeleton`.
2. Archivar este cambio, cuyos deltas son solo `ADDED`.
