#!/usr/bin/env python3
"""Build a multiple-choice practice exam PDF from a JSON question bank.

Usage:
    python3 exam_pdf.py bank.json <profile>/materials/generated/E7_practice_exam.pdf \
        [--profile <profile>/config.json] [--difficulty low|high|max]

Bank format (UTF-8):
{
  "code": "E7",
  "title": "Topic wording as it appears in the syllabus",
  "difficulty": "low",
  "note": "Optional text under the header (currency warnings, etc.)",
  "seed": 7,
  "blocks": [
    {"title": "Block 1. ...",
     "scenario": "Optional: practical case common to every question in the block",
     "questions": [{"q": "Question", "answer": "Correct answer",
                    "distractors": ["Distractor 1", "Distractor 2", "Distractor 3"]}]}
  ],
  "sources": [{"title": "Entity - Title", "url": "https://...", "opened": true}]
}

The exam name, scope and document texts come from the profile
(`config.json -> name, scope, pdf.texts`). Without a profile, the English defaults are used.

Difficulty comes from --difficulty or, if absent, from the bank's "difficulty" field
(default: low; levels: low, high, max). It only changes the PDF header: the real level is set by the questions in the bank
(see SKILL.md, section 9). A block with "scenario" prints the case in a box before its questions.

The script shuffles the options and spreads the correct letter evenly.
Questions are printed with no mark, so the test can be taken without seeing the answers.
Then come the sources and, as a final section on a separate page, the solutions:
a quick answer key and the full answer to each question. Only reportlab is needed
(if missing, run skills/setup, step 1).
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

LETTERS = "abcd"
GREEN, BLUE, GREY = "#1b7a3a", colors.HexColor("#1f3a5f"), colors.HexColor("#444444")

TEXTS = {
    "header": "Practice exam · Topic {code}",
    "context": "{total} questions, one correct answer · Difficulty {difficulty}. "
               "Solutions are in the last section, on a separate page.",
    "sources": "Study sources for the topic",
    "notice": "Practice questions written for this topic; they do not come from official exams. "
              "Check every fact against the original source before the exam.",
    "solutions": "Solutions",
    "distribution": "Distribution of the correct answer: {distribution}",
    "footer": "Topic {code}",
    "meta_title": "Practice exam · Topic {code} · difficulty {difficulty}",
    "meta_author": "{name}",
    "difficulties": {"low": "low", "high": "high", "max": "maximum"},
}


def load_profile(path):
    """Return (name, scope, texts). Without a profile, empty values and the default texts."""
    texts = {k: v for k, v in TEXTS.items()}
    texts["difficulties"] = dict(TEXTS["difficulties"])
    if not path:
        return "", "", texts
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    own = config.get("pdf", {}).get("texts", {})
    for key, value in own.items():
        if key == "difficulties":
            texts["difficulties"].update(value)
        else:
            texts[key] = value
    return config.get("name", ""), config.get("scope", ""), texts


def typography():
    """DejaVu covers marks and accents; otherwise use Helvetica and an ASCII mark."""
    for base in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/"):
        if os.path.exists(base + "DejaVuSans.ttf"):
            pdfmetrics.registerFont(TTFont("DV", base + "DejaVuSans.ttf"))
            pdfmetrics.registerFont(TTFont("DVB", base + "DejaVuSans-Bold.ttf"))
            pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB")
            return "DV", "DVB", "✔"
    return "Helvetica", "Helvetica-Bold", "(correct)"


def validate(bank, difficulty):
    errors = []
    if difficulty not in TEXTS["difficulties"]:
        errors.append(f"Unknown difficulty: {difficulty} (use low, high or max)")
    if difficulty in ("high", "max") and not any(b.get("scenario") for b in bank["blocks"]):
        print(f"Warning: {difficulty} difficulty with no block that has a practical scenario.",
              file=sys.stderr)
    for b in bank["blocks"]:
        for p in b["questions"]:
            options = [p["answer"], *p["distractors"]]
            if len(p["distractors"]) != 3:
                errors.append(f"Needs 3 distractors: {p['q'][:60]}")
            if len({o.strip().lower() for o in options}) != len(options):
                errors.append(f"Repeated options: {p['q'][:60]}")
    if errors:
        sys.exit("Invalid bank:\n- " + "\n- ".join(errors))


def main(bank_path, pdf_path, difficulty=None, profile_path=None):
    if not os.path.isfile(bank_path):
        sys.exit(f"No such question bank: {bank_path}")
    with open(bank_path, encoding="utf-8") as f:
        bank = json.load(f)
    difficulty = difficulty or bank.get("difficulty", "low")
    validate(bank, difficulty)
    name, scope, texts = load_profile(profile_path)
    label = texts["difficulties"][difficulty]
    normal, bold, mark = typography()

    s_title = ParagraphStyle("t", fontName=bold, fontSize=15, leading=19, textColor=BLUE, spaceAfter=4)
    s_sub = ParagraphStyle("s", fontName=normal, fontSize=9.5, leading=13, textColor=GREY)
    s_block = ParagraphStyle("b", fontName=bold, fontSize=11.5, leading=15, textColor=BLUE,
                             spaceBefore=10, spaceAfter=6)
    s_q = ParagraphStyle("q", fontName=bold, fontSize=9.5, leading=12.5, spaceAfter=2)
    s_option = ParagraphStyle("o", fontName=normal, fontSize=9.2, leading=12, leftIndent=14)
    s_solution = ParagraphStyle("sol", fontName=normal, fontSize=8.8, leading=11.5, spaceAfter=1.5,
                                leftIndent=16, firstLineIndent=-16)
    s_source = ParagraphStyle("src", fontName=normal, fontSize=8.6, leading=11.5, spaceAfter=5,
                              leftIndent=12, firstLineIndent=-12)
    s_case = ParagraphStyle("case", fontName=normal, fontSize=9.2, leading=12.5)

    total = sum(len(b["questions"]) for b in bank["blocks"])
    rng = random.Random(bank.get("seed", 7))
    positions = [i % 4 for i in range(total)]
    rng.shuffle(positions)

    code = bank["code"]
    context = " · ".join(x for x in (name, scope) if x)
    context = (context + " · " if context else "") + texts["context"].format(
        total=total, difficulty=label)
    story = [Paragraph(texts["header"].format(code=escape(code)), s_title),
             Paragraph(escape(bank["title"]), s_sub), Spacer(1, 3),
             Paragraph(context, s_sub)]
    if bank.get("note"):
        story += [Spacer(1, 3), Paragraph(escape(bank["note"]), s_sub)]

    # 1. Questions, with no mark of the correct answer.
    key, solutions, ranges, n = [], [], [], 0
    for block in bank["blocks"]:
        start = n + 1
        # The title, the scenario and the first question stay together across pages.
        header = [Paragraph(escape(block["title"]), s_block)]
        if block.get("scenario"):
            case = Table([[Paragraph(f"<b>Scenario.</b> {escape(block['scenario'])}", s_case)]],
                         colWidths=[A4[0] - 36 * mm])
            case.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f6fa")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#9aa7b8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            header += [case, Spacer(1, 7)]
        for p in block["questions"]:
            n += 1
            pos = positions[n - 1]
            options = list(p["distractors"])
            rng.shuffle(options)
            options.insert(pos, p["answer"])
            key.append(LETTERS[pos])
            solutions.append((n, LETTERS[pos], p["answer"]))
            parts = [Paragraph(f"{n}. {escape(p['q'])}", s_q)]
            parts += [Paragraph(f"{LETTERS[i]}) {escape(t)}", s_option) for i, t in enumerate(options)]
            parts.append(Spacer(1, 5))
            story.append(KeepTogether(header + parts))
            header = []
        ranges.append((block["title"], start, n))

    # 2. Study sources.
    sources = bank.get("sources", [])
    if sources:
        story += [PageBreak(), Paragraph(texts["sources"], s_title), Spacer(1, 4)]
        for i, src in enumerate(sources, 1):
            state = "" if src.get("opened", True) else " <i>(not opened)</i>"
            story.append(Paragraph(
                f"{i}. <b>{escape(src['title'])}</b>{state}<br/>"
                f"<font color='#1f3a5f'><link href='{escape(src['url'])}'>{escape(src['url'])}</link></font>",
                s_source))
    story += [Spacer(1, 8), Paragraph(texts["notice"], s_sub)]

    # 3. Solutions: quick answer key and the full answer to each question, at the end.
    story += [PageBreak(), Paragraph(texts["solutions"], s_title), Spacer(1, 6)]
    columns = (total + 9) // 10
    rows = [[f"{c * 10 + r + 1}. {key[c * 10 + r]}" if c * 10 + r < total else ""
             for c in range(columns)] for r in range(min(10, total))]
    table = Table(rows, colWidths=[17 * mm] * columns, rowHeights=7 * mm)
    table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), normal, 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa7b8")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f6fa"))]))
    distribution = " · ".join(f"{l}) {key.count(l)}" for l in LETTERS)
    story += [table, Spacer(1, 4), Paragraph(texts["distribution"].format(distribution=distribution), s_sub)]
    for title, start, end in ranges:
        story.append(Paragraph(f"{escape(title)} (questions {start}–{end})", s_block))
        for num, letter, text in solutions[start - 1:end]:
            story.append(Paragraph(f"<b>{num}. {letter})</b> {escape(text)} "
                                   f"<font color='{GREEN}'>{mark}</font>", s_solution))

    footer_text = texts["footer"].format(code=code)
    if context_footer := " · ".join(x for x in (name, scope) if x):
        footer_text = f"{context_footer} · {footer_text}"

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(normal, 7.5)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(18 * mm, 10 * mm, footer_text)
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=18 * mm,
                            title=texts["meta_title"].format(code=code, difficulty=label),
                            author=texts["meta_author"].format(name=name or "opositor"),
                            subject=bank["title"])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"{pdf_path}: {total} questions · difficulty {difficulty} · {distribution}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bank", help="question bank in JSON")
    ap.add_argument("pdf", help="output PDF path")
    ap.add_argument("--difficulty", choices=sorted(TEXTS["difficulties"]),
                    help="low (default), high or max; if absent, the bank's 'difficulty' field is used")
    ap.add_argument("--profile", help="config.json of the profile (name, scope and document texts)")
    args = ap.parse_args()
    main(args.bank, args.pdf, args.difficulty, args.profile)
