# Estilos y diseño de un sitio sobre Orion

Para quien le da su diseño a un sitio sobre Orion, con o sin asistente de IA. Orion trae su
hoja de estilos ya compilada, así que un proyecto nuevo se ve bien sin tocar nada; esta guía
explica dónde y cómo se cambia el aspecto. Para crear un bloque propio, ver
[Crear un bloque](crear-un-bloque.md); para decidir si hace falta, [Trabajar con
IA](trabajar-con-ia.md).

## 1. Dónde vive el CSS del proyecto

| Archivo | Qué es | ¿Se edita? | ¿Se versiona? |
|---|---|---|---|
| `static_src/project.css` | Fuente del CSS del proyecto | Sí | Sí |
| `assets/project/css/project.css` | CSS compilado que carga el sitio | No, se genera | Sí |
| `templates/orion/base.html` | Carga el CSS compilado del proyecto después del de Orion | Rara vez | Sí |
| `.tailwind/` | Binario de Tailwind descargado | No | No |

`static_src/project.css` importa la hoja de Orion (colores, fuentes y las clases de sus
componentes) y compila las clases de Tailwind que se usen en `home/` y en `templates/`. Para
compilarlo:

```bash
pipenv run css-build    # una vez
pipenv run css-watch    # mientras se diseña: recompila con cada cambio
```

El CSS compilado se versiona porque los despliegues no compilan. Después de un cambio de
estilos, compilar antes de hacer el commit.

## 2. Colores y tipografías

Los colores y las fuentes son variables CSS. Se cambian redefiniéndolas en
`static_src/project.css`, **fuera de cualquier `@layer`**, de modo que ganen a las de Orion:

```css
:root {
  --color-primary-700: #1d4ed8;
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
}
```

Las variables disponibles son la escala `--color-primary-50` a `--color-primary-900`,
`--color-accent-500`, `--color-accent-600`, `--color-surface`, `--color-surface-muted`,
`--color-ink`, `--color-ink-muted`, `--color-line`, `--font-sans` y `--font-display` (títulos).
Están en el bloque `@theme` de `src/orion/core/static_src/orion.css`.

Una tipografía propia se sirve desde el sitio en `woff2`, sin servicios de fuentes externos:
poner el archivo en `assets/project/fonts/`, declararla con `@font-face` y `font-display: swap`
en `static_src/project.css` (la ruta es relativa al CSS compilado, `../fonts/mi-fuente.woff2`),
redefinir `--font-sans` y `--font-display`, y precargarla desde los ajustes:

```python
ORION_FONT_PRELOAD = ["project/fonts/mi-fuente.woff2"]
```

## 3. Por qué el CSS propio va fuera de `@layer`

Los templates de Orion usan utilidades de Tailwind (`bg-surface-muted`, `text-ink-muted`…),
que viven dentro de una capa. Una regla propia dentro de `@layer` pierde contra ellas sin
avisar, aunque parezca más específica. Escribir el CSS propio fuera de cualquier capa.

Un caso frecuente: el `<section>` interno de varios bloques trae su propio fondo. Para pintar
una banda de color a todo el ancho hay que anular ese fondo (`background: transparent`) en
la regla de la banda.

## 4. Variantes de un bloque: estilos de bloque

Cada bloque tiene un campo "Estilo" en su engranaje del editor. Las opciones las declara el
proyecto en los ajustes (`<proyecto>/settings.py`), con la clave del bloque; Orion siempre suma
"Estándar" primero y el editor no ve el campo mientras haya una sola opción:

```python
ORION_BLOCK_STYLES = {
    "hero": [("split", "Imagen al costado")],
    "cards": [("oscuro", "Banda oscura")],
}
```

El estilo elegido llega al CSS de dos maneras:

- La envoltura del bloque lleva `data-block-style="oscuro"` (el estándar no lo lleva), útil
  para una banda de color: `[data-block-style="oscuro"] { background: #0f172a; }`.
- Los templates de Orion agregan la clase `block-<clave>--<estilo>`, por ejemplo
  `block-hero--split`.

Cambiar la lista no requiere migraciones, y un bloque cuyo estilo se quitó se muestra con el
estándar.

## 5. Imágenes: tamaños y recortes

Los templates muestran las imágenes con medidas con nombre (`hero`, `image`, `image_text`,
`gallery`, `card`, `logo`, `article`, `site_logo`). `card`, que usan las tarjetas y los pasos,
**recorta a 8:5** en el servidor: una ilustración o un logo se corta. Para esos casos, declarar
una medida sin recorte y usarla en el template:

```python
ORION_IMAGE_SIZES = {
    "ilustracion": {
        "filters": "width-{480,800}",
        "sizes": "(min-width: 48rem) 33vw, 100vw",
    },
}
```

```django
{% load orion_core %}
{% responsive_image item.image "ilustracion" alt=item.title %}
```

Al cambiar `ORION_IMAGE_SIZES` hay que generar los recortes de las imágenes que ya estaban
cargadas:

```bash
pipenv run manage orion_generate_renditions
```

En el bloque Tarjetas, la opción de mostrar las imágenes completas, sin recortar, resuelve
buena parte de estos casos sin una medida nueva.

## 6. Cambiar el HTML de un bloque o del encabezado

Un template de Orion se reemplaza creando uno con el mismo nombre dentro de `templates/` del
proyecto:

| Para cambiar | Crear |
|---|---|
| Un bloque | `templates/orion/blocks/<clave>.html` (por ejemplo `hero.html`, `cards.html`) |
| El encabezado | `templates/orion/includes/header.html` |
| El pie | `templates/orion/includes/footer.html` |

Un template con el mismo nombre dentro de una app del proyecto **no** alcanza: las apps de
Orion van antes en `INSTALLED_APPS` y su template se encuentra primero. Las clases de Tailwind
que use el template nuevo las compila `css-build`.

Antes de reemplazar un template entero, probar si un estilo de bloque con CSS alcanza.

## 7. Movimiento

`ORION_BLOCK_REVEAL = True` hace que los bloques, salvo el primero, aparezcan con un fundido al
entrar en pantalla. Viene apagado y el contenido nunca queda oculto sin JavaScript. Todo
movimiento propio respeta `prefers-reduced-motion` y, si se repite, se puede pausar.

## 8. Qué revisar al terminar

Abrir el sitio a 390 y a 1280 px recorriendo la página entera (las imágenes perezosas no
cargan si solo se mira el principio), y comprobar el contraste del texto sobre fotos y el
orden de los títulos. El detalle está en [Trabajar con IA](trabajar-con-ia.md#5-qué-revisar-siempre-a-mano).
