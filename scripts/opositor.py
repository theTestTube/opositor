#!/usr/bin/env python3
"""CLI de la skill opositor. Solo biblioteca estándar.

Uso:
    python3 scripts/opositor.py init <slug> --nombre "..." --ambito "..." [--idioma es-ES]
    python3 scripts/opositor.py check [<slug>] [--privacidad]
    python3 scripts/opositor.py path [<slug>] [--json]
    python3 scripts/opositor.py tts-page <guion.txt> <salida.html> [--titulo T] [--lang es]
    python3 scripts/opositor.py tts-page --demo <salida.html>
    python3 scripts/opositor.py doctor

La raíz de datos es $OPOSITOR_DATA o, si no está definida, <repo>/oposiciones.
Todo lo que se escribe ahí queda fuera del control de versiones.
"""
import argparse
import json
import os
import re
import shutil
import sys
import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLAS = RAIZ / "references" / "plantillas"
IGNORADOS = {".git", "oposiciones", ".scratchpad", "__pycache__", ".venv", "node_modules"}


def raiz_datos() -> Path:
    return Path(os.environ.get("OPOSITOR_DATA") or RAIZ / "oposiciones").expanduser()


def perfil(slug: str) -> Path:
    return raiz_datos() / slug


def perfiles():
    base = raiz_datos()
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith("."))


def resolver_slug(slug):
    if slug:
        return slug
    disponibles = perfiles()
    if len(disponibles) == 1:
        return disponibles[0]
    if not disponibles:
        sys.exit("No hay ningún perfil. Créalo con: opositor.py init <slug> …")
    sys.exit("Hay varios perfiles; indica cuál: " + ", ".join(disponibles))


def leer_config(slug):
    ruta = perfil(slug) / "config.json"
    if not ruta.is_file():
        sys.exit(f"Falta {ruta}. ¿Está bien el slug?")
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"config.json no es JSON válido: {e}")


def marcadores(texto):
    return sorted(set(re.findall(r"\{\{\s*([a-z0-9_]+)\s*\}\}", texto)))


def contar_temas(texto):
    """Temas reales: encabezados ### cuyo título ya no es un marcador de plantilla."""
    return len([m for m in re.finditer(r"^###\s+(.+)$", texto, re.M) if "{{" not in m.group(1)])


def render(nombre_plantilla, valores):
    texto = (PLANTILLAS / nombre_plantilla).read_text(encoding="utf-8")
    for clave, valor in valores.items():
        texto = texto.replace("{{" + clave + "}}", valor)
    return texto


def cmd_init(args):
    slug = args.slug
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        sys.exit("Slug no válido: minúsculas, números y guiones (ej. mi-oposicion).")
    destino = perfil(slug)
    if destino.exists():
        sys.exit(f"Ya existe {destino}. Usa check para revisarlo o elige otro slug.")

    for sub in ("materiales/propios", "materiales/terceros", "materiales/generados/audio"):
        (destino / sub).mkdir(parents=True, exist_ok=True)

    hoy = datetime.date.today().isoformat()
    comun = {"slug": slug, "nombre": args.nombre, "ambito": args.ambito, "idioma": args.idioma}
    config = {
        "slug": slug,
        "nombre": args.nombre,
        "ambito": args.ambito,
        "idioma": args.idioma,
        "creado": hoy,
        "bloques": [{"nombre": "Materias comunes", "prefijo": "C"},
                    {"nombre": "Materias específicas", "prefijo": "E"}],
        "sinonimos_puesto": [],
        "pdf": {"textos": {}},
        "audio": {"motor": "navegador", "lang": args.idioma.split("-")[0].lower()},
    }
    (destino / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    (destino / "temario.md").write_text(render("temario.md", comun), encoding="utf-8")
    (destino / "perfil.md").write_text(render("perfil.md", comun), encoding="utf-8")
    (destino / "fuentes.md").write_text(render("fuentes.md", comun), encoding="utf-8")
    (destino / "materiales" / "LEEME.md").write_text(render("materiales-LEEME.md", comun), encoding="utf-8")
    (destino / "log.md").write_text(
        f"# Registro de {args.nombre}\n\n## [{hoy}] alta | Perfil creado con el esqueleto vacío\n",
        encoding="utf-8")

    print(f"Perfil creado: {destino}")
    print("Siguiente paso: rellenar temario.md con el programa oficial, perfil.md con la norma del puesto")
    print("y fuentes.md con los dominios; después, `opositor.py check " + slug + "`.")


def cmd_check(args):
    errores, avisos = [], []
    slug = args.slug

    if not slug:
        disponibles = perfiles()
        if len(disponibles) == 1:
            slug = disponibles[0]
        elif not args.privacidad:
            resolver_slug(None)  # sin perfil único y sin privacidad, no hay nada que validar

    if slug:
        base = perfil(slug)
        if not base.is_dir():
            sys.exit(f"No existe el perfil {base}")

        try:
            config = leer_config(slug)
        except SystemExit as e:
            print(e)
            return 1
        for campo in ("slug", "nombre", "ambito", "idioma"):
            if not str(config.get(campo, "")).strip():
                errores.append(f"config.json: falta «{campo}»")

        esperados = {
            "temario.md": ("temario", contar_temas, 1),
            "perfil.md": ("perfil del puesto", None, None),
            "fuentes.md": ("fuentes", None, None),
            "materiales/LEEME.md": ("inventario de materiales", None, None),
        }
        for rel, (etiqueta, medidor, minimo) in esperados.items():
            ruta = base / rel
            if not ruta.is_file():
                errores.append(f"falta {rel} ({etiqueta})")
                continue
            texto = ruta.read_text(encoding="utf-8")
            pendientes = marcadores(texto)
            if pendientes:
                avisos.append(f"{rel}: {len(pendientes)} marcador(es) sin rellenar: "
                              + ", ".join(pendientes[:6]))
            if medidor and medidor(texto) < minimo:
                errores.append(f"{rel}: no se detecta ningún tema (### …)")

        fuentes = base / "fuentes.md"
        if fuentes.is_file() and "http" not in fuentes.read_text(encoding="utf-8"):
            avisos.append("fuentes.md: no hay ninguna URL de partida")

        perfil_txt = base / "perfil.md"
        if perfil_txt.is_file():
            t = perfil_txt.read_text(encoding="utf-8")
            if "Definición literal" not in t:
                avisos.append("perfil.md: falta la sección «Definición literal»")
            if re.search(r"Comprobado[^\n]*\{\{", t):
                avisos.append("perfil.md: falta la fecha de comprobación")

        temas = (contar_temas((base / "temario.md").read_text(encoding="utf-8"))
                 if (base / "temario.md").is_file() else 0)
        print(f"Perfil: {base}")
        print(f"Temas detectados: {temas}")
        for e in errores:
            print(f"  ✗ {e}")
        for a in avisos:
            print(f"  · {a}")
        if not errores and not avisos:
            print("  ✓ Perfil completo")

    if args.privacidad:
        errores += revisar_privacidad()
    return 1 if errores else 0


def archivos_versionados():
    try:
        salida = __import__("subprocess").run(["git", "-C", str(RAIZ), "ls-files"],
                                             capture_output=True, text=True, check=True).stdout
        archivos = [RAIZ / linea for linea in salida.splitlines() if linea.strip()]
        if archivos:
            return archivos
    except Exception:
        pass
    # Sin git o sin archivos rastreados todavía: se revisa el árbol, menos lo ignorado.
    return [p for p in RAIZ.rglob("*")
            if p.is_file() and not (set(p.relative_to(RAIZ).parts) & IGNORADOS)]


def coincide(termino, texto):
    """Los términos cortos se buscan como palabra completa para no marcar siglas dentro de otra palabra."""
    t = termino.strip()
    if len(t) <= 8 and " " not in t:
        return re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texto, re.I) is not None
    return t.lower() in texto.lower()


def revisar_privacidad():
    lista = raiz_datos() / ".privacidad.txt"
    if not lista.is_file():
        print(f"  · privacidad: no hay lista de términos en {lista}; nada que comprobar")
        return []
    terminos = [t.strip() for t in lista.read_text(encoding="utf-8").splitlines()
                if t.strip() and not t.startswith("#")]
    if not terminos:
        return []
    hallazgos = []
    for ruta in archivos_versionados():
        if not ruta.is_file() or ruta.suffix.lower() in {".pdf", ".png", ".jpg", ".mp3", ".wav"}:
            continue
        try:
            texto = ruta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for termino in terminos:
            if coincide(termino, texto):
                hallazgos.append(f"privacidad: «{termino}» aparece en "
                                 f"{ruta.relative_to(RAIZ)}")
    if hallazgos:
        print("  ✗ Fuga de términos privados en archivos versionados:")
        for h in hallazgos:
            print(f"    {h}")
    else:
        print(f"  ✓ Privacidad: {len(terminos)} término(s) buscados en "
              f"{len(archivos_versionados())} archivo(s) versionado(s), sin coincidencias")
    return hallazgos


def cmd_path(args):
    slug = resolver_slug(args.slug)
    base = perfil(slug)
    if not base.is_dir():
        sys.exit(f"No existe el perfil {base}")
    datos = {
        "perfil": str(base),
        "config": str(base / "config.json"),
        "temario": str(base / "temario.md"),
        "perfil_puesto": str(base / "perfil.md"),
        "fuentes": str(base / "fuentes.md"),
        "materiales": str(base / "materiales"),
        "generados": str(base / "materiales" / "generados"),
        "audio": str(base / "materiales" / "generados" / "audio"),
        "propios": str(base / "materiales" / "propios"),
        "terceros": str(base / "materiales" / "terceros"),
    }
    if args.json:
        print(json.dumps(datos, ensure_ascii=False, indent=2))
    else:
        for clave, valor in datos.items():
            print(f"{clave}: {valor}")


def cmd_tts_page(args):
    sys.path.insert(0, str(RAIZ / "scripts"))
    from tts_page import build_page

    if args.demo:
        texto = ("Prueba de voces. Si estás oyendo esto, el navegador tiene al menos una voz "
                 "instalada y la página funciona. Cambia de voz y de velocidad con los controles.")
        titulo = args.titulo or "Prueba de voces del navegador"
    else:
        if not args.texto:
            sys.exit("Falta el guion: opositor.py tts-page <guion.txt> <salida.html>")
        origen = Path(args.texto)
        if not origen.is_file():
            sys.exit(f"No existe el guion: {origen}")
        texto = origen.read_text(encoding="utf-8")
        titulo = args.titulo or origen.stem

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(build_page(texto, titulo, args.lang), encoding="utf-8")
    palabras = len(texto.split())
    print(f"{salida}: {palabras} palabras ≈ {round(palabras / 167)} min a 167 ppm")
    print("Ábrelo en Edge, Chrome, Firefox o Brave. Si no hay voces, la página lo dirá.")


def cmd_doctor(args):
    def estado(ok, detalle=""):
        return f"{'✓' if ok else '✗'} {detalle}".strip()

    print(f"Repositorio: {RAIZ}")
    print(f"Datos: {raiz_datos()}")
    v = sys.version_info
    print(estado(v >= (3, 10), f"Python {v.major}.{v.minor}.{v.micro}"))
    try:
        import reportlab
        print(estado(True, f"reportlab {reportlab.Version} (PDF disponible)"))
    except ImportError:
        print(estado(False, "reportlab ausente → ejecuta skills/setup, paso 1"))
    for binario in ("ffmpeg", "ffprobe", "piper"):
        ruta = shutil.which(binario)
        print(estado(bool(ruta), f"{binario}: {ruta or 'no encontrado'}"))
    voces = Path.home() / ".cache" / "opositor" / "voices"
    n = len(list(voces.glob("*.onnx"))) if voces.is_dir() else 0
    print(estado(bool(n), f"voces Piper: {n} en {voces}"))
    navegadores = [b for b in ("microsoft-edge", "google-chrome", "chromium", "brave-browser", "firefox")
                   if shutil.which(b)]
    print(estado(bool(navegadores),
                 "navegadores: " + (", ".join(navegadores) or "ninguno → página de escucha no verificable")))
    disponibles = perfiles()
    print(estado(bool(disponibles), "perfiles: " + (", ".join(disponibles) or "ninguno")))
    print("\nEl MP3 y el PDF son opcionales. Sin ellos: fuentes sí, examen degradado, audio por navegador.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="crea oposiciones/<slug>/ desde las plantillas")
    p.add_argument("slug")
    p.add_argument("--nombre", required=True)
    p.add_argument("--ambito", required=True)
    p.add_argument("--idioma", default="es-ES")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("check", help="valida un perfil y, si se pide, la privacidad del núcleo")
    p.add_argument("slug", nargs="?")
    p.add_argument("--privacidad", action="store_true")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("path", help="rutas resueltas del perfil")
    p.add_argument("slug", nargs="?")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_path)

    p = sub.add_parser("tts-page", help="genera la página de escucha del navegador")
    p.add_argument("texto", nargs="?")
    p.add_argument("salida")
    p.add_argument("--titulo")
    p.add_argument("--lang", default="es")
    p.add_argument("--demo", action="store_true", help="texto de prueba para comprobar las voces")
    p.set_defaults(func=cmd_tts_page)

    p = sub.add_parser("doctor", help="estado del entorno")
    p.set_defaults(func=cmd_doctor)

    args = ap.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
