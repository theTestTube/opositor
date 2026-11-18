---
name: setup
description: Prepare this repository and a new examination profile so the opositor skill can run without the user typing commands. Detects Python, the PDF library, audio engines and browser voices, installs only what is missing, scaffolds oposiciones/<slug>/, and reports what works and what degraded.
---

# Preparar el entorno

Esta skill la ejecuta **el agente**, no el usuario. El usuario pide («prepárate», «instala lo que falte»,
«crea la oposición X») y tú corres los comandos, compruebas el resultado y cuentas qué ha quedado.

Regla dura: **no pidas al usuario que ejecute comandos**. Si algo no se puede resolver sin privilegios, se
explica en una línea y se sigue con la degradación más cercana.

## 0. Diagnóstico antes de instalar

Ejecuta y guarda la salida:

```bash
python3 --version
python3 -c "import reportlab, sys; print('reportlab', reportlab.Version)" 2>&1 | tail -1
command -v ffmpeg ffprobe piper uv pipx
ls ~/.cache/opositor/voices 2>/dev/null
```

Interpretación:

| Señal | Significa | Acción |
|---|---|---|
| `python3` ≥ 3.10 | Base correcta | Seguir |
| `python3` < 3.10 | Sin soporte | Avisar: hay que actualizar el intérprete; el resto puede funcionar |
| `reportlab` importa | PDF disponible | Nada que hacer |
| `ModuleNotFoundError` | Falta PDF | Paso 1 |
| `ffmpeg` y `ffprobe` presentes | MP3 y verificación de duración | Nada que hacer |
| `piper` o voces en `~/.cache/opositor/voices` | MP3 sin depender del navegador | Nada que hacer |
| Nada de audio | Solo página de escucha del navegador | Es válido: es el modo por defecto |

**No asumas `uv`.** Está muy bien si aparece, pero el camino principal es `venv` + `pip` de la distribución.
Si tampoco hay `venv`, el camino es `pip install --user`, y si el sistema bloquea la instalación (PEP 668),
se queda en modo degradado y se dice.

## 1. PDF (opcional, pero necesario para exámenes)

Crea el entorno dentro del repositorio, que ya está ignorado por git:

```bash
python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip reportlab
```

Si `python3 -m venv` falla porque falta el módulo del sistema, prueba en este orden y para en el primero que
funcione:

1. `python3 -m venv --without-pip .venv` y luego `python3 -m ensurepip --upgrade` dentro del entorno.
2. `pip install --user reportlab` (sin entorno).
3. `uv venv .venv && uv pip install --python .venv/bin/python reportlab`, solo si `uv` existe.
4. `pipx` no sirve aquí: reportlab es una biblioteca, no una aplicación.

Si nada funciona, informa de que el examen saldrá en HTML o no saldrá, y sigue. **No instales paquetes del
sistema ni uses `sudo`** sin permiso explícito del usuario.

Comprueba siempre con el mismo intérprete que se usará después:

```bash
.venv/bin/python -c "import reportlab; print(reportlab.Version)"
```

Y recuerda al usuario, en la respuesta final, qué intérprete queda activo: `.venv/bin/python` o `python3`.

## 2. Audio

Hay dos caminos y **el de por defecto no instala nada**:

| Camino | Requisitos | Salida | Cuándo |
|---|---|---|---|
| Página de escucha | Solo un navegador con voces del sistema | HTML autocontenido | Por defecto |
| MP3 con Piper | `piper` + voces + `ffmpeg` | `.mp3` | Coche, móvil, compartir, sin navegador |

1. **Comprueba el navegador.** Genera una página de prueba y ábrela:

   ```bash
   python3 scripts/opositor.py tts-page --demo .scratchpad/prueba-voces.html
   ```

   La propia página lista las voces detectadas. Si dice «0 voces», explica el arreglo del sistema
   (`speech-dispatcher` en Linux; en Windows y macOS suele haber voces de serie) y ofrece el MP3.
2. **Instala Piper solo si el usuario quiere MP3.** Entorno propio, sin tocar el del PDF:

   ```bash
   python3 -m venv ~/.cache/opositor/piper-venv
   ~/.cache/opositor/piper-venv/bin/python -m pip install piper-tts
   ```

   Las voces van a `~/.cache/opositor/voices` (una por idioma del perfil). No descargues voces sin decir
   cuál y por qué.
3. **No prometas MP3 si no hay Piper.** La página de escucha no puede exportar audio: el navegador sintetiza
   y reproduce, no escribe archivos.

## 3. Alta de una oposición

Con el entorno listo, crea el perfil siguiendo `references/alta.md`:

```bash
python3 scripts/opositor.py init <slug> --nombre "<nombre>" --ambito "<administración>" [--idioma es-ES]
```

Luego rellena los archivos con datos oficiales (temario, perfil del puesto, fuentes y `materiales/LEEME.md`)
y valida:

```bash
python3 scripts/opositor.py check <slug>
```

Si el usuario ya tenía un perfil de una versión anterior, `check` es lo primero que se ejecuta: dice qué
campos faltan sin tocar nada.

## 4. Verificación final

```bash
python3 scripts/opositor.py doctor
python3 scripts/opositor.py check --privacidad
```

`doctor` resume intérprete, PDF, audio y perfiles detectados. `check --privacidad` compara los archivos
versionados con la lista local de términos y avisa de cualquier fuga antes de publicar.

## 5. Qué contesta el agente

Una tabla corta, sin jerga:

| Pieza | Estado | Cómo se usa |
|---|---|---|
| Python 3.x | ✅ / ⚠️ | |
| PDF (`reportlab`) | ✅ / ❌ | Examen en PDF o degradado |
| Página de escucha | ✅ | Se abre en el navegador |
| MP3 (`piper`) | ✅ / ❌ | Audio descargable |
| Perfil `<slug>` | ✅ / pendiente | |

Y una frase con el siguiente paso concreto. Nada de listas de comandos para copiar y pegar.

## Errores conocidos

- **`externally-managed-environment`** al instalar: es PEP 668. Usa entorno virtual; no lo fuerces con
  `--break-system-packages`.
- **`No module named venv`**: falta `python3-venv` en el sistema. Cae a `pip --user`.
- **La página de escucha no dice nada**: el navegador no tiene voces o el audio está silenciado. En Linux,
  `speech-dispatcher` y una voz instalada; en navegadores snap, la confinación puede bloquear el acceso.
- **Piper instala pero no encuentra el modelo**: la voz debe estar en el directorio de voces y con su `.json`
  al lado.
