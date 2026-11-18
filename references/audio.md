---
title: Audio y reproductores
description: Cómo se convierte un guion en algo escuchable. Dos motores en uso (voz del navegador y Piper a MP3), por qué el navegador no puede exportar su propia voz, qué costaría hacerlo con un motor WASM, y las reglas del guion hablado.
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

Tampoco sirve capturar la pestaña. La captura de audio de pestaña (`getDisplayMedia({audio: true})`) recoge el
audio del grafo de la pestaña, y en Chromium la voz sintetizada no pasa por ahí: sale por el motor de voz del
sistema, fuera de la pestaña. Está documentado en el informe
[40753195](https://issues.chromium.org/issues/40753195), abierto desde 2021. Solo la captura de **pantalla
completa con audio del sistema** recoge esa voz, y eso obliga a compartir el escritorio, mezcla el resto de
sonidos y depende del sistema operativo.

Y aunque se capturase, no saldría un MP3: `MediaRecorder` entrega WebM/Opus, y **ningún navegador codifica MP3**
(`AudioEncoder` con `mp3` tiene 0 % de soporte en la tabla de WebCodecs; solo decodifica). Convertirlo exige una
biblioteca JavaScript de terceros.

Consecuencia práctica: si el usuario pide «un MP3», se genera con Piper. Si pide «escucharlo», la página vale y
es instantánea.

### La tercera vía: MP3 con un motor dentro de la página

Sí existe una forma de generar audio —y MP3— dentro de una página: **no usar la voz del sistema, sino un motor
de síntesis compilado a WebAssembly**. Proyectos como `piper-tts-web` (MIT) devuelven un WAV listo para
descargar, y con un codificador JavaScript (`lamejs`) se convierte en MP3.

Lo que cuesta, medido con las cifras publicadas por esos proyectos:

| Pieza | Tamaño | Nota |
|---|---|---|
| Voz Piper (`.onnx` + `.json`) | 30–75 MB | Una por idioma, caché del navegador |
| `onnxruntime-web` | ~10 MB | Motor de inferencia |
| Datos de espeak-ng | ~17 MB | Fonemización |
| Codificador MP3 en JS | ~150 KB | Necesario: el navegador no codifica MP3 |

Dos consecuencias que lo aplazan, no que lo hagan imposible:

1. **No ahorra la instalación, la cambia de sitio.** La primera vez hay que bajar ~90 MB, y no se puede cachear
   si la página se abre con `file://`: ese origen es opaco y el navegador no le da almacenamiento persistente.
   Hace falta servirla por `http://localhost`, o sea, un servidor estático.
2. **Es más lento y peor voz que la del sistema.** La inferencia en CPU va a 3–5× el tiempo real; la página
   actual es instantánea y usa la voz que el usuario ya tiene instalada.

Por eso la página de escucha no lleva botón de descarga: un botón que solo funciona en la mitad de los casos y
tras una descarga de 90 MB es peor que decir la verdad. La ruta WASM queda como puerta abierta para un modo sin
Python, no como función de esta página. Si algún día se implementa, va como página aparte y con su propio
contrato: aviso de tamaño, caché en origen `http` y MP3 opcional.

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
| No hay botón de descarga en la página | Es deliberado: el navegador no captura su voz ni codifica MP3 | Generar el MP3 con Piper |
