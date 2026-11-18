# speak-summary — notas de instalación local

Skill de [github/awesome-copilot](https://github.com/github/awesome-copilot/blob/main/skills/speak-summary/SKILL.md)
adaptada para convertir guiones de estudio en audio. `SKILL.md` es el original; los cambios están en
`scripts/` y se explican aquí.

## Dos motores, y por qué

| Motor | Voces | Velocidad | Cuenta |
|---|---|---|---|
| **Piper** (por defecto aquí) | Voces neuronales por idioma | Muy por encima del tiempo real | Ninguna |
| `pocket-tts` (upstream) | Multilingüe, catálogo corto | Similar o más lento | Clonación con login |

Piper gana para estudiar: voz del idioma del perfil, sin registro, modelos pequeños y rápidos en CPU.
`pocket-tts` queda disponible con `SPEAK_ENGINE=pocket`.

La tercera vía —y la que no instala nada— es la **página de escucha** que genera
`scripts/opositor.py tts-page`: usa la voz del navegador y sirve para repasar, pero no produce archivos.

## Dónde vive cada cosa

| Pieza | Ruta |
|---|---|
| Entorno de Piper | `~/.cache/opositor/piper-venv` |
| Modelos de voz (`.onnx` + `.json`) | `~/.cache/opositor/voices` |
| Entorno de `pocket-tts` | `~/.cache/speak-summary/venv` |
| Estado de la vigilancia de voces | `~/.cache/opositor/voice-watch` |

## Preparar el motor

Lo hace la skill `setup`, no el usuario. A mano sería:

```bash
python3 -m venv ~/.cache/opositor/piper-venv
~/.cache/opositor/piper-venv/bin/python -m pip install piper-tts
```

Hace falta además `ffmpeg` para escribir MP3 (sin él, el script deja un WAV). Los modelos de voz se
descargan del catálogo de Piper y se dejan en el directorio de voces con su `.json` al lado.

## Uso

```bash
skills/speak-summary/scripts/tts.sh entrada.txt salida.mp3
skills/speak-summary/scripts/tts.sh entrada.txt salida.mp3 es_ES-davefx-medium
SPEAK_PIPER_LANG=fr skills/speak-summary/scripts/tts.sh entrada.txt salida.mp3
SPEAK_ENGINE=pocket skills/speak-summary/scripts/tts.sh entrada.txt salida.mp3
```

El flujo correcto es **reescribir para el oído → sintetizar**, no volcar el texto escrito tal cual. Las
reglas del guion están en `references/audio.md`.

## Elegir voz

- El idioma sale de `SPEAK_PIPER_LANG` (por defecto `es`), que `setup` fija con el idioma del perfil.
- Una voz concreta se pasa como tercer argumento o con `SPEAK_PIPER_VOICE`.
- Si el directorio tiene varias voces del mismo idioma, gana la primera por orden alfabético. Ordénalas
  renombrándolas si quieres controlar cuál es la de por defecto.

## Ritmo

Piper genera muy por encima del tiempo real en CPU: un resumen de 20 minutos tarda menos de un minuto.
`pocket-tts` es notablemente más lento; úsalo solo si buscas su timbre.

## Vigilancia de voces nuevas (opcional)

`scripts/voice-watch.py` compara el catálogo con la última pasada y avisa si aparece algo nuevo. No descarga
ni instala nada. Se puede programar con systemd de usuario, cron o el planificador del sistema:

```bash
python3 skills/speak-summary/scripts/voice-watch.py --status
python3 skills/speak-summary/scripts/voice-watch.py
```

## Encadenar con la skill principal

Patrón útil: `opositor` (buscar fuentes o generar examen) → guion hablado → `speak-summary` → MP3 para el
coche o el paseo. Si el usuario solo quiere escuchar, la página de escucha es más rápida y no depende de
Piper.
