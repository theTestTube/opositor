#!/usr/bin/env python3
"""Genera una página de escucha autocontenida con la voz del navegador (Web Speech API).

No exporta audio: `speechSynthesis` reproduce y no escribe archivos. Para MP3, usa Piper
(`skills/speak-summary/scripts/tts.sh`). Este módulo solo construye el HTML.

Uso desde la CLI: `python3 scripts/opositor.py tts-page guion.txt salida.html`.
"""
import json
import re

PLANTILLA = """<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITULO__</title>
<style>
  :root { color-scheme: light dark; --fondo:#fbfaf7; --texto:#1d1d1f; --suave:#6b6b70;
          --linea:#e3e0d8; --acento:#7a4b16; --activo:#f3ead9; }
  @media (prefers-color-scheme: dark) {
    :root { --fondo:#16161a; --texto:#ececf1; --suave:#9a9aa2; --linea:#2c2c33;
            --acento:#e0b070; --activo:#26242a; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--fondo); color:var(--texto);
         font: 17px/1.65 ui-serif, Georgia, "Iowan Old Style", serif; }
  .barra { position: sticky; top:0; z-index:5; backdrop-filter: blur(8px);
           background: color-mix(in srgb, var(--fondo) 92%, transparent);
           border-bottom:1px solid var(--linea); padding:.7rem clamp(1rem, 4vw, 3rem); }
  .fila { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; }
  .fila + .fila { margin-top:.5rem; }
  button { font: inherit; font-size:.9rem; padding:.4rem .85rem; border-radius:999px;
           border:1px solid var(--linea); background:transparent; color:var(--texto); cursor:pointer; }
  button:hover { border-color: var(--acento); color: var(--acento); }
  button.principal { background: var(--acento); color:#fff; border-color: var(--acento); }
  select, input[type=range] { font: inherit; font-size:.85rem; color:var(--texto);
           background:transparent; border:1px solid var(--linea); border-radius:8px; padding:.3rem; }
  select { max-width: 19rem; }
  .estado { color: var(--suave); font-size:.85rem; }
  main { max-width: 44rem; margin: 0 auto; padding: 2rem clamp(1rem, 4vw, 3rem) 6rem; }
  h1 { font-size: 1.5rem; line-height:1.3; margin: 0 0 1.5rem; letter-spacing:-.01em; }
  p { margin: 0 0 1.15rem; cursor: pointer; border-radius: 8px; padding: .2rem .4rem;
      transition: background .15s ease; }
  p:hover { background: color-mix(in srgb, var(--activo) 60%, transparent); }
  p.sonando { background: var(--activo); box-shadow: -3px 0 0 var(--acento); }
  .aviso { border:1px solid var(--linea); border-left:3px solid var(--acento);
           padding:.9rem 1rem; border-radius:8px; font-size:.9rem; margin-bottom:2rem; }
  .aviso code { font-size:.85em; }
  .oculto { display:none; }
  footer { color: var(--suave); font-size:.8rem; text-align:center; padding: 0 1rem 3rem; }
</style>
</head>
<body>
<div class="barra">
  <div class="fila">
    <button id="play" class="principal" aria-label="Reproducir o pausar">▶︎ Reproducir</button>
    <button id="prev" aria-label="Párrafo anterior">⟨</button>
    <button id="next" aria-label="Párrafo siguiente">⟩</button>
    <button id="stop" aria-label="Detener">■</button>
    <span class="estado" id="estado">listo</span>
  </div>
  <div class="fila">
    <label class="estado" for="voz">Voz</label>
    <select id="voz"></select>
    <label class="estado" for="ritmo">Ritmo</label>
    <input id="ritmo" type="range" min="0.6" max="1.8" step="0.05" value="1">
    <span class="estado" id="ritmoVal">1.00×</span>
  </div>
</div>
<main>
  <div id="aviso" class="aviso oculto"></div>
  <h1>__TITULO__</h1>
  <div id="texto"></div>
</main>
<footer>Página de escucha generada por opositor · la voz la pone tu navegador · sin conexión</footer>
<script>
const PARRAFOS = __PARRAFOS__;
const LANG = "__LANG__";
const textos = PARRAFOS.map(t => t);
const cont = document.getElementById('texto');
const estadoEl = document.getElementById('estado');
const sel = document.getElementById('voz');
const ritmo = document.getElementById('ritmo');
const ritmoVal = document.getElementById('ritmoVal');
const aviso = document.getElementById('aviso');
let nodos = [], actual = -1, hablando = false, pausado = false;

textos.forEach((t, i) => {
  const p = document.createElement('p');
  p.textContent = t;
  p.dataset.i = i;
  p.addEventListener('click', () => { detener(); hablar(i); });
  cont.appendChild(p);
  nodos.push(p);
});

function voces() {
  const todas = speechSynthesis.getVoices().filter(v => v.lang && v.lang.toLowerCase().startsWith(LANG));
  return todas.length ? todas : speechSynthesis.getVoices();
}
function pintarVoces() {
  const lista = voces();
  sel.innerHTML = '';
  if (!lista.length) return;
  lista.forEach((v, i) => {
    const o = document.createElement('option');
    o.value = i; o.textContent = v.name + ' · ' + v.lang + (v.localService ? '' : ' (en línea)');
    sel.appendChild(o);
  });
  const guardada = Number(localStorage.getItem('opositor-voz') || -1);
  if (guardada >= 0 && guardada < lista.length) sel.value = String(guardada);
  if (!lista.length) avisarSinVoces();
}
function avisarSinVoces() {
  aviso.classList.remove('oculto');
  aviso.innerHTML = '<b>Este navegador no ha detectado ninguna voz.</b><br>' +
    'La página funciona, pero el sistema no ofrece motores de síntesis. En Linux suele ser ' +
    '<code>speech-dispatcher</code> con una voz instalada; en navegadores instalados como snap, ' +
    'el confinamiento puede bloquearlo. Alternativa: genera un MP3 con Piper.';
}
function vozElegida() { const l = voces(); return l[Number(sel.value) || 0]; }

function marcar(i) {
  nodos.forEach(n => n.classList.remove('sonando'));
  if (nodos[i]) { nodos[i].classList.add('sonando'); nodos[i].scrollIntoView({block:'center', behavior:'smooth'}); }
}
function hablar(i) {
  if (i >= textos.length) { terminar(); return; }
  actual = i; marcar(i);
  const u = new SpeechSynthesisUtterance(textos[i]);
  const v = vozElegida();
  if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = LANG; }
  u.rate = Number(ritmo.value);
  u.onend = () => { if (actual === i) hablar(i + 1); };
  u.onerror = e => { if (e.error !== 'interrupted') { estadoEl.textContent = 'error: ' + e.error; } };
  hablando = true; pausado = false;
  speechSynthesis.speak(u);
  estadoEl.textContent = 'párrafo ' + (i + 1) + ' de ' + textos.length;
  document.getElementById('play').textContent = '⏸ Pausa';
}
function terminar() { hablando = false; actual = -1; marcar(-1); estadoEl.textContent = 'fin';
  document.getElementById('play').textContent = '▶︎ Reproducir'; }
function detener() { speechSynthesis.cancel(); hablando = false; pausado = false; actual = -1;
  marcar(-1); estadoEl.textContent = 'detenido';
  document.getElementById('play').textContent = '▶︎ Reproducir'; }

document.getElementById('play').onclick = () => {
  if (!textos.length) return;
  if (!hablando) { hablar(actual >= 0 ? actual : 0); return; }
  if (pausado) { speechSynthesis.resume(); pausado = false; estadoEl.textContent = 'reanudado';
                 document.getElementById('play').textContent = '⏸ Pausa'; }
  else { speechSynthesis.pause(); pausado = true; estadoEl.textContent = 'en pausa';
         document.getElementById('play').textContent = '▶︎ Seguir'; }
};
document.getElementById('stop').onclick = detener;
document.getElementById('prev').onclick = () => { const i = Math.max(0, (actual < 0 ? 0 : actual) - 1);
  detener(); hablar(i); };
document.getElementById('next').onclick = () => { const i = Math.min(textos.length - 1, (actual < 0 ? -1 : actual) + 1);
  detener(); hablar(i); };
ritmo.oninput = () => { ritmoVal.textContent = Number(ritmo.value).toFixed(2) + '×';
  localStorage.setItem('opositor-ritmo', ritmo.value); };
sel.onchange = () => { localStorage.setItem('opositor-voz', sel.value); if (hablando) {
  const i = actual; detener(); hablar(i); } };
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') return;
  if (e.code === 'Space') { e.preventDefault(); document.getElementById('play').click(); }
  if (e.code === 'ArrowRight') document.getElementById('next').click();
  if (e.code === 'ArrowLeft') document.getElementById('prev').click();
  if (e.code === 'Escape') detener();
});
const ritmoGuardado = localStorage.getItem('opositor-ritmo');
if (ritmoGuardado) { ritmo.value = ritmoGuardado; ritmoVal.textContent = Number(ritmoGuardado).toFixed(2) + '×'; }
pintarVoces();
speechSynthesis.onvoiceschanged = pintarVoces;
setTimeout(() => { pintarVoces(); if (!voces().length) avisarSinVoces(); }, 600);
</script>
</body>
</html>
"""


def parrafos(texto):
    """Convierte el guion en párrafos hablables: fuera markdown, una unidad por bloque."""
    limpio = []
    for bloque in re.split(r"\n\s*\n", texto.strip()):
        bloque = re.sub(r"^\s{0,3}#{1,6}\s*", "", bloque, flags=re.M)
        bloque = re.sub(r"[*_`>]", "", bloque)
        bloque = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", bloque)
        bloque = re.sub(r"^\s*[-•*]\s*", "", bloque, flags=re.M)
        bloque = re.sub(r"\s+", " ", bloque).strip()
        if bloque:
            limpio.append(bloque)
    return limpio


def build_page(texto, titulo, lang="es"):
    trozos = parrafos(texto)
    return (PLANTILLA
            .replace("__TITULO__", titulo.replace("<", "&lt;"))
            .replace("__LANG__", lang)
            .replace("__PARRAFOS__", json.dumps(trozos, ensure_ascii=False).replace("</", "<\\/")))
