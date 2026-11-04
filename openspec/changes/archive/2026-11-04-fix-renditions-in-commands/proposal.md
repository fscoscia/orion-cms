## Why

Orion genera las variantes de una imagen en un hilo de fondo incluso cuando la imagen se
guarda desde un comando, donde nadie espera una respuesta. El hilo muere al terminar el
proceso: el comando puede fallar con `cannot schedule new futures after interpreter
shutdown` y las variantes se pierden sin aviso. Lo encontró la carga de contenido de
Intervita, y una reproducción aislada dejó 0 variantes.

## What Changes

- Fuera de una petición web, las variantes se generan antes de que termine el guardado.
- Dentro de una petición siguen en segundo plano, sin demorar la respuesta del admin.

**Fuera del alcance:** una cola de tareas, reintentos, y el hilo de fondo que se corta si
un proceso web se reinicia justo durante la generación (`orion_generate_renditions` y la
generación al mostrar la página ya cubren ese caso).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `image-library`: las variantes están completas al terminar un comando.

## Impact

- **Código:** `orion.core.image_library`.
- **Dependencias y migraciones:** ninguna.
- **Comandos que guardan imágenes:** tardan más, porque esperan las variantes.
