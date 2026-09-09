#!/usr/bin/env python3
"""
approach_pages.py: emit the three approach pages from one template.

Plan section 3 rule 5 requires equal budget across the three approaches
"enforced by construction". Three hand-written pages cannot deliver that: the
one written first sets the shape and the other two drift toward it. So the nine
sections, their order, their heading text and their per-approach counts come
from a single function, and the only thing that varies per page is the prose
that has to vary.

What the template fixes, and what a page therefore cannot change:
    six sections, same order. Section 1's heading is per approach,
      because what each one publishes is the subject of it; the other six
      are the same words on all three pages
    three strengths and three risks in section 2, from data/tradeoffs.json
    no figures anywhere: every count lives on the scenario page
    six question subsections, generated from data/six-questions.json
    three sentences in section 7, same frames on all three pages

What a page supplies:
    the lede, 25 to 60 words, which is the whole summary
    two or three paragraphs per question

Gate 7 removed quotations and proponent attribution from the whole site. No
personal name and no proponent organization appears on any page. An approach is
named by its structural name. Characterizations trace to a JSON pointer into a
shipped file, or to a cited source document.

Usage:
    python tools/approach_pages.py
    python tools/approach_pages.py --out DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(TOOLS_DIR)
DATA = os.path.join(SITE_ROOT, "data")

#  Alphabetical by structural name, everywhere, stated on the page.
ORDER = ["assessment-first", "catalog-first", "component-first"]

#  Plan section 3 rule 6: consequences, not verdicts. An approach page describes
#  one approach; a comparative on it reads as a verdict delivered out of the
#  reader's sight, where the other two columns are not there to answer it.
BANNED = re.compile(
    r"\b(unlike|whereas|better than|worse than|more than|fewer than|"
    r"only approach|the only one that|superior|inferior|weaker|stronger than)\b",
    re.I)


def load(rel: str):
    with open(os.path.join(DATA, rel), "r", encoding="utf-8") as fh:
        return json.load(fh)


def words(html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    return len([w for w in text.split() if any(c.isalnum() for c in w)])


# --------------------------------------------------------------------------- #
# the authored content, one block per approach                                 #
# --------------------------------------------------------------------------- #

CONTENT = {

# =========================================================== assessment-first
"assessment-first": {
"title": "Assessment-first",
"lede": "Assessment-first represents a rule as an assessment plan activity or step. A property named check identifies the check on the activity or step. Activities state requirements, and steps describe the procedures used to verify those requirements.",
"description": "Hardening guidance uses OSCAL assessment plan activities and "
               "steps, with properties identifying checks and activities "
               "linking to controls.",

"exists": "",









},

# ============================================================== catalog-first
"catalog-first": {
"title": "Catalog-first",
"lede": "Catalog-first represents a <strong>rule</strong> as a catalog control and a <strong>check</strong> as a software component. <strong>TechnicalControlId</strong> links the control to the check component; <strong>ConfigRuleId</strong> identifies the executable rule. The control states the requirement, and the component describes the check.",
"description": "Hardening guidance uses catalog controls linked to checks "
               "represented as software components in component definitions.",

"exists": "",









},

# ============================================================ component-first
"component-first": {
"title": "Component-first",
"lede": "Component-first represents a rule in the proposed rules assembly on the product component. The check uses the proposed checks assembly on a separate component of type validation. The rule states the required configuration; the check describes how to test the configuration.",
"description": "Product components contain proposed rules assemblies; "
               "validation components contain proposed checks assemblies. "
               "A composite key links each check to a rule.",

"exists": "",









},
}


# --------------------------------------------------------------------------- #
# the template                                                                 #
# --------------------------------------------------------------------------- #

NAV = [("index.html", "Start here"),
       ("six-questions.html", "The six questions"),
       ("scenario.html", "A worked scenario"),
       ("catalog-first.html", "Catalog-first"),
       ("component-first.html", "Component-first"),
       ("assessment-first.html", "Assessment-first"),
       ("questions.html", "Open questions"),
       ("oscal-artifacts.html", "OSCAL artifacts")]

#  Identical on all three pages. Changing one changes all three.
#  Seven sections, not eight. "SC-28 followed end to end" is gone: the first of
#  the two rules the site walks IS protection of data at rest, sc-28, so section
#  4 now follows it end to end in all three shapes, and the old section followed
#  it through each publisher's own shipped content instead. That made the same
#  point twice, once from our encodings and once from a corpus, and the corpus
#  version dragged publisher-specific identifiers into a walkthrough that is
#  supposed to hold one subject constant. What each group actually ships is on
#  the artifacts page.
#  Tradeoffs open the page. They used to be section 6, two boxes at the foot,
#  which meant a reader met a thousand words of description before being told
#  what the thing is good and bad at. The section that carried them is gone
#  rather than duplicated, and what the pre-read recorded and the two papers do
#  not is carried inside the new block as one line per approach.
#  No figures on these pages. The site describes one scenario, on the page built
#  for it, and every count belongs there: a number quoted here would be a second
#  scenario, implied and unstated. What an approach page carries is the shape of
#  the approach, and tools/verify.py fails the build if a figure appears on one.
#  Four sections. There were five: a per-question walk sat third, restating
#  this approach's column of the six questions with its own prose, its own
#  answer strip and the published extracts. It is gone. The six questions page
#  carries all three columns of that material side by side, which is the
#  comparison a reader is making, and one column of it here was the same
#  content read twice with nothing to compare it against.
#  Section 3 was "Which OSCAL models this touches": a footprint paragraph and
#  the seven-model map with this approach's models outlined. It said where the
#  content lives, which is the first line of the stakeholder mapping above it
#  and the model row on every answer on the six questions page, and it had to
#  disclaim itself in its own caption because a footprint is not a measure of
#  anything. The join chain was nested under it as 3.1 and is the section now.
HEADINGS = [
    ("stakeholder", "1. Stakeholder roles and OSCAL models"),
    ("tradeoffs", "2. Strengths and risks"),
    ("joins", "3. Tracing rules and checks from implementation to assessment"),
]


PATTERNS = json.load(open(os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "data", "pattern-examples.json"), encoding="utf-8"))


#  One box, two glyphs. Drawing a tick inside a circle and a cross inside a
#  triangle would have made the risk column louder than the strength column
#  before a word of either was read, so the two marks are the same size, the
#  same weight and the same shape, and only what is inside them differs. That
#  difference is a shape difference, which is what a reader who cannot separate
#  the two colours is left with.
MARK = {
    "pro": ('<rect x="1.1" y="1.1" width="13.8" height="13.8" rx="3.2" '
            'fill="none" stroke="currentColor" stroke-width="1.6"/>'
            '<path d="M4.4 8.3 L6.9 10.8 L11.6 5.4" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round"/>'),
    "con": ('<rect x="1.1" y="1.1" width="13.8" height="13.8" rx="3.2" '
            'fill="none" stroke="currentColor" stroke-width="1.6"/>'
            '<path d="M5.4 5.4 L10.6 10.6 M10.6 5.4 L5.4 10.6" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'),
}


def mark(kind: str) -> str:
    """The tick or the cross, as decoration.

    aria-hidden, because the column it sits in is headed with the word and a
    screen reader that announced "image" sixteen times on one page would be
    worse served than one that hears nothing. The meaning is in the heading.
    """
    return ('<span class="tradeoff__mark">'
            f'<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
            f'{MARK[kind]}</svg></span>')


def tradeoffs_section(key: str, tr) -> str:
    """Section 2: three strengths and three risks, marked and coloured.

    Equal budget is the point of the block, so the count is read from the data
    rather than from the list: three pages printing a different number of
    strengths would be making an argument in the layout, where no reader would
    think to look for one.

    Nothing here is cited on the page. What each entry rests on is recorded in
    BUILD-LOG.md, and where an entry turns on what a model can express, the
    schema fragment behind it is named in the data and checked by
    tools/verify.py without being rendered.
    """
    a = tr["approaches"][key]
    o = [f'<section id="tradeoffs">\n<h2>{HEADINGS[1][1]}</h2>']
    o.append(f'<div class="tier2">\n  <p>{a["intro"]}</p>\n</div>')

    def entries(kind, side, head):
        out = [f'  <div class="tradeoffs__side tradeoffs__side--{kind}">',
               f'    <h3 class="tradeoffs__head">{mark(kind)}{head}'
               f'<span class="tradeoffs__count">{len(side)}</span></h3>',
               '    <ol class="tradeoffs__list">']
        for e in side:
            out.append('      <li class="tradeoff">')
            out.append(f'        {mark(kind)}')
            out.append(f'        <p class="tradeoff__title">{e["title"]}</p>')
            out.append(f'        <p class="tradeoff__body">{e["body"]}</p>')
            out.append('      </li>')
        out += ['    </ol>', '  </div>']
        return out

    o.append('<div class="tradeoffs">')
    o += entries("pro", a["pros"], "2.1 Strengths")
    o += entries("con", a["cons"], "2.2 Risks")
    o.append('</div>')
    o.append('</section>')
    return "\n".join(o)


#  One icon per model. The emitter lives in tools/model_icons.py, beside the
#  generator that writes data/model-icons.json, because the scenario page draws
#  the same tiles and two copies of it would drift.
#
#  Every tile used to draw the same page-with-a-folded-corner. In a table whose
#  entire subject is which model each party works in, that said "this is a file"
#  seven times and distinguished nothing: a reader had to read the name to learn
#  what the drawing was there to tell them.
from model_icons import model_icon, model_tile as model_chip


#  The runtime, drawn rather than named.
#
#  Every other party in the mapping writes a document, so a file tile says what
#  they do. The policy engine is not a document: it is the thing that reads
#  OSCAL, executes, and writes OSCAL back. Drawing it in the same shape as the
#  parties that produce documents said it was one of them.
#
#  Something arrives, a machine runs, something leaves. Both arrowheads are part
#  of the glyph, which is why a row carrying it does not also carry the arrow the
#  other rows use.
RUNTIME_GLYPH = (
    '<svg class="mflow__runtime" viewBox="0 0 46 20" aria-hidden="true" '
    'focusable="false">'
    '<path d="M1,10 H12.5" fill="none" stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M16.4,10 L10.8,7.1 v5.8 Z" fill="currentColor"/>'
    '<rect x="17.6" y="1.7" width="12.2" height="16.6" rx="3.2" fill="none" '
    'stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M21.5,6.1 L26.7,10 L21.5,13.9 Z" fill="currentColor"/>'
    '<path d="M30.6,10 H41" fill="none" stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M45,10 L39.4,7.1 v5.8 Z" fill="currentColor"/></svg>')

#  The same mark in a flow row, where it stands in for the arrow, plus the
#  sentence it draws. The glyph is aria-hidden, so without this a screen reader
#  hears two model names in a row and nothing about the machine between them,
#  which is the whole content of the row.
#  The mark is captioned, like every other item in a run. Two reasons, and the
#  second is the one that shows: a reader meeting an unlabelled glyph has to
#  infer it, and a row of items where only some carry a second line has nothing
#  to align on, so the mark sat half a caption below the tiles beside it.
RUNTIME = ('<span class="lineage__end lineage__end--mark">'
           '<span class="lineage__box">' + RUNTIME_GLYPH + '</span>'
           '<span class="lineage__q">runtime</span>'
           '<span class="visually-hidden"> is read by the policy engine, which '
           'runs and writes </span></span>')


def model_tile(m, boxed: bool = False) -> str:
    """One model, drawn as itself, with its component type if it has one.

    Boxed puts it in the same two-part stack the marks use, a box on the first
    line and a caption line under it, so a row of tiles and marks lines up on
    both. The caption is empty for a tile: the name is inside the box already,
    and what the second line is doing is holding the row's shape.
    """
    tile = model_chip(m["model"], m.get("kind"))
    if not boxed:
        return tile
    return (f'<span class="lineage__end"><span class="lineage__box">{tile}'
            f'</span><span class="lineage__q"></span></span>')


def model_tiles(models, boxed: bool = False) -> str:
    return "".join(model_tile(m, boxed) for m in models)


def stakeholder_section(key: str, c, view, sh) -> str:
    """Section 1: which OSCAL model each party works in.

    This was two sections, one on what kind of thing a rule is and one naming
    which of three stakeholders an approach served first. Both were the same
    question at a resolution nobody could act on.

    Seven parties touch a rule, each works in a model, and which model is the
    whole of what an approach asks of them.

    Two of the seven are grouped, being one role played by two kinds of
    organisation. One of the seven, the mapping provider, exists because a
    hardening guide does not always carry the tie to a framework and whoever
    writes the guide is often not whoever ties it. And the checks belong to the
    policy engine provider wherever they are written, because a check is what
    triggers an engine to run: a component definition in two of the approaches,
    the assessment plan in the third, where the guidance authors write the
    activity and the engine provider writes the check inside it.

    Not every row runs something. On the assessment approach the system owner
    writes the plan of record and runs nothing, because an assessor's route
    takes no dependency on the owner's tooling and cannot see it.
    """
    a = sh["approaches"][key]
    ARROW = ('<span class="mflow__arrow" aria-hidden="true">&rarr;</span>'
             '<span class="visually-hidden"> produces </span>')

    o = [f'<section id="stakeholder">\n<h2>{HEADINGS[0][1]}</h2>']
    o.append('<div class="tier2">')
    o.append(f'  <p>{c["title"]} treats a hardening rule as '
             f'<strong>{view["label"][0].lower() + view["label"][1:]}</strong>, '
             f'using the <code>{view["implies_model"]}</code> model in the '
             f'{view["implies_layer"]} layer. The table shows the models '
             f'each party uses to publish guidance, implement controls or '
             f'record assessment results.</p>')
    o.append(f'  <p>{sh["intro"]}</p>')
    o.append('</div>')

    o.append('<table class="criteria-table stakeholders">')
    o.append('  <thead><tr><th scope="col">Party</th>'
             '<th scope="col">OSCAL model</th></tr></thead>\n  <tbody>')
    #  Two of the seven are one role played by two kinds of organisation: a
    #  benchmark body writing for a product it does not own, and a vendor
    #  writing for its own. They were two rows saying the same thing about the
    #  same model, and a reader had no way to tell that was deliberate. A group
    #  heading spans them, so the repetition reads as the point rather than as
    #  an oversight.
    groups = {g["key"]: g for g in sh.get("groups", [])}
    names = {p["key"]: p["name"] for p in sh["parties"]}
    seen = set()
    for party in sh["parties"]:
        g = party.get("group")
        if g and g not in seen:
            seen.add(g)
            o.append(f'    <tr class="stakeholders__group">'
                     f'<th scope="colgroup" colspan="2">{groups[g]["label"]}'
                     f'<span class="stakeholders__note">{groups[g]["note"]}'
                     f'</span></th></tr>')
        e = a[party["key"]]
        parts = []
        if e.get("writes"):
            parts.append(f'<span class="mflow">{model_tiles(e["writes"])}</span>')
        #  The engine's flow is an execution, not a derivation, so it gets the
        #  runtime glyph where the other rows would take a plain arrow. Any
        #  other party with a flow keeps the arrow: what they do is produce one
        #  document from another, which is what an arrow means everywhere else
        #  on the site.
        #  The runtime is drawn on the row of whoever runs it, which is never
        #  the row that built it. A provider ships the checks and runs nothing;
        #  the system owner and the auditor take the same checks and run them,
        #  and the row says what each run makes. Any other flow is a derivation,
        #  one document produced from another, and keeps the plain arrow.
        for fl in e.get("flows", []):
            src, dst = (fl["from"], fl["to"]) if isinstance(fl, dict) else fl
            runs = isinstance(fl, dict) and fl.get("runtime")
            lab = (f'<span class="mflow__by">runs the checks, making '
                   f'{fl["makes"]}</span>' if runs else "")
            #  What goes in, the runtime, and what comes out are one thing to
            #  read and are held on one line. They were three flex items beside
            #  a label, so the label took the first line and the output wrapped
            #  onto a third, which read as two separate facts.
            parts.append(f'<span class="mflow">{lab}'
                         f'<span class="mflow__run">'
                         f'{model_tiles(src, runs)}'
                         f'{RUNTIME if runs else ARROW}'
                         f'{model_tiles(dst, runs)}'
                         f'</span></span>')
        #  A row says what a party produces, and nothing about what a person
        #  opens. The auditor row used to carry a "reads" line naming the plan
        #  of record and the prior results, which is a description of somebody
        #  reading a document: true, and not what this site is about. What the
        #  machine consumes is already on the row, as the input side of the run.
        #
        #  A party with nothing to write in this approach is not an empty cell.
        #  The mapping provider has no document in two of the three, because the
        #  tie to the framework is inline there, and that is a finding rather
        #  than a gap in the table.
        if not parts:
            parts.append('<span class="mflow"><span class="mflow__none">'
                         'no separate document</span></span>')
        note = (f'<span class="stakeholders__note">{e["note"]}</span>'
                if e.get("note") else "")
        row = ' class="stakeholders__in"' if g else ""
        o.append(f'    <tr{row}><th scope="row">{party["name"]}'
                 f'<span class="stakeholders__who">{party["who"]}</span></th>'
                 f'<td>{"".join(parts)}{note}</td></tr>')
    o.append('  </tbody>\n</table>')
    #  The mark is defined where it is used. It is also in the legend of the
    #  chain figure further down the page, but a reader meeting it here should
    #  not have to scroll two sections to find out what it means.
    o.append(f'<p class="stakeholders__key">{RUNTIME_GLYPH}'
             f'<span><strong>The runtime.</strong> {sh["runtime"]}</span></p>')
    o.append('</section>')
    return "\n".join(o)


def joins_section(key: str, jn, six_questions) -> str:
    """The chain: every foreign key from the rule to the claim and the result.

    The six questions are answered one at a time, which leaves the thing that
    decides whether the set works invisible. A rule is only useful if something
    can get from it to the check that tests it, from the check to whatever runs
    that check, and from the outcome back again.

    So this is the chain rather than a list of joins. It starts where the rule
    is introduced and walks to the claim and the result, and at every step it
    names the field that holds the pointer and the field it resolves to. A step
    can be made of more than one relationship, which is itself the finding:
    getting from a rule to its check costs one relationship in one approach and
    two in another.

    The table is the fields and the figure beneath it is the same chain with the
    values, which are rule 1 exactly as the six questions page encodes it. A
    reader can take either and check it against the other.
    """
    a = jn["approaches"][key]
    stage = {s["key"]: s for s in jn["stages"]}
    short = key.split("-")[0]

    #  The section's own heading now, rather than a 3.1 under a footprint
    #  section that has gone. The id stays "joins", which is what it always was
    #  and what the six questions page links back to.
    o = [f'<div class="tier2">\n  <p>{jn["intro"]}</p>']
    #  This was a table: four columns, a row per relationship, the fields and
    #  the questions and the way each one resolves. The figure below draws the
    #  same chain with the values on it, so the table was the figure again in
    #  words, at the length of a screen and a half, directly above it.
    #
    #  What the figure cannot draw is why a step costs what it costs, so the
    #  notes stay. Each one keeps the two links the table's cells carried, on
    #  the stage names, which is where a reader would reach for them.
    o.append('  <ol class="joins__steps">')
    #  Where the rule is defined, before anything that points at it. The chain
    #  used to open on the tie from the rule to a control, which in catalog-first
    #  meant the mapping collection was the first document a reader met and the
    #  catalog holding the rule came second. The figure had always started here;
    #  the notes beside it had not.
    intro = a["introduced"]
    st = stage[intro["slot"] and "rule"]
    o.append(f'    <li><strong><a href="{esc_href(st["slot"], key)}">'
             f'{st["label"]}</a> definition.</strong> '
             f'{intro["note"]} '
             f'<code>{intro["model"]}</code>, <code>{intro["field"]}</code>.</li>')
    for hop in a["hops"]:
        ends = []
        for end in ("from", "to"):
            st = stage[hop[end]]
            ends.append(f'<a href="{esc_href(st["slot"], key)}">{st["label"]}'
                        f'</a>')
        o.append(f'    <li><strong>{ends[0]} '
                 f'<span class="joins__to" aria-hidden="true">&rarr;</span>'
                 f'<span class="visually-hidden">to</span> {ends[1]}.</strong> '
                 f'{hop["note"]}</li>')
    o.append('  </ol>\n</div>')

    o.append('<figure>')
    o.append(f'  <div class="diagram" data-diagram="73-join-{short}"></div>')
    o.append('  <figcaption>The chain uses rule 1, data at rest, from the '
             'six questions page. Each step shows the fields and values a '
             'consumer follows. The relationship type indicates whether '
             'resolution uses schema-defined references, containment or '
             'publisher conventions.</figcaption>')
    o.append('</figure>')
    return "\n".join(o)

def esc_href(slot: str, approach: str) -> str:
    return f'./six-questions.html#q{slot}-{approach}'


def build(key: str, six_questions, views, tradeoffs, stakeholders,
          joins) -> str:
    c = CONTENT[key]
    ap = [a for a in six_questions["approaches"] if a["key"] == key][0]
    short = key.split("-")[0]
    view = [v for v in views["views"] if v["aligned_approach"] == key][0]
    o = []
    o.append(f'<h1>{c["title"]}</h1>')
    o.append(f'<p class="lede">{c["lede"]}</p>')

    o.append('<nav class="toc" aria-label="On this page">\n'
             '  <span class="toc__label">On this page</span>\n  <ol>')
    for anchor, text in HEADINGS:
        o.append(f'    <li><a href="#{anchor}">{text}</a></li>')
    o.append('  </ol>\n</nav>')

    # ---- 1. how this approach is published -------------------------------
    # ---- 1. the stakeholder mapping ---------------------------------------
    o.append(stakeholder_section(key, c, view, stakeholders))

    # ---- 2. strengths and risks -------------------------------------------
    o.append(tradeoffs_section(key, tradeoffs))

    #  Section 3 used to be here: the six questions, answered one at a time
    #  for this approach, with an answer strip above them and the published
    #  extracts inside each one. All of it said again what six-questions.html
    #  says with all three columns visible, so the reader who wanted to know
    #  what a catalog-first answer to question 3 costs had to hold the other
    #  two in their head. The strip went with it for the same reason: a
    #  scorecard for one approach is a row of a table whose other rows are the
    #  point. What this page owes is the argument, and the argument is the
    #  stakeholder mapping, the strengths and risks, and the joins below.

    # ---- 3. what joins one answer to the next -------------------------------
    o.append(f'<section id="joins" class="wide">\n<h2>{HEADINGS[2][1]}</h2>')
    o.append(joins_section(key, joins, six_questions))
    o.append('</section>')

    #  A status section closed these pages: what the content conforms to, how
    #  complete it is, and the publisher's own statement about it. All three are
    #  facts about a corpus rather than about an approach, and the corpus is
    #  what the artifacts page is for. On a page whose subject is the shape of
    #  an approach, it read as a verdict on the people who published it.

    page = "\n".join(o)

    #  A note here counted the extracts on the page and explained why the three
    #  pages showed different numbers: an unanswered question has nothing to
    #  extract. The extracts were in section 3 and went with it, so all that is
    #  left on a page is the evidence under its status section, and a count of
    #  one with a paragraph explaining variation was explaining nothing. The
    #  extracts themselves are on the six questions page, rendered from the same
    #  snippet_ids the matrix has always declared.
    return page


PAGE = """<!doctype html>
<html lang="en" data-base=".">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Automating Technical Hardening Guidance with OSCAL</title>
<meta name="description" content="{description}">
<meta name="color-scheme" content="light dark">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Automating Technical Hardening Guidance with OSCAL">
<meta property="og:locale" content="en">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<link rel="stylesheet" href="./assets/site.css">
<script>
  /* Set the theme before first paint so the page never flashes the wrong one. */
  (function () {{
    var t = null;
    try {{ t = localStorage.getItem("tfg-theme"); }} catch (e) {{}}
    if (!t) t = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", t);
  }})();
</script>
</head>
<body>

<a class="skip-link" href="#main">Skip to content</a>

<aside class="wip-banner" aria-label="Analysis status" hidden>
    <span>Work in progress</span>
    <button type="button" class="wip-banner__dismiss" aria-label="Dismiss work in progress notice" hidden><span aria-hidden="true">×</span></button>
</aside>

<header class="site-header">
  <div class="site-header__inner">
    <p class="site-title"><a href="./index.html"><img class="site-logo site-logo--light" src="./assets/brand/oscal-foundation.png" alt="" width="208" height="96"><img class="site-logo site-logo--dark" src="./assets/brand/oscal-foundation-rev.png" alt="" width="208" height="96"><span>Automating Technical Hardening Guidance with OSCAL</span></a></p>
    <nav class="site-nav" aria-label="Sections">
      <ul>
{nav}
      </ul>
    </nav>
    <button type="button" class="theme-toggle" aria-pressed="false">Dark theme</button>
  </div>
</header>

<main id="main">

{main}

</main>

<!-- Footer kept identical to assets/shell.html. The generator used to emit a
     longer one carrying provenance, sources and a data-generated stamp; the
     shell was since reduced to the one line that matters and site.js stopped
     wiring data-generated, so regenerating these pages reintroduced a hook
     nothing filled. One footer, one place. -->
<footer class="site-footer">
  <div class="site-footer__inner">
     <p><strong>No recommendation is made.</strong> The analysis compares three
         approaches and the published OSCAL content.</p>
  </div>
</footer>

<!-- Read only when the page is opened from a folder rather than served.
     Generated by tools/bundle.py from data/; a served copy ignores it. -->
<script src="./assets/bundle.js"></script>
<script src="./assets/highlight.js"></script>
<script src="./assets/site.js"></script>

</body>
</html>
"""


def run(outdir: str, quiet: bool = False, force: bool = False) -> dict[str, int]:
    six_questions = load("six-questions.json")
    views = load("views.json")
    tradeoffs = load("tradeoffs.json")
    stakeholders = load("stakeholders.json")
    joins = load("joins.json")
    people = sorted({q["speaker"] for q in load("quotes.json")["quotes"]
                     if q.get("speaker")})

    nav = "\n".join(f'        <li><a href="./{h}">{t}</a></li>' for h, t in NAV)
    counts, files = {}, {}

    for key in ORDER:
        c = CONTENT[key]
        main = build(key, six_questions, views, tradeoffs, stakeholders,
                     joins)
        text = re.sub(r"<[^>]+>", " ", main)

        #  Gate 7: no quotations anywhere, and no personal name. The name list
        #  is taken from quotes.json, which is retained as provenance precisely
        #  so that this check knows who must not appear.
        if "blockquote" in main or "data-quote" in main:
            raise AssertionError(f"{key}: the site carries no quotations")
        named = [n for n in people if n in text]
        if named:
            raise AssertionError(f"{key}: names a person: {named}")
        for org in ("Easy Dynamics", "IBM"):
            #  File paths carry the organization and are provenance. Prose must
            #  not. A path is always inside a snippet header, which is rendered
            #  from data/ and is not part of this string.
            if org in text:
                raise AssertionError(f"{key}: names a proponent organization: {org}")

        bad = BANNED.findall(re.sub(r"<[^>]+>", " ", main))
        if bad:
            raise AssertionError(
                f"{key}: comparative language on an approach page: {sorted(set(bad))}. "
                f"An approach page describes one approach.")

        #  The lede is the summary. It is held short on purpose: a reader who
        #  wanted the long version would be reading the sections below it.
        g = words(c["lede"])
        if not 25 <= g <= 60:
            raise AssertionError(f"{key}: the lede is {g} words, outside 25 to 60")

        #  Prose, not payload. The budget exists so no approach is argued at
        #  greater length than another, and a field name is not argument: its
        #  size is set by the data's shape rather than by anything rhetorical.
        prose = main
        for pat in (r"<code[^>]*>.*?</code>",
                    r'<span class="mtile">.*?</span></span>'):
            prose = re.sub(pat, " ", prose, flags=re.S)
        counts[key] = words(prose)
        files[key] = PAGE.format(
            title=c["title"], description=c["description"], nav=nav,
            slug=f"{key}.html", main=main)

    #  Equal budget inside the strengths and risks, measured per point.
    #
    #  Counted per column and per page this rule said an approach with more to
    #  say must say each thing in fewer words, which is not what it was written
    #  for. What it was written for is that no claim gets more room than the
    #  claim it is being weighed against, and that is a property of a point.
    def _pt(entries):
        return [len(re.sub(r"<[^>]+>", " ", e["title"] + " " + e["body"]).split())
                for e in entries]

    for key in ORDER:
        tr_a = tradeoffs["approaches"][key]
        sides = {side: _pt(tr_a[side]) for side in ("pros", "cons")}
        for side, lens in sides.items():
            if len(lens) < 3:
                raise AssertionError(
                    f"{key}: {len(lens)} {side} in the strengths and risks, "
                    f"which is too few to weigh against the other column")
        means = {side: sum(v) / len(v) for side, v in sides.items()}
        s_, h_ = means["pros"], means["cons"]
        if abs(s_ - h_) / min(s_, h_) > 0.15:
            raise AssertionError(
                f"{key}: a strength runs {s_:.0f} words and a risk {h_:.0f}, "
                f"over 15 per cent apart")

    #  And across the three pages, so one approach's points are not each given
    #  more room than another's.
    sect = {k: _pt(tradeoffs["approaches"][k]["pros"]
                   + tradeoffs["approaches"][k]["cons"]) for k in ORDER}
    per = {k: sum(v) / len(v) for k, v in sect.items()}
    slo, shi = min(per.values()), max(per.values())
    if (shi - slo) / slo > 0.10:
        raise AssertionError(
            "a point runs " + ", ".join(f"{k} {v:.0f}" for k, v in per.items())
            + f" words, a spread of {(shi - slo) / slo:.0%}, over the budget")

    lo, hi = min(counts.values()), max(counts.values())
    spread = (hi - lo) / lo
    if spread > 0.10:
        raise AssertionError(
            "equal budget failed: " +
            ", ".join(f"{k} {v}" for k, v in counts.items()) +
            f"; spread {spread:.1%} over 10 per cent. Cut the longest.")

    #  These three pages are generated, and a generated file that someone has
    #  edited by hand looks exactly like a generated file. This run destroyed a
    #  page that had been edited in place, silently, because nothing checked.
    #
    #  So the hash of every page this tool writes is recorded next to it, and
    #  before overwriting, the page on disk is compared against that record. If
    #  it does not match, someone changed the page since it was generated and
    #  the change is not in the data, so the run stops and says which file and
    #  where the edit should go instead. --force writes anyway, for the case
    #  where the hand edit has already been folded back into the data.
    os.makedirs(outdir, exist_ok=True)
    stamp_path = os.path.join(outdir, "data", "generated-pages.json")
    stamps = {}
    if os.path.isfile(stamp_path):
        stamps = json.load(open(stamp_path, encoding="utf-8"))["sha256"]

    edited = []
    for key in files:
        path = os.path.join(outdir, f"{key}.html")
        if key not in stamps or not os.path.isfile(path):
            continue
        on_disk = hashlib.sha256(
            open(path, "rb").read()).hexdigest()
        if on_disk != stamps[key]:
            edited.append(f"{key}.html")
    if edited and not force:
        raise SystemExit(
            "\n  These pages were edited after they were generated:\n"
            + "".join(f"    {e}\n" for e in edited)
            + "\n  Writing would destroy those edits. They belong in the data:\n"
              "    section 1, the strengths and risks   data/tradeoffs.json\n"
              "    the lede and the per-question prose  the CONTENT block in this file\n"
              "\n  Fold the edit in there, then run again. To overwrite anyway,\n"
              "  which is right once the edit is already in the data:\n"
              "    python tools/approach_pages.py --force\n")

    for key, html in files.items():
        with open(os.path.join(outdir, f"{key}.html"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        stamps[key] = hashlib.sha256(html.encode("utf-8")).hexdigest()
        if not quiet:
            print(f"  {key + '.html':26s} {counts[key]:>5,} words of prose")
    os.makedirs(os.path.dirname(stamp_path), exist_ok=True)
    with open(stamp_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({
            "note": ("The hash of each approach page as this tool last wrote it. "
                     "tools/approach_pages.py compares the page on disk against "
                     "this before overwriting, so a hand edit to a generated page "
                     "stops the build instead of disappearing into it."),
            "written_by": "tools/approach_pages.py",
            "sha256": stamps,
        }, fh, indent=2)
        fh.write("\n")
    if not quiet:
        print(f"\n  spread {spread:.1%}, inside the 10 per cent budget")
    return counts


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=SITE_ROOT)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--force", action="store_true",
                   help="overwrite a page that was edited after it was "
                        "generated. Right only once the edit is in the data.")
    a = p.parse_args()
    run(a.out, a.quiet, a.force)


if __name__ == "__main__":
    main()
