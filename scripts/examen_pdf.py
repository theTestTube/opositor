#!/usr/bin/env python3
"""Genera el PDF de un examen tipo test a partir de un banco de preguntas en JSON.

Uso:
    python3 examen_pdf.py banco.json <perfil>/materiales/generados/E7_examen_test.pdf \
        [--perfil <perfil>/config.json] [--difficulty low|high]

Formato del banco (UTF-8):
{
  "codigo": "E7",
  "titulo": "Enunciado del tema tal como figura en el temario",
  "dificultad": "low",
  "nota": "Texto opcional bajo la cabecera (avisos de vigencia, etc.)",
  "semilla": 7,
  "bloques": [
    {"titulo": "Bloque 1. …",
     "supuesto": "Opcional: caso práctico común a todas las preguntas del bloque",
     "preguntas": [{"q": "Enunciado", "ok": "Respuesta correcta",
                    "mal": ["Distractor 1", "Distractor 2", "Distractor 3"]}]}
  ],
  "fuentes": [{"titulo": "Entidad – Título", "url": "https://…", "abierta": true}]
}

El nombre de la oposición, el ámbito y los textos del documento salen del perfil
(`config.json → nombre, ambito, pdf.textos`). Sin perfil, se usan los textos por defecto en español.

La dificultad sale de --difficulty o, si falta, del campo "dificultad" del banco (por defecto, low).
Solo cambia la cabecera del PDF: el nivel real lo dan las preguntas del banco (ver SKILL.md, §9).
Un bloque con "supuesto" imprime el caso en un recuadro antes de sus preguntas.

El script baraja las opciones y reparte la letra correcta de forma equilibrada.
Las preguntas salen sin ninguna marca, para hacer el test sin ver las respuestas.
Después van las fuentes y, como sección final en página aparte, las soluciones:
una plantilla rápida y la respuesta completa de cada pregunta. Solo necesita reportlab
(si falta, ejecuta skills/setup, paso 1).
"""
import argparse
import json
import os
import random
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

LETRAS = "abcd"
VERDE, AZUL, GRIS = "#1b7a3a", colors.HexColor("#1f3a5f"), colors.HexColor("#444444")

TEXTOS = {
    "cabecera": "Examen tipo test · Tema {codigo}",
    "contexto": "{total} preguntas, una sola respuesta válida · Dificultad {dificultad}. "
                "Las soluciones están en la última sección, en página aparte.",
    "fuentes": "Fuentes de estudio del tema",
    "aviso": "Preguntas de práctica elaboradas para este tema; no proceden de exámenes oficiales. "
             "Contrasta los datos con la fuente original antes del examen.",
    "soluciones": "Soluciones",
    "reparto": "Reparto de la respuesta correcta: {reparto}",
    "pie": "Tema {codigo}",
    "meta_titulo": "Examen tipo test · Tema {codigo} · dificultad {dificultad}",
    "meta_autor": "{nombre}",
    "dificultades": {"low": "baja", "high": "alta"},
}


def cargar_perfil(ruta):
    """Devuelve (nombre, ambito, textos). Sin perfil, todo vacío y textos por defecto."""
    textos = {k: v for k, v in TEXTOS.items()}
    textos["dificultades"] = dict(TEXTOS["dificultades"])
    if not ruta:
        return "", "", textos
    with open(ruta, encoding="utf-8") as f:
        config = json.load(f)
    propios = config.get("pdf", {}).get("textos", {})
    for clave, valor in propios.items():
        if clave == "dificultades":
            textos["dificultades"].update(valor)
        else:
            textos[clave] = valor
    return config.get("nombre", ""), config.get("ambito", ""), textos


def fuentes_tipograficas():
    """DejaVu cubre marcas y acentos; si no está, usa Helvetica y una marca ASCII."""
    for base in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/"):
        if os.path.exists(base + "DejaVuSans.ttf"):
            pdfmetrics.registerFont(TTFont("DV", base + "DejaVuSans.ttf"))
            pdfmetrics.registerFont(TTFont("DVB", base + "DejaVuSans-Bold.ttf"))
            pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB")
            return "DV", "DVB", "✔"
    return "Helvetica", "Helvetica-Bold", "(correcta)"


def validar(banco, dificultad):
    errores = []
    if dificultad not in TEXTOS["dificultades"]:
        errores.append(f"Dificultad desconocida: {dificultad} (usa low o high)")
    if dificultad == "high" and not any(b.get("supuesto") for b in banco["bloques"]):
        print("Aviso: dificultad high sin ningún bloque con supuesto práctico.", file=sys.stderr)
    for b in banco["bloques"]:
        for p in b["preguntas"]:
            opciones = [p["ok"], *p["mal"]]
            if len(p["mal"]) != 3:
                errores.append(f"Necesita 3 distractores: {p['q'][:60]}")
            if len({o.strip().lower() for o in opciones}) != len(opciones):
                errores.append(f"Opciones repetidas: {p['q'][:60]}")
    if errores:
        sys.exit("Banco no válido:\n- " + "\n- ".join(errores))


def main(ruta_banco, ruta_pdf, dificultad=None, ruta_perfil=None):
    if not os.path.isfile(ruta_banco):
        sys.exit(f"No existe el banco de preguntas: {ruta_banco}")
    with open(ruta_banco, encoding="utf-8") as f:
        banco = json.load(f)
    dificultad = dificultad or banco.get("dificultad", "low")
    validar(banco, dificultad)
    nombre, ambito, textos = cargar_perfil(ruta_perfil)
    etiqueta = textos["dificultades"][dificultad]
    normal, negrita, marca = fuentes_tipograficas()

    s_tit = ParagraphStyle("t", fontName=negrita, fontSize=15, leading=19, textColor=AZUL, spaceAfter=4)
    s_sub = ParagraphStyle("s", fontName=normal, fontSize=9.5, leading=13, textColor=GRIS)
    s_blq = ParagraphStyle("b", fontName=negrita, fontSize=11.5, leading=15, textColor=AZUL,
                           spaceBefore=10, spaceAfter=6)
    s_q = ParagraphStyle("q", fontName=negrita, fontSize=9.5, leading=12.5, spaceAfter=2)
    s_o = ParagraphStyle("o", fontName=normal, fontSize=9.2, leading=12, leftIndent=14)
    s_sol = ParagraphStyle("sol", fontName=normal, fontSize=8.8, leading=11.5, spaceAfter=1.5,
                           leftIndent=16, firstLineIndent=-16)
    s_src = ParagraphStyle("src", fontName=normal, fontSize=8.6, leading=11.5, spaceAfter=5,
                           leftIndent=12, firstLineIndent=-12)
    s_caso = ParagraphStyle("caso", fontName=normal, fontSize=9.2, leading=12.5)

    total = sum(len(b["preguntas"]) for b in banco["bloques"])
    rng = random.Random(banco.get("semilla", 7))
    posiciones = [i % 4 for i in range(total)]
    rng.shuffle(posiciones)

    codigo = banco["codigo"]
    contexto = " · ".join(x for x in (nombre, ambito) if x)
    contexto = (contexto + " · " if contexto else "") + textos["contexto"].format(
        total=total, dificultad=etiqueta)
    story = [Paragraph(textos["cabecera"].format(codigo=escape(codigo)), s_tit),
             Paragraph(escape(banco["titulo"]), s_sub), Spacer(1, 3),
             Paragraph(contexto, s_sub)]
    if banco.get("nota"):
        story += [Spacer(1, 3), Paragraph(escape(banco["nota"]), s_sub)]

    # 1. Preguntas, sin ninguna marca de la respuesta correcta.
    clave, soluciones, rangos, n = [], [], [], 0
    for bloque in banco["bloques"]:
        inicio = n + 1
        # El título, el supuesto y la primera pregunta van juntos para no quedar separados entre páginas.
        cabecera = [Paragraph(escape(bloque["titulo"]), s_blq)]
        if bloque.get("supuesto"):
            caso = Table([[Paragraph(f"<b>Supuesto.</b> {escape(bloque['supuesto'])}", s_caso)]],
                         colWidths=[A4[0] - 36 * mm])
            caso.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f6fa")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#9aa7b8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            cabecera += [caso, Spacer(1, 7)]
        for p in bloque["preguntas"]:
            n += 1
            pos = posiciones[n - 1]
            opciones = list(p["mal"])
            rng.shuffle(opciones)
            opciones.insert(pos, p["ok"])
            clave.append(LETRAS[pos])
            soluciones.append((n, LETRAS[pos], p["ok"]))
            partes = [Paragraph(f"{n}. {escape(p['q'])}", s_q)]
            partes += [Paragraph(f"{LETRAS[i]}) {escape(t)}", s_o) for i, t in enumerate(opciones)]
            partes.append(Spacer(1, 5))
            story.append(KeepTogether(cabecera + partes))
            cabecera = []
        rangos.append((bloque["titulo"], inicio, n))

    # 2. Fuentes de estudio.
    fuentes = banco.get("fuentes", [])
    if fuentes:
        story += [PageBreak(), Paragraph(textos["fuentes"], s_tit), Spacer(1, 4)]
        for i, fte in enumerate(fuentes, 1):
            estado = "" if fte.get("abierta", True) else " <i>(no abierta)</i>"
            story.append(Paragraph(
                f"{i}. <b>{escape(fte['titulo'])}</b>{estado}<br/>"
                f"<font color='#1f3a5f'><link href='{escape(fte['url'])}'>{escape(fte['url'])}</link></font>",
                s_src))
    story += [Spacer(1, 8), Paragraph(textos["aviso"], s_sub)]

    # 3. Soluciones: plantilla rápida y respuesta completa de cada pregunta, al final del documento.
    story += [PageBreak(), Paragraph(textos["soluciones"], s_tit), Spacer(1, 6)]
    columnas = (total + 9) // 10
    filas = [[f"{c * 10 + r + 1}. {clave[c * 10 + r]}" if c * 10 + r < total else ""
              for c in range(columnas)] for r in range(min(10, total))]
    tabla = Table(filas, colWidths=[17 * mm] * columnas, rowHeights=7 * mm)
    tabla.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), normal, 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa7b8")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f6fa"))]))
    reparto = " · ".join(f"{l}) {clave.count(l)}" for l in LETRAS)
    story += [tabla, Spacer(1, 4), Paragraph(textos["reparto"].format(reparto=reparto), s_sub)]
    for titulo, ini, fin in rangos:
        story.append(Paragraph(f"{escape(titulo)} (preguntas {ini}–{fin})", s_blq))
        for num, letra, texto in soluciones[ini - 1:fin]:
            story.append(Paragraph(f"<b>{num}. {letra})</b> {escape(texto)} "
                                   f"<font color='{VERDE}'>{marca}</font>", s_sol))

    pie_texto = textos["pie"].format(codigo=codigo)
    if contexto_pie := " · ".join(x for x in (nombre, ambito) if x):
        pie_texto = f"{contexto_pie} · {pie_texto}"

    def pie(c, d):
        c.saveState()
        c.setFont(normal, 7.5)
        c.setFillColor(colors.HexColor("#777777"))
        c.drawString(18 * mm, 10 * mm, pie_texto)
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Página {d.page}")
        c.restoreState()

    os.makedirs(os.path.dirname(os.path.abspath(ruta_pdf)), exist_ok=True)
    doc = SimpleDocTemplate(ruta_pdf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=18 * mm,
                            title=textos["meta_titulo"].format(codigo=codigo, dificultad=etiqueta),
                            author=textos["meta_autor"].format(nombre=nombre or "opositor"),
                            subject=banco["titulo"])
    doc.build(story, onFirstPage=pie, onLaterPages=pie)
    print(f"{ruta_pdf}: {total} preguntas · dificultad {dificultad} · {reparto}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("banco", help="banco de preguntas en JSON")
    ap.add_argument("pdf", help="ruta del PDF de salida")
    ap.add_argument("--difficulty", choices=sorted(TEXTOS["dificultades"]),
                    help="low (por defecto) o high; si falta, se usa el campo 'dificultad' del banco")
    ap.add_argument("--perfil", help="config.json del perfil (nombre, ámbito y textos del documento)")
    args = ap.parse_args()
    main(args.banco, args.pdf, args.difficulty, args.perfil)
