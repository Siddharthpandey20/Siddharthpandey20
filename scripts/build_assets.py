#!/usr/bin/env python3
"""Generate the animated SVG assets used by the profile README.

Every animation is SMIL inside the SVG, which GitHub renders when the file is
shown through an <img> tag. Each card comes in dark / light and desktop /
mobile variants; the README picks one with <picture> media queries.

Usage (from the repository root):  python scripts/build_assets.py
Brand icons come from simple-icons (CC0) and are cached in scripts/.icon-cache/.
"""
import base64
import html
import json
import math
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
PORTRAIT = os.path.join(HERE, "portrait.png")
ICON_CACHE = os.path.join(HERE, ".icon-cache")
SI_VERSION = "16.37.0"

SANS = "'Segoe UI',Inter,-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','Cascadia Code','SF Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"

DARK = dict(name="dark", bg0="#0D131A", bg1="#111B25", border="#243041", text="#E6EDF3", text2="#A9B4C0",
            muted="#6B7787", acc="#2DD4BF", accHi="#99F6E4", acc2="#38BDF8", acc3="#A78BFA", ok="#34D399",
            warn="#FBBF24", bad="#F87171", inset="#0A0F15", insetB="#1C2633", chip="#141D28", chipB="#283548",
            grid="#FFFFFF", gridOp="0.035", glowOp="0.22", silver="#C9D1D9", bronze="#E0A16B", gold="#F5C542",
            shine="#FFFFFF")
LIGHT = dict(name="light", bg0="#FFFFFF", bg1="#F2F7F9", border="#D5DDE5", text="#1F2328", text2="#4B5563",
             muted="#7D8590", acc="#0D9488", accHi="#5EEAD4", acc2="#0284C7", acc3="#7C3AED", ok="#16A34A",
             warn="#D97706", bad="#DC2626", inset="#F6F9FB", insetB="#D9E1E8", chip="#F3F6F9", chipB="#D5DDE5",
             grid="#0F172A", gridOp="0.045", glowOp="0.14", silver="#7D8794", bronze="#B4692E", gold="#C99A06",
             shine="#FFFFFF")
THEMES = (DARK, LIGHT)


# ----------------------------------------------------------------------------- basics
def e(s):
    return html.escape(str(s), quote=False)


def q(s):
    return html.escape(str(s), quote=True)


def f(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def write(rel, content):
    path = os.path.join(ASSETS, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def svg(w, h, title, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{q(title)}">'
            f'<title>{e(title)}</title><defs>{defs}</defs>{body}</svg>\n')


def text(x, y, s, size, fill, family=SANS, weight=None, anchor=None, extra="", ls=None, op=None):
    attrs = f'x="{f(x)}" y="{f(y)}" font-family="{family}" font-size="{f(size)}" fill="{fill}"'
    if weight:
        attrs += f' font-weight="{weight}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    if ls is not None:
        attrs += f' letter-spacing="{f(ls)}"'
    if op is not None:
        attrs += f' opacity="{op}"'
    return f'<text {attrs} {extra}>{e(s)}</text>'


def mono_w(s, size, ls=0.0):
    return len(s) * (size * 0.6 + ls)


# ----------------------------------------------------------------------------- animation helpers
def loop(attr, T, pts, begin=0.0, calc="linear"):
    """Looping animation through (time, value) points inside a cycle of T seconds."""
    pts = sorted(pts, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts = [(0.0, pts[0][1])] + pts
    if pts[-1][0] < T:
        pts = pts + [(T, pts[-1][1])]
    ks = []
    for t, _ in pts:
        k = min(1.0, max(0.0, t / T))
        if ks and k <= ks[-1]:
            k = ks[-1] + 0.0002
        ks.append(k)
    ks[0], ks[-1] = 0.0, 1.0
    for i in range(len(ks) - 2, 0, -1):
        if ks[i] >= ks[i + 1]:
            ks[i] = ks[i + 1] - 0.0002
    vals = ";".join(str(v) for _, v in pts)
    kts = ";".join(f"{k:.4f}" for k in ks)
    return (f'<animate attributeName="{attr}" dur="{f(T)}s" begin="{f(begin)}s" repeatCount="indefinite" '
            f'values="{vals}" keyTimes="{kts}" calcMode="{calc}"/>')


def window(T, a, b, fade=0.25, begin=0.0, lo=0, hi=1, attr="opacity"):
    fade = min(fade, (b - a) / 2)
    return loop(attr, T, [(a, lo), (a + fade, hi), (b - fade, hi), (b, lo)], begin)


def enter(begin, dur=0.55, dy=8.0, dx=0.0):
    return (f'<animate attributeName="opacity" from="0" to="1" begin="{f(begin)}s" dur="{f(dur)}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="{f(dx)} {f(dy)}" to="0 0" '
            f'begin="{f(begin)}s" dur="{f(dur)}s" fill="freeze" calcMode="spline" keyTimes="0;1" '
            f'keySplines="0.2 0.7 0.2 1"/>')


def g_enter(content, begin, dur=0.55, dy=8.0, dx=0.0):
    return f'<g opacity="0">{enter(begin, dur, dy, dx)}{content}</g>'


def typing(cid, x, y, s, size, fill, begin, cps=16.0, ls=0.0, weight=None, cursor=None, cursor_hide=None):
    """Text revealed one character at a time, with an optional block cursor."""
    cw = size * 0.6 + ls
    n = max(1, len(s))
    dur = max(0.25, n / cps)
    widths = [i * cw for i in range(n)] + [4000]
    kts = ";".join(f"{i / n:.4f}" for i in range(n)) + ";1"
    out = (f'<clipPath id="{cid}"><rect x="{f(x - 1)}" y="{f(y - size * 1.05)}" height="{f(size * 1.5)}" width="0">'
           f'<animate attributeName="width" values="{";".join(f(w) for w in widths)}" keyTimes="{kts}" '
           f'calcMode="discrete" begin="{f(begin)}s" dur="{f(dur)}s" fill="freeze"/></rect></clipPath>')
    out += f'<g clip-path="url(#{cid})">{text(x, y, s, size, fill, MONO, weight, ls=ls if ls else None)}</g>'
    if cursor:
        xs = [x + i * cw for i in range(n + 1)]
        ckts = ";".join(f"{i / n:.4f}" for i in range(n + 1))
        hide = ""
        if cursor_hide is not None:
            hide = f'<set attributeName="visibility" to="hidden" begin="{f(cursor_hide)}s"/>'
        out += (f'<rect x="{f(x)}" y="{f(y - size * 0.86)}" width="{f(size * 0.58)}" height="{f(size * 1.08)}" '
                f'fill="{cursor}" rx="1">'
                f'<animate attributeName="x" values="{";".join(f(v) for v in xs)}" keyTimes="{ckts}" '
                f'calcMode="discrete" begin="{f(begin)}s" dur="{f(dur)}s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" calcMode="discrete" dur="1.05s" '
                f'repeatCount="indefinite"/>{hide}</rect>')
    return out, begin + dur


def motion(path_id, T, a, b, begin=0.0, reverse=False):
    kp = "1;1;0;0" if reverse else "0;0;1;1"
    a = max(a, 0.002)
    return (f'<animateMotion dur="{f(T)}s" begin="{f(begin)}s" repeatCount="indefinite" keyPoints="{kp}" '
            f'keyTimes="0;{a / T:.4f};{b / T:.4f};1" calcMode="linear">'
            f'<mpath href="#{path_id}" xlink:href="#{path_id}"/></animateMotion>')


def packet(path_id, T, a, b, color, r=4.2, begin=0.0, reverse=False, flt="url(#glow)"):
    return (f'<circle r="{f(r)}" fill="{color}" opacity="0" filter="{flt}">'
            f'{motion(path_id, T, a, b, begin, reverse)}{window(T, a, b, 0.07, begin)}</circle>')


GLOW = ('<filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="2.4" '
        'result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def card(W, H, p, rx=18, grid=True, running=True, run_dur=12.0, glow_at=None):
    defs = (f'<linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p["bg0"]}"/>'
            f'<stop offset="1" stop-color="{p["bg1"]}"/></linearGradient>')
    body = f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{rx}" fill="url(#cbg)"/>'
    if grid:
        defs += (f'<pattern id="cgrid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" '
                 f'fill="none" stroke="{p["grid"]}" stroke-opacity="{p["gridOp"]}"/></pattern>')
        body += f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{rx}" fill="url(#cgrid)"/>'
    if glow_at:
        gx, gy, gr = glow_at
        defs += (f'<radialGradient id="cglow"><stop offset="0" stop-color="{p["acc"]}" stop-opacity="1"/>'
                 f'<stop offset="1" stop-color="{p["acc"]}" stop-opacity="0"/></radialGradient>')
        body += (f'<circle cx="{gx}" cy="{gy}" r="{gr}" fill="url(#cglow)" opacity="{p["glowOp"]}">'
                 f'{loop("opacity", 7, [(0, p["glowOp"]), (3.5, float(p["glowOp"]) * 0.55), (7, p["glowOp"])])}'
                 f'</circle>')
    body += f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{rx}" fill="none" stroke="{p["border"]}" stroke-width="1.2"/>'
    if running:
        body += (f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{rx}" fill="none" stroke="{p["acc"]}" '
                 f'stroke-width="1.6" stroke-linecap="round" pathLength="1000" stroke-dasharray="80 920" '
                 f'stroke-opacity="0.75"><animate attributeName="stroke-dashoffset" values="1000;0" '
                 f'dur="{f(run_dur)}s" repeatCount="indefinite"/></rect>')
    return defs, body


def chip(x, y, label, p, size=11.5, h=24, fill=None, stroke=None, color=None, family=MONO):
    w = len(label) * size * 0.6 + 18
    s = (f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{h}" rx="{f(h / 2 - 3)}" fill="{fill or p["chip"]}" '
         f'stroke="{stroke or p["chipB"]}"/>' + text(x + 9, y + h / 2 + size * 0.36, label, size, color or p["text2"], family))
    return w, s


def chips_row(x, y, labels, p, size=11.5, h=24, gap=8, max_x=None, row_gap=8):
    out, cx, cy = "", x, y
    for lab in labels:
        w = len(lab) * size * 0.6 + 18
        if max_x and cx + w > max_x and cx > x:
            cx, cy = x, cy + h + row_gap
        _, s = chip(cx, cy, lab, p, size, h)
        out += s
        cx += w + gap
    return out, cy + h


def pill(x, y, label, color, p, size=10.5, h=22, fill_op=0.13, dot=False, T=None):
    w = mono_w(label, size, 1.0) + (34 if dot else 20)
    s = (f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{h}" rx="{h / 2}" fill="{color}" fill-opacity="{fill_op}" '
         f'stroke="{color}" stroke-opacity="0.55"/>')
    tx = x + 10
    if dot:
        cx, cy = x + 13, y + h / 2
        s += (f'<circle cx="{f(cx)}" cy="{f(cy)}" r="3.6" fill="{color}"/>'
              f'<circle cx="{f(cx)}" cy="{f(cy)}" r="3.6" fill="none" stroke="{color}" stroke-width="1.4">'
              f'<animate attributeName="r" values="3.6;10" dur="1.8s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="0.9;0" dur="1.8s" repeatCount="indefinite"/></circle>')
        tx = x + 24
    s += text(tx, y + h / 2 + size * 0.36, label, size, color, MONO, "600", ls=1.0)
    return w, s


# ----------------------------------------------------------------------------- hero
def hero(p, mobile=False):
    if mobile:
        W, H = 600, 694
        lab_y, lab_size = 92, 18
        name_y, name_size = 178, 74
        subs = [("Backend systems · Distributed", 228), ("pipelines · Applied AI", 262)]
        sub_size = 25
        info_y, info_size = 310, 17
        pill_y, pill_size = 334, 15.5
        bw, bh, bfs = 140, 50, 19
        cols, rows = (40, 230, 420), (446, 574)
        cap_y, cap_size = 668, 15
    else:
        W, H = 900, 300
        lab_y, lab_size = 80, 13
        name_y, name_size = 142, 60
        subs = [("Backend systems · Distributed pipelines · Applied AI", 180)]
        sub_size = 16.5
        info_y, info_size = 214, 12.5
        pill_y, pill_size = 236, 12
        bw, bh, bfs = 88, 34, 13
        cols, rows = (560, 670, 780), (74, 180)
        cap_y, cap_size = 270, 10.5
    defs, body = card(W, H, p, grid=True, running=False,
                      glow_at=((W - 160, 150, 260) if not mobile else (300, 520, 300)))
    defs += GLOW
    # left accent bar
    defs += (f'<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["acc"]}"/>'
             f'<stop offset="1" stop-color="{p["acc2"]}"/></linearGradient>'
             f'<clipPath id="cardclip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18"/></clipPath>')
    body += f'<rect x="0" y="0" width="5" height="{H}" fill="url(#bar)" clip-path="url(#cardclip)"/>'
    x0 = 44 if not mobile else 40
    # label typing
    t, t_end = typing("lab", x0, lab_y, "SOFTWARE ENGINEER", lab_size, p["acc"], 0.25, cps=22, ls=3,
                      weight="600", cursor=p["acc"])
    body += t
    # name with a shine sweep
    nx2 = x0 + name_size * 5.2
    defs += (f'<linearGradient id="name" gradientUnits="userSpaceOnUse" x1="{f(x0 - 400)}" y1="0" x2="{f(x0 - 100)}" y2="0">'
             f'<stop offset="0" stop-color="{p["text"]}"/><stop offset="0.42" stop-color="{p["text"]}"/>'
             f'<stop offset="0.5" stop-color="{p["accHi"] if p is DARK else p["acc"]}"/>'
             f'<stop offset="0.58" stop-color="{p["text"]}"/><stop offset="1" stop-color="{p["text"]}"/>'
             f'{loop("x1", 8, [(0, x0 - 400), (1.6, nx2 + 60), (8, nx2 + 60)], begin=1.6)}'
             f'{loop("x2", 8, [(0, x0 - 100), (1.6, nx2 + 360), (8, nx2 + 360)], begin=1.6)}'
             f'</linearGradient>')
    body += g_enter(text(x0 - 2, name_y, "Siddharth", name_size, "url(#name)", SANS, "700", ls=-1), 0.7, 0.7, 12)
    for i, (s, y) in enumerate(subs):
        body += g_enter(text(x0, y, s, sub_size, p["text2"]), 1.0 + i * 0.1, 0.6, 6)
    body += g_enter(text(x0, info_y, "IIIT Naya Raipur  ·  B.Tech CSE  ·  2024–28", info_size, p["muted"], MONO),
                    1.25, 0.6, 6)
    pl = "Open to SDE · Backend · AI Engineering roles"
    pw = mono_w(pl, pill_size) + 40
    ph = pill_size * 2.4
    pill_s = (f'<rect x="{x0}" y="{pill_y}" width="{f(pw)}" height="{f(ph)}" rx="{f(ph / 2)}" fill="{p["ok"]}" '
              f'fill-opacity="0.10" stroke="{p["ok"]}" stroke-opacity="0.45"/>'
              f'<circle cx="{f(x0 + ph / 2)}" cy="{f(pill_y + ph / 2)}" r="{f(pill_size * 0.32)}" fill="{p["ok"]}"/>'
              f'<circle cx="{f(x0 + ph / 2)}" cy="{f(pill_y + ph / 2)}" r="{f(pill_size * 0.32)}" fill="none" '
              f'stroke="{p["ok"]}" stroke-width="1.4"><animate attributeName="r" values="{f(pill_size * 0.32)};'
              f'{f(pill_size * 0.95)}" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" '
              f'values="0.9;0" dur="2s" repeatCount="indefinite"/></circle>'
              + text(x0 + ph * 0.95, pill_y + ph / 2 + pill_size * 0.36, pl, pill_size, p["text2"], MONO))
    body += g_enter(pill_s, 1.45, 0.6, 6)

    # ------------------------------------------------ living system diagram
    T, B0 = 5.4, 1.9
    hl = {"queue": [0.6], "cache": [0.6], "workers": [1.25, 2.65], "index": [1.95], "llm": [1.95], "api": [3.75]}
    names = [["api", "queue", "workers"], ["cache", "index", "llm"]]
    centers = {}

    def hl_anim(nm):
        pts = [(0, 0)]
        for t0 in hl[nm]:
            pts += [(t0 - 0.02, 0), (t0 + 0.08, 0.32), (t0 + 0.55, 0)]
        return loop("opacity", T, pts, B0)
    boxes = ""
    order = 0
    for r, row in enumerate(names):
        for c, nm in enumerate(row):
            bx, by = cols[c], rows[r]
            centers[nm] = (bx + bw / 2, by + bh / 2, bx, by)
            primary = r == 0
            stroke = p["acc"] if primary else p["chipB"]
            fill = p["chip"]
            col = p["acc"] if primary else p["text2"]
            inner = (f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="9" fill="{fill}" stroke="{stroke}" '
                     f'stroke-width="1.4"/>'
                     f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="9" fill="{p["acc"]}" '
                     f'opacity="0">{hl_anim(nm)}</rect>'
                     + text(bx + bw / 2, by + bh / 2 + bfs * 0.36, nm, bfs, col, MONO, "600", "middle"))
            boxes += g_enter(inner, 0.8 + order * 0.09, 0.5, 6)
            order += 1
    cx = {k: v[0] for k, v in centers.items()}
    cy = {k: v[1] for k, v in centers.items()}
    top = {k: v[3] for k, v in centers.items()}
    gap = 3
    paths = {
        "e_aq": f'M{f(cols[0] + bw + gap)},{f(cy["api"])} H{f(cols[1] - gap - 2)}',
        "e_qw": f'M{f(cols[1] + bw + gap)},{f(cy["api"])} H{f(cols[2] - gap - 2)}',
        "e_ac": f'M{f(cx["api"])},{f(rows[0] + bh + gap)} V{f(rows[1] - gap - 2)}',
        "e_wi": f'M{f(cx["workers"] - bw * 0.2)},{f(rows[0] + bh + gap)} L{f(cx["index"] + bw * 0.2)},{f(rows[1] - gap - 2)}',
        "e_wl": f'M{f(cx["workers"])},{f(rows[0] + bh + gap)} V{f(rows[1] - gap - 2)}',
    }
    arc_h = 34 if not mobile else 46
    paths["e_resp"] = (f'M{f(cx["workers"])},{f(top["workers"] - gap)} C{f(cx["workers"])},{f(top["workers"] - arc_h)} '
                       f'{f(cx["api"])},{f(top["api"] - arc_h)} {f(cx["api"])},{f(top["api"] - gap - 2)}')
    defs += (f'<marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" '
             f'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{p["acc"]}"/></marker>')
    edges = ""
    for i, (pid, d) in enumerate(paths.items()):
        dashed = pid in ("e_ac", "e_resp")
        col = p["acc2"] if pid == "e_ac" else (p["acc3"] if pid == "e_resp" else p["acc"])
        attrs = f'd="{d}" fill="none" stroke="{col}" stroke-width="1.5" stroke-opacity="0.75"'
        if dashed:
            edges += g_enter(f'<path id="{pid}" {attrs} stroke-dasharray="4 5" marker-end="url(#arr)"/>', 1.2 + i * 0.08, 0.5, 0)
        else:
            edges += g_enter(f'<path id="{pid}" {attrs} marker-end="url(#arr)" pathLength="100" stroke-dasharray="100" '
                             f'stroke-dashoffset="100"><animate attributeName="stroke-dashoffset" from="100" to="0" '
                             f'begin="{f(1.1 + i * 0.1)}s" dur="0.5s" fill="freeze"/></path>', 1.1 + i * 0.1, 0.25, 0)
    pk = ""
    pr = 4.2 if not mobile else 6
    pk += packet("e_aq", T, 0.0, 0.6, p["acc"], pr, B0)
    pk += packet("e_ac", T, 0.0, 0.6, p["acc2"], pr * 0.8, B0)
    pk += packet("e_qw", T, 0.65, 1.25, p["acc"], pr, B0)
    pk += packet("e_wi", T, 1.3, 1.95, p["acc"], pr, B0)
    pk += packet("e_wl", T, 1.3, 1.95, p["acc"], pr, B0)
    pk += packet("e_wi", T, 2.05, 2.65, p["acc2"], pr * 0.85, B0, reverse=True)
    pk += packet("e_wl", T, 2.05, 2.65, p["acc2"], pr * 0.85, B0, reverse=True)
    pk += packet("e_resp", T, 2.75, 3.75, p["acc3"], pr, B0)
    # caption: highlight each stage in turn
    words = [("request", 0.0, 0.65), ("queue", 0.65, 1.3), ("retrieve", 1.3, 2.05),
             ("generate", 1.3, 2.7), ("respond", 2.75, 3.85)]
    cap = ""
    xpos = cols[0]
    sep = "  →  " if mobile else " → "
    for i, (w, a, b) in enumerate(words):
        cap += (f'<tspan fill="{p["muted"]}">{e(w)}'
                f'{loop("fill", T, [(a, p["muted"]), (a + 0.05, p["acc"]), (b, p["acc"]), (b + 0.15, p["muted"])], B0, "discrete")}'
                f'</tspan>')
        if i < len(words) - 1:
            cap += f'<tspan fill="{p["muted"]}" opacity="0.6">{e(sep)}</tspan>'
    caption = f'<text x="{xpos}" y="{cap_y}" font-family="{MONO}" font-size="{cap_size}">{cap}</text>'
    body += boxes + edges + pk + g_enter(caption, 1.6, 0.6, 0)
    title = "Siddharth, software engineer: backend systems, distributed pipelines, applied AI"
    return svg(W, H, title, body, defs)


# ----------------------------------------------------------------------------- neofetch terminal
NEO_LINES = [
    ("Role", "Software Engineer", "Software Engineer"),
    ("Focus", "Backend systems · Applied AI", "Backend systems · Applied AI"),
    ("Now", "AI Engineering Intern @ Hiring Bazaar", "AI Engineering Intern @ Hiring Bazaar"),
    ("Education", "B.Tech CSE · IIIT Naya Raipur", "B.Tech CSE · IIIT Naya Raipur"),
    ("CGPA", "9.74 / 10", "9.74 / 10"),
    ("Languages", "Python · TypeScript · C++ · C · SQL", "Python · TypeScript · C++ · C · SQL"),
    ("Backend", "FastAPI · Express · Celery · BullMQ · Redis", "FastAPI · Express · Celery · BullMQ"),
    ("Data", "PostgreSQL · SQLite · ChromaDB · FAISS", "PostgreSQL · Redis · ChromaDB · FAISS"),
    ("AI", "RAG · Agents · LangGraph · OpenAI Agents SDK", "RAG · LangGraph · OpenAI Agents SDK"),
    ("Research", "CSP optimisation · Multi-agent RL · LLM security", "CSP · Multi-agent RL · LLM security"),
    ("Practice", "Benchmarks · Test suites · CI · Fallbacks", "Benchmarks · Tests · CI · Fallbacks"),
    ("Motto", "\"Explain the why, not just the what.\"", "\"Explain the why, not just the what.\""),
]


def neofetch(mobile=False):
    p = DARK
    png = base64.b64encode(open(PORTRAIT, "rb").read()).decode()
    pw_px, ph_px = 104, 131
    if mobile:
        W, H = 620, 1048
        fs, lh = 16.5, 28
        prompt_y = 92
        img_w = 300
        img_x, img_y = (W - img_w) / 2, 118
        info_x, info_y0 = 28, 566
        bar_h = 46
    else:
        W, H = 900, 506
        fs, lh = 14, 22
        prompt_y = 74
        img_w = 246
        img_x, img_y = 26, 96
        info_x, info_y0 = 300, 112
        bar_h = 38
    img_h = img_w * ph_px / pw_px
    term_bg, bar_bg = "#0A0E13", "#121820"
    defs = GLOW
    body = (f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="{term_bg}" stroke="#2A3441" stroke-width="1.2"/>'
            f'<path d="M1,{bar_h} V15 a14,14 0 0 1 14,-14 H{W - 15} a14,14 0 0 1 14,14 V{bar_h} Z" fill="{bar_bg}"/>'
            f'<line x1="1" y1="{bar_h}" x2="{W - 1}" y2="{bar_h}" stroke="#2A3441"/>')
    dot_y, dr = bar_h / 2, (6.5 if not mobile else 8)
    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        body += f'<circle cx="{f(24 + i * (dr * 3.2))}" cy="{f(dot_y)}" r="{dr}" fill="{col}"/>'
    body += text(W / 2, dot_y + 4.5 * (1.3 if mobile else 1), "siddharth@github: ~", 12.5 if not mobile else 16,
                 "#7D8590", MONO, anchor="middle")
    # prompt + typed command
    px = 24
    prompt = (f'<text x="{px}" y="{prompt_y}" font-family="{MONO}" font-size="{fs}">'
              f'<tspan fill="#2DD4BF" font-weight="600">siddharth@github</tspan><tspan fill="#8B949E">:</tspan>'
              f'<tspan fill="#38BDF8">~</tspan><tspan fill="#8B949E">$ </tspan></text>')
    body += prompt
    cmd_x = px + mono_w("siddharth@github:~$ ", fs)
    t, t_end = typing("cmd", cmd_x, prompt_y, "neofetch", fs, "#E6EDF3", 0.35, cps=12, cursor="#E6EDF3",
                      cursor_hide=1.15)
    body += t
    out0 = 1.15
    # portrait: scanline render + CRT lines + periodic sweep
    steps = 34
    vals = ";".join(f(img_h * i / steps) for i in range(steps + 1))
    kts = ";".join(f"{i / steps:.4f}" for i in range(steps + 1))
    defs += (f'<clipPath id="reveal"><rect x="{f(img_x)}" y="{f(img_y)}" width="{f(img_w)}" height="0">'
             f'<animate attributeName="height" values="{vals}" keyTimes="{kts}" calcMode="discrete" '
             f'begin="{f(out0)}s" dur="1.3s" fill="freeze"/></rect></clipPath>'
             f'<pattern id="crt" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" '
             f'fill="#000" opacity="0.28"/></pattern>'
             f'<linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5EEAD4" '
             f'stop-opacity="0"/><stop offset="0.5" stop-color="#5EEAD4" stop-opacity="0.32"/>'
             f'<stop offset="1" stop-color="#5EEAD4" stop-opacity="0"/></linearGradient>'
             f'<clipPath id="imgclip"><rect x="{f(img_x)}" y="{f(img_y)}" width="{f(img_w)}" height="{f(img_h)}"/></clipPath>')
    body += (f'<g clip-path="url(#reveal)"><image x="{f(img_x)}" y="{f(img_y)}" width="{f(img_w)}" height="{f(img_h)}" '
             f'preserveAspectRatio="none" style="image-rendering:pixelated;image-rendering:crisp-edges" '
             f'href="data:image/png;base64,{png}" xlink:href="data:image/png;base64,{png}"/>'
             f'<rect x="{f(img_x)}" y="{f(img_y)}" width="{f(img_w)}" height="{f(img_h)}" fill="url(#crt)"/></g>')
    # scan bar during the render
    body += (f'<rect x="{f(img_x - 4)}" y="{f(img_y)}" width="{f(img_w + 8)}" height="3" fill="#99F6E4" opacity="0" '
             f'filter="url(#glow)"><animate attributeName="y" from="{f(img_y)}" to="{f(img_y + img_h)}" '
             f'begin="{f(out0)}s" dur="1.3s" fill="freeze"/><animate attributeName="opacity" values="0;0.9;0.9;0" '
             f'keyTimes="0;0.05;0.9;1" begin="{f(out0)}s" dur="1.3s" fill="freeze"/></rect>')
    # periodic soft sweep
    sw_h = 46
    body += (f'<g clip-path="url(#imgclip)"><rect x="{f(img_x)}" y="{f(img_y - sw_h)}" width="{f(img_w)}" '
             f'height="{sw_h}" fill="url(#sweep)">'
             f'{loop("y", 7, [(0, img_y - sw_h), (2.4, img_y + img_h), (7, img_y + img_h)], begin=3.2)}</rect></g>')
    # info block
    kw = 12 if mobile else 14
    y = info_y0
    hdr = (f'<text x="{info_x}" y="{y}" font-family="{MONO}" font-size="{fs}" font-weight="700">'
           f'<tspan fill="#2DD4BF">siddharth</tspan><tspan fill="#8B949E">@</tspan><tspan fill="#2DD4BF">github</tspan></text>')
    body += g_enter(hdr, out0, 0.4, 0, -6)
    y += lh * 0.95
    body += g_enter(text(info_x, y, "─" * 16, fs, "#3D4754", MONO), out0 + 0.08, 0.4, 0, -6)
    y += lh * 1.15
    for i, (k, v_d, v_m) in enumerate(NEO_LINES):
        v = v_m if mobile else v_d
        dots = "." * max(2, kw - len(k) - 2)
        vstyle = 'fill="#FBBF24" font-weight="700"' if k == "CGPA" else 'fill="#E6EDF3"'
        line = (f'<text x="{info_x}" y="{f(y)}" font-family="{MONO}" font-size="{fs}" xml:space="preserve">'
                f'<tspan fill="#2DD4BF">{e(k)}</tspan><tspan fill="#3D4754"> {dots} </tspan>'
                f'<tspan {vstyle}>{e(v)}</tspan></text>')
        body += g_enter(line, out0 + 0.18 + i * 0.085, 0.35, 0, -8)
        y += lh
    # colour blocks
    y += lh * 0.2
    colours = ["#484F58", "#FF7B72", "#3FB950", "#D29922", "#58A6FF", "#BC8CFF", "#39C5CF", "#B1BAC4"]
    bw = 26 if not mobile else 30
    for i, col in enumerate(colours):
        body += g_enter(f'<rect x="{f(info_x + i * bw)}" y="{f(y - fs * 0.9)}" width="{bw}" height="{f(fs * 1.15)}" fill="{col}"/>',
                        out0 + 1.3 + i * 0.05, 0.3, 0, 0)
    # final prompt with blinking cursor
    fy = H - (26 if not mobile else 34)
    fin = (f'<text x="{px}" y="{f(fy)}" font-family="{MONO}" font-size="{fs}">'
           f'<tspan fill="#2DD4BF" font-weight="600">siddharth@github</tspan><tspan fill="#8B949E">:</tspan>'
           f'<tspan fill="#38BDF8">~</tspan><tspan fill="#8B949E">$ </tspan></text>'
           f'<rect x="{f(cmd_x)}" y="{f(fy - fs * 0.86)}" width="{f(fs * 0.58)}" height="{f(fs * 1.08)}" fill="#E6EDF3">'
           f'<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" calcMode="discrete" dur="1.05s" '
           f'repeatCount="indefinite"/></rect>')
    body += g_enter(fin, out0 + 1.75, 0.2, 0, 0)
    title = ("neofetch-style profile card: Siddharth, Software Engineer; AI Engineering Intern at Hiring Bazaar; "
             "B.Tech CSE at IIIT Naya Raipur, CGPA 9.74/10; Python, TypeScript, C++; FastAPI, Celery, Redis, RAG")
    return svg(W, H, title, body, defs)


# ----------------------------------------------------------------------------- project motifs (370 x 194)
def inset(p, w=370, h=194):
    return f'<rect x="0" y="0" width="{w}" height="{h}" rx="12" fill="{p["inset"]}" stroke="{p["insetB"]}"/>'


def motif_examprep(p):
    T = 8.0
    s = inset(p)
    s += text(16, 24, "celery · job #7 · sse stream", 10.5, p["muted"], MONO)
    s += (f'<circle cx="324" cy="20" r="3.5" fill="{p["ok"]}"><animate attributeName="opacity" values="1;0.25;1" '
          f'dur="1.4s" repeatCount="indefinite"/></circle>' + text(332, 24, "live", 10.5, p["ok"], MONO))
    stages = [("ingest", 0.3, 1.3), ("structure", 1.35, 2.5), ("index", 2.55, 3.4)]
    for i, (nm, a, b) in enumerate(stages):
        y = 50 + i * 26
        s += text(16, y + 4, nm, 11.5, p["text2"], MONO)
        s += f'<rect x="100" y="{y - 4}" width="190" height="8" rx="4" fill="{p["chipB"]}" opacity="0.7"/>'
        s += (f'<rect x="100" y="{y - 4}" width="0" height="8" rx="4" fill="{p["acc"]}">'
              f'{loop("width", T, [(a, 0), (b, 190), (T - 0.4, 190), (T - 0.1, 0)])}</rect>')
        s += (f'<g opacity="0">{window(T, b, T - 0.25, 0.15)}'
              + text(300, y + 4, "✓ done", 11, p["ok"], MONO) + '</g>')
    s += f'<line x1="16" y1="122" x2="354" y2="122" stroke="{p["insetB"]}"/>'
    q1 = (f'<g opacity="0">{window(T, 3.6, T - 0.25, 0.2)}'
          + text(16, 144, "› \"tcp congestion window\"", 11.5, p["text"], MONO) + '</g>')
    s += q1
    seq = [("BM25", 16, 4.1, p["acc2"]), ("dense", 80, 4.3, p["acc2"]), ("RRF", 166, 4.7, p["acc"]),
           ("cited answer", 236, 5.1, p["ok"])]
    for lab, x, a, col in seq:
        w = len(lab) * 11 * 0.6 + 16
        s += (f'<g opacity="0">{window(T, a, T - 0.25, 0.2)}'
              f'<rect x="{x}" y="160" width="{f(w)}" height="22" rx="8" fill="{col}" fill-opacity="0.14" stroke="{col}" '
              f'stroke-opacity="0.6"/>' + text(x + 8, 175, lab, 11, col, MONO) + '</g>')
    for x1, x2, a in ((58, 80, 4.3), (135, 166, 4.7), (201, 236, 5.1)):
        sym = "+" if x1 == 64 else "→"
        s += (f'<g opacity="0">{window(T, a, T - 0.25, 0.2)}'
              + text((x1 + x2) / 2 + (0 if sym == "+" else 0), 175, sym, 12, p["muted"], MONO, anchor="middle") + '</g>')
    return s


def motif_causalline(p):
    T = 8.4
    s = inset(p)
    N = {"S": (44, 104), "A1": (118, 60), "A2": (118, 148), "A3": (200, 60), "A4": (200, 148), "A5": (282, 104)}
    E = [("S", "A1", "inf"), ("S", "A2", "exp"), ("A1", "A3", "inf"), ("A2", "A4", "exp"),
         ("A1", "A4", "exp"), ("A3", "A5", "inf"), ("A4", "A5", "exp")]
    r = 13
    for a_, b_, kind in E:
        (x1, y1), (x2, y2) = N[a_], N[b_]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        sx, sy, ex, ey = x1 + ux * (r + 2), y1 + uy * (r + 2), x2 - ux * (r + 4), y2 - uy * (r + 4)
        s += f'<line x1="{f(sx)}" y1="{f(sy)}" x2="{f(ex)}" y2="{f(ey)}" stroke="{p["chipB"]}" stroke-width="1.6"/>'
        if kind == "inf":
            order = {"S": 0, "A1": 1, "A3": 2}[a_]
            a = 2.0 + order * 0.4
            s += (f'<line x1="{f(sx)}" y1="{f(sy)}" x2="{f(ex)}" y2="{f(ey)}" stroke="{p["bad"]}" stroke-width="2.2" '
                  f'opacity="0">{window(T, a, 4.6 + order * 0.45, 0.2)}</line>')
        else:
            s += (f'<line x1="{f(sx)}" y1="{f(sy)}" x2="{f(ex)}" y2="{f(ey)}" stroke="{p["warn"]}" stroke-width="1.8" '
                  f'stroke-dasharray="3 4" opacity="0">{window(T, 2.2, 4.0, 0.2)}</line>')
    for nm, (x, y) in N.items():
        label = "src" if nm == "S" else nm.lower()
        s += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{p["chip"]}" stroke="{p["acc"]}" stroke-width="1.6"/>'
        if nm == "S":
            s += (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{p["bad"]}" opacity="0">{window(T, 1.0, T - 0.3, 0.2)}</circle>'
                  f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{p["bad"]}" stroke-width="1.5" opacity="0">'
                  f'{loop("r", T, [(1.0, r), (1.9, r + 11), (T, r + 11)])}{window(T, 1.0, 1.9, 0.1)}</circle>')
        if nm in ("A1", "A3", "A5"):
            k = {"A1": 0, "A3": 1, "A5": 2}[nm]
            a = 2.4 + k * 0.4
            rep = 4.6 + k * 0.45
            s += (f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{p["bad"]}" stroke-width="2.4" opacity="0">'
                  f'{window(T, a, rep, 0.15)}</circle>')
            s += (f'<circle cx="{x}" cy="{y}" r="{r + 4}" fill="none" stroke="{p["acc"]}" stroke-width="2" '
                  f'stroke-dasharray="6 5" opacity="0">{window(T, rep - 0.05, rep + 0.75, 0.12)}'
                  f'<animateTransform attributeName="transform" type="rotate" from="0 {x} {y}" to="360 {x} {y}" '
                  f'dur="1.2s" repeatCount="indefinite"/></circle>')
            s += (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{p["acc"]}" opacity="0">'
                  f'{loop("opacity", T, [(rep + 0.6, 0), (rep + 0.85, 0.85), (T - 0.4, 0.85), (T - 0.1, 0)])}</circle>')
        if nm in ("A2", "A4"):
            s += (f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{p["warn"]}" stroke-width="2.2" opacity="0">'
                  f'{window(T, 2.3, 4.0, 0.2)}</circle>'
                  f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{p["ok"]}" stroke-width="2.2" opacity="0">'
                  f'{window(T, 4.0, T - 0.3, 0.2)}</circle>')
        s += text(x, y + 4, label, 10, p["text"], MONO, "600", "middle")
    s += (f'<g opacity="0">{window(T, 1.0, T - 0.3, 0.2)}' + text(16, 22, "detector: poisoned source", 10.5, p["bad"], MONO)
          + '</g>')
    s += (f'<g opacity="0">{window(T, 2.3, T - 0.3, 0.2)}' + text(16, 186, "exposed ≠ influenced", 10.5, p["warn"], MONO)
          + '</g>')
    s += (f'<g opacity="0">{window(T, 4.8, T - 0.3, 0.2)}' + text(354, 186, "replayed · kept", 10.5, p["acc"], MONO, anchor="end")
          + '</g>')
    s += (f'<g opacity="0">{window(T, 6.2, T - 0.3, 0.2)}' + text(354, 22, "✓ verified", 11, p["ok"], MONO, "600", "end")
          + '</g>')
    return s


def motif_studyai(p):
    T = 7.0
    s = inset(p)
    # document
    dx, dy = 22, 62
    s += (f'<path d="M{dx},{dy} h34 l12,12 v46 h-46 z" fill="{p["chip"]}" stroke="{p["acc"]}" stroke-width="1.5"/>'
          f'<path d="M{dx + 34},{dy} v12 h12" fill="none" stroke="{p["acc"]}" stroke-width="1.5"/>')
    for i in range(4):
        s += f'<rect x="{dx + 8}" y="{dy + 18 + i * 9}" width="{30 - (i % 2) * 8}" height="3" rx="1.5" fill="{p["muted"]}"/>'
    s += text(dx + 23, dy + 74, "notes.pdf", 10, p["muted"], MONO, anchor="middle")
    outs = ["flashcards", "MCQs", "mind map", "learning path", "revision notes", "exam questions"]
    cx0, w, h, step = 132, 124, 22, 27
    for i, lab in enumerate(outs):
        y = 15 + i * step
        a = 0.5 + i * 0.3
        pid = f"beam{i}"
        sx, sy = dx + 48, dy + 30
        ex, ey = cx0 - 3, y + h / 2
        d = f"M{sx},{sy} C{sx + 34},{sy} {ex - 34},{f(ey)} {ex},{f(ey)}"
        s += f'<path id="{pid}" d="{d}" fill="none" stroke="{p["chipB"]}" stroke-width="1.3"/>'
        s += (f'<path d="{d}" fill="none" stroke="{p["acc"]}" stroke-width="1.6" opacity="0">'
              f'{window(T, a + 0.3, T - 0.3, 0.2)}</path>')
        s += packet(pid, T, a, a + 0.32, p["acc"], 3.2)
        s += f'<rect x="{cx0}" y="{y}" width="{w}" height="{h}" rx="7" fill="{p["chip"]}" stroke="{p["chipB"]}"/>'
        s += (f'<rect x="{cx0}" y="{y}" width="{w}" height="{h}" rx="7" fill="{p["acc"]}" fill-opacity="0.16" '
              f'stroke="{p["acc"]}" opacity="0">{window(T, a + 0.32, T - 0.3, 0.15)}</rect>')
        s += text(cx0 + w / 2, y + 15, lab, 10.5, p["text"], MONO, anchor="middle")
    bx, by, bw, bh = 270, 52, 88, 88
    s += (f'<g opacity="0">{window(T, 2.6, T - 0.3, 0.25)}'
          f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="{p["acc2"]}" fill-opacity="0.12" '
          f'stroke="{p["acc2"]}" stroke-opacity="0.55"/>'
          + text(bx + 10, by + 22, "Q&A", 11, p["acc2"], MONO, "700")
          + text(bx + 10, by + 42, "answers", 10.5, p["text"], MONO)
          + text(bx + 10, by + 57, "only from", 10.5, p["text"], MONO)
          + text(bx + 10, by + 72, "your doc ✓", 10.5, p["acc2"], MONO) + '</g>')
    return s


def motif_proveit(p):
    T = 8.0
    s = inset(p)
    heads = [("CODE DECIDES", 70), ("AGENTS ARGUE", 194), ("HUMANS RULE", 310)]
    for h, x in heads:
        s += text(x, 22, h, 9.5, p["muted"], MONO, "600", "middle", ls=1)
    # sandbox
    s += f'<rect x="14" y="34" width="112" height="118" rx="10" fill="{p["chip"]}" stroke="{p["chipB"]}"/>'
    s += (f'<path d="M24,48 v-4 a5,5 0 0 1 10,0 v4" fill="none" stroke="{p["muted"]}" stroke-width="1.5"/>'
          f'<rect x="21" y="48" width="16" height="11" rx="2" fill="{p["muted"]}"/>')
    s += text(42, 57, "sandbox", 10, p["muted"], MONO)
    rows = [("vulnerable", 76, "CODE_EXECUTION", p["bad"], 0.6), ("patched", 112, "NOT_REPRODUCED", p["ok"], 1.3)]
    for lab, y, res, col, a in rows:
        s += text(22, y, lab, 9.5, p["muted"], MONO)
        s += (f'<g opacity="0">{window(T, a, T - 0.3, 0.2)}' + text(22, y + 15, res, 10, col, MONO, "700") + '</g>')
    s += (f'<g opacity="0">{window(T, 1.6, T - 0.3, 0.2)}' + text(22, 144, "3/3 runs each", 9.5, p["text2"], MONO) + '</g>')
    # agents
    for nm, x, col in (("R", 166, p["acc"]), ("S", 222, p["acc3"])):
        s += f'<circle cx="{x}" cy="50" r="14" fill="{p["chip"]}" stroke="{col}" stroke-width="1.6"/>'
        s += text(x, 54.5, nm, 12, col, MONO, "700", "middle")
    s += text(166, 76, "claude", 9, p["muted"], MONO, anchor="middle") + text(222, 76, "codex", 9, p["muted"], MONO, anchor="middle")
    bubbles = [(140, 88, "reproduced", p["acc"], 2.0), (150, 112, "dispute", p["warn"], 2.7), (150, 136, "concur ✓", p["ok"], 3.5)]
    for x, y, lab, col, a in bubbles:
        w = len(lab) * 10 * 0.6 + 16
        s += (f'<g opacity="0">{window(T, a, T - 0.3, 0.2)}<rect x="{x}" y="{y}" width="{f(w)}" height="19" rx="8" '
              f'fill="{col}" fill-opacity="0.14" stroke="{col}" stroke-opacity="0.6"/>'
              + text(x + 8, y + 13.5, lab, 10, col, MONO) + '</g>')
    # maintainer
    mx = 310
    s += (f'<circle cx="{mx}" cy="46" r="9" fill="none" stroke="{p["text2"]}" stroke-width="1.6"/>'
          f'<path d="M{mx - 16},76 a16,14 0 0 1 32,0" fill="none" stroke="{p["text2"]}" stroke-width="1.6"/>')
    s += text(mx, 94, "maintainer", 9.5, p["muted"], MONO, anchor="middle")
    s += (f'<g opacity="0">{window(T, 4.4, T - 0.3, 0.2)}<rect x="{mx - 40}" y="106" width="80" height="22" rx="8" '
          f'fill="{p["acc"]}" fill-opacity="0.16" stroke="{p["acc"]}"/>'
          + text(mx, 121, "escalate ✓", 10.5, p["acc"], MONO, "600", "middle") + '</g>')
    # state ticker
    states = [("in_triage", 0.2, 2.0), ("reproduced", 2.0, 2.7), ("disputed", 2.7, 4.4), ("escalated", 4.4, T - 0.3)]
    tick = ""
    for i, (st, a, b) in enumerate(states):
        tick += (f'<tspan fill="{p["muted"]}">{e(st)}'
                 f'{loop("fill", T, [(a, p["muted"]), (a + 0.05, p["acc"]), (b, p["acc"]), (b + 0.05, p["muted"])], 0, "discrete")}'
                 f'</tspan>')
        if i < len(states) - 1:
            tick += f'<tspan fill="{p["muted"]}" opacity="0.6"> → </tspan>'
    s += f'<text x="14" y="180" font-family="{MONO}" font-size="10.5">{tick}</text>'
    return s


def motif_lumen(p):
    T = 7.4
    s = inset(p)
    # receipt
    rx0, ry0, rw, rh = 22, 20, 104, 150
    zig = "".join(f" l-{f(rw / 16)},6 l-{f(rw / 16)},-6" for _ in range(8))
    s += f'<path d="M{rx0},{ry0} h{rw} v{rh}{zig} z" fill="{p["chip"]}" stroke="{p["chipB"]}"/>'
    s += text(rx0 + 10, ry0 + 20, "FreshMart", 11, p["text"], SANS, "700")
    for i in range(5):
        s += f'<rect x="{rx0 + 10}" y="{ry0 + 34 + i * 14}" width="{56 + (i * 13) % 26}" height="4" rx="2" fill="{p["muted"]}" opacity="0.55"/>'
    s += f'<line x1="{rx0 + 10}" y1="{ry0 + 110}" x2="{rx0 + rw - 10}" y2="{ry0 + 110}" stroke="{p["muted"]}" stroke-dasharray="3 3"/>'
    s += text(rx0 + 10, ry0 + 128, "TOTAL ₹1,159.20", 9.5, p["text"], MONO, "700")
    s += (f'<rect x="{rx0 - 4}" y="{ry0}" width="{rw + 8}" height="2.5" fill="{p["acc"]}" filter="url(#glow)" opacity="0">'
          f'{loop("y", T, [(0.3, ry0), (1.7, ry0 + rh - 4), (T, ry0 + rh - 4)])}{window(T, 0.3, 1.75, 0.1)}</rect>')
    fields = [("merchant", "FreshMart", 1.8), ("total", "₹1,159.20", 2.1), ("category", "Groceries", 2.4),
              ("index", "per-user FAISS", 2.8)]
    for i, (k, v, a) in enumerate(fields):
        y = 34 + i * 22
        col = p["acc"] if k == "category" else (p["acc2"] if k == "index" else p["text"])
        s += (f'<g opacity="0">{window(T, a, T - 0.3, 0.2)}' + text(148, y, k, 10.5, p["muted"], MONO)
              + text(222, y, v, 10.5, col, MONO, "600" if k in ("category", "index") else None) + '</g>')
    s += (f'<g opacity="0">{window(T, 3.4, T - 0.3, 0.2)}<rect x="148" y="122" width="206" height="22" rx="9" '
          f'fill="{p["chip"]}" stroke="{p["chipB"]}"/>' + text(158, 137, "› spend on groceries?", 10.5, p["text"], MONO) + '</g>')
    s += (f'<g opacity="0">{window(T, 4.2, T - 0.3, 0.2)}<rect x="168" y="150" width="186" height="22" rx="9" '
          f'fill="{p["acc"]}" fill-opacity="0.14" stroke="{p["acc"]}" stroke-opacity="0.6"/>'
          + text(178, 165, "answered from your data", 10.5, p["acc"], MONO) + '</g>')
    return s


PROJECTS = [
    dict(slug="examprep", idx="01", name="ExamPrep AI", pill="SOLO BUILD",
         tag=["Turns slides and past papers into an exam-ranked", "knowledge base that answers with citations."],
         tag_m=["Turns slides and past papers into an", "exam-ranked knowledge base that", "answers with citations."],
         chips=["FastAPI", "Celery", "Redis", "ChromaDB", "Agents SDK"], motif=motif_examprep),
    dict(slug="causalline", idx="02", name="CausalLine", pill="LEAD DEVELOPER · RESEARCH",
         tag=["Recovers multi-agent LLM workflows after prompt", "injection, replaying only the work it influenced."],
         tag_m=["Recovers multi-agent LLM workflows", "after prompt injection, replaying only", "the work it influenced."],
         chips=["Python 3.11", "Provenance", "Counterfactuals", "600+ tests"], motif=motif_causalline),
    dict(slug="studyai", idx="03", name="Study AI", pill="3RD PLACE · APIHUB 2025",
         tag=["Turns notes into six kinds of study material, with", "grounded document Q&A and shared study groups."],
         tag_m=["Turns notes into six kinds of study", "material, with grounded document Q&A", "and shared study groups."],
         chips=["FastAPI", "SQLAlchemy", "FAISS + BM25", "OAuth 2.0"], motif=motif_studyai),
    dict(slug="proveit", idx="04", name="Prove It", pill="HACKATHON · TEAM OF 4",
         tag=["Bug reports must reproduce in a locked-down sandbox", "before a maintainer reads them."],
         tag_m=["Bug reports must reproduce in a", "locked-down sandbox before a", "maintainer reads them."],
         chips=["Docker", "Claude Code", "Codex", "325 tests · CI"], motif=motif_proveit),
    dict(slug="lumen", idx="05", name="Lumen", pill="2ND PLACE (NATIONAL) · HACK-A-SOL",
         tag=["Reads receipts with an LLM, categorises spending,", "and answers questions from the user's own records."],
         tag_m=["Reads receipts with an LLM,", "categorises spending, and answers", "questions from your own records."],
         chips=["FastAPI", "PostgreSQL", "React + TS", "FAISS", "Gemini"], motif=motif_lumen),
]


def project_card(pr, p, mobile=False):
    if mobile:
        W = 620
        x0 = 32
        sc = 556 / 370
        cr, chips_bottom = chips_row(x0, 174 + len(pr["tag_m"]) * 30 - 4, pr["chips"], p, size=15, h=32, gap=10,
                                     max_x=W - 32)
        oy = chips_bottom + 26
        H = int(oy + 194 * sc + 30)
        defs, body = card(W, H, p, running=True, run_dur=14)
        body += text(x0, 62, pr["idx"], 18, p["acc"], MONO, "700")
        _, ps = pill(x0 + 40, 44, pr["pill"], p["acc"], p, size=13, h=27)
        body += ps
        body += g_enter(text(x0, 134, pr["name"], 44, p["text"], SANS, "700", ls=-0.5), 0.2, 0.6, 8)
        for i, ln in enumerate(pr["tag_m"]):
            body += g_enter(text(x0, 174 + i * 30, ln, 21, p["text2"]), 0.35 + i * 0.08, 0.6, 6)
        body += g_enter(cr, 0.6, 0.6, 6)
        defs += GLOW
        body += f'<g transform="translate({x0},{f(oy)}) scale({f(sc)})">{pr["motif"](p)}</g>'
    else:
        W, H = 900, 250
        defs, body = card(W, H, p, running=True, run_dur=12)
        defs += GLOW
        x0 = 36
        body += text(x0, 51, pr["idx"], 13, p["acc"], MONO, "700")
        _, ps = pill(x0 + 30, 36, pr["pill"], p["acc"], p)
        body += ps
        body += g_enter(text(x0, 108, pr["name"], 34, p["text"], SANS, "700", ls=-0.5), 0.15, 0.6, 8)
        for i, ln in enumerate(pr["tag"]):
            body += g_enter(text(x0, 142 + i * 22, ln, 15, p["text2"]), 0.3 + i * 0.08, 0.6, 6)
        cr, _ = chips_row(x0, 194, pr["chips"], p, size=11.5, h=25, gap=8, max_x=480)
        body += g_enter(cr, 0.5, 0.6, 6)
        body += f'<g transform="translate(500,28)">{pr["motif"](p)}</g>'
    title = f'{pr["name"]}: ' + " ".join(pr["tag"])
    return svg(W, H, title, body, defs)


# ----------------------------------------------------------------------------- small project cards
MORE = [
    dict(slug="finance", name="Finance RBAC Backend",
         lines=["Async fintech API with RBAC enforced", "at route and query level, Decimal", "money, UUID keys, soft deletes."],
         chips=["FastAPI", "asyncpg", "Alembic"]),
    dict(slug="mpwms", name="MP-WMS Workforce Portal",
         lines=["Role-based portal for power-plant", "maintenance: six-level hierarchy,", "work-order state machine, audit log."],
         chips=["FastAPI", "React + TS", "pytest"]),
    dict(slug="airquality", name="Air-Quality Forecasting",
         lines=["Stacked XGBoost + LightGBM ensemble", "on CPCB data: PM2.5 R² 0.883,", "benchmarked against published work."],
         chips=["XGBoost", "LightGBM", "RidgeCV"]),
]


def mini_card(m, p, i):
    W, H = 284, 176
    defs, body = card(W, H, p, rx=14, grid=False, running=False)
    defs += (f'<linearGradient id="topline" gradientUnits="userSpaceOnUse" x1="-200" y1="0" x2="0" y2="0">'
             f'<stop offset="0" stop-color="{p["acc"]}" stop-opacity="0"/><stop offset="0.5" stop-color="{p["acc"]}"/>'
             f'<stop offset="1" stop-color="{p["acc"]}" stop-opacity="0"/>'
             f'{loop("x1", 6, [(0, -200), (2.2, W), (6, W)], begin=0.4 + i * 0.7)}'
             f'{loop("x2", 6, [(0, 0), (2.2, W + 200), (6, W + 200)], begin=0.4 + i * 0.7)}</linearGradient>')
    body += f'<rect x="14" y="1" width="{W - 28}" height="2" fill="url(#topline)"/>'
    body += text(18, 38, m["name"], 16, p["text"], SANS, "700")
    body += text(W - 18, 37, "↗", 14, p["muted"], SANS, anchor="end")
    for k, ln in enumerate(m["lines"]):
        body += text(18, 66 + k * 19, ln, 12, p["text2"])
    cr, _ = chips_row(18, 136, m["chips"], p, size=10.5, h=22, gap=6)
    body += cr
    return svg(W, H, f'{m["name"]}: ' + " ".join(m["lines"]), g_enter(body, 0.1 + i * 0.12, 0.6, 6), defs)


# ----------------------------------------------------------------------------- research
RESEARCH = [
    dict(status="ONGOING", color="warn", venue="Paper in preparation · first author, lead developer",
         venue_m=["Paper in preparation", "First author, lead developer"],
         title=["CausalLine: Influence-Aware Selective Recovery After", "Prompt Injection in Multi-Agent LLM Systems"],
         title_m=["CausalLine: Influence-Aware Selective", "Recovery After Prompt Injection in", "Multi-Agent LLM Systems"],
         summary="Recovers compromised agent workflows by replaying only influenced work, then verifying the result.",
         summary_m=["Recovers compromised agent workflows by", "replaying only influenced work, then", "verifying the result."]),
    dict(status="ACCEPTED", color="ok", venue="MMCITRE 2025 · Springer LNNS Vol. 2101 (forthcoming) · first author",
         venue_m=["MMCITRE 2025 · Springer LNNS Vol. 2101", "Forthcoming · first author"],
         title=["2D Floor Plan Generation via Constraint Satisfaction Problem Modeling"],
         title_m=["2D Floor Plan Generation via Constraint", "Satisfaction Problem Modeling"],
         summary="CP-SAT model, no training data: 100% hard-constraint satisfaction, 85.82% space utilisation, <8 s solves.",
         summary_m=["CP-SAT model with no training data: 100%", "hard-constraint satisfaction, 85.82% space", "utilisation, under 8 s average solve."]),
    dict(status="ACCEPTED", color="ok", venue="NCA 2026 workshop, Italy · not yet published · first author",
         venue_m=["NCA 2026 workshop, Italy", "Not yet published · first author"],
         title=["Comparative Performance Evaluation of Fixed-Time and Hierarchical", "Traffic Signal Control Using Real-World Urban Traffic Data"],
         title_m=["Comparative Performance Evaluation of", "Fixed-Time and Hierarchical Traffic Signal", "Control Using Real-World Urban Traffic Data"],
         summary="Double-DQN control in SUMO on real SCATS data: 94%+ lower average wait than fixed-time plans, +15% throughput.",
         summary_m=["Double-DQN control in SUMO on real SCATS", "data: over 94% lower average wait than", "fixed-time plans, +15% network throughput."]),
]


def research(p, mobile=False):
    if mobile:
        W = 620
        row_h = [300, 280, 300]
        fs_t, fs_s, fs_v = 21, 17, 14.5
    else:
        W = 900
        row_h = [150, 128, 150]
        fs_t, fs_s, fs_v = 17, 13.2, 11.5
    H = sum(row_h) + 12
    defs, body = card(W, H, p, rx=18, grid=False, running=False)
    y0 = 6
    for i, r in enumerate(RESEARCH):
        col = p[r["color"]]
        h = row_h[i]
        inner = ""
        x0 = 30 if not mobile else 28
        # status bar that grows in
        inner += (f'<rect x="{x0 - 14}" y="{y0 + 22}" width="3" height="0" rx="1.5" fill="{col}">'
                  f'<animate attributeName="height" from="0" to="{h - 44}" begin="{f(0.3 + i * 0.2)}s" dur="0.7s" '
                  f'fill="freeze"/></rect>')
        pw, ps = pill(x0, y0 + 22, r["status"], col, p, size=10.5 if not mobile else 13.5,
                      h=22 if not mobile else 28, dot=(r["status"] == "ONGOING"))
        inner += ps
        if r["status"] == "ACCEPTED":
            # check mark inside a small circle after the pill + periodic shine on the pill
            cxp = x0 + pw + (14 if not mobile else 18)
            inner += (f'<circle cx="{f(cxp)}" cy="{f(y0 + 22 + (11 if not mobile else 14))}" r="{8 if not mobile else 10}" '
                      f'fill="{col}"/><path d="M{f(cxp - 4)},{f(y0 + 22 + (11 if not mobile else 14))} l3,3 l5,-6" '
                      f'fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round"/>')
        vx = x0 + pw + (34 if r["status"] == "ACCEPTED" else 12) + (8 if mobile else 0)
        if mobile:
            ty = y0 + 22 + 28 + 30
            for k, ln in enumerate(r["venue_m"]):
                inner += text(x0, ty + k * 21, ln, fs_v, p["muted"], MONO)
            ty += len(r["venue_m"]) * 21 + 16
        else:
            inner += text(vx, y0 + 37, r["venue"], fs_v, p["muted"], MONO)
            ty = y0 + 22 + 22 + 30
        tl = r["title_m"] if mobile else r["title"]
        for k, ln in enumerate(tl):
            inner += text(x0, ty + k * (fs_t * 1.32), ln, fs_t, p["text"], SANS, "700")
        sy = ty + (len(tl) - 1) * fs_t * 1.32 + fs_t * 1.45
        sl = r["summary_m"] if mobile else [r["summary"]]
        for k, ln in enumerate(sl):
            inner += text(x0, sy + k * fs_s * 1.4, ln, fs_s, p["text2"])
        body += g_enter(inner, 0.15 + i * 0.2, 0.6, 8)
        if i < len(RESEARCH) - 1:
            body += f'<line x1="20" y1="{y0 + h}" x2="{W - 20}" y2="{y0 + h}" stroke="{p["border"]}"/>'
        y0 += h
    title = "Research: " + " | ".join(" ".join(r["title"]) + " (" + r["status"].lower() + ")" for r in RESEARCH)
    return svg(W, H, title, body, defs)


# ----------------------------------------------------------------------------- tech stack
STACK = [
    ("Languages", [("Python", "python"), ("TypeScript", "typescript"), ("JavaScript", "javascript"),
                   ("C++", "cplusplus"), ("C", "c"), ("SQL", None)]),
    ("Backend & APIs", [("FastAPI", "fastapi"), ("Node.js", "nodedotjs"), ("Express", "express"), ("Prisma", "prisma"),
                        ("SQLAlchemy", "sqlalchemy"), ("Pydantic", "pydantic"), ("Zod", "zod"), ("LiveKit", "livekit"),
                        ("REST · WebSockets · SSE", None)]),
    ("Data & Messaging", [("PostgreSQL", "postgresql"), ("SQLite", "sqlite"), ("Redis", "redis"), ("Celery", "celery"),
                          ("BullMQ", None), ("RabbitMQ", "rabbitmq"), ("ChromaDB", None), ("FAISS", None)]),
    ("AI & LLM", [("OpenAI Agents SDK", None), ("LangChain", "langchain"), ("LangGraph", "langgraph"),
                  ("Gemini", "googlegemini"), ("Ollama", "ollama"), ("Sentence Transformers", "huggingface"),
                  ("Hybrid search · BM25 + RRF", None)]),
    ("ML & Optimisation", [("PyTorch", "pytorch"), ("scikit-learn", "scikitlearn"), ("XGBoost", None),
                           ("LightGBM", None), ("OR-Tools CP-SAT", "google"), ("SUMO", None)]),
    ("Frontend", [("React", "react"), ("Next.js", "nextdotjs"), ("Vite", "vite")]),
    ("DevOps & Tooling", [("Docker", "docker"), ("GitHub Actions", "githubactions"), ("Git", "git"),
                          ("pytest", "pytest"), ("n8n", "n8n")]),
]
_SI = {"c": "A8B9CC", "celery": "37814A", "cplusplus": "00599C", "docker": "2496ED", "express": "0A0A0A", "fastapi": "009688", "git": "F03C2E", "githubactions": "2088FF", "google": "4285F4", "googlegemini": "8E75B2", "huggingface": "FFD21E", "javascript": "F7DF1E", "langchain": "7FC8FF", "langgraph": "7FC8FF", "livekit": "FFFFFF", "n8n": "FF91AC", "nextdotjs": "000000", "nodedotjs": "5FA04E", "ollama": "000000", "postgresql": "4169E1", "prisma": "2D3748", "pydantic": "E92063", "pytest": "0A9EDC", "python": "3776AB", "pytorch": "EE4C2C", "rabbitmq": "FF6600", "react": "61DAFB", "redis": "FF4438", "scikitlearn": "F7931E", "sqlalchemy": "D71F00", "sqlite": "003B57", "typescript": "3178C6", "vite": "9135FF", "zod": "408AFF"}


def icon_path(slug):
    path = os.path.join(ICON_CACHE, f"{slug}.svg")
    if not os.path.exists(path):
        os.makedirs(ICON_CACHE, exist_ok=True)
        urllib.request.urlretrieve(f"https://cdn.jsdelivr.net/npm/simple-icons@{SI_VERSION}/icons/{slug}.svg", path)
    raw = open(path, encoding="utf-8").read()
    return re.search(r'<path d="([^"]+)"', raw).group(1)


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def mix(hexc, other, t):
    a = [int(hexc[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(other[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def icon_color(slug, p):
    hexc = _SI.get(slug, "2DD4BF")
    L = lum(hexc)
    if p is DARK and L < 0.28:
        return mix(hexc, "FFFFFF", 0.72) if L < 0.08 else mix(hexc, "FFFFFF", 0.45)
    if p is LIGHT and L > 0.72:
        return mix(hexc, "000000", 0.35)
    return "#" + hexc


def stack(p, mobile=False):
    if mobile:
        W, fs, h, gap, isz = 620, 15.5, 38, 10, 20
        lab_fs = 15
    else:
        W, fs, h, gap, isz = 900, 12.5, 30, 8, 16
        lab_fs = 12
    body, y = "", 26
    n = 0
    for cat, items in STACK:
        if mobile:
            body += g_enter(text(26, y + 14, cat.upper(), lab_fs, p["acc"], MONO, "700", ls=1.5), 0.1 + n * 0.02, 0.4, 0, -6)
            y += 28
            x_start, max_x = 26, W - 24
        else:
            body += g_enter(f'<rect x="24" y="{y + 8}" width="3" height="14" rx="1.5" fill="{p["acc"]}"/>'
                            + text(36, y + 20, cat.upper(), lab_fs, p["text2"], MONO, "700", ls=1.2), 0.1 + n * 0.02, 0.4, 0, -6)
            x_start, max_x = 214, W - 24
        x = x_start
        for lab, slug in items:
            w = 12 + isz + 9 + len(lab) * fs * 0.6 + 12
            if x + w > max_x and x > x_start:
                x, y = x_start, y + h + gap
            ic = ""
            if slug:
                sc = isz / 24
                ic = (f'<path transform="translate({f(x + 12)},{f(y + (h - isz) / 2)}) scale({f(sc)})" '
                      f'fill="{icon_color(slug, p)}" d="{icon_path(slug)}"/>')
            else:
                cx0, cy0 = x + 12 + isz / 2, y + h / 2
                d = isz * 0.32
                ic = (f'<path d="M{f(cx0)},{f(cy0 - d)} L{f(cx0 + d)},{f(cy0)} L{f(cx0)},{f(cy0 + d)} '
                      f'L{f(cx0 - d)},{f(cy0)} Z" fill="{p["acc"]}"/>')
            c = (f'<rect x="{f(x)}" y="{y}" width="{f(w)}" height="{h}" rx="8" fill="{p["chip"]}" stroke="{p["chipB"]}"/>'
                 + ic + text(x + 12 + isz + 9, y + h / 2 + fs * 0.36, lab, fs, p["text"], MONO))
            body += g_enter(c, 0.15 + n * 0.035, 0.45, 6)
            n += 1
            x += w + gap
        y += h + (22 if not mobile else 26)
    H = y + 4
    defs, bg = card(W, H, p, rx=18, grid=True, running=False)
    return svg(W, H, "Tech stack: " + "; ".join(f"{c}: " + ", ".join(i[0] for i in it) for c, it in STACK),
               bg + body, defs)


# ----------------------------------------------------------------------------- awards
def trophy(cx, cy, col):
    return (f'<path d="M{cx - 11},{cy - 12} h22 v8 a11,11 0 0 1 -22,0 z" fill="none" stroke="{col}" stroke-width="2"/>'
            f'<path d="M{cx - 11},{cy - 9} h-5 a5,6 0 0 0 5,9 M{cx + 11},{cy - 9} h5 a5,6 0 0 1 -5,9" fill="none" '
            f'stroke="{col}" stroke-width="2"/><path d="M{cx},{cy + 7} v5 M{cx - 7},{cy + 14} h14" stroke="{col}" '
            f'stroke-width="2" stroke-linecap="round"/>')


def medal(cx, cy, col):
    return (f'<path d="M{cx - 8},{cy - 15} l5,10 M{cx + 8},{cy - 15} l-5,10" stroke="{col}" stroke-width="2" '
            f'stroke-linecap="round"/><circle cx="{cx}" cy="{cy + 4}" r="10" fill="none" stroke="{col}" stroke-width="2"/>'
            + text(cx, cy + 8.5, "3", 12, col, SANS, "700", "middle"))


def star(cx, cy, col):
    pts = []
    for k in range(10):
        r = 14 if k % 2 == 0 else 6.2
        a = -math.pi / 2 + k * math.pi / 5
        pts.append(f"{f(cx + r * math.cos(a))},{f(cy + r * math.sin(a))}")
    return f'<polygon points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>'


def people(cx, cy, col):
    return (f'<circle cx="{cx}" cy="{cy - 7}" r="5.5" fill="none" stroke="{col}" stroke-width="2"/>'
            f'<path d="M{cx - 10},{cy + 12} a10,9 0 0 1 20,0" fill="none" stroke="{col}" stroke-width="2"/>'
            f'<circle cx="{cx - 13}" cy="{cy - 3}" r="4" fill="none" stroke="{col}" stroke-width="1.6" opacity="0.7"/>'
            f'<circle cx="{cx + 13}" cy="{cy - 3}" r="4" fill="none" stroke="{col}" stroke-width="1.6" opacity="0.7"/>')


AWARDS = [
    dict(slug="hackasol", icon=trophy, color="silver", title="2nd Place · National",
         lines=["Hack-A-Sol 2025 · 300+ teams", "Built Lumen"]),
    dict(slug="apihub", icon=medal, color="bronze", title="3rd Place",
         lines=["APIHub Hackathon 2025 · 500+ teams", "Built Study AI"]),
    dict(slug="algouniversity", icon=star, color="acc", title="National Select",
         lines=["AlgoUniversity Tech Fellowship 2025", "Top 1000"]),
    dict(slug="aiml", icon=people, color="acc2", title="Head, AI/ML Club",
         lines=["IIIT Naya Raipur · 2025–26", "AI Impact Summit 2026 · 500+ participants"]),
]


def award(a, p, i):
    W, H = 428, 108
    defs, body = card(W, H, p, rx=14, grid=False, running=False)
    col = p[a["color"]]
    defs += (f'<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{p["shine"]}" '
             f'stop-opacity="0"/><stop offset="0.5" stop-color="{p["shine"]}" stop-opacity="{0.07 if p is DARK else 0.6}"/>'
             f'<stop offset="1" stop-color="{p["shine"]}" stop-opacity="0"/></linearGradient>'
             f'<clipPath id="tile"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>')
    body += (f'<g clip-path="url(#tile)"><rect x="-140" y="0" width="120" height="{H}" fill="url(#shine)" '
             f'transform="skewX(-20)">{loop("x", 7, [(0, -140), (1.6, W + 120), (7, W + 120)], begin=1.0 + i * 0.6)}'
             f'</rect></g>')
    cx, cy = 54, 54
    body += (f'<circle cx="{cx}" cy="{cy}" r="31" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-opacity="0.35"/>'
             f'<circle cx="{cx}" cy="{cy}" r="31" fill="none" stroke="{col}" stroke-width="1.5" stroke-opacity="0.6" '
             f'pathLength="100" stroke-dasharray="18 82">'
             f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" '
             f'dur="{6 + i}s" repeatCount="indefinite"/></circle>')
    body += a["icon"](cx, cy, col)
    body += text(102, 44, a["title"], 16.5, p["text"], SANS, "700")
    for k, ln in enumerate(a["lines"]):
        body += text(102, 68 + k * 19, ln, 12.6, p["text2"] if k == 0 else p["muted"])
    return svg(W, H, a["title"] + ": " + "; ".join(a["lines"]), g_enter(body, 0.1 + i * 0.12, 0.6, 6), defs)


# ----------------------------------------------------------------------------- small UI pieces
def divider():
    W, H = 900, 12
    defs = ('<linearGradient id="base" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8B949E" stop-opacity="0"/>'
            '<stop offset="0.5" stop-color="#8B949E" stop-opacity="0.45"/><stop offset="1" stop-color="#8B949E" '
            'stop-opacity="0"/></linearGradient><linearGradient id="pulse" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0" stop-color="#14B8A6" stop-opacity="0"/><stop offset="0.5" stop-color="#2DD4BF"/>'
            '<stop offset="1" stop-color="#14B8A6" stop-opacity="0"/></linearGradient>')
    body = (f'<rect x="0" y="5.5" width="{W}" height="1" fill="url(#base)"/>'
            f'<rect x="-180" y="4.5" width="180" height="3" rx="1.5" fill="url(#pulse)">'
            f'<animate attributeName="x" values="-180;{W}" dur="5s" repeatCount="indefinite"/></rect>'
            f'<circle cx="{W / 2}" cy="6" r="2.6" fill="#2DD4BF"><animate attributeName="opacity" values="1;0.35;1" '
            f'dur="2.5s" repeatCount="indefinite"/></circle>')
    return svg(W, H, "section divider", body, defs)


def wave():
    W, H = 900, 130
    defs = ('<linearGradient id="w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2DD4BF"/>'
            '<stop offset="1" stop-color="#0EA5E9"/></linearGradient>')

    def layer(period, amp, base, dur, op, rev):
        n = int((W + period * 2) / period) + 1
        d = f"M0,{base}"
        for k in range(n * 2):
            x = (k + 1) * period / 2
            cy = base - amp if k % 2 == 0 else base + amp
            d += f" Q{f(x - period / 4)},{cy} {f(x)},{base}"
        d += f" V{H} H0 Z"
        frm, to = ("0 0", f"-{period} 0") if not rev else (f"-{period} 0", "0 0")
        return (f'<path d="{d}" fill="url(#w)" opacity="{op}"><animateTransform attributeName="transform" '
                f'type="translate" from="{frm}" to="{to}" dur="{dur}s" repeatCount="indefinite"/></path>')
    body = layer(300, 10, 62, 9, 0.22, False) + layer(420, 14, 76, 13, 0.30, True) + layer(240, 7, 92, 7, 0.55, False)
    return svg(W, H, "wave", body, defs)


def button(label, kind):
    if kind == "demo":
        W, H, fill, stroke = 142, 32, "#0D9488", "#14B8A6"
    else:
        W, H, fill, stroke = 104, 32, "#24292F", "#3D444D"
    body = f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="9" fill="{fill}" stroke="{stroke}"/>'
    if kind == "demo":
        body += ('<circle cx="20" cy="16" r="9" fill="none" stroke="#FFFFFF" stroke-opacity="0.6">'
                 '<animate attributeName="r" values="7;12" dur="1.6s" repeatCount="indefinite"/>'
                 '<animate attributeName="opacity" values="0.8;0" dur="1.6s" repeatCount="indefinite"/></circle>'
                 '<path d="M16.5,10.5 L25,16 L16.5,21.5 Z" fill="#FFFFFF"/>')
    else:
        body += ('<path d="M17,11 L12,16 L17,21 M23,11 L28,16 L23,21" fill="none" stroke="#FFFFFF" stroke-width="1.8" '
                 'stroke-linecap="round" stroke-linejoin="round"/>')
    body += text(36, 20.5, label, 13, "#FFFFFF", SANS, "600")
    return svg(W, H, label, body)


# ----------------------------------------------------------------------------- build
def main():
    for p in THEMES:
        n = p["name"]
        write(f"hero/hero-{n}.svg", hero(p))
        write(f"hero/hero-{n}-m.svg", hero(p, mobile=True))
        for pr in PROJECTS:
            write(f"projects/{pr['slug']}-{n}.svg", project_card(pr, p))
            write(f"projects/{pr['slug']}-{n}-m.svg", project_card(pr, p, mobile=True))
        for i, m in enumerate(MORE):
            write(f"more/{m['slug']}-{n}.svg", mini_card(m, p, i))
        write(f"research/research-{n}.svg", research(p))
        write(f"research/research-{n}-m.svg", research(p, mobile=True))
        write(f"stack/stack-{n}.svg", stack(p))
        write(f"stack/stack-{n}-m.svg", stack(p, mobile=True))
        for i, a in enumerate(AWARDS):
            write(f"awards/{a['slug']}-{n}.svg", award(a, p, i))
    write("terminal/neofetch.svg", neofetch())
    write("terminal/neofetch-m.svg", neofetch(mobile=True))
    write("ui/divider.svg", divider())
    write("ui/wave.svg", wave())
    write("ui/btn-code.svg", button("Code", "code"))
    write("ui/btn-demo.svg", button("Demo Video", "demo"))


if __name__ == "__main__":
    main()
