#!/usr/bin/env python3
"""
scenario_page.py: emit scenario.html from data/scenario.json.

WHY THIS PAGE EXISTS, AND WHY IT IS THE ONLY ONE OF ITS KIND.

The three approaches can each express everything the others can. What separates
them is how many documents it takes and what the plan of record ends up holding,
and neither is visible until the same task is put to all three.

That task is described once. Every count on this site lives here: a figure on an
approach page would be a second scenario, implied and never stated, and a reader
comparing two pages would be comparing two different systems without being told.
tools/verify.py fails the build if a figure appears anywhere else.

Nothing here is typed. The framework count is the length of an id list stored in
data/scenario-evidence/, each guide's count is recomputed from the plan it came
from, and the file inventory follows a rule stated per approach. The three
figures are drawn on one grid by tools/diagrams.py.

Usage:
    python tools/scenario_page.py
    python tools/scenario_page.py --out DIR
"""

from __future__ import annotations

import argparse
import json
import os

from model_icons import model_tile

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(TOOLS_DIR)
DATA = os.path.join(SITE_ROOT, "data")

#  The option-letter order, A then B then C, which is the order the
#  rest of the site uses: assets/site.js orders every JS-rendered block by it
#  and tools/pagecheck.js asserts it.
#
#  This file was alphabetical by structural name, and the comment above it said
#  that was the order used everywhere, which was not true and had not been for
#  some time. The effect was that the one page comparing the three side by side
#  in a table put them in a different order from the page comparing them
#  question by question. Ordering is the easiest way for a site like this to
#  argue without saying anything, so two orders is worse than either.
ORDER = ["catalog-first", "component-first", "assessment-first"]
LABEL = {"assessment-first": "Assessment-first",
         "catalog-first": "Catalog-first",
         "component-first": "Component-first"}

#  Two sections. What the schemas force used to be a third, and what each count
#  makes concrete on an approach page a fourth; the first is now stated on the
#  file rows it explains, and the second is argued on the approach pages
#  themselves, where the strengths and risks are.
HEADINGS = [
    ("inputs", "1. System and requirements"),
    ("files", "2. Files produced by each approach"),
]


def load(rel: str):
    with open(os.path.join(DATA, rel), "r", encoding="utf-8") as fh:
        return json.load(fh)


def build(sc) -> str:
    hard = sum(h["requirements"] for h in sc["hardening"])
    reg = sc["framework"]["controls"]
    o = []

    o.append(f'<h1>{sc["title"]}</h1>')
    o.append(f'<p class="lede">{sc["summary"]}</p>')

    o.append('<nav class="toc" aria-label="On this page">\n'
             '  <span class="toc__label">On this page</span>\n  <ol>')
    for anchor, text in HEADINGS:
        o.append(f'    <li><a href="#{anchor}">{text}</a></li>')
    o.append('  </ol>\n</nav>')

    # ---- 1. the inputs ---------------------------------------------------
    o.append(f'<section id="inputs">\n<h2>{HEADINGS[0][1]}</h2>')
    o.append('<div class="tier2">')
    o.append('  <p>The comparison holds the system, baseline and hardening '
             'guides constant. Counts derive from the published source files '
             'and OSCAL schema constraints.</p>')
    o.append('  <dl class="scenario__inputs">')
    o.append(f'    <dt>Framework</dt><dd>{sc["framework"]["label"]}. '
             f'<strong>{reg}</strong> controls: {sc["framework"]["base"]} base and '
             f'{sc["framework"]["enhancements"]} enhancements, across '
             f'{sc["framework"]["families"]} families.</dd>')
    for h in sc["hardening"]:
        o.append(f'    <dt>{h["technology"]}</dt><dd>{h["label"]}. '
                 f'<strong>{h["requirements"]}</strong> requirements in '
                 f'{h["grouping"]} {h["grouping_label"]}.</dd>')
    o.append(f'    <dt>Total requirements</dt><dd><strong>{hard}</strong> hardening '
             f'requirements alongside <strong>{reg}</strong> regulatory controls, '
             f'for <strong>{reg + hard}</strong> requirements across one '
             f'system.</dd>')
    o.append('  </dl>')
    #  The excluded model is not named here either. It said that the scenario
    #  uses every OSCAL model except the plan of action and milestones, and why:
    #  that document records what was not met and is the same in all three
    #  approaches, so it separates none of them. True, and it is a sentence
    #  about a document the page then never mentions again.
    #
    #  It stays in data/scenario.json and stays checked. The model list is
    #  asserted to be seven and to exclude it, and the icon coverage check reads
    #  it too, so the exclusion is still a claim the build holds rather than
    #  something dropped.
    o.append('</div>')

    #  The derivations are not printed here. They said, for each figure, which
    #  file it was counted from and by what rule, in a disclosure under the
    #  inputs, and they are four paragraphs of build detail on a page whose
    #  subject is one system modelled three ways.
    #
    #  They stay in data/scenario.json and stay checked, which is where the
    #  work they were doing actually happens: verify.py --scenario opens each
    #  file a derivation names and recomputes the count by the rule it states,
    #  so a figure that drifted from its own corpus fails the build. Printing
    #  the sentence asked a reader to take on trust what the harness proves.
    o.append('</section>')

    # ---- 2. the file sets ------------------------------------------------
    o.append(f'<section id="files" class="wide">\n<h2>{HEADINGS[1][1]}</h2>')
    o.append('<div class="tier2">\n  <p>Each tile represents one file. All three '
             'diagrams use the same tile size and grid to compare file counts. '
             'An unused model appears as a dashed line labelled none. File '
             'counts do not measure overall implementation effort.</p>\n</div>')

    o.append('<table class="criteria-table">')
    o.append('  <caption class="small muted">Files by model, ordered by OSCAL '
             'layer from controls to assessment.</caption>')
    o.append('  <thead><tr><th scope="col">Model</th>'
             + "".join(f'<th scope="col">{LABEL[k]}</th>' for k in ORDER)
             + '</tr></thead>\n  <tbody>')
    for i, model in enumerate(sc["models"]):
        cells = []
        for k in ORDER:
            f = [x for x in sc["approaches"][k]["files"] if x["model"] == model][0]
            cells.append(f'<td>{f["count"]}</td>' if f["count"]
                         else '<td class="is-none">none</td>')
        #  The same chip the approach pages draw, not a bare <code>. A reader
        #  arrives here from a stakeholder table where every model wore its icon
        #  and met the same seven names again as plain text, which is two
        #  vocabularies for one set of things. The icon also carries the layer
        #  colour, so the three bands this table is ordered by are visible in the
        #  first column rather than only stated in the caption.
        o.append(f'    <tr><th scope="row">{model_tile(model)}</th>'
                 + "".join(cells) + '</tr>')
    o.append('    <tr class="is-total"><th scope="row">Total files</th>'
             + "".join(f'<td><strong>'
                       f'{sum(x["count"] for x in sc["approaches"][k]["files"])}'
                       f'</strong></td>' for k in ORDER)
             + '</tr>')
    o.append('    <tr><th scope="row">Models used</th>'
             + "".join(f'<td>{sum(1 for x in sc["approaches"][k]["files"] if x["count"])}'
                       f' of {len(sc["models"])}</td>' for k in ORDER)
             + '</tr>')
    o.append('  </tbody>\n</table>')

    for k in ORDER:
        a = sc["approaches"][k]
        short = k.split("-")[0]
        total = sum(f["count"] for f in a["files"])
        o.append(f'<h3 id="files-{short}">2.{ORDER.index(k) + 1} {LABEL[k]}, '
                 f'{total} files</h3>')
        o.append(f'<div class="tier2">\n  <p>{a["rule"]}</p>\n</div>')
        o.append('<figure>')
        o.append(f'  <div class="diagram" data-diagram="710-scenario-{short}"></div>')
        o.append(f'  <figcaption>{a["plan_of_record"]}. '
                 f'See <a href="./{k}.html">{LABEL[k]}</a> for roles, '
                 f'tradeoffs and references.</figcaption>')
        o.append('</figure>')
        #  The file list is not printed under the figure. It was every model
        #  again as a term, with its count, what it is for, a further sentence
        #  of detail, and the names of the files, and the figure directly above
        #  it already draws all of that: the count as tiles, the names on the
        #  tiles, and what the model is for as the line under each group. Three
        #  approaches, seven models each, so the page said the same thing twice
        #  eighteen times over, and the second telling was the longer one.
        #
        #  The screen reader case that justified it is covered where it should
        #  be. Each figure carries a <desc> naming every model, its count, what
        #  it is for and every file in it, wired through aria-labelledby, and
        #  the harness checks that against the same data the drawing comes from.
        #  A reader who cannot see the tiles gets the description of the tiles,
        #  not a second list beneath them.
        #
        #  The detail sentences stay in data/scenario.json. Some of them are
        #  the sharpest lines on the page and none of them is now printed, which
        #  is the same trade this page already made twice, for the derivations
        #  and for the excluded model. They stay checked.
    o.append('</section>')

    return "\n".join(o)


def run(outdir: str, quiet: bool = False) -> str:
    sc = load("scenario.json")
    main = build(sc)
    shell = open(os.path.join(SITE_ROOT, "assets", "shell.html"),
                 encoding="utf-8").read()
    #  The shell carries its own explanatory comment for a human copying it.
    shell = shell[shell.index("<html"):]
    page = (shell
            .replace("{{TITLE}}", "A worked scenario")
            .replace("{{DESCRIPTION}}",
                     "One system under 800-53 High with three hardening guides, "
                     "comparing the files and system security plan content "
                     "produced by three OSCAL approaches.")
            .replace("{{SLUG}}", "scenario.html")
            .replace("{{BASE}}", ".")
            .replace("{{MAIN}}", main))
    path = os.path.join(outdir, "scenario.html")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    if not quiet:
        import re
        print(f"  scenario.html    "
              f"{len(re.sub(r'<[^>]+>', ' ', main).split()):>5,} words of prose")
    return page


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=SITE_ROOT)
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args()
    run(a.out, a.quiet)


if __name__ == "__main__":
    main()
