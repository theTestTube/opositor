---
title: Opositor
description: Skill agnóstica para preparar cualquier oposición. El repositorio solo contiene el método; el temario y los materiales de cada oposición viven fuera del control de versiones.
idioma: es-ES
---

# Opositor

Skill para estudiar una oposición con material abierto: busca fuentes por tema, las puntúa y las ordena,
y si se lo piden prepara un examen tipo test en PDF y un resumen hablado.

No está atada a ninguna oposición concreta. **La oposición y su temario son el primer parámetro**: el
repositorio guarda el método (cómo buscar, cómo puntuar, cómo examinar, cómo sonar) y cada oposición aporta
sus datos en una carpeta propia que no se versiona.

## Instalación

```bash
git clone https://github.com/theTestTube/opositor.git ~/Code/opositor
ln -s ~/Code/opositor ~/.claude/skills/opositor        # Claude Code
# OpenCode y otros clientes: apunta al SKILL.md de la carpeta o a ~/.claude/skills
```

Requisitos: `python3` (3.10 o superior). Nada más es obligatorio: el PDF necesita `reportlab` y el MP3
necesita Piper, pero ambos son opcionales y la skill los prepara por ti.

## Primer uso

Pide en lenguaje natural: «prepárate» o «crea la oposición X». La skill `setup` diagnostica el entorno,
instala lo que falte en un `.venv` del repositorio y crea `oposiciones/x/` con el mismo esqueleto que tenía la
skill original: `config.json`, `temario.md`, `perfil.md`, `fuentes.md` y `materiales/`.

Tú no ejecutas comandos. Si algo no se puede instalar sin privilegios, te lo dirá en una línea y seguirá con
la degradación más cercana (por ejemplo, fuentes y página de escucha funcionando, MP3 no).

Después: «temas 3 y 4 de x», «examen difícil del tema 7», «resumen para escuchar del tema 9».

## Estructura

```
SKILL.md                  Método completo (pasos 0–13)
references/               Núcleo transversal y versionado (esquema y método)
  _index.md               Mapa de capas y la decisión sobre `references`
  temario.md              Cómo leer y validar un temario
  fuentes.md              Niveles de autoridad y protocolo de búsqueda
  perfil.md               Cómo documentar el puesto y el formato del ejercicio
  alta.md                 Cómo dar de alta una oposición nueva
  audio.md                Motores de audio y su viabilidad
  plantillas/             Esqueletos que usa `init`
scripts/
  opositor.py             init · check · path · tts-page · doctor
  examen_pdf.py           Banco JSON → PDF
  tts_page.py             Guion → página de escucha con la voz del navegador
skills/
  setup/                  Prepara entorno y perfiles (lo ejecuta el agente)
  speak-summary/          Síntesis local a MP3 (Piper), reutilizada
oposiciones/              Datos por oposición — fuera de git
```

## Privacidad

`oposiciones/` y `.scratchpad/` están en `.gitignore`. Nada de lo que escribas ahí (temario, apuntes,
exámenes, audios, nombres de la administración convocante) puede acabar en el repositorio.

El núcleo versionado no menciona ninguna oposición concreta. Para comprobarlo:

```bash
printf '%s\n' "término1" "término2" > oposiciones/.privacidad.txt
python3 scripts/opositor.py check --privacidad
```

La lista de términos vive en la zona no versionada: la comprobación se ejecuta sin que el repositorio
llegue a nombrar lo que protege.

## Idioma

- La `description` del frontmatter de `SKILL.md` va **siempre en inglés (en-US)**: es lo que leen los
  enrutadores de skills.
- Los documentos (`references/`, `materiales/` y las salidas) van en el **idioma nativo del usuario**,
  el que declare `config.json → idioma` (por defecto `es-ES`).
