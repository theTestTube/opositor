---
title: Audio y reproductores
description: Cómo se convierte un guion en algo escuchable. Dos motores (voz del navegador y Piper a MP3), qué puede y qué no puede hacer cada uno, y las reglas del guion hablado.
idioma: es-ES
capa: núcleo
---

# Audio y reproductores

Dos formas de escuchar un tema, con costes distintos. La de por defecto no instala nada.

| | Página de escucha | MP3 local (Piper) |
|---|---|---|
| Requisitos | Un navegador con voces | `piper`, voces y `ffmpeg` |
| Salida | HTML autocontenido | `.mp3` |
| Instalación | Ninguna | Entorno Python + descarga de voz |
| Voz | La del sistema, elegible | Modelo neuronal fijo |
| Sin conexión | Sí | Sí |
| Exportable | **No** | Sí |
| Uso típico | Repasar en el escritorio, seguir el guion | Coche, móvil, compartir |

## La página de escucha

```bash
python3 scripts/opositor.py tts-page guion.txt <perfil>/materiales/generados/audio/E7_resumen.html \
  --titulo "Tema E7 · Resumen"
```

Genera un HTML sin dependencias que se abre en Edge, Chrome, Firefox o Brave. Usa la **Web Speech API**
(`speechSynthesis`), que todos los navegadores de escritorio modernos implementan:

| Navegador | Voces | Nota |
|---|---|---|
| Edge | Sistema + voces en línea de alta calidad | Las voces en línea pueden requerir conexión |
| Chrome | Voces del sistema | En Linux pasa por `speech-dispatcher` |
| Brave | Voces de Chromium | Igual que Chrome; el modo lectura no sustituye a la página |
| Firefox | Voces del sistema | En Linux, sin `speech-dispatcher` puede quedarse sin voces |
| Safari | Voces del sistema | Funciona, con otra selección de voces |

La página trae selector de voz (filtrado por el idioma del perfil), velocidad, párrafo actual resaltado,
clic en un párrafo para empezar ahí y atajos de teclado. Si detecta cero voces, lo dice y propone el MP3.

### Lo que el navegador no puede hacer

**No se puede exportar el audio que sintetiza.** `speechSynthesis` reproduce directamente en el dispositivo de
salida; no expone un `MediaStream`, así que `MediaRecorder` no lo captura. La API `chrome.tts` sí puede entregar
trozos de audio, pero solo para extensiones y no en una página normal. Grabar la salida del sistema con un
dispositivo virtual es posible fuera del navegador, y no es portable: no se propone.

Consecuencia práctica: si el usuario pide «un MP3», se genera con Piper. Si pide «escucharlo», la página vale y
es instantánea.

### Comprobación de viabilidad

- **Chromium y Brave en modo headless devuelven cero voces** (no hay dispositivo de audio), así que la
  viabilidad no se puede verificar desde un agente sin interfaz. La página incluye su propio diagnóstico: al
  abrirla, muestra cuántas voces encuentra.
- **Linux:** el navegador habla con `speech-dispatcher`. Si no está instalado o el navegador va confinado
  (snap), la lista de voces puede salir vacía aunque el sistema tenga voces.
- **Windows y macOS:** las voces del sistema están disponibles de serie; es el caso más sencillo.

## MP3 con Piper

```bash
skills/speak-summary/scripts/tts.sh guion.txt <perfil>/materiales/generados/audio/E7_resumen_2026-11-15.mp3
```

- Un resumen de 20 minutos tarda menos de un minuto de CPU.
- Verifica duración y tamaño con `ffprobe`. Si se aleja de 20 minutos (menos de 18, más de 22), ajusta el
  guion y regenera.
- La voz se elige por idioma del perfil (`SPEAK_PIPER_LANG`, por defecto `es`). No inventes nombres de voz ni
  cambies la voz sin que el usuario lo pida.

## El guion

El guion es lo que hace útil al audio. Se escribe para el oído, no se lee de los apuntes.

- **Duración fija, densidad variable.** 20 minutos. En castellano, una voz de ~167 palabras por minuto da
  3.200–3.500 palabras. En otro idioma, mide una vez la velocidad de la voz elegida y ajusta el rango.
- **Sin marcas visuales.** Ni viñetas, ni tablas, ni código, ni URL. Nada que el oyente no pueda ver.
- **Apertura con orientación:** qué tema es, qué epígrafes cubre y cuánto dura.
- **Conectores explícitos:** «Primero…», «El punto delicado es…», «Para terminar…».
- **Siglas desarrolladas** la primera vez; cifras y fechas como se dicen.
- **Frases de menos de 25 palabras.** Un audio no se relee.
- **Cierre con lo que hay que retener** y una pregunta de repaso.
- **Reparto 80/20:** si hay material propio, su estructura y sus conceptos mandan; toda cifra se verifica en
  una fuente abierta antes de decirla en voz alta.

## Errores conocidos

| Síntoma | Causa | Arreglo |
|---|---|---|
| La página no suena | Cero voces | Instalar voces del sistema; usar MP3 |
| Suena en otro idioma | Voz por defecto del sistema | Elegir voz en el selector |
| Se corta a media frase | Párrafo demasiado largo | Párrafos más cortos en el guion |
| Pronuncia mal un nombre | Grafía opaca | Escribirlo fonéticamente en el guion |
| El MP3 dura 12 minutos | Guion corto | Ampliar contenido, no estirar el relleno |
