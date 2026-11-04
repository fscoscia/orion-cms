## Context

Ver `proposal.md` ("Why"). Lo que condiciona el enfoque, comprobado en la verificación:

- Nada lee `.env` salvo `pipenv run`. Las guías de VPS (unidad systemd) y cPanel
  (Passenger y `python manage.py`) lanzan el proceso sin `pipenv`.
- `base.py` no define `LOGGING`. Con `DEBUG=False`, Django solo envía los errores a
  `mail_admins`, y Orion no define `ADMINS`: un 500 no deja ninguna línea.
- Bajo `SCRIPT_NAME=/sub`, `request.path` vale `/sub/admin/` y `request.path_info`,
  `/admin/`. En cambio, `settings.STATIC_URL` y `MEDIA_URL` ya incluyen el prefijo
  (`/sub/static/`), mientras que `ORION_ADMIN_PATH` y `/_preview/` no.
- Wagtail ya fuerza como texto las celdas de Excel que openpyxl detecta como fórmula
  (`generate_xlsx_row`). Solo el CSV sale crudo.

## Goals / Non-Goals

**Goals:**

- Que un proyecto generado funcione con las guías tal como están escritas.
- Que ninguna protección falle abierta por el modo de despliegue.

**Non-Goals:**

- Soporte completo de subrutas (ver el alcance en `proposal.md`).
- Niveles de log configurables por variable de entorno o rotación de archivos: de eso se
  ocupan systemd y Passenger.

## Decisions

### 1. `python-dotenv` para leer `.env`

Se agrega `python-dotenv` como dependencia de Orion, envuelta en
`orion.settings.env.load_env_file(path)`, que llama a
`load_dotenv(path, override=False, interpolate=False)`.

**Justificación de la dependencia:** `get_random_secret_key()`, el comando que indica
`.env.example`, genera claves con `#`, `$`, `(` y `=`, justo los casos donde un lector
propio se equivoca. `python-dotenv` es pura Python, sin dependencias, y es lo que usa
`pipenv`, así que el archivo se interpreta igual en desarrollo y en producción.
`interpolate=False` evita que un `$` de la clave se expanda.

**Alternativas descartadas:**

- Parser propio: menos de 20 líneas, pero repite un formato con casos borde en el camino
  de los secretos.
- Solo documentación (`EnvironmentFile=` en systemd, variables en la interfaz de cPanel):
  systemd no admite el mismo formato, cada comando manual de `manage.py` necesitaría
  cargarlas aparte, y cPanel no las aplica en su terminal.

### 2. La carga va en los ajustes del proyecto, antes de importar los de Orion

`settings.py-tpl` queda así, porque `orion.settings.base` lee el entorno al importarse:

```python
BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR / ".env")

from orion.settings.base import *  # noqa: E402, F403
```

Un solo punto cubre `manage.py`, WSGI y `passenger_wsgi.py`. `orion.settings.env` no
importa nada de Django que necesite ajustes. `example/` no cambia: sigue usando `pipenv`.

Alternativa descartada: cargarlo en `manage.py` y `wsgi.py`. Son dos lugares, y
`passenger_wsgi.py`, que escribe cada proyecto, quedaría afuera.

### 3. `LOGGING` mínimo a la salida de errores

En `base.py`: un handler `console` (`StreamHandler`, nivel `WARNING`, con formato de
fecha, nivel y logger) en el logger raíz; `django` sin handlers propios y propagando a la
raíz; y `django.request` en nivel `ERROR`, para que los 4xx no se registren.

La salida de errores es el destino común: Gunicorn y systemd la llevan al journal, y
Passenger a su log. Ese destino queda escrito en cada guía.

Se reemplazan los handlers por defecto del logger `django`. Un proyecto que quiera
`mail_admins` redefine `LOGGING`, y queda documentado. Los logs de `runserver`
(`django.server`) no cambian. El mensaje de Django lleva la ruta, no los datos enviados,
así que los formularios no llegan al log.

### 4. Dos preguntas distintas para reconocer rutas internas

Un módulo nuevo `orion.core.paths` con dos funciones que reciben el request:

- `is_admin_request`: compara `request.path_info` con `/{ORION_ADMIN_PATH}`.
- `is_asset_request`: compara `request.path` con `STATIC_URL` y `MEDIA_URL`, que ya llevan
  el prefijo.

Las usan `TwoFactorMiddleware`, la CSP, `PageCacheMiddleware` y `NotFoundMiddleware`, que
hoy repiten la misma tupla. La caché y el monitor de 404 usan además `is_internal_request`,
que suma `/_preview/` contra `path_info`. `is_public_path(path)` desaparece; solo la usaba
su middleware.

Alternativa descartada: cambiar todo a `path_info`. Rompería la exclusión de estáticos y
medios, porque esos ajustes llevan el prefijo.

### 5. Neutralizar solo en CSV, con una excepción para números

`OrionSubmissionsListView` sobrescribe `preprocess_field_value`, que Wagtail llama con el
formato. En CSV, una cadena que empieza con `=`, `+`, `-`, `@`, tabulación o retorno lleva
un `'` delante, como recomienda OWASP. Excepción: las cadenas formadas solo por dígitos,
espacios y `+-().` quedan iguales. Sin ella, cada teléfono `+595…` se vería con apóstrofo,
y esas cadenas no pueden llamar funciones ni enlaces.

Alternativas descartadas: neutralizar también en Excel, que ya es seguro y mostraría el
apóstrofo; y aplicarlo en `to_row_dict`, que comparten ambos formatos.

### 6. `.gitignore` anclado a la raíz

`/media/`, `/static/` y `/private/` con barra inicial. `ORION_FORMS_PRIVATE_ROOT` puede
apuntar a otro lado: entonces queda fuera del proyecto y no hace falta ignorarla.

### 7. El CSS compilado del proyecto se versiona

La instalación limpia mostró que, sin `project/css/project.css`, el `{% static %}` de
`templates/orion/base.html` lanza `ValueError` fuera de debug y toda página pública
responde 500: `WHITENOISE_MANIFEST_STRICT = False` no cubre un archivo que no existe.

Se saca `assets/` del `.gitignore` y la plantilla trae `assets/project/css/project.css` con
solo un comentario, que `css-build` reemplaza. El flujo es el de Orion con su propio CSS:
se compila en la máquina de desarrollo y se commitea. El deploy no compila.

Alternativa descartada: compilar en el servidor. Suma un paso a cada deploy, depende de que
el hosting deje bajar y ejecutar el binario de Tailwind y un fallo deja el sitio caído;
además, la ruta absoluta del `@import` de `project.css` no existiría en el servidor.

## Risks / Trade-offs

- [`mail_admins` deja de funcionar para un proyecto que defina `ADMINS`] → ningún proyecto
  lo hace hoy; queda documentado cómo redefinir `LOGGING`.
- [Un valor que el CSV debía conservar exacto gana un `'`, por ejemplo `-texto`] → es lo
  que pide la neutralización; el detalle del envío en el admin sigue mostrando el original.
- [El `.env` queda legible por otros usuarios del servidor] → las guías indican
  `chmod 600 .env` y dejarlo fuera de la carpeta pública.
- [Alguien commitea sin compilar y el sitio sale con estilos viejos] → es visible y no
  rompe nada; la guía de desarrollo lo indica.
- [Guías de cPanel sin probar en un cPanel real] → se validan en entorno limpio y sin
  `pipenv`; la prueba en un hosting real queda para el despliegue de Intervita.

## Migration Plan

1. Archivar `add-project-tailwind-build` antes de aplicar este cambio.
2. Sin migraciones de base de datos. Revertir es volver a la versión anterior.
3. En Intervita, a mano: agregar la carga del `.env`, quitar el `ORION_SEARCH_CONFIG=spanish`
   que ya no hace falta, anclar el `.gitignore`, sacar de ahí `assets/`, compilar con
   `pipenv run css-build` y commitear `assets/project/css/project.css`. Si ya hubiera archivos de `private/` en
   su historial, habría que sacarlos; hoy no tiene esa carpeta.
