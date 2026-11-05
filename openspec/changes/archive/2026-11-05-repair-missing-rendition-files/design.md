## Context

`generate_renditions(image)` (en `orion/core/image_library.py`) calcula los recortes faltantes
comparando los filtros esperados con `image.renditions.values_list("filter_spec",
"focal_point_key")`. Un recorte cuya fila existe pero cuyo archivo no, nunca aparece como
faltante. Después `image.get_renditions(...)` de Wagtail devuelve la fila existente sin mirar
el archivo, y el template usa su URL: la página muestra una imagen rota (404).

Reproducido sin éxito: una carga limpia del SVG real (`logo-header.svg`, 207,479 × 32, también
con anchos enteros y de 400 × 200) deja `height-80` en disco. El estado roto no sale de la
carga, sino de perder el archivo después.

## Goals / Non-Goals

**Goals:**
- Que `orion_generate_renditions` repare los recortes con archivo perdido.
- Sin costo adicional al mostrar páginas.

**Non-Goals:**
- Averiguar cómo se perdió el archivo en Bolt Emprende.
- Verificar el archivo en cada render ni en cada guardado desde el admin.

## Decisions

1. **La comprobación vive en `generate_renditions`.** Para cada recorte registrado se pregunta
   `rendition.file.storage.exists(rendition.file.name)`. Alternativa descartada: comprobarlo en
   `responsive_image`: sumaría una consulta de almacenamiento por imagen en cada render sin
   caché de página, y con almacenamiento remoto sería una petición de red.
2. **Regenerar = borrar la fila rota y volver a crearla.** `get_renditions` solo crea las filas
   que no existen, por lo que la fila se borra antes. Wagtail intenta borrar el archivo al
   eliminar la fila; con un archivo inexistente `FileSystemStorage.delete` no falla, y hay que
   confirmarlo con una prueba (también para el almacenamiento configurado por proyecto).
3. **El conteo suma los reparados**, así el comando informa cuántos creó sin una cifra nueva.
4. **Sin cambios en la señal de subida ni en el hilo de fondo:** ya generan recortes completos
   y la propuesta no los toca.

## Risks / Trade-offs

- [El comando consulta el almacenamiento una vez por recorte] → Solo se corre a mano o al
  desplegar; con almacenamiento remoto tarda más en bibliotecas grandes. Se documenta en la
  ayuda del comando.
- [Un error temporal del almacenamiento marcaría un recorte sano como perdido] → Si `exists`
  lanza una excepción, la imagen se informa como fallida (como hoy) y no se borra nada.

## Migration Plan

Sin migraciones. Para reparar un sitio roto: `orion_generate_renditions`.
