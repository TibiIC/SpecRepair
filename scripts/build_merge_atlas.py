"""
Build the Corrected Merge Atlas page from the pulled graphs.

The atlas was hand-written the first time, which made adding a run a matter of
editing four megabytes of base64 by hand. This rebuilds it from two inputs:

    docs/results/graphs/<run>_{asm,gar,gr1}.png   the graphs, as pulled
    docs/results/merge_atlas_stats.json           per-run stage counts

A run appears on the page if it has graphs *or* stats - a merge that has
finished but whose graphs are still drawing is shown as numbers with a note,
rather than being withheld until the pictures exist. Its stat strip is
whatever the JSON holds for it, in the order the JSON holds it - runs
post-processed in the old order list `unique` before `strongest`, and the
corrected ones list `strongest` first, so the strip reads as the pipeline
actually ran rather than as a fixed template.

Usage:
    python scripts/build_merge_atlas.py [-o docs/results/merge-atlas.html]
"""
import argparse
import base64
import json
import os
import re
import struct
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPHS = os.path.join(ROOT, "docs", "results", "graphs")
STATS = os.path.join(ROOT, "docs", "results", "merge_atlas_stats.json")

# Assumptions and guarantees only. The whole-GR1 view answers neither of the
# questions these graphs are read for - how the assumption sets differ, and how
# the guarantee sets differ - while costing an hour a trace to draw and timing
# out on amba every time. Older runs left gr1 PNGs behind; they are simply not
# shown.
TYPES = [("asm", "Assumptions", "tealed"),
         ("gar", "Guarantees", "siennaed")]

FAMILY_ORDER = ["amba", "elevator", "gyro", "lift", "minepump",
                "minepump_liveness", "pcar", "traffic_single", "traffic_updated"]


def family_of(run):
    """`minepump_liveness_trace2` -> `minepump_liveness`, not `minepump`."""
    return re.sub(r"_trace\d+$", "", run)


def trace_of(run):
    m = re.search(r"_trace(\d+)$", run)
    return int(m.group(1)) if m else -1


# A 50-node merge lays out as a single wide row: minepump trace 4's guarantee
# graph is 12721x485. Squeezed into a 190px grid cell that is a 7px sliver, and
# scaled to fit the lightbox it is still only ~78px tall. Anything this wide gets
# its own full-width row, and the lightbox shows it at natural size to be panned.
WIDE_RATIO = 4.0


def png_size(path):
    """Width and height from the IHDR chunk, without a Pillow dependency."""
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def data_uri(path):
    with open(path, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode("ascii")


def collect(stats=None):
    runs = OrderedDict()
    for name in sorted(os.listdir(GRAPHS)):
        m = re.match(r"(.+)_(asm|gar|gr1)\.png$", name)
        if not m:
            continue
        runs.setdefault(m.group(1), {})[m.group(2)] = os.path.join(GRAPHS, name)
    # A run whose merge has finished but whose graphs have not been drawn yet
    # still belongs on the page - the counts are the result, the graphs explain it.
    for run in (stats or {}):
        runs.setdefault(run, {})
    return runs


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_run(run, graphs, stats):
    strip = "".join(
        f'<div class="st"><span class="stn">{esc(v)}</span>'
        f'<span class="stl">{esc(k)}</span></div>'
        for k, v in stats.get("stats", [])
    )
    figs = []
    missing = []
    for key, caption, klass in TYPES:
        path = graphs.get(key)
        if not path:
            missing.append(caption)
            continue
        uri = data_uri(path)
        size = png_size(path)
        wide = bool(size and size[1] and size[0] / size[1] > WIDE_RATIO)
        dims = f' ({size[0]}&times;{size[1]})' if size else ""
        figs.append(
            f'<figure class="g {klass}{" wide" if wide else ""}">'
            f'<a href="#z-{run}-{key}" class="gz">'
            f'<img loading="lazy" alt="{caption} implication graph for {run}" src="{uri}"></a>'
            f'<figcaption>{caption}{dims if wide else ""}</figcaption></figure>'
            f'<div class="lb{" wide" if wide else ""}" id="z-{run}-{key}">'
            f'<a class="lbbg" href="#{run}"></a>'
            f'<img alt="{caption} implication graph for {run}, enlarged" src="{uri}">'
            f'{"<p class=lbhint>Scroll sideways &mdash; shown at full size</p>" if wide else ""}</div>'
        )
    notes = list(stats.get("notes", []))
    if not graphs:
        notes = notes or ["Graphs still drawing"]
    elif missing and not notes:
        notes = [f"{m} graph did not complete" for m in missing]
    note_html = "".join(f'<p class="miss">{esc(n)}</p>' for n in notes)
    return (
        f'<article class="run" id="{run}">\n'
        f'<header class="runh"><h3>trace {trace_of(run)}</h3>'
        f'<div class="strip">{strip}</div></header>\n'
        f'<div class="grid">{"".join(figs)}</div>{note_html}\n'
        f'</article>'
    )


def build(out_path):
    stats = json.load(open(STATS)) if os.path.exists(STATS) else {}
    runs = collect(stats)

    by_family = OrderedDict()
    for run in sorted(runs, key=lambda r: (family_of(r), trace_of(r))):
        by_family.setdefault(family_of(run), []).append(run)

    ordered = [f for f in FAMILY_ORDER if f in by_family]
    ordered += [f for f in by_family if f not in FAMILY_ORDER]

    n_graphs = sum(len(g) for g in runs.values())
    pending = [r for r, g in runs.items() if not g]
    merged_values = {
        dict(stats.get(r, {}).get("stats", [])).get("merged")
        for r in runs
    }
    merged_values.discard(None)
    multi = sorted(
        (r for r in runs
         if dict(stats.get(r, {}).get("stats", [])).get("merged", "1") != "1"),
        key=lambda r: (family_of(r), trace_of(r)),
    )
    if not multi:
        merge_line = "every run merges to <b>1</b>"
        headline = ("Every run on this page collapses to a single specification: the merge "
                    "finds the repairs compatible and conjoins them.")
    else:
        merge_line = f"merged counts <b>1&ndash;{max(int(v) for v in merged_values)}</b>"
        names = ", ".join(r.replace("_", " ") for r in multi)
        headline = (
            f"Not every run collapses to a single specification any more. {names} "
            f"merge to counts in the tens rather than to 1 &mdash; the first runs here whose "
            f"repairs are not all mutually compatible. These counts are upper bounds: "
            f"<code>merge_solutions</code> does not test every pair."
        )

    nav = "".join(
        f'<li><a href="#fam-{f}">{f.replace("_", " ")}'
        f'<span>{len(by_family[f])}</span></a></li>'
        for f in ordered
    )

    sections = []
    for f in ordered:
        body = "\n".join(render_run(r, runs[r], stats.get(r, {})) for r in by_family[f])
        sections.append(
            f'<section class="fam" id="fam-{f}"><h2>{f.replace("_", " ")}</h2>\n{body}\n</section>'
        )

    html = TEMPLATE.format(
        n_runs=len(runs),
        n_graphs=n_graphs,
        merge_line=merge_line,
        nav=nav,
        sections="\n".join(sections),
        headline=headline,
        pending_meta=(f'<span><b>{len(pending)}</b> awaiting graphs</span>' if pending else ""),
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    size = os.path.getsize(out_path)
    print(f"{len(runs)} runs, {n_graphs} graphs -> {out_path} ({size/1e6:.1f} MB)")
    if pending:
        print("awaiting graphs: " + ", ".join(sorted(pending)))
    if size > 16_000_000:
        print("WARNING: over the 16MB artifact limit")
    return out_path


TEMPLATE = """<title>Corrected Merge Atlas</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{
  --ink:#0f141b; --paper:#f6f7f9; --card:#ffffff; --muted:#5a6472; --rule:#dce0e6;
  --teal:#1a6b66; --sienna:#9c4f1e; --shadow:0 1px 2px rgba(15,20,27,.06),0 8px 24px rgba(15,20,27,.05);
  --imgbg:#ffffff;
}}
@media (prefers-color-scheme:dark){{ :root:not([data-theme="light"]){{
  --ink:#e6e9ee; --paper:#0d1117; --card:#141a22; --muted:#98a2b1; --rule:#242c37;
  --teal:#5fb8b1; --sienna:#d98a52; --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.3);
  --imgbg:#eef1f4;
}}}}
:root[data-theme="dark"]{{
  --ink:#e6e9ee; --paper:#0d1117; --card:#141a22; --muted:#98a2b1; --rule:#242c37;
  --teal:#5fb8b1; --sienna:#d98a52; --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.3);
  --imgbg:#eef1f4;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}
.wrap{{display:grid;grid-template-columns:minmax(0,1fr);gap:0;max-width:1180px;margin:0 auto;padding:0 20px 96px}}
@media(min-width:960px){{.wrap{{grid-template-columns:210px minmax(0,1fr);gap:44px}}}}
header.top{{grid-column:1/-1;padding:56px 0 28px;border-bottom:1px solid var(--rule);margin-bottom:36px}}
h1{{font-family:Spectral,Georgia,serif;font-weight:600;font-size:clamp(1.9rem,4vw,2.7rem);
  margin:0 0 .4em;letter-spacing:-.01em;text-wrap:balance}}
.lede{{margin:0;max-width:64ch;color:var(--muted);font-size:1.02rem}}
.lede.second{{margin-top:14px;padding-left:12px;border-left:2px solid var(--sienna);color:var(--ink)}}
.meta{{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:20px;font-family:"IBM Plex Mono",monospace;
  font-size:.76rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}}
.meta b{{color:var(--teal);font-weight:500}}
nav{{display:none}}
@media(min-width:960px){{nav{{display:block;position:sticky;top:24px;align-self:start;max-height:90vh;overflow:auto}}}}
nav ul{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:1px}}
nav a{{display:flex;justify-content:space-between;gap:8px;padding:6px 8px;border-radius:4px;
  color:var(--muted);text-decoration:none;font-size:.83rem;border-left:2px solid transparent}}
nav a:hover,nav a:focus-visible{{background:var(--card);color:var(--ink);border-left-color:var(--teal)}}
nav a span{{font-family:"IBM Plex Mono",monospace;font-size:.74rem;opacity:.7}}
main{{min-width:0;display:flex;flex-direction:column;gap:52px}}
.fam>h2{{font-family:Spectral,Georgia,serif;font-weight:600;font-size:1.42rem;margin:0 0 16px;
  padding-bottom:8px;border-bottom:1px solid var(--rule);letter-spacing:-.005em}}
.fam{{display:flex;flex-direction:column;gap:18px}}
.run{{background:var(--card);border:1px solid var(--rule);border-radius:6px;box-shadow:var(--shadow);
  padding:16px 16px 18px}}
.runh{{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:12px;margin-bottom:14px}}
.runh h3{{margin:0;font-family:"IBM Plex Mono",monospace;font-size:.8rem;font-weight:500;
  letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.strip{{display:flex;align-items:center;gap:0;flex-wrap:wrap}}
.st{{display:flex;flex-direction:column;align-items:flex-end;padding:0 12px;border-right:1px solid var(--rule)}}
.st:last-child{{border-right:0;padding-right:0}}
.stn{{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;font-size:1.02rem;
  font-weight:500;line-height:1.2}}
.st:last-child .stn{{color:var(--teal)}}
.stl{{font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}}
.miss{{font-size:.74rem;color:var(--sienna);margin:10px 0 0;font-style:italic}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.g{{margin:0;display:flex;flex-direction:column;gap:7px}}
.gz{{display:block;background:var(--imgbg);border:1px solid var(--rule);border-radius:4px;padding:8px;
  transition:border-color .15s ease}}
.gz:hover,.gz:focus-visible{{border-color:var(--teal);outline:none}}
.g img{{display:block;width:100%;height:auto}}
figcaption{{font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);
  padding-left:2px;border-left:2px solid transparent}}
.tealed figcaption{{border-left-color:var(--teal);padding-left:7px}}
.siennaed figcaption{{border-left-color:var(--sienna);padding-left:7px}}
.inked figcaption{{border-left-color:var(--muted);padding-left:7px}}
/* A wide graph takes the whole grid row rather than one 190px cell, and is
   capped in height so a 25:1 strip cannot swallow the page. */
.g.wide{{grid-column:1/-1}}
.g.wide .gz{{overflow-x:auto}}
.g.wide .gz img{{width:auto;max-width:none;height:auto;max-height:190px}}
.lb{{display:none}}
.lb:target{{display:flex;position:fixed;inset:0;z-index:50;align-items:center;justify-content:center;padding:28px}}
.lbbg{{position:absolute;inset:0;background:rgba(8,11,15,.82)}}
.lb img{{position:relative;max-width:96vw;max-height:92vh;background:#fff;padding:14px;border-radius:6px}}
/* Fitting a 12000px graph to the viewport leaves it ~78px tall and unreadable,
   so a wide one opens at natural size inside a scrollable panel instead. */
.lb.wide:target{{display:block;overflow:auto;padding:0}}
.lb.wide img{{max-width:none;max-height:none;margin:28px;display:block}}
.lbhint{{position:fixed;left:0;right:0;bottom:0;margin:0;padding:8px 14px;text-align:center;
  background:rgba(8,11,15,.86);color:#e6e9ee;font-size:.74rem;letter-spacing:.06em;
  text-transform:uppercase;z-index:2}}
@media(prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
<div class="wrap">
<header class="top">
<h1>Corrected Merge Atlas</h1>
<p class="lede">Implication graphs for every case&nbsp;study&nbsp;3 run that has been through the
methodology in its specified order &mdash; semantically unique, then strongest guarantees, then merge.
Each run is shown three ways: assumptions alone, guarantees alone, and the whole GR1 specification.</p>
<p class="lede second">{headline}</p>
<div class="meta"><span><b>{n_runs}</b> runs</span><span><b>{n_graphs}</b> graphs</span>
<span>{merge_line}</span><span>date <b>2026-08-13</b></span>{pending_meta}</div>
</header>
<nav aria-label="Case studies"><ul>{nav}</ul></nav>
<main>
{sections}
</main>
</div>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output",
                    default=os.path.join(ROOT, "docs", "results", "merge-atlas.html"))
    args = ap.parse_args(argv)
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
