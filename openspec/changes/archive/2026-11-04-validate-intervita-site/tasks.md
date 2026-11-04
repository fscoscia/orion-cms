## 1. Repositorio y entorno de Intervita

- [x] 1.1 Pedir confirmación al usuario del nombre y la ruta exacta del repositorio nuevo
  (por defecto `/Users/fscoscia/Proyectos/intervita`) antes de crear nada fuera de
  `orion/`, y verificar con `ls` que el directorio está vacío o no existe.
- [x] 1.2 Inicializar el repositorio git de Intervita (`git init`) y correr
  `pipenv run orion-start intervita` desde Orion para generar el proyecto; verificar que
  el directorio resultante tiene `manage.py`, los ajustes, las rutas, la app `home`,
  `templates/`, `.env.example` y `Pipfile` (requisitos de `project-template`).
- [x] 1.3 Instalar Orion con un path local editable
  (`pipenv install -e /Users/fscoscia/Proyectos/orion`) y verificar con
  `pipenv run pip show orion` que apunta a esa ruta.
- [x] 1.4 Completar `.env` desde `.env.example` (`SECRET_KEY`, `DATABASE_URL` a
  PostgreSQL local, `ALLOWED_HOSTS`, `LANGUAGE_CODE`) y verificar que
  `pipenv run python manage.py check` no reporta errores de configuración.

## 2. Instalación y arranque

- [x] 2.1 Correr `pipenv run python manage.py orion_install` (con
  `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`) y
  verificar que termina sin error, informa el idioma base y deja los formularios de
  ejemplo cargados (`Contacto`, `Trabajá con nosotros`). Requirió un workaround en el
  `.env` de Intervita (`ORION_SEARCH_CONFIG=spanish` explícito) por un bug de Orion
  encontrado en el camino (ver "Hallazgos de la validación" en `design.md`).
- [x] 2.2 Correr el comando una segunda vez y verificar que no duplica el contenido de
  ejemplo ni falla por el superusuario ya existente (requisito de `installer`).
- [x] 2.3 Levantar el servidor (`pipenv run python manage.py runserver`) y verificar que
  el sitio público y `/admin/` (o la ruta de `ORION_ADMIN_PATH`) responden.

## 3. Verificación funcional contra las fases 0 a 6

- [x] 3.1 Verificar en el admin: idioma en español, panel de inicio, menú lateral,
  marca por defecto, y que un editor puede crear una página de ejemplo con vista previa
  en vivo abierta por defecto. Verificado por backend (admin en español, "Panel de
  control - Intervita", creación y publicación de `ContentPage`, servido en el sitio
  público). La vista previa en vivo abierta por defecto es comportamiento de JS en el
  navegador: esta sesión no tiene una herramienta de navegador real, así que ese punto
  puntual queda sin confirmar visualmente (anotado en "Hallazgos de la validación", no
  es un bug encontrado, es un límite de esta sesión).
- [x] 3.2 Verificar seguridad: activar 2FA para el administrador, confirmar que
  `pipenv run python manage.py check --deploy` no reporta hallazgos con `DEBUG=False`, y
  que tras varios intentos de login fallidos la cuenta se bloquea temporalmente
  (django-axes). Las tres verificaciones pasaron (2FA exigido para entrar al panel, 0
  hallazgos con `DEBUG=false`, bloqueo HTTP 429 "Demasiados intentos" al sexto intento,
  con el límite en 5 configurado).
- [x] 3.3 Verificar rendimiento y SEO: la portada de ejemplo responde cacheada en una
  segunda visita (header de caché o tiempo de respuesta notablemente menor), y
  `/sitemap.xml` y `/robots.txt` existen y listan la página de ejemplo. Con
  `ORION_PAGE_CACHE=true`, la segunda visita a una página respondió con
  `X-Orion-Cache: hit` (la primera, `miss`); `/sitemap.xml` y `/robots.txt` responden
  200, con `Sitemap:` referenciado en `robots.txt`.
- [x] 3.4 Verificar buscador y formularios: una búsqueda sobre el contenido de ejemplo
  devuelve resultados, y un envío de prueba al formulario "Contacto" aparece en la
  bandeja de envíos del admin. `/buscar/?q=prueba` encontró la página de prueba; el
  honeypot, el consentimiento y el campo `rendered_at` (antispam por tiempo) estaban
  presentes en el formulario, y el envío válido quedó guardado y disponible para el
  admin.
- [x] 3.5 Verificar backups: correr `orion_backup` y `orion_inspect_backup` sobre el
  proyecto Intervita y confirmar que el archivo generado se inspecciona sin error.

## 4. Guías y checklist como ensayo

- [x] 4.1 Seguir `docs/alta-de-cliente.md` como ensayo (sin cuentas reales) contra el
  proyecto Intervita y anotar en `design.md` ("Hallazgos de la validación") cualquier
  paso incompleto, ambiguo o fuera de orden. El checklist asume el proyecto ya
  desplegado y nunca menciona `orion-start`/`orion_install` ni `ORION_SEARCH_CONFIG`
  entre las variables de entorno de la sección 4 — el mismo vacío que las guías de
  deploy, ligado al hallazgo 1 de `design.md`. El resto de los pasos (SMTP, DNS, cron,
  prueba final) son claros y están en orden.
- [x] 4.2 Seguir `docs/guias/crear-un-tipo-de-pagina.md` para crear un tipo de página de
  prueba en Intervita (por ejemplo una página de servicio) y verificar que la migración
  se genera y aplica sin errores, y que la página se publica. `ServicePage` en la app
  `home` de Intervita, siguiendo el ejemplo de la guía al pie de la letra: migración
  generada y aplicada sin tocar nada, página publicada y servida en `/servicio-de-prueba/`
  con su propio template.
- [x] 4.3 Seguir `docs/guias/crear-un-bloque.md` para agregar un bloque de prueba al
  cuerpo de esa página y verificar que aparece en el selector de bloques con su vista
  previa y descripción. `TestimonialBlock` creado al pie de la letra, sumado a un
  `ProjectStreamBlock` propio y usado en el `body` de `ServicePage`: publicó y renderizó
  con su propio template. El selector de bloques (ícono, descripción y vista previa en
  el editor) es UI de admin que no se verificó visualmente, por el mismo límite de
  sesión sin navegador que 3.1.
- [x] 4.4 Revisar las guías de deploy del README (VPS y cPanel) contra lo que el
  proyecto Intervita realmente necesita (Gunicorn/Passenger, estáticos, cron) y anotar en
  `design.md` cualquier paso que falte o esté desactualizado. Ambas guías corren
  `orion_install` como parte del deploy, así que cualquier cliente que las siga de
  punta a punta se topa con el mismo bug de `ORION_SEARCH_CONFIG` (hallazgo 1 de
  `design.md`); ninguna de las dos lo menciona.

## 5. Cierre de la validación

- [x] 5.1 Completar la sección "Hallazgos de la validación" de `design.md` con cada
  fricción encontrada, marcando cuáles ameritan un cambio de OpenSpec propio.
- [x] 5.2 Confirmar con el usuario qué hallazgos se proponen como cambios de OpenSpec
  separados y con qué prioridad, antes de abrir cualquiera de ellos. Usuario confirmó
  abrir los dos ahora, empezando por el bug de `env_str` (hallazgo 1), después el
  `.gitignore` de `project-template` (hallazgo 2); se proponen como cambios separados
  una vez cerrado este.
- [x] 5.3 Dejar un primer commit en el repositorio de Intervita con el proyecto generado
  e instalado, y verificar con `git status` que no hay archivos sensibles (`.env`,
  credenciales) incluidos. Commit raíz `ec8f4ca`; `.env` quedó afuera (excluido por el
  `.gitignore` agregado en la tarea 1.4/hallazgo 2).
