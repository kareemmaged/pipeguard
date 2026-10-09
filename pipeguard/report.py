from __future__ import annotations

from datetime import datetime, timezone
from html import escape

LABEL = {"pass": "Passed", "warn": "Warning", "fail": "Failed", "skip": "Skipped"}

INK = "#000000"
PURPLE_DARK = "#52057B"
PURPLE_MID = "#892CDC"
PURPLE_LIGHT = "#BC6FF1"

_SPARK = "M50 3C54 34 66 46 97 50C66 54 54 66 50 97C46 66 34 54 3 50C34 46 46 34 50 3Z"


def star(cls: str, fill: str = "none") -> str:
    return (f'<svg class="star {cls}" viewBox="0 0 100 100" aria-hidden="true"><path d="{_SPARK}" fill="{fill}" '
            f'stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/></svg>')


def pretty_time(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return iso


CSS = """
:root{
  --bg:#000000;
  --panel:#52057B;
  --row:#BC6FF1;
  --ink:#000000;
  --text:#ffffff;
  --text-muted:#d3b8f5;
  --pass:#892CDC;
  --warn:#BC6FF1;
  --fail:#52057B;
  --skip:#3b0359;
  --u:clamp(.6px,calc(100vw / 1920),1px);
}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;background:var(--bg);color:var(--text);
font:calc(18*var(--u))/1.5 Inter,"Segoe UI",system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
nav{border-bottom:calc(3*var(--u)) solid var(--pass);background:var(--bg)}
.in,.wrap{width:min(calc(1348*var(--u)),calc(100vw - 36px));margin:0 auto}
.in{height:calc(101*var(--u));display:flex;justify-content:space-between;align-items:center}
.logo{font-size:calc(34*var(--u));font-weight:800;letter-spacing:-.05em;line-height:1;color:#fff}.logo b{color:var(--pass);font-weight:800}
.file{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:calc(16*var(--u));border:calc(3*var(--u)) solid var(--pass);border-radius:calc(14*var(--u));padding:calc(14*var(--u));color:#fff;background:var(--pass)}
.wrap{padding-bottom:calc(60*var(--u))}
.hero{position:relative;text-align:center;padding:calc(66*var(--u)) 0 calc(62*var(--u))}
h1{margin:0;font-size:calc(100*var(--u));line-height:1.02;font-weight:800;letter-spacing:-.055em;color:#fff}
.sub{margin:calc(24*var(--u)) 0 0;font-size:calc(22*var(--u));color:var(--text-muted)}
.star{position:absolute;overflow:visible}
.s1{left:calc(-29*var(--u));top:calc(43*var(--u));width:calc(80*var(--u));height:calc(80*var(--u))}
.s1b{left:calc(73*var(--u));top:calc(20*var(--u));width:calc(30*var(--u));height:calc(30*var(--u))}
.s2{right:calc(-15*var(--u));top:calc(156*var(--u));width:calc(72*var(--u));height:calc(72*var(--u))}
.panel{background:var(--panel);border:calc(3*var(--u)) solid var(--pass);border-radius:calc(24*var(--u));
box-shadow:calc(13*var(--u)) calc(13*var(--u)) 0 #000;padding:calc(38*var(--u))}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:calc(22*var(--u));margin-bottom:calc(36*var(--u))}
.card{border:calc(3*var(--u)) solid var(--ink);border-radius:calc(14*var(--u));box-shadow:calc(7*var(--u)) calc(7*var(--u)) 0 var(--ink);
padding:calc(14*var(--u)) calc(22*var(--u)) calc(16*var(--u));min-height:calc(110*var(--u));color:#fff}
.card b{display:block;font-size:calc(44*var(--u));line-height:1.2;font-weight:800}
.card span{display:block;font-size:calc(19*var(--u));margin-top:calc(8*var(--u))}
.card.pass{background:var(--pass)}.card.warn{background:var(--warn);color:var(--ink)}.card.fail{background:var(--fail)}.card.skip{background:var(--skip)}
.row{border:calc(3*var(--u)) solid var(--ink);border-radius:calc(16*var(--u));box-shadow:calc(6*var(--u)) calc(6*var(--u)) 0 var(--ink);
margin:0 calc(6*var(--u)) calc(26*var(--u)) 0;background:var(--row);color:var(--ink);overflow:hidden}
.row>summary,.row>.head{display:flex;align-items:center;height:calc(72*var(--u));padding:0 calc(22*var(--u));list-style:none}
.row>summary{cursor:pointer}.row>summary::-webkit-details-marker{display:none}
.row>summary::after{content:"\\2b";margin-left:auto;font-weight:800;font-size:calc(26*var(--u));line-height:1}
.row[open]>summary::after{content:"\\2013"}
.badge{flex:none;width:calc(104*var(--u));text-align:center;font-size:calc(17*var(--u));font-weight:800;line-height:calc(32*var(--u));
border:calc(3*var(--u)) solid var(--ink);border-radius:999px;box-shadow:calc(3*var(--u)) calc(3*var(--u)) 0 var(--ink);margin-right:calc(18*var(--u));color:#fff}
.pass .badge{background:var(--pass)}.warn .badge{background:var(--warn);color:var(--ink)}.fail .badge{background:var(--fail)}.skip .badge{background:var(--skip)}
.name{flex:none;width:calc(267*var(--u));font-weight:800;font-size:calc(20*var(--u))}
.sum{flex:1;color:#2a0040;font-size:calc(20*var(--u))}
ul{margin:0;padding:calc(22*var(--u)) calc(22*var(--u)) calc(22*var(--u)) calc(44*var(--u));border-top:calc(3*var(--u)) solid var(--ink);
background:#e9cbfb;color:var(--ink);font-size:calc(17*var(--u));overflow-x:auto}
li{margin:calc(3*var(--u)) 0;line-height:1.55;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.panel>:last-child{margin-bottom:0}
@media(max-width:520px){.cards{grid-template-columns:repeat(2,1fr)}.sum{display:none}.name{width:auto;flex:1}}
"""


def render(state: dict) -> str:
    results = state["results"]
    counts = {s: sum(r["status"] == s for r in results) for s in LABEL}
    overall = "fail" if counts["fail"] else "warn" if counts["warn"] else "pass"
    title = {"pass": "All checks passed", "warn": "Passed with warnings", "fail": "Data quality report"}[overall]

    cards = "".join(f'<div class="card {s}"><b>{counts[s]}</b><span>{LABEL[s]}</span></div>' for s in LABEL)
    rows = []
    for r in results:
        head = (f'<span class="badge">{LABEL[r["status"]]}</span><span class="name">{escape(r["name"])}</span>'
                f'<span class="sum">{escape(r["summary"])}</span>')
        if r["details"]:
            items = "".join(f"<li>{escape(str(d))}</li>" for d in r["details"])
            rows.append(f'<details class="row {r["status"]}"><summary>{head}</summary><ul>{items}</ul></details>')
        else:
            rows.append(f'<div class="row {r["status"]}"><div class="head">{head}</div></div>')

    stars = star("s1", PURPLE_MID) + star("s1b", PURPLE_LIGHT) + star("s2", PURPLE_MID)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PipeGuard report · {escape(state["name"])}</title><style>{CSS}</style></head>
<body>
<nav><div class="in"><span class="logo">Pipe<b>Guard</b></span><span class="file">{escape(state["name"])}</span></div></nav>
<div class="wrap">
<section class="hero">{stars}<h1>{escape(title)}</h1>
<p class="sub">{state["rows"]:,} rows × {state["columns"]} columns · checked</p></section>
<section class="panel">
<div class="cards">{cards}</div>
{"".join(rows)}
</section>
</div></body></html>"""