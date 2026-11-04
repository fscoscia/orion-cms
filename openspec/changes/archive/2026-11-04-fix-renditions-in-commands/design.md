## Context

Ver `proposal.md`. `schedule_renditions` lanza un hilo `daemon` en cada guardado.
`Image.get_renditions` usa a su vez un `ThreadPoolExecutor`.

## Goals / Non-Goals

**Goals:** que ningún guardado fuera de una petición dependa de un hilo que el proceso
puede matar.

**Non-Goals:** cambiar cómo se generan las variantes dentro de una petición.

## Decisions

### Decidir por si hay una petición en curso

Los receptores de `request_started` y `request_finished` marcan en un `threading.local`
si el hilo atiende una petición. `schedule_renditions` usa el hilo de fondo solo entonces;
si no, genera en el momento. `ORION_IMAGE_RENDITIONS_IN_BACKGROUND = False` sigue forzando
la generación en el momento.

Alternativas descartadas:

- Hilo no `daemon`: Python ejecuta el cierre de `concurrent.futures` antes de esperar a
  esos hilos, así que el `ThreadPoolExecutor` seguiría rechazando trabajo.
- Apagar el ajuste en cada comando: obliga a cada proyecto a recordarlo, y el error es
  silencioso.
- Mirar `sys.argv`: depende de cómo se lance el proceso.

## Risks / Trade-offs

- [Un comando que guarda muchas imágenes tarda más] → es el costo de que queden completas;
  antes ese trabajo se perdía.
