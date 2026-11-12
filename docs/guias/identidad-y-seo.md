# Identidad y SEO del sitio

Para quien deja listo un sitio sobre Orion antes de entregarlo: el ícono de la pestaña
(favicon), la imagen que aparece al compartir, lo que muestran los buscadores y el archivo
`robots.txt`. Orion ya resuelve las etiquetas, el sitemap y los datos estructurados; esta
guía cubre lo único que falta, que son los datos propios de cada sitio. Se leen en este
orden: qué se carga y dónde, qué le toca al asistente, cómo preparar los archivos y cómo
comprobar el resultado.

## 1. Qué se carga y dónde

Todo se carga desde el admin, con una cuenta que pueda editar los datos del sitio.

| Dato | Dónde | Notas |
|---|---|---|
| Favicon | **Propiedades → Datos del sitio → SEO** | Imagen cuadrada; Orion genera los tamaños |
| Imagen para redes por defecto | **Propiedades → Datos del sitio → SEO** | La usan las páginas sin imagen propia |
| Código de verificación de Google Search Console | **Propiedades → Datos del sitio → SEO** | Solo el código, ver la sección 4 |
| `robots.txt` | **Propiedades → Datos del sitio → SEO** | Vacío: permite todo salvo el admin |
| Logo y logo del pie | **Propiedades → Datos del sitio → Identidad** | Sin logo, el encabezado muestra el nombre del sitio |
| Teléfono, email, dirección, redes | **Propiedades → Datos del sitio** (pestañas Contacto y Redes sociales) | Salen en los datos estructurados de la organización |
| Descripción del sitio, una por idioma | **Fragmentos → Textos del sitio** | Se usa en las páginas sin descripción propia |
| Título SEO, descripción e imagen para redes de una página | La pestaña **Promocionar** de esa página | Cada página de Orion la tiene |
| «No indexar» y «No seguir los enlaces» | La pestaña **Promocionar** de esa página | Una página «no indexar» tampoco figura en el sitemap |

## 2. Qué le toca al asistente y qué a una persona

Estos datos son ajustes únicos del sitio, guardados en la base de datos, y el admin los valida
(por ejemplo, rechaza la etiqueta completa de Search Console). Por eso **se cargan desde el
admin y no se le pide al asistente que los escriba en la base**.

| Tarea | Quién |
|---|---|
| Redactar el título y la descripción SEO de cada página | El asistente propone; una persona revisa |
| Preparar el favicon cuadrado y la imagen para redes | El asistente o el diseño; una persona revisa |
| Cargar los datos en el admin | Una persona |
| Comprobar el resultado en el navegador | El asistente, y una persona recorre las páginas |

Un pedido para los textos de las páginas, con el contenido ya cargado:

```text
Para cada página del sitio, propón un título SEO de hasta 60 caracteres y una descripción
de hasta 155, en una tabla con tres columnas: página, título, descripción. Usa solo lo que
dice el contenido de la página, sin inventar datos, y el idioma de cada página. No
escribas código ni toques la base de datos: voy a cargar la tabla en el admin.
```

Los límites de 60 y 155 caracteres son una convención habitual de los buscadores, no una
regla de Orion: si un título es más largo, la página funciona igual.

## 3. Preparar los archivos

- **Favicon:** una imagen cuadrada, mejor si es de 192 píxeles o más, en PNG o SVG. Con él
  cargado, cada página enlaza el ícono en 32 y 192 píxeles y el de Apple en 180 (y el SVG tal
  cual, si lo es), y `/favicon.ico` lleva al de 32 píxeles. Sin favicon, `/favicon.ico`
  responde 404.
- **Imagen para redes:** de 1200 × 630 píxeles. Orion la recorta a ese tamaño en JPEG, que es
  el formato que leen las redes. Si una página no tiene imagen propia, se usa, en este orden,
  la imagen del artículo, la del Hero que abre la página y la imagen por defecto del sitio.
- **Texto en las imágenes:** conviene dejar los bordes libres, porque cada red recorta distinto.

## 4. Código de Search Console

Search Console da una etiqueta del tipo `<meta name="google-site-verification"
content="abc123…">`. En el campo del admin se pega **solo el valor de `content`**, no la
etiqueta completa: acepta únicamente letras, números, guiones y guiones bajos, y rechaza lo
demás con un mensaje que lo explica.

## 5. Qué hace Orion por su cuenta

- **Título:** el título SEO de la página, o, si no tiene, su título seguido de « | » y el
  nombre del sitio.
- **Descripción:** la de la página (en un artículo, su resumen) o, si falta, la del sitio en el
  idioma de la página. Sin ninguna, la página no lleva etiqueta de descripción.
- **Compartir en redes:** etiquetas Open Graph y Twitter Card en cada página.
- **URL canónica:** absoluta y sin parámetros de consulta; el número de página de un listado
  se conserva desde la segunda.
- **Sitemap:** `/sitemap.xml` lista las páginas públicas publicadas en todos los idiomas
  públicos.
- **`robots.txt`:** el texto del admin o, si está vacío, uno que permite todo salvo el admin;
  siempre anuncia el sitemap.
- **Datos estructurados:** el sitio web, la organización con sus datos de contacto, las migas
  de pan y, en los artículos, el artículo con sus fechas.

## 6. Comprobar el resultado

En el navegador, con el sitio publicado o en local:

| Qué | Cómo |
|---|---|
| Título y descripción | Ver el código fuente de la página: `<title>` y `<meta name="description">` |
| Imagen para redes | En el código fuente, `og:image`; abrirla y confirmar que mide 1200 × 630 |
| URL canónica | En el código fuente, `<link rel="canonical">`: absoluta y sin `?utm_…` |
| Favicon | La pestaña del navegador, y abrir `/favicon.ico` |
| Sitemap | Abrir `/sitemap.xml` y ver las páginas esperadas, sin las marcadas «no indexar» |
| `robots.txt` | Abrir `/robots.txt` y ver la línea `Sitemap:` con la URL completa |

Desde la terminal, contra el sitio en local:

```bash
curl -s http://localhost:8000/ | grep -E '<title>|name="description"|og:image|rel="canonical"'
curl -s http://localhost:8000/robots.txt
curl -sI http://localhost:8000/favicon.ico
```

Un pedido para que el asistente haga la revisión:

```text
Revisa estas páginas en el navegador: [lista]. Para cada una dime el <title>, la
descripción, og:image y la canónica, y marca cuáles faltan o se repiten entre páginas.
Revisa también /sitemap.xml, /robots.txt y /favicon.ico. No cambies ningún archivo.
```

## Siguientes guías

- [Empezar](empezar.md): del equipo preparado al sitio funcionando.
- [Trabajar con IA](trabajar-con-ia.md): reparto de trabajo y qué revisar a mano.
- [Crear un formulario](crear-un-formulario.md): el resto del contenido que carga el admin.
