#!/usr/bin/env python3
"""build_wiki_html — generate a self-contained interactive wiki/index.html.

Single-sourced from wiki/*.md. Renders the markdown subset used by the wiki
(headings, bold, inline + fenced code, lists, tables, blockquotes, links, hr)
into one offline-capable HTML page with sidebar nav, cross-page search, and a
"tuning console" aesthetic. Dependency-free.

Run:    python3 scripts/build_wiki_html.py           (from the repo root)
Check:  python3 scripts/build_wiki_html.py --check   (CI freshness gate: exit 1 if
        the committed wiki/index.html no longer matches a fresh build)
Out:  wiki/index.html
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WIKI = os.path.join(HERE, "..", "wiki")
MODELS_JSON = os.path.join(HERE, "..", "skills", "omnitune", "references", "models.json")
VERSION_LOG_JSON = os.path.join(HERE, "..", "skills", "omnitune", "references", "version-log.json")

# Nav order + clean labels (filename -> (slug, nav label))
PAGES = [
    ("Home.md", "overview", "Overview"),
    ("How-It-Works.md", "how-it-works", "How It Works"),
    ("Install-Setup.md", "install", "Install & Setup"),
    ("Configuration.md", "configuration", "Configuration"),
    ("Auto-Sync.md", "auto-sync", "Auto-Sync"),
    ("__models__", "models", "Models"),
    ("FAQ.md", "faq", "FAQ"),
]
FILE_TO_SLUG = {f: s for f, s, _ in PAGES}


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", text).strip("-") or "section"


def inline(text):
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)

    def link(m):
        label, href = m.group(1), m.group(2)
        # rewrite inter-wiki .md links into in-app nav
        base = href.split("/")[-1]
        if base in FILE_TO_SLUG:
            return '<a class="xnav" data-target="%s" href="#%s">%s</a>' % (
                FILE_TO_SLUG[base], FILE_TO_SLUG[base], label)
        return '<a href="%s">%s</a>' % (href, label)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)

    def unstash(m):
        return "<code>%s</code>" % html.escape(spans[int(m.group(1))])

    return re.sub(r"\x00(\d+)\x00", unstash, text)


def md_to_html(md, headings_out):
    lines = md.split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]

        # fenced code
        m = re.match(r"^```(\w*)\s*$", line)
        if m:
            lang = m.group(1)
            i += 1
            buf = []
            while i < n and not re.match(r"^```\s*$", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append('<pre class="code" data-lang="%s"><code>%s</code></pre>'
                       % (lang, html.escape("\n".join(buf))))
            continue

        # table
        if line.strip().startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ['<div class="tablewrap"><table><thead><tr>']
            t += ["<th>%s</th>" % inline(h) for h in header]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            raw = m.group(2).strip()
            hid = slugify(raw)
            if lvl in (2, 3):
                headings_out.append({"text": re.sub(r"[^\w\s&/:.-]", "", raw).strip(), "id": hid})
            out.append('<h%d id="%s" class="h%d">%s</h%d>' % (lvl, hid, lvl, inline(raw), lvl))
            i += 1
            continue

        # hr
        if re.match(r"^(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # blockquote
        if line.strip().startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(buf)))
            continue

        # unordered list
        if re.match(r"^\s*[-*]\s+", line):
            buf = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                buf.append(inline(re.sub(r"^\s*[-*]\s+", "", lines[i])))
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % x for x in buf) + "</ul>")
            continue

        # ordered list
        if re.match(r"^\s*\d+\.\s+", line):
            buf = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                buf.append(inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>" + "".join("<li>%s</li>" % x for x in buf) + "</ol>")
            continue

        # blank
        if line.strip() == "":
            i += 1
            continue

        # paragraph
        buf = [line]
        i += 1
        while i < n and lines[i].strip() != "" and not re.match(
                r"^(#{1,6}\s|```|\s*[-*]\s|\s*\d+\.\s|>|\|)", lines[i]) and not re.match(r"^(-{3,})\s*$", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out)


def _models_section(models_path, log_path):
    """Generated 'Models & lineage' table from models.json + version-log.json."""
    try:
        with open(models_path) as f:
            models = json.load(f).get("models", [])
    except Exception:  # noqa: BLE001
        models = []
    log = {}
    try:
        with open(log_path) as f:
            for e in json.load(f).get("entries", []):
                log[e.get("model_id")] = e  # entries oldest-first -> last wins = newest
    except Exception:  # noqa: BLE001
        pass
    rows = []
    for m in models:
        e = log.get(m.get("id"), {})
        srcs = e.get("source_urls") or m.get("source_urls") or []
        synced = e.get("last_synced") or m.get("ga_date") or "—"
        rows.append("<tr><td>%s</td><td><code>%s</code></td><td>%s</td><td>%s</td><td>%d</td></tr>"
                    % (html.escape(m.get("provider", "")), html.escape(m.get("id", "")),
                       html.escape(m.get("status", "")), html.escape(str(synced)), len(srcs)))
    table = ('<div class="tablewrap"><table><thead><tr>'
             '<th>Provider</th><th>Model</th><th>Status</th><th>Last synced</th><th>Sources</th>'
             '</tr></thead><tbody>%s</tbody></table></div>') % "".join(rows)
    return ('<p>Generated from <code>version-log.json</code> + <code>models.json</code> '
            'at build time — never hand-edited, so it cannot drift from the library.</p>' + table)


def build():
    sections, nav, index = [], [], []
    for idx, (fname, slug, label) in enumerate(PAGES):
        if fname == "__models__":
            title, headings, body = label, [], _models_section(MODELS_JSON, VERSION_LOG_JSON)
        else:
            with open(os.path.join(WIKI, fname), encoding="utf-8") as f:
                md = f.read()
            # pull first H1 as page title; render the rest
            title = label
            m = re.search(r"^#\s+(.*)$", md, re.M)
            if m:
                md = md.replace(m.group(0), "", 1)
            headings = []
            body = md_to_html(md.strip(), headings)
        index.append({"slug": slug, "label": label, "headings": headings})
        active = " active" if idx == 0 else ""
        nav.append(
            '<a class="navlink%s" data-target="%s" href="#%s" style="--d:%d">'
            '<span class="dot"></span>%s</a>' % (active, slug, slug, idx, html.escape(label)))
        sections.append(
            '<section class="page%s" id="%s" data-label="%s">'
            '<div class="pagehead"><span class="kicker">%02d / %s</span>'
            '<h1 class="pagetitle">%s</h1></div>%s</section>'
            % (" show" if idx == 0 else "", slug, html.escape(label), idx + 1,
               html.escape(label.upper()), html.escape(title), body))

    return TEMPLATE.replace("/*NAV*/", "\n".join(nav)) \
                   .replace("/*CONTENT*/", "\n".join(sections)) \
                   .replace("/*INDEX*/", json.dumps(index))


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="console">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>omnitune — wiki</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0b0d0c; --bg2:#0e1110; --panel:#121615; --panel2:#161b19;
  --line:rgba(233,228,217,.10); --line2:rgba(233,228,217,.06);
  --ink:#e9e4d9; --muted:#8b918a; --faint:#5b615b;
  --amber:#e9b14c; --teal:#5ad6b0; --amber-soft:rgba(233,177,76,.13); --teal-soft:rgba(90,214,176,.12);
  --serif:'Instrument Serif',Georgia,serif; --mono:'IBM Plex Mono',ui-monospace,monospace; --sans:'IBM Plex Sans',system-ui,sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;font-family:var(--sans);color:var(--ink);background:var(--bg);
  font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased;
  background-image:radial-gradient(120% 80% at 8% -10%,rgba(233,177,76,.10),transparent 55%),
    radial-gradient(90% 60% at 100% 0%,rgba(90,214,176,.06),transparent 50%);
  background-attachment:fixed;
}
/* fine instrument grid + grain */
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.5;
  background-image:linear-gradient(var(--line2) 1px,transparent 1px),linear-gradient(90deg,var(--line2) 1px,transparent 1px);
  background-size:46px 46px;mask-image:radial-gradient(120% 100% at 50% 0,#000,transparent 90%);}
body::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.035;mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");}

.layout{display:grid;grid-template-columns:286px 1fr;min-height:100vh;position:relative;z-index:1}

/* ---------- sidebar ---------- */
aside{position:sticky;top:0;height:100vh;border-right:1px solid var(--line);
  background:linear-gradient(180deg,var(--panel),var(--bg2));display:flex;flex-direction:column;padding:26px 20px 18px}
.brand{display:flex;align-items:center;gap:11px;margin-bottom:4px}
.brand .wave{width:34px;height:22px;flex:none}
.brand .wave path{stroke:var(--amber);stroke-width:2;fill:none;stroke-linecap:round}
.brand .nm{font-family:var(--mono);font-weight:600;letter-spacing:.02em;font-size:15px}
.brand .nm b{color:var(--amber)}
.tagline{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin:2px 0 18px 45px}

.readout{border:1px solid var(--line);border-radius:9px;background:var(--bg);padding:9px 11px;margin-bottom:16px;font-family:var(--mono);font-size:11px;display:flex;align-items:center;gap:8px;color:var(--muted)}
.readout .pip{width:7px;height:7px;border-radius:50%;background:var(--teal);box-shadow:0 0 0 0 var(--teal);animation:pip 2.6s infinite}
.readout b{color:var(--ink);font-weight:500}
@keyframes pip{0%{box-shadow:0 0 0 0 rgba(90,214,176,.45)}70%{box-shadow:0 0 0 7px rgba(90,214,176,0)}100%{box-shadow:0 0 0 0 rgba(90,214,176,0)}}

.search{position:relative;margin-bottom:16px}
.search input{width:100%;background:var(--bg);border:1px solid var(--line);border-radius:9px;color:var(--ink);
  font-family:var(--mono);font-size:12.5px;padding:9px 11px 9px 30px;outline:none;transition:.2s}
.search input:focus{border-color:var(--amber);box-shadow:0 0 0 3px var(--amber-soft)}
.search svg{position:absolute;left:9px;top:9px;width:14px;height:14px;stroke:var(--faint)}
.search .key{position:absolute;right:8px;top:7px;font-family:var(--mono);font-size:10px;color:var(--faint);border:1px solid var(--line);border-radius:4px;padding:1px 5px}
.results{position:absolute;top:42px;left:0;right:0;background:var(--panel2);border:1px solid var(--line);border-radius:9px;overflow:hidden;z-index:30;display:none;box-shadow:0 14px 40px rgba(0,0,0,.5)}
.results.show{display:block}
.results a{display:block;padding:8px 11px;font-size:12.5px;color:var(--muted);text-decoration:none;border-bottom:1px solid var(--line2)}
.results a:last-child{border-bottom:0}
.results a:hover,.results a.sel{background:var(--amber-soft);color:var(--ink)}
.results a .pg{font-family:var(--mono);font-size:10px;color:var(--amber);display:block;letter-spacing:.05em}

nav{display:flex;flex-direction:column;gap:1px;overflow-y:auto;margin:-4px -8px 0;padding:4px 8px}
.navlink{position:relative;display:flex;align-items:center;gap:11px;padding:9px 12px;border-radius:8px;color:var(--muted);
  text-decoration:none;font-size:13.5px;font-weight:500;letter-spacing:.01em;transition:.18s;
  opacity:0;transform:translateX(-8px);animation:navin .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:calc(var(--d) * 55ms + 120ms)}
@keyframes navin{to{opacity:1;transform:none}}
.navlink .dot{width:6px;height:6px;border-radius:50%;background:var(--faint);transition:.18s;flex:none}
.navlink:hover{color:var(--ink);background:var(--line2)}
.navlink:hover .dot{background:var(--muted)}
.navlink.active{color:var(--ink);background:var(--amber-soft)}
.navlink.active .dot{background:var(--amber);box-shadow:0 0 9px var(--amber)}
.navlink.active::before{content:"";position:absolute;left:-8px;top:8px;bottom:8px;width:2px;border-radius:2px;background:var(--amber);box-shadow:0 0 10px var(--amber)}
.spacer{flex:1}
.foot{font-family:var(--mono);font-size:10.5px;color:var(--faint);letter-spacing:.05em;padding-top:14px;border-top:1px solid var(--line2);line-height:1.7}
.foot a{color:var(--muted);text-decoration:none}
.foot a:hover{color:var(--amber)}

/* ---------- main ---------- */
main{padding:0;min-width:0;position:relative}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:14px;height:54px;padding:0 40px;
  border-bottom:1px solid var(--line);background:rgba(11,13,12,.72);backdrop-filter:blur(12px)}
.crumb{font-family:var(--mono);font-size:11.5px;letter-spacing:.04em;color:var(--muted)}
.crumb b{color:var(--amber)}
.meter{margin-left:auto;display:flex;align-items:center;gap:7px;font-family:var(--mono);font-size:10.5px;color:var(--faint);letter-spacing:.08em}
.meter .bars{display:flex;gap:2px;align-items:flex-end;height:14px}
.meter .bars i{width:3px;background:var(--teal);border-radius:1px;opacity:.5;animation:eq 1.4s ease-in-out infinite}
.meter .bars i:nth-child(2){animation-delay:.2s}.meter .bars i:nth-child(3){animation-delay:.4s}.meter .bars i:nth-child(4){animation-delay:.1s}.meter .bars i:nth-child(5){animation-delay:.3s}
@keyframes eq{0%,100%{height:4px}50%{height:14px}}
.menubtn{display:none}

.scroll{height:calc(100vh - 54px);overflow-y:auto;scroll-behavior:smooth}
.wrap{max-width:780px;margin:0 auto;padding:52px 40px 120px}
.page{display:none;animation:pagein .45s cubic-bezier(.2,.8,.2,1)}
.page.show{display:block}
@keyframes pagein{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

.pagehead{margin-bottom:34px;padding-bottom:26px;border-bottom:1px solid var(--line)}
.kicker{font-family:var(--mono);font-size:11px;letter-spacing:.22em;color:var(--amber);text-transform:uppercase}
.pagetitle{font-family:var(--serif);font-weight:400;font-size:clamp(40px,6vw,62px);line-height:1.02;margin:12px 0 0;letter-spacing:.005em}

.page h2{font-family:var(--mono);font-weight:600;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--amber);
  margin:46px 0 16px;padding-top:14px;border-top:1px solid var(--line2)}
.page h3{font-family:var(--sans);font-weight:600;font-size:18px;margin:30px 0 10px;color:var(--ink)}
.page h4{font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:22px 0 8px}
.page p{margin:14px 0;color:#d7d3c8}
.page strong{color:var(--ink);font-weight:600}
.page em{color:var(--teal);font-style:italic}
.page a{color:var(--amber);text-decoration:none;border-bottom:1px solid var(--amber-soft);transition:.15s}
.page a:hover{border-bottom-color:var(--amber)}
.page a.xnav{cursor:pointer}
.page ul,.page ol{margin:14px 0;padding-left:22px;color:#d7d3c8}
.page li{margin:7px 0}
.page li::marker{color:var(--amber)}
.page hr{border:0;border-top:1px solid var(--line);margin:34px 0}
.page blockquote{margin:20px 0;padding:14px 18px;border-left:2px solid var(--teal);background:var(--teal-soft);border-radius:0 8px 8px 0;color:var(--ink)}

code{font-family:var(--mono);font-size:.86em;background:var(--panel2);border:1px solid var(--line2);border-radius:5px;padding:1.5px 6px;color:var(--amber)}
pre.code{position:relative;margin:18px 0;background:var(--bg2);border:1px solid var(--line);border-radius:11px;padding:18px 18px 16px;overflow-x:auto}
pre.code code{background:none;border:0;padding:0;color:#cfd6cf;font-size:13px;line-height:1.6;display:block}
pre.code::before{content:attr(data-lang);position:absolute;top:0;right:14px;transform:translateY(-50%);font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);background:var(--bg);padding:2px 8px;border:1px solid var(--line2);border-radius:20px}

.tablewrap{overflow-x:auto;margin:20px 0;border:1px solid var(--line);border-radius:11px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{font-family:var(--mono);font-weight:500;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--amber);text-align:left;padding:11px 14px;background:var(--panel);border-bottom:1px solid var(--line)}
td{padding:11px 14px;border-bottom:1px solid var(--line2);color:#d2cfc5;vertical-align:top}
tr:last-child td{border-bottom:0}
tr:hover td{background:rgba(233,177,76,.03)}

::-webkit-scrollbar{width:11px;height:11px}
::-webkit-scrollbar-thumb{background:#2a302d;border-radius:6px;border:3px solid var(--bg)}
::-webkit-scrollbar-thumb:hover{background:#3a423d}

/* ---------- responsive ---------- */
.scrim{display:none}
@media(max-width:880px){
  .layout{grid-template-columns:1fr}
  aside{position:fixed;left:0;top:0;width:286px;z-index:60;transform:translateX(-100%);transition:.28s cubic-bezier(.2,.8,.2,1)}
  aside.open{transform:none;box-shadow:30px 0 80px rgba(0,0,0,.6)}
  .menubtn{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);cursor:pointer}
  .menubtn svg{width:17px;height:17px;stroke:var(--ink)}
  .scrim.show{display:block;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:55}
  .wrap{padding:38px 22px 100px}
  .topbar{padding:0 18px}
}
</style>
</head>
<body>
<div class="layout">
  <div class="scrim" id="scrim"></div>
  <aside id="aside">
    <div class="brand">
      <svg class="wave" viewBox="0 0 34 22"><path d="M1 11 H6 L8 4 L11 18 L14 8 L17 14 L20 2 L23 16 L26 11 H33"/></svg>
      <span class="nm"><b>prompt</b>-tuner</span>
    </div>
    <div class="tagline">tuning console</div>
    <div class="readout"><span class="pip"></span><span>rubric&nbsp;·&nbsp;<b id="rdModel">claude-opus-4-8</b></span></div>
    <div class="search">
      <svg viewBox="0 0 24 24" fill="none" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
      <input id="q" type="text" placeholder="Search the docs" autocomplete="off" spellcheck="false">
      <span class="key">/</span>
      <div class="results" id="results"></div>
    </div>
    <nav id="nav">/*NAV*/</nav>
    <div class="spacer"></div>
    <div class="foot">v0.2 · MIT<br><a href="https://github.com/RobertBMoore/omnitune">github.com/RobertBMoore/omnitune</a></div>
  </aside>

  <main>
    <div class="topbar">
      <button class="menubtn" id="menubtn" aria-label="Menu"><svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
      <div class="crumb">wiki&nbsp;/&nbsp;<b id="crumb">Overview</b></div>
      <div class="meter"><span>in&nbsp;tune</span><span class="bars"><i></i><i></i><i></i><i></i><i></i></span></div>
    </div>
    <div class="scroll" id="scroll">
      <div class="wrap">/*CONTENT*/</div>
    </div>
  </main>
</div>

<script>
const INDEX = /*INDEX*/;
const nav = document.getElementById('nav');
const scroll = document.getElementById('scroll');
const crumb = document.getElementById('crumb');
const aside = document.getElementById('aside');
const scrim = document.getElementById('scrim');

function setPage(slug, hid){
  const pages = document.querySelectorAll('.page');
  let found=false;
  pages.forEach(p=>{ const on = p.id===slug; p.classList.toggle('show',on); if(on) found=true; });
  if(!found){ document.querySelector('.page').classList.add('show'); slug=document.querySelector('.page').id; }
  document.querySelectorAll('.navlink').forEach(a=>a.classList.toggle('active',a.dataset.target===slug));
  const lbl = document.querySelector('#'+CSS.escape(slug)).dataset.label;
  crumb.textContent = lbl;
  history.replaceState(null,'', '#'+slug + (hid?('::'+hid):''));
  scroll.scrollTop = 0;
  if(hid){ const el=document.getElementById(hid); if(el) setTimeout(()=>el.scrollIntoView({behavior:'smooth',block:'start'}),60); }
  closeMenu();
}
nav.addEventListener('click',e=>{const a=e.target.closest('.navlink'); if(a){e.preventDefault(); setPage(a.dataset.target);}});
document.addEventListener('click',e=>{const a=e.target.closest('a.xnav'); if(a){e.preventDefault(); setPage(a.dataset.target);}});

// ---- search ----
const q=document.getElementById('q'), results=document.getElementById('results');
const flat=[];
INDEX.forEach(p=>{ flat.push({page:p.label,slug:p.slug,text:p.label,id:''}); p.headings.forEach(h=>flat.push({page:p.label,slug:p.slug,text:h.text,id:h.id})); });
let sel=-1, cur=[];
function render(list){
  cur=list; sel=-1;
  if(!list.length){results.classList.remove('show');results.innerHTML='';return;}
  results.innerHTML=list.slice(0,8).map(r=>`<a data-slug="${r.slug}" data-id="${r.id}"><span class="pg">${r.page}</span>${r.text}</a>`).join('');
  results.classList.add('show');
}
q.addEventListener('input',()=>{
  const v=q.value.trim().toLowerCase();
  if(!v){render([]);return;}
  render(flat.filter(r=>r.text.toLowerCase().includes(v)));
});
results.addEventListener('click',e=>{const a=e.target.closest('a'); if(a){setPage(a.dataset.slug,a.dataset.id||null); q.value='';render([]);}});
q.addEventListener('keydown',e=>{
  if(e.key==='Escape'){q.value='';render([]);q.blur();}
  if(!cur.length)return;
  if(e.key==='ArrowDown'){e.preventDefault();sel=(sel+1)%Math.min(cur.length,8);}
  else if(e.key==='ArrowUp'){e.preventDefault();sel=(sel-1+Math.min(cur.length,8))%Math.min(cur.length,8);}
  else if(e.key==='Enter'){const r=cur[sel<0?0:sel]; if(r){setPage(r.slug,r.id||null);q.value='';render([]);}return;}
  else return;
  [...results.children].forEach((a,i)=>a.classList.toggle('sel',i===sel));
});
document.addEventListener('keydown',e=>{ if(e.key==='/' && document.activeElement!==q){e.preventDefault();q.focus();} });
document.addEventListener('click',e=>{ if(!e.target.closest('.search')) render([]); });

// ---- mobile menu ----
const menubtn=document.getElementById('menubtn');
function closeMenu(){aside.classList.remove('open');scrim.classList.remove('show');}
menubtn&&menubtn.addEventListener('click',()=>{aside.classList.toggle('open');scrim.classList.toggle('show');});
scrim.addEventListener('click',closeMenu);

// ---- deep link on load ----
(function(){
  const h=location.hash.replace('#','');
  if(h){const [slug,hid]=h.split('::'); if(document.getElementById(slug)) setPage(slug,hid||null);}
})();
</script>
</body>
</html>
"""

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    unknown = [a for a in args if a != "--check"]
    if unknown:
        print("usage: build_wiki_html.py [--check]", file=sys.stderr)
        return 2
    out = os.path.join(WIKI, "index.html")
    fresh = build()
    if "--check" in args:
        try:
            with open(out, encoding="utf-8") as f:
                on_disk = f.read()
        except OSError:
            on_disk = None
        if on_disk != fresh:
            print("stale: wiki/index.html does not match its sources — "
                  "regenerate with: python3 scripts/build_wiki_html.py", file=sys.stderr)
            return 1
        print("wiki/index.html is fresh")
        return 0
    with open(out, "w", encoding="utf-8") as f:
        f.write(fresh)
    print("wrote", os.path.relpath(out, os.path.join(HERE, "..")), "(%d bytes)" % os.path.getsize(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
