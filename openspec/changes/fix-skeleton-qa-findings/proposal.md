## Why

La revisión de QA de la Fase 0 encontró fallas que conviene corregir antes de archivar
`add-project-skeleton`, para que las specs vigentes nazcan sobre pruebas confiables:

- el flujo de pruebas documentado con Docker corre en silencio contra las bases locales;
- hay pruebas que dependen del orden de ejecución y del `.env` de cada desarrollador;
- el idioma del sitio cambia según el navegador del visitante;
- y `.env.example` no coincide con lo que lee el código.

## What Changes

- **Variables de entorno bajo pipenv:** `pipenv run` carga `.env` pisando las variables
  del shell. Se documenta en el README, en `.env.example` y en `docker-compose.yml`, y las
  instrucciones para apuntar las pruebas a Docker pasan a decir que se edita `.env`. El
  comentario de los ajustes del proyecto de ejemplo que afirma lo contrario se corrige.
- **Pruebas aisladas:**
  - Las pruebas de rutas del admin dejan de depender del orden de ejecución: la
    configuración de URLs se restaura después de restaurar los ajustes.
  - Las pruebas de ajustes limpian todas las variables que lee la base, para no depender
    del entorno de quien las corre.
- **Idioma del sitio fijo:** se quita `LocaleMiddleware`, así el sitio público se muestra
  siempre en `LANGUAGE_CODE` sin importar `Accept-Language`. La Fase 1 lo vuelve a
  incorporar junto con las URLs por idioma.
- **`.env.example` completo:** se agrega `DATABASE_CONN_MAX_AGE`, y una prueba verifica que
  toda variable leída por los ajustes base figure en `.env.example`.
- **TLS de email por defecto:** `EMAIL_USE_TLS` vale `true` salvo que se active
  `EMAIL_USE_SSL`, en línea con el puerto 587 por defecto y con `.env.example`. Activar
  SSL solo ya no exige apagar TLS a mano.
- `CHANGELOG.md` registra los cambios.

**Fuera del alcance:**
- Los demás hallazgos del informe de QA:
  - archivo y commit de la Fase 0;
  - tarea 5.1 marcada como hecha sin verificar;
  - traducciones `locale/es`;
  - versión de la CLI de OpenSpec;
  - `WAGTAILADMIN_BASE_URL` en producción, slugs reservados, proxy HTTPS, `/health/` por
    IP, `LOGGING` y `ADMINS`;
  - pruebas faltantes de `ALLOWED_HOSTS` y de la barra de edición, nombre del paquete,
    versiones de Python y detalles menores.
- Ejecutar las pruebas en los contenedores de Docker (sigue siendo opcional).
- Multi-idioma y URLs por idioma (Fase 1).

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `site-routing`: se agrega que el idioma de las páginas no depende del navegador del
  visitante.
- `project-configuration`: se agrega que el email usa TLS por defecto salvo que se elija
  SSL.

Las dos capacidades las crea `add-project-skeleton`, que todavía no está archivado. Por eso
estos deltas solo agregan requisitos (`ADDED`) y no modifican los existentes.

## Impact

- **Código:**
  - [src/orion/settings/base.py](../../../src/orion/settings/base.py): middleware y
    default de TLS.
  - [example/example/settings.py](../../../example/example/settings.py): solo el
    comentario.
- **Pruebas:**
  - Se modifican `tests/test_routing.py` y `tests/test_settings_base.py`.
  - Se agrega una prueba de cobertura de `.env.example`.
- **Documentación:** `README.md`, `.env.example`, `docker-compose.yml` y `CHANGELOG.md`.
- **Dependencias y migraciones:** sin dependencias nuevas ni migraciones.
- **Compatibilidad:**
  - Un proyecto que hoy define `EMAIL_HOST` sin `EMAIL_USE_TLS` pasa a negociar TLS. Si
    su servidor SMTP no lo soporta, tiene que poner `EMAIL_USE_TLS=false`.
  - El login del admin se muestra en `LANGUAGE_CODE` en vez del idioma del navegador.
