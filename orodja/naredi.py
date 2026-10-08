#!/usr/bin/env python3
"""Izriše carousele (7 slajdov, 1080 x 1350 JPG) iz vsebine v plan/<mesec>.json.

Uporaba:  python3 orodja/naredi.py plan/2026-10.json [številka objave ...]
Zahteva:  npm install (pisave), pip paket playwright, Chromium.
Rezultat: objave/dan-NN/slajd-0X.jpg in objave/dan-NN/pregled.jpg

Barve, pisave in besedilni slog so vedno enaki. Postavitev se menja:
  naslovnica: 3 različice (1 modra levo, 2 krem levo, 3 modra sredinsko)
  nasvet:     4 različice (A lok desno, B lok levo, C modra podlaga, D pas zgoraj)
  zaključek:  plan = modra podlaga, follow = krem podlaga
Katera različica pride kam, določa številka objave (glej COVERS in TIPS). Posamezno
objavo lahko prepišeš v JSON s "cover_layout": 1..3 in "layouts": ["A","D","B","C","D"].
"""
import asyncio, html, json, os, sys
from PIL import Image
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUE, CREAM, INK, MUTED, TRACK = "#1F3BE0", "#FBF3E2", "#111111", "#2B2A26", "#E3D9C3"
FAINT = "rgba(251,243,226,0.3)"
HANDLE = "@fitnesdanijel"
COND = "font-family:'Barlow Condensed',sans-serif;font-weight:900;text-transform:uppercase"

# Postavitev poz na slajdih z nasvetom. h = višina, r = odmik od roba, b = od spodaj.
POSES = {
    "ledja":      dict(f="lik-01-ledja.png", h=800, r=119, b=312, alt="Danijel s leđa"),
    "pokazuje":   dict(f="lik-02-pokazuje.png", h=800, r=96, b=312, alt="Danijel pokazuje na biceps"),
    "dupli":      dict(f="lik-03-dupli-biceps.png", h=780, r=86, b=312, alt="Danijel pokazuje oba bicepsa"),
    "povrce":     dict(f="lik-05-povrce.png", h=700, r=0, b=312, edge=True, alt="Danijel secka povrće"),
    "voda":       dict(f="lik-06-voda.png", h=790, r=56, b=310, alt="Danijel pije vodu"),
    "obrok":      dict(f="lik-07-obrok.png", h=640, r=58, b=306, alt="Danijel jede obrok"),
    "cucanj":     dict(f="lik-08-cucanj.png", h=690, r=64, b=312, alt="Danijel radi čučanj"),
    "sklek":      dict(f="lik-09-sklek.png", h=250, r=30, b=392, arch=420, low=True, alt="Danijel radi sklek"),
    "trk":        dict(f="lik-11-trk.png", h=660, r=50, b=318, alt="Danijel trči"),
    "hod-napred": dict(f="lik-12-hod-napred.png", h=800, r=100, b=312, alt="Danijel hoda"),
    "hod-profil": dict(f="lik-13-hod-profil.png", h=800, r=60, b=312, alt="Danijel hoda"),
    "san":        dict(f="lik-10-san.png", scene=True, alt="Danijel spava"),
}
# Zaporedje postavitev glede na številko objave.
COVERS = {2: 2, 0: 3, 1: 1}                       # n % 3 -> različica naslovnice
TIPS = ["A", "D", "B", "C", "D"]                  # zavrti se za n mest


def e(s):
    return html.escape(str(s), quote=True)


def lik(name):
    return "file://" + os.path.join(ROOT, "lik", POSES[name]["f"])


def pose_w(name, h):
    w, hh = Image.open(os.path.join(ROOT, "lik", POSES[name]["f"])).size
    return round(w * h / hh)


def fonts():
    out = ""
    for fam, pk, ws in (("Barlow", "barlow", (500, 600, 700)), ("Barlow Condensed", "barlow-condensed", (800, 900))):
        for w in ws:
            for sub, rng in (("latin", "U+0000-00FF,U+2000-206F"), ("latin-ext", "U+0100-024F")):
                p = f"{ROOT}/node_modules/@fontsource/{pk}/files/{pk}-{sub}-{w}-normal.woff2"
                if not os.path.exists(p):
                    sys.exit("Manjkajo pisave. Zaženi: npm install")
                out += f"@font-face{{font-family:'{fam}';font-weight:{w};src:url('file://{p}') format('woff2');unicode-range:{rng}}}\n"
    return out


def header(i, fg):
    return (f'<div style="position:absolute;top:64px;left:72px;right:72px;display:flex;justify-content:space-between;align-items:center;z-index:5">'
            f'<div style="font-size:30px;font-weight:700;letter-spacing:0.01em">{HANDLE}</div>'
            f'<div style="font-size:26px;font-weight:700;letter-spacing:0.06em;padding:6px 20px;border:2px solid {fg};border-radius:999px">0{i} / 07</div></div>')


def progress(i, on, off):
    return "".join(f'<div style="flex:1;height:8px;border-radius:4px;background:{on if k < i else off}"></div>' for k in range(7))


def root(bg, fg, inner):
    return (f'<div id="root" style="width:1080px;height:1350px;box-sizing:border-box;position:relative;overflow:hidden;'
            f"background:{bg};color:{fg};font-family:'Barlow',sans-serif\">{inner}</div>")


def swipe():
    arrow = f'<svg width="44" height="24" viewBox="0 0 44 24" fill="none" stroke="{CREAM}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h38"></path><path d="M30 3l10 9-10 9"></path></svg>'
    return f'<div style="display:flex;align-items:center;gap:14px;font-size:28px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;background:{INK};color:{CREAM};padding:12px 22px;border-radius:999px"><div>Prevuci</div>{arrow}</div>'


# ---------- naslovnice ----------

def cover(p):
    v = p.get("cover_layout") or COVERS[p["n"] % 3]
    c = p["cover"]
    alt = e(POSES[c["pose"]]["alt"])
    kick = f'<div style="font-size:26px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;margin-bottom:20px">{e(p["kicker"])}</div>'
    if v == 3:  # modra podlaga, vse sredinsko, lik spodaj
        h = 550
        w = pose_w(c["pose"], h)
        joined = " ".join(c["lines"])
        return root(BLUE, CREAM, f'''
<div style="position:absolute;left:300px;bottom:140px;width:480px;height:480px;border-radius:50%;background:{CREAM}"></div>
<img src="{lik(c["pose"])}" alt="{alt}" style="position:absolute;left:{round(540 - w / 2)}px;bottom:108px;height:{h}px;width:auto">
{header(1, CREAM)}
<div style="position:absolute;left:60px;right:60px;top:150px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:14px">
{kick}
<div id="big" data-max="900" style="{COND};font-size:190px;line-height:0.9;background:{INK};color:{CREAM};padding:6px 26px 14px;white-space:nowrap">{e(c["big"])}</div>
<div id="joined" data-maxh="250" style="max-width:900px;{COND};font-size:88px;line-height:1.36"><span style="background:{CREAM};color:{BLUE};padding:0 20px 6px;-webkit-box-decoration-break:clone;box-decoration-break:clone">{e(joined)}</span></div>
</div>
<div style="position:absolute;left:72px;right:72px;bottom:60px;display:flex;align-items:center;gap:28px">
<div style="flex:1;display:flex;gap:10px">{progress(1, CREAM, FAINT)}</div>{swipe()}</div>''')
    dark = v == 1
    bg, fg = (BLUE, CREAM) if dark else (CREAM, INK)
    big_bg, big_fg = (INK, CREAM) if dark else (BLUE, CREAM)
    ln_bg, ln_fg = (CREAM, BLUE) if dark else (INK, CREAM)
    h = 810
    w = pose_w(c["pose"], h)
    r = max(20, round(1080 - 790 - w / 2))
    lines = "".join(f'<div class="line" style="{COND};font-size:104px;line-height:0.95;background:{ln_bg};color:{ln_fg};padding:6px 22px 12px;white-space:nowrap">{e(l)}</div>' for l in c["lines"])
    return root(bg, fg, f'''
<div style="position:absolute;right:50px;bottom:190px;width:520px;height:520px;border-radius:50%;background:{CREAM if dark else BLUE}"></div>
<img src="{lik(c["pose"])}" alt="{alt}" style="position:absolute;right:{r}px;bottom:116px;height:{h}px;width:auto">
{header(1, fg)}
<div style="position:absolute;left:72px;top:210px;display:flex;flex-direction:column;align-items:flex-start;gap:12px">
{kick}
<div id="big" data-max="640" style="{COND};font-size:190px;line-height:0.9;background:{big_bg};color:{big_fg};padding:6px 24px 14px;white-space:nowrap">{e(c["big"])}</div>
{lines}
</div>
<div style="position:absolute;left:72px;bottom:150px;width:400px;font-size:38px;font-weight:600;line-height:1.3">{e(c["sub"])}</div>
<div style="position:absolute;left:72px;right:72px;bottom:60px;display:flex;align-items:center;gap:28px">
<div style="flex:1;display:flex;gap:10px">{progress(1, CREAM if dark else BLUE, FAINT if dark else TRACK)}</div>{swipe()}</div>''')


# ---------- nasveti ----------

def action_bar(p, t, dark):
    bg, fg = (CREAM, INK) if dark else (INK, CREAM)
    return (f'<div style="position:absolute;left:72px;right:72px;bottom:120px;height:150px;box-sizing:border-box;padding:0 36px;background:{bg};color:{fg};border-radius:28px;display:flex;align-items:center;gap:28px">'
            f'<div style="flex:none;font-size:24px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;background:{BLUE};color:{CREAM};padding:12px 18px;border-radius:12px">{e(p.get("label", "Uradi danas"))}</div>'
            f'<div id="action" style="font-size:36px;font-weight:600;line-height:1.25">{e(t["action"])}</div></div>')


def wsize(word):
    return {1: 520, 2: 520, 3: 460, 4: 400, 5: 340, 6: 290}.get(len(word), 250)


def tip_side(p, k, side, dark):
    """A (desno, krem), B (levo, krem), C (desno, modra podlaga)."""
    t = p["tips"][k]
    i = k + 2
    pz = POSES[t["pose"]]
    other = "left" if side == "right" else "right"
    flip = "transform:scaleX(-1);" if side == "left" else ""
    bg, fg = (BLUE, CREAM) if dark else (CREAM, INK)
    stroke = "rgba(251,243,226,0.34)" if dark else "rgba(31,59,224,0.3)"
    arch = f"position:absolute;{side}:72px;bottom:300px;width:420px;height:{pz.get('arch', 640)}px;border-radius:210px 210px 28px 28px"
    if pz.get("scene"):
        art = f'<div style="{arch};overflow:hidden;background:{CREAM}"><img src="{lik(t["pose"])}" alt="{e(pz["alt"])}" style="width:100%;height:100%;object-fit:cover;object-position:28% 20%;display:block"></div>'
    else:
        if dark:
            shape = f'<div style="position:absolute;{side}:62px;bottom:{300 if pz.get("low") else 340}px;width:440px;height:440px;border-radius:50%;background:{CREAM}"></div>'
        else:
            shape = f'<div style="{arch};background:{BLUE}"></div>'
        art = shape + f'<img src="{lik(t["pose"])}" alt="{e(pz["alt"])}" style="position:absolute;{side}:{pz["r"]}px;bottom:{pz["b"]}px;height:{pz["h"]}px;width:auto;{flip}">'
    return root(bg, fg, f'''
<div id="word" data-max="640" style="position:absolute;{side}:28px;top:104px;{COND};font-size:{wsize(t["word"])}px;line-height:0.86;white-space:nowrap;color:transparent;-webkit-text-stroke:4px {stroke}">{e(t["word"])}</div>
{art}
{header(i, fg)}
<div id="col" style="position:absolute;{other}:72px;top:170px;bottom:300px;width:{470 if side == "left" else 500}px;display:flex;flex-direction:column;justify-content:flex-end;gap:26px">
<div id="num" style="{COND};font-size:250px;line-height:0.8;color:{CREAM if dark else BLUE}">0{k + 1}</div>
<h2 id="title" style="margin:0;{COND};font-size:104px;line-height:0.95">{e(t["title"])}</h2>
<div id="body" style="font-size:38px;font-weight:500;line-height:1.35;color:{CREAM if dark else MUTED}">{e(t["body"])}</div>
</div>
{action_bar(p, t, dark)}
<div style="position:absolute;left:72px;right:72px;bottom:60px;display:flex;gap:10px">{progress(i, CREAM if dark else BLUE, FAINT if dark else TRACK)}</div>''')


def tip_top(p, k):
    """D: moder pas zgoraj s številko in likom, besedilo čez celo širino spodaj."""
    t = p["tips"][k]
    i = k + 2
    pz = POSES[t["pose"]]
    if pz.get("low"):
        h, bottom = 250, 700
    else:
        h, bottom = round(pz["h"] * 0.72), 672
    w = pose_w(t["pose"], h)
    r = 72 if pz.get("edge") else max(84, round(1080 - 770 - w / 2))
    return root(CREAM, INK, f'''
<div style="position:absolute;left:72px;right:72px;top:180px;height:500px;border-radius:44px;background:{BLUE}"></div>
<div id="word" data-max="430" style="position:absolute;right:104px;top:206px;{COND};font-size:{round(wsize(t["word"]) * 0.7)}px;line-height:0.86;white-space:nowrap;color:transparent;-webkit-text-stroke:4px rgba(251,243,226,0.34)">{e(t["word"])}</div>
<div style="position:absolute;left:118px;top:292px;{COND};font-size:350px;line-height:0.8;color:{CREAM}">0{k + 1}</div>
<img src="{lik(t["pose"])}" alt="{e(pz["alt"])}" style="position:absolute;right:{r}px;bottom:{bottom}px;height:{h}px;width:auto">
{header(i, INK)}
<div id="col" style="position:absolute;left:72px;right:72px;top:712px;bottom:300px;display:flex;flex-direction:column;justify-content:center;gap:22px">
<h2 id="title" style="margin:0;{COND};font-size:104px;line-height:0.95">{e(t["title"])}</h2>
<div id="body" style="font-size:38px;font-weight:500;line-height:1.35;color:{MUTED}">{e(t["body"])}</div>
</div>
{action_bar(p, t, False)}
<div style="position:absolute;left:72px;right:72px;bottom:60px;display:flex;gap:10px">{progress(i, BLUE, TRACK)}</div>''')


def tip(p, k):
    seq = p.get("layouts") or [TIPS[(j + p["n"]) % len(TIPS)] for j in range(5)]
    lay = seq[k]
    if lay == "D" and POSES[p["tips"][k]["pose"]].get("scene"):
        lay = "B"
    if lay == "D":
        return tip_top(p, k)
    return tip_side(p, k, "left" if lay == "B" else "right", lay == "C")


# ---------- zaključek ----------

def cta(p):
    c = p["cta"]
    plan = p["type"] == "plan"
    bg, fg = (BLUE, CREAM) if plan else (CREAM, INK)
    box_bg, box_fg = (INK, CREAM) if plan else (BLUE, CREAM)
    stroke = "rgba(251,243,226,0.34)" if plan else "rgba(31,59,224,0.3)"
    h = 880
    w = pose_w(c["pose"], h)
    r = max(24, round(1080 - 835 - w / 2))
    if plan:
        body = f'''<h2 style="margin:0;{COND};font-size:112px;line-height:0.95">Želiš plan za 21 dan?</h2>
<div style="display:flex;flex-direction:column;align-items:flex-start;gap:18px">
<div style="font-size:40px;font-weight:600;line-height:1.25">Napiši u komentar</div>
<div style="{COND};font-size:200px;line-height:0.9;letter-spacing:0.03em;background:{box_bg};color:{box_fg};padding:10px 40px 22px;border-radius:24px">PLAN</div>
<div style="font-size:40px;font-weight:600;line-height:1.25;width:440px">i šaljem ti link u poruku.</div></div>'''
        pill, word = "Sačuvaj objavu za kasnije", "Plan"
    else:
        body = f'''<h2 style="margin:0;{COND};font-size:112px;line-height:0.95">Želiš još ovakvih saveta?</h2>
<div style="display:flex;flex-direction:column;align-items:flex-start;gap:18px">
<div style="font-size:40px;font-weight:600;line-height:1.25">Klikni</div>
<div style="{COND};font-size:128px;line-height:0.9;letter-spacing:0.02em;background:{box_bg};color:{box_fg};padding:12px 30px 20px;border-radius:22px">Zaprati</div>
<div style="font-size:40px;font-weight:600;line-height:1.25;width:430px">Novi savet svakog ponedeljka, srede i petka.</div></div>'''
        pill, word = "Sledeće: " + c["teaser"], "Još"
    pill_bg, pill_fg = (CREAM, BLUE) if plan else (INK, CREAM)
    return root(bg, fg, f'''
<div style="position:absolute;right:-44px;top:104px;{COND};font-size:290px;line-height:0.86;white-space:nowrap;color:transparent;-webkit-text-stroke:5px {stroke}">{word}</div>
<div style="position:absolute;right:40px;bottom:190px;width:480px;height:480px;border-radius:50%;background:{CREAM if plan else BLUE}"></div>
<img src="{lik(c["pose"])}" alt="{e(POSES[c["pose"]]["alt"])}" style="position:absolute;right:{r}px;bottom:112px;height:{h}px;width:auto">
{header(7, fg)}
<div style="position:absolute;left:72px;top:200px;width:540px;display:flex;flex-direction:column;align-items:flex-start;gap:36px">{body}</div>
<div style="position:absolute;left:72px;bottom:116px;max-width:540px;box-sizing:border-box;font-size:28px;font-weight:700;line-height:1.25;background:{pill_bg};color:{pill_fg};padding:14px 24px;border-radius:26px">{e(pill)}</div>
<div style="position:absolute;left:72px;right:72px;bottom:60px;display:flex;gap:10px">{progress(7, CREAM if plan else BLUE, CREAM)}</div>''')


# Prilagodi velikost pisave, da se nič ne preliva; vrne seznam opozoril.
FIT = r"""
() => {
  const warn = [], px = el => parseFloat(getComputedStyle(el).fontSize), $ = id => document.getElementById(id);
  const shrink = (el, ok, min) => { let s = px(el); while (!ok() && s > min) { s -= 2; el.style.fontSize = s + 'px'; } return ok(); };
  const big = $('big');
  if (big) {
    const max = +big.dataset.max;
    if (!shrink(big, () => big.getBoundingClientRect().width <= max, 90)) warn.push('big');
    const ls = [...document.querySelectorAll('.line')];
    if (ls.length) {
      let s = 104; const wide = () => Math.max(...ls.map(l => l.getBoundingClientRect().width));
      while (wide() > 545 && s > 60) { s -= 2; ls.forEach(l => l.style.fontSize = s + 'px'); }
      if (wide() > 545) warn.push('lines');
    }
    const j = $('joined');
    if (j && !shrink(j, () => j.getBoundingClientRect().height <= +j.dataset.maxh, 56)) warn.push('joined');
  }
  const w = $('word');
  if (w) shrink(w, () => w.getBoundingClientRect().width <= +w.dataset.max, 150);
  const t = $('title'), col = $('col');
  if (t) {
    if (!shrink(t, () => t.scrollWidth <= t.clientWidth + 1, 60)) warn.push('title-width');
    const num = $('num'), over = () => col.scrollHeight > col.clientHeight + 1;
    let guard = 0;
    while (over() && guard++ < 60) {
      if (num && px(num) > 170) num.style.fontSize = (px(num) - 10) + 'px'; else if (px(t) > 70) t.style.fontSize = (px(t) - 2) + 'px'; else break;
    }
    if (over()) warn.push('col-height');
    const a = $('action');
    if (!shrink(a, () => a.getBoundingClientRect().height <= 96, 28)) warn.push('action');
  }
  return warn;
}
"""


async def main(plan_path, only):
    posts = json.load(open(plan_path, encoding="utf-8"))["posts"]
    css = fonts()
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1350})
        for p in posts:
            if only and p["n"] not in only:
                continue
            assert len(p["tips"]) == 5, f'objava {p["n"]}: potrebnih je 5 nasvetov'
            out = os.path.join(ROOT, "objave", f'dan-{p["n"]:02d}')
            os.makedirs(out, exist_ok=True)
            slides = [cover(p)] + [tip(p, k) for k in range(5)] + [cta(p)]
            thumbs = []
            for i, body in enumerate(slides, 1):
                tmp = os.path.join(out, f".slajd-{i}.html")
                open(tmp, "w", encoding="utf-8").write(f"<!doctype html><html lang='sr-Latn'><meta charset='utf-8'><style>{css}body{{margin:0}}</style>{body}</html>")
                await pg.goto("file://" + tmp)
                await pg.evaluate("document.fonts.ready")
                await pg.wait_for_timeout(250)
                warn = await pg.evaluate(FIT)
                if warn:
                    print(f'OPOZORILO objava {p["n"]} slajd {i}: {warn}')
                jpg = os.path.join(out, f"slajd-0{i}.jpg")
                await pg.screenshot(path=jpg, type="jpeg", quality=93)
                os.remove(tmp)
                thumbs.append(Image.open(jpg).resize((432, 540)))
            sheet = Image.new("RGB", (432 * 7 + 60, 540), (60, 60, 60))
            for i, t in enumerate(thumbs):
                sheet.paste(t, (i * 442, 0))
            sheet.save(os.path.join(out, "pregled.jpg"), quality=85)
            print(f'objava {p["n"]} ({p["date"]}): 7 slajdov -> {out}')
        await br.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], {int(x) for x in sys.argv[2:]}))
