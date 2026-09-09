# Build log

Dated record. Each session records what it did and every decision it had to make.
Gate decisions from Pirooz go in their own headed section and are binding on
subsequent sessions.

**Maintenance note, 2026-09-09:** Historical entries have been edited to remove
unsupported traceability claims; Git history is unchanged. The 15 criteria and
open questions are maintained as analysis content and verified structurally.
The snippet manifest now contains 32 JSON-only extracts from published OSCAL
examples resolved through the repository's source lock. Historical check totals below
describe earlier versions of the harness, not current strict verification.
Four known assessment-plan schema defects remain: missing associated-activity
`subjects` in Maester and ScubaGear, and activity-title line breaks in Windows
Server 2019 and 2022. CI uses the 24 committed example files and a hash-verified
public AWS archive pinned in `tools/source-lock.json`; no personal corpus folder
or source-repository variables are required.

---

## Phase 1: the data layer

**Date:** 2026-08-12
**Scope:** scaffold, snippet manifest, extractor, verifier, schema evidence, content data files
**Result:** complete. 27 snippets resolved, 65 of 65 verification checks pass.

### What was built

```
.nojekyll  .gitignore  LICENSE (CC BY 4.0)  README.md  index.html (placeholder)
tools/manifest.yaml   27 declared snippets
tools/extract.py      RFC 6901 resolution, trim, max_prose, provenance
tools/verify.py       4 phases implemented, 8 registered for later
data/snippets/        27 files
data/schema-evidence/ 5 files
data/{six questions,criteria,views,glossary,corpus-stats,provenance}.json
```

### Extraction summary

```
27 snippets resolved (assessment-first 14, catalog-first 6, component-first 7)
```

The count asymmetry is a property of the corpora, not an editorial choice.
Assessment-first has the most snippets because it fills the most slots with
distinct constructs and because it has three separate check conventions that all
have to be shown. Slot coverage, which is what the site actually compares, is
even: every approach has a cell in every slot.

### Verification summary

```
[snippets]  re-extraction byte-identical; 9 asserted facts       PASS
[schema]    15 OSCAL 1.2.1 constraints behind the slot 2 claim   PASS
[stats]     19 cited figures recomputed from source              PASS
[data]      18 internal consistency checks                       PASS
                                                    65/65 checks passed
```

Every figure quoted in the plan recomputed exactly. Nothing had to be corrected.

### Decisions made during the build

1. **`groups/15`, confirmed.** `CloudTrail.2` is at
   `/catalog/groups/15/controls/2`. `groups/16/controls/2` is `CloudWatch.17`.
   The manifest carries a comment and `verify.py` asserts the id, so this class
   of error cannot recur silently.

2. **CISA `assessment-assets` is an object, not an array.** An earlier analysis
   recorded it as an array. Corrected in the manifest against the file.

3. **`ibm-ap-activity` points at `/assessment-plan/local-defintions`.** The key
   is misspelled in IBM's source. Reproduced verbatim with a manifest comment,
   because silently correcting a publisher's field name would misrepresent the
   artifact.

4. **Two snippets carry `max_prose`, none carries an undeclared trim.**
   `ez-stig-sc28-v270747` and several CIS and CISA steps embed long shell
   scripts in `description`. Truncation is explicit, marked ` [truncated]` in
   the rendered content, and declared in the manifest. `ez-cis-resolution-status`
   is the only entry using `trim`, eliding a 32-item `include-controls` array.

5. **`slot: 2b` was added to the six questions.** The plan's §2.4 introduced a "late
   binding available" row beneath slot 2. It behaves as its own row in the
   matrix, so `six-questions.json` carries eight slot rows: 1, 2, 2b, 3, 4, 5, 6a, 6b.

6. **Schema evidence fragments are complete, not excerpted.** All five
   definitions were small enough to embed whole, so no `fragment_note` was
   needed and no reader has to trust an elision.

7. **Figures require a reproducible derivation.** Scale claims that cannot be
   recomputed from the published OSCAL examples are not evidence for this analysis.

8. **`views.json` records the claim the site does not make.** Alongside the
   automation argument it carries a `claim_not_made` field stating that the site
   does not assert hardening guidance is never performed manually, and the CIS
   PostgreSQL counterexample (0 automated, 144 manual) sits in the evidence
   array beside the two supporting rows.

### Notes for phase 2

- `verify.py` registers `--quotes --criteria --slots --diagrams --css --links
  --budget --a11y` but does not implement them. Each later phase implements its
  own and the flag is already wired.
- `data/six-questions.json` `empty_states` defines the three renderings phase 2 must
  build as CSS tokens: `empty-by-design`, `empty-not-asserted`, `empty-absent`.
  They must survive grayscale printing.
- The slot palette needs eight distinguishable treatments, not six, because 2b
  and the 6a/6b split each need their own. Suggest six hues with 2b as a tint of
  slot 2 and 6a/6b as tints of slot 6.
- `tools/__pycache__` could not be removed by the sandbox. Delete it locally;
  `.gitignore` already excludes it.

### Open for Gate 1

Three items for review, in the order they matter:

1. **`data/six-questions.json` fill matrix.** Twenty-four cells, and they are the
   site's central claim set. The empty cells carry the most weight: check that
   each of the seven is classified into the right one of the three empty
   states, especially catalog-first slot 2 (`empty-not-asserted`, on Fritz's
   stated reason) and assessment-first slot 6a (`empty-by-design`, on the
   proponents' own claim).
2. **`data/criteria.json`.** Fifteen criteria maintained as analysis content;
   review wording and mappings as well as structural checks.
3. **Three snippets at random** against their source files, to confirm no trim
   changed a meaning.

---

## Gate 1 decisions

_(Pirooz: record corrections here. Phase 2 reads this section first.)_

**Phase 2 note:** this section was empty when phase 2 began, so phase 2 proceeded
on the phase 1 defaults. The one open item carried forward is the snippet-count
asymmetry (assessment-first 14, catalog-first 6, component-first 7). Nothing in
phase 2 depends on it. It has to be settled before phase 6, which is where the
counts become visible to a reader.

---

## Phase 2: the design system

**Date:** 2026-08-12
**Scope:** tokens, slot palette, component library, page shell, script, print, verification
**Result:** complete. 165 of 165 verification checks pass, up from 65.

### What was built

```
assets/site.css          8 sections, tokens through reduced-motion
assets/highlight.js      syntax highlighter, ~130 lines
assets/site.js           theme, data cache, snippets, strips,
                         glossary cards, tabs, matrix toggles
assets/shell.html        documented page template
assets/kitchen-sink.html every component, both themes, not published
tools/verify.py          --css and --a11y implemented
```

### The slot palette was chosen by simulation, not by eye

Three attempts, and the first two are worth recording because they failed for a
reason that constrains any future change.

1. **Okabe-Ito**, the usual colourblind-safe recommendation, was rejected on
   measurement. Under deuteranopia its orange and vermillion collapse to
   dE 19.7, and its green and reddish-purple to dE 19.0. Fine for categorical
   charts with few series; not fine for six slots that must be told apart at a
   glance on every diagram.

2. **Six hues at one fixed lightness** was rejected next, and this is the
   structural finding: under dichromacy, hue collapses onto a single axis, so
   six equal-lightness colours land on a short segment no matter which hues are
   chosen. Best achievable was dE 10.3. **Equal lightness cannot work here.**

3. **Six hues on a monotonic lightness ladder** is what shipped. Dichromats
   retain lightness perfectly, so the ladder is a second discriminating channel
   that survives when hue does not. Light theme L\* runs 30 to 55 in five-point
   steps; the dark theme lifts the whole ladder by 26 and keeps the same hue per
   slot, so slot identity is stable across themes.

Measured minimum CIE76 distance across normal vision, deuteranopia and protanopia:

| Theme | Dichromat | Normal vision |
|---|---|---|
| Light | 23.4 | 32.9 |
| Dark | 18.8 | 35.0 |

Hue per slot: 1 = 30, 2 = 290, 3 = 200, 4 = 260, 5 = 110, 6 = 160.

**Honest caveat.** The dark theme's 18.8 is the weakest number in the set. It is
above the roughly 15 threshold at which two colours read as clearly different,
but it is not comfortable. It is acceptable here only because colour is never
the sole channel: every slot rendering carries the number and a short name, and
`verify.py --a11y` asserts the lightness ladder stays monotonic so the fallback
channel cannot be removed by accident. If a later phase finds the dark strips
hard to read, the fix is to widen the ladder rather than to re-pick hues.

Sub-slots 2b, 6a and 6b inherit their parent hue deliberately, because they are
subdivisions rather than peers. They are distinguished by label and by a
double left border, never by hue.

### Prism was not vendored

The spec called for vendoring Prism locally. Prism could not be retrieved as
text through the tooling available in this session, and fetching it by other
means is out of scope. Adding a CDN reference is forbidden by the same spec.

`assets/highlight.js` replaces it: about 130 lines for syntax highlighting.
The extract manifest now contains JSON only. Everything is HTML-escaped on the
way out. For this site the trade is favourable, since there is no supply chain
to keep patched and the whole file can be audited in one sitting. It also does
one thing Prism would not have: it renders the extractor's ` [truncated]`
marker as a visible token, so a reader always knows a snippet was cut.

**If you would rather have Prism**, drop `prism.js` and `prism.css` into
`assets/`, swap the two `<script>` tags in the shell, and delete
`highlight.js`. Nothing else depends on it.

### The three empty states are carried by geometry

Per plan section 7, and this is the phase's most consequential visual decision:

| State | Rendering |
|---|---|
| Not applicable by design | hollow, plain outline |
| Deliberately not asserted | hollow plus a small open circle, top right |
| Absent, no stated position | hollow plus a fine dotted fill |

None of the three uses colour to carry its meaning, so all three survive
grayscale and print. The kitchen sink renders the five cell states twice, once
normally and once forced to grayscale, side by side, so this can be checked
rather than assumed.

### Two accessibility failures were found and fixed

`--border-strong` is not decorative here: it draws the outline of every empty
slot cell, which is meaningful information, so it needs the 3:1 non-text
minimum rather than the looser bar a hairline separator would get.

| Token | Was | Contrast | Now | Contrast |
|---|---|---|---|---|
| light `--border-strong` | `#A9B2BE` | 2.14 | `#848C99` | 3.39 |
| dark `--border-strong` | `#4A5563` | 2.39 | `#606D7C` | 3.44 |

Both were caught by `verify.py --a11y`, not by looking at the screen.

### Verification added

`--css`: no raw hex below the token block, with pure black and white permitted
inside `@media print` only; every `--slot-N` has bg, fg and border variants in
both themes; the three empty-state classes exist; empty states differ by
geometry; a print stylesheet exists; reduced motion is honoured; no `@import`
and no remote `url()`.

`--a11y`: body, muted, faint, accent and strong-border contrast in both themes;
every slot base against its page background at 3:1; every chip foreground on its
chip background at 4.5:1; and the monotonic luminance ladder.

That last check is the important one. It is what stops a future edit from
quietly removing the fallback channel the whole palette depends on.

### Decisions made during the build

1. **`--border` and `--border-strong` are two different jobs.** Hairline
   separators stay light and decorative; anything that carries meaning uses
   `--border-strong` and is held to 3:1. Documented inline in the token block.
2. **Syntax highlighting uses deliberately low-chroma colours** drawn from the
   slot foreground tokens, so code colouring never competes with the slot
   palette, which is the site's meaningful colour channel.
3. **The theme is set by an inline script before first paint**, so no page
   flashes the wrong theme. That script is the only inline JavaScript in the
   shell.
4. **The nav is nine items in a fixed order** with the three approach pages
   alphabetical by structural name. The shell carries a comment saying the
   ordering is alphabetical so a later phase does not "improve" it.
5. **`data-base` on `<html>`** carries the site root so every page uses one
   loader and relative paths keep working from `file://` as well as from Pages.
6. **Tables stack to cards below 768px** rather than scrolling horizontally, per
   the spec. The `data-label` attribute on each `td` supplies the row header in
   the stacked view, so page authors must set it.

### Notes for phase 3

- Diagrams must use only `var(--slot-N)` and the surface tokens. `verify.py
  --diagrams` will reject any literal colour in an SVG.
- The shape vocabulary is fixed in plan section 7. The three empty renderings
  now have CSS precedents in `.is-empty-*`; SVG diagrams should match them
  visually so the two systems read as one.
- `assets/diagrams/74-slot-strip.js` is specified as a component rather than a
  file. The strip already exists in `site.js` as `renderStrip`, driven by
  `data-strip`, so phase 3 should extend that rather than write a second one.
- The kitchen sink is the place to add each new diagram for review before it
  goes on a page.

### Open for Gate 2

1. **Open `assets/kitchen-sink.html` in a browser, both themes.** The palette
   appears on every diagram on every page, so a weak palette is expensive later.
2. **Print the kitchen sink in grayscale.** Look at the five-cell state row and
   its grayscale twin directly beneath it. If you cannot tell the three empty
   states apart, say so now.
3. **The dark theme dichromat number is 18.8.** Look at the three large slot
   strips in dark mode and judge whether that is comfortable. If not, the fix
   is a wider lightness ladder.
4. **The gist box.** It should invite a reader to stop and read, not look like
   a warning banner. Say if it reads wrong.
5. **Prism.** Confirm the substitution is acceptable, or supply the two files.

---

## Gate 2 decisions

_(Pirooz: record corrections here. Phase 3 reads this section first.)_

**Phase 3 note:** this section was empty when phase 3 began, so phase 3 proceeded
on the phase 2 defaults. Prism is still not vendored, and the palette shipped as
measured. Both remain open.

---

## Phase 3: the diagram library

**Date:** 2026-08-12
**Scope:** every diagram in plan section 7, the slot-strip component, the scale
figure's script, diagram verification, the grayscale contact sheet
**Result:** complete. 485 of 485 verification checks pass, up from 165.

### What was built

```
tools/diagrams.py         generates all 19 SVGs from data/, ~1,900 lines
tools/svgrender.py        a restricted SVG rasteriser, for the grayscale sheet
assets/diagrams/          19 .svg, 74-slot-strip.js, 79-scale.js, README.md
assets/site.css           approach tokens, .diagram wrapper, print rules
assets/site.js            inline diagram loader; renderStrip delegates to 74
assets/kitchen-sink.html  every diagram, both themes, plus approach swatches
tools/verify.py           --diagrams implemented; --a11y extended
build/grayscale/          38 renders and a contact sheet, git-ignored
```

Nineteen files, not eighteen: 7.5 needs a base drawing plus one overlay per
approach, which is four.

### The diagrams are generated, not hand-authored

This is the phase's largest decision and it is worth defending, because the
prompt asked for standalone files and standalone files are what shipped. The
generator is how they are produced, not what the site loads.

Three reasons, in the order they matter.

1. **Section 6 forbids hand-typing anything that came out of a corpus.** The
   join diagrams print literal identifier strings. Typed, they drift. Read from
   `data/snippets/` at generation time, they cannot. `verify.py --diagrams` then
   re-derives every quoted literal on a join diagram and fails if one is not a
   string the extractor produced.

2. **Field names get the same treatment.** Every OSCAL field name printed on a
   node passes through `F()`, which refuses a name that is not a key of the
   snippet it claims to come from. Section 7.2 asks for "real field names,
   verbatim from the files"; this is the difference between asserting that and
   checking it.

3. **Equal budget is enforced by construction, per rule 5.** Each
   three-approach family is one function over one list of three. The verifier
   then counts: one drawing per approach per family, seven slot markers in each
   six-questions diagram, two joins in each join diagram.

The cost is that an `.svg` in `assets/diagrams/` must never be hand-edited. The
README says so in the second paragraph.

### The approach palette is governed by the opposite rule to the slot palette

Phase 2 established that six slots need a monotonic lightness ladder, because
hue collapses onto one axis under dichromacy and lightness is the channel that
survives. The three approach colours needed for 7.1's overlay are the opposite
case, and getting this backwards would have been an argument in a channel no
word count can see.

**They are held at one lightness on purpose.** An approach drawn darker or
brighter than the other two is louder than the other two. Light theme L\* 47,
dark theme L\* 71, equal chroma, and `verify.py --a11y` asserts the luminance
spread stays under 0.02.

**The hues avoid a valence.** Any triad spaced 120 degrees apart puts a red, a
green and an amber on three positions in a live disagreement. The hues shipped
are 185, 265 and 340: teal, blue, mauve. No traffic light.

**Equal lightness costs dichromat separation, and that is accepted** because
colour is never the channel that says which approach a mark belongs to. Every
approach mark also carries an outline offset, a marker shape (circle, square,
triangle) and a written label. `verify.py --diagrams` asserts that any file
using an approach colour carries both a shape and a label, so the fallback
cannot be deleted by accident.

Assignment is mechanical and stated on the figures: hues in ascending order to
approaches in alphabetical order by structural name.

### Two marks were added to the vocabulary, and one was deliberately not

Section 7's vocabulary has no mark for containment, and 7.2 and 7.3 both need
one, since a step inside an activity is not a reference. A plain elbow with no
arrowhead carries it, and it is declared in the legend of every figure that uses
it.

7.7 needs an empty socket, which the vocabulary describes in words but not in
geometry. It is drawn as a hollow rounded rect with two seating tabs.

7.7 also needs "struck through". **The strike is not a dash pattern.** Dashed
already means "partly filled" in this vocabulary and must not acquire a second
sense, so an unavailable route is marked with two short bars across it, which is
the standard "open circuit" mark and is unambiguous in grayscale.

### Text size is a derived number, not a taste

Every diagram is authored on a 960 unit canvas with no text below 16 units.
`site.css` gives `.diagram > svg` a `min-width` of 720px, and 960 x 12/16 = 720,
so the smallest label is at least 12 CSS px at every width the wrapper permits;
below that the wrapper scrolls rather than shrinking. `verify.py --diagrams`
re-derives that arithmetic from the CSS and from each file rather than trusting
the comment, so changing one number without the other is a build failure.

### A rasteriser had to be written to satisfy gate 3

Gate 3 asks a person to look through `build/grayscale/` and confirm that every
distinction survives. There is no browser and no cairo in the environment this
site is built in, and no network to fetch one. `tools/svgrender.py` renders the
restricted subset that `diagrams.py` emits: rects with radii, circles, paths in
the commands actually used, text, translate and rotate, class-based styling, and
custom properties resolved from `site.css` in both themes. It refuses anything
outside that subset and must not be reused as a general renderer.

It earns its keep: dashed outlines and the dotted empty-absent fill are rendered
properly rather than approximated, because those two are exactly the
distinctions gate 3 exists to check.

`build/grayscale/index.html` is a contact sheet showing all 19 diagrams in both
themes. It is the gate.

### Four errors the checks caught

1. **A join diagram was wrong.** The first draft of `73-join-component` panel 2
   showed the assessment result's `assessment-check-id` of `check-1` resolving
   to `check-2` on the ANSIBLE component. It does not. The observation's
   `assessment-asset/component-uuid` is `...984e8`, which is the OSCAP component,
   not ANSIBLE's `...984f8`. The panel was rebuilt around the real return path,
   which turns out to be a second composite key: check id plus asset uuid,
   resolved against the assessment plan. The generator now asserts that the pair
   resolves to exactly one plan activity, so this cannot recur silently. The
   corrected panel is more useful than the wrong one, because it shows that
   component-first uses a composite key in both directions.

2. **Composed JSON paths were printed in quotes**, which made
   `"implemented-requirements[0].control-id"` look like a verbatim key. It is a
   path this site composed. Paths are now unquoted and only true literals are
   quoted, which is also what makes the literal check meaningful.

3. **An invented ellipsis.** A STIG activity title was printed as
   `"V-259312: ..."`. The extractor marks truncation explicitly with
   `[truncated]` and nothing else may invent its own. The line now prints the
   `stig-group-id` prop, which is the literal `V-259312`.

4. **`--slot-6a-bg` and friends looked undefined.** They are declared under the
   combined selector `:root, [data-theme="dark"]`, which the first token parser
   did not match. A real parsing bug in the tool, not in the stylesheet, but
   worth recording because any future tool that reads `site.css` will hit it.

### Decisions made during the build

1. **Diagrams are injected inline, not used as `<img src>`.** An external SVG in
   an `<img>` is an isolated document: it cannot see the page's custom
   properties, so it would not theme, and its `<title>` and `<desc>` would never
   reach the accessibility tree. `site.js` fetches and injects.
2. **Every style rule is scoped to its root id.** An inlined SVG's `<style>` is
   not scoped by the browser, so an unscoped `.box` rule would restyle every
   other diagram on the page. The verifier rejects any rule that is not scoped,
   and asserts root ids are unique across the library.
3. **`74-slot-strip.js` is the one implementation** and `site.js` delegates to
   it, per the phase 2 note. `site.js` keeps a small fallback for the case where
   the file is not loaded, so a page cannot silently lose its strips.
4. **The scale figure works without scripting.** All three destinations and all
   three resulting counts are printed in the SVG. The script moves the bar
   between three sockets and updates the readout, reading both the socket
   positions and the counts out of the SVG so the two cannot disagree.
5. **Footprint is defined once and stated identically on all three variants:**
   the OSCAL models in which an approach's shipped content exists. It is an
   inventory of where content lives, not a measure of completeness, and the
   caption says so on every variant. Counts carry their denominators on all
   three, per rule 8.
6. **7.5's overlays are driven by `serves_reader_first` in `six-questions.json`**, one
   reader per approach, so which path each approach shortens is a data
   statement rather than a judgement made at drawing time.
7. **7.7's route availability is derived where it can be.** The late-binding row
   is read from the fill matrix's slot 2b. Inline and by-pointer are marked
   available to all three, which is plan section 2.2.2's own third column, and
   the constant carries that citation in a comment.
8. **The layer map's band names moved inside the bands.** A left gutter wide
   enough for the word IMPLEMENTATION would have taken a sixth of the drawing
   away from the models.
9. **Legend lines are capped at 46 characters and wrapped by `LI()`**, and
   `legend()` raises on anything longer. Legends are laid out column-major with
   the split nudged so a wrapped entry is never cut across the column boundary.

### Verification added

`--diagrams`, 312 checks:

- viewBox present, no fixed width or height, `<title>` then `<desc>` first, desc
  at least 40 words, `aria-labelledby` wired to both, root id unique
- every style rule scoped to the root id
- no literal hex or `rgb()` in a style block or in a fill or stroke attribute
- every `var(--token)` used resolves in both themes
- smallest font size against the CSS min-width, re-derived, at least 12px
- five layer maps and four three-readers drawings share byte-identical geometry,
  modulo the root id
- one drawing per approach in each of the four families
- each six-questions diagram shows all seven slots exactly once, and each slot is
  drawn in the state `six-questions.json` claims for it
- each join diagram shows exactly two joins
- every quoted literal on a join diagram is a string the extractor produced,
  including values nested inside JSON held in a prop, with at least one uuid
  traced per diagram
- any file using an approach colour carries a marker shape and a written label
- 38 grayscale renders plus a contact sheet

`--a11y` gained the approach tokens: 3:1 against the page in both themes, and an
assertion that the three are equally light.

```
[snippets]  12    [schema] 15    [stats] 20    [data] 18
[css]       62    [a11y]   46    [diagrams] 312
                                              485/485 checks passed
```

### Notes for phase 4

- Use `<div class="diagram" data-diagram="NAME"></div>` inside a `<figure>`.
  The `figcaption` is the page's job; the SVG carries only its legend.
- 7.5 requires the caption to say it is an organizing structure and not a
  thesis. The words are on the figure already; do not drop them from the page.
- 7.8's three destination labels are fixed by the plan and must be used verbatim
  in the buttons. `79-scale.js` documents the exact markup.
- Nothing in `assets/diagrams/` may be hand-edited. Change `tools/diagrams.py`
  and re-run.

### Open for Gate 3

1. **The join diagrams, literal by literal.** They are the figures a reader will
   trust most and screenshot. The verifier proves each literal came out of
   `data/snippets/`; it cannot prove the snippet is the right fragment to show.
   `73-join-component` panel 2 is the one to read twice, since it was wrong once.
2. **Grayscale.** Open `build/grayscale/index.html`. The five cell states and
   the three empty states are the distinctions to check, and the struck routes
   on 7.7.
3. **7.7's framing, which the build guide asks about directly.** It is drawn so
   that the struck routes sit under a schema constraint printed in full, and the
   legend and the desc both say the gap is in OSCAL rather than in any approach.
   Read it cold and say whether it lands as "OSCAL has a gap" or as "AWS wins".
4. **7.8, three views.** All three nodes are the same size, at the same x,
   evenly spaced, in the order `views.json` gives, which that file records as
   layer order and not a ranking. Your own view is the third. Check it twice.
5. **Visual density across the three six-questions diagrams.** They share one column
   grid, sized to the widest field name in any of the three, so none can look
   tidier by having been drawn first. Confirm that reads as intended.
6. **The approach palette.** Teal, blue and mauve, equally light. If any of the
   three reads as favoured or disfavoured, say so; the fix is a hue rotation and
   costs nothing, because hue carries no meaning here.
7. **Snippet-count asymmetry is still open from Gate 1** and is now one phase
   closer to phase 6, where it becomes visible to a reader.

---

## Gate 3 decisions

_(Pirooz: record corrections here. Phase 4 reads this section first.)_

**Phase 4 note:** this section was empty when phase 4 began, so phase 4 proceeded
on the phase 3 defaults. The 7.7 framing question and the approach palette both
remain open, and neither blocked this phase.

---

## Phase 4: the six-questions page and the glossary

**Date:** 2026-08-12
**Scope:** `six-questions.html` in nine parts per plan section 4.3, `glossary.html` per
section 4.4, the runtime components both need, `verify.py --quotes`, and a page
test harness
**Result:** complete. 539 of 539 verification checks pass, up from 485, plus 384
page checks.

### What was built

```
six-questions.html            nine parts, 67 snippets, 9 schema
                        fragments, 8 tables, 3 figures
glossary.html           33 terms, filterable, one anchor each
assets/site.js          twelve data components, plus a schema-evidence renderer
assets/site.css         .state-swatch, .slot-fill, .worked, .filter-bar,
                        .glossary, .toc
tools/pagecheck.js      a DOM harness that runs a page and inspects the result
tools/verify.py         --quotes and --pages implemented
data/glossary.json      one term added
```

### The pages are markup plus data, not generated HTML

Phase 3 generated its SVGs from `data/` with a Python builder. These pages
deliberately do not work that way, and the difference is worth recording because
the two look inconsistent until you know why.

Plan section 8 says content loads from `data/` so that regeneration never
touches markup. A diagram is a drawing: it has to be a file, and generating it
is the only way to keep its literals honest. A page is a document: if the fill
matrix were baked into HTML, correcting one cell in `six-questions.json` would leave
the page stale until someone remembered to rebuild it. So the repeating,
data-bearing parts of a page render at load time from `data/`, exactly as
snippets already did.

Twelve components were added for this: the three views, the automation evidence,
the working definition, the binding times, the cost of an empty tie, one slot's
fill across the three approaches, the fill matrix, a criterion, a slot's
question, a recomputed figure, the matrix finding, and the glossary.

### Equal budget is a property of the loop

Editorial rule 5 asks for equal budget enforced by construction. On this page it
is: `renderSlotFill` iterates one hard-coded alphabetical list of three, so
every slot section emits one item per approach with the same fields in the same
order, and the state comes from `six-questions.json` rather than from prose. There is
no place to write more about one approach than another without editing a loop.

`tools/pagecheck.js` then asserts it after rendering: every slot-fill block has
exactly three items, and their headings are Assessment-first, Catalog-first,
Component-first in that order. That check would fail before a reader noticed.

### A DOM harness, because a runtime-rendered page cannot be checked by reading it

The cost of the choice above is that a mistyped hook, a dangling snippet id or a
renderer that silently produced nothing is invisible to anything that only reads
the HTML. There is no browser and no network in this environment, and `jsdom`
cannot be installed.

`tools/pagecheck.js` supplies a DOM small enough to run `site.js` and honest
about being a test harness: an HTML parser, a node tree, the selector subset
`site.js` actually uses, a `fetch` that reads `data/` off disk, and a
`DOMParser` for the inline SVG loader. It loads a page, runs `boot()`, waits for
the promises to settle, and asserts on the result. 384 checks.

It found five real defects that no amount of reading would have caught. It also
needed two fidelity fixes of its own before its signal was trustworthy, and both
are recorded below because a harness that lies is worse than no harness.

### Five defects the harness caught

1. **Schema fragments were being rendered as corpus snippets.**
   `six-questions.json` cites `observation`, `finding`, `finding-target`,
   `mapping-item` and `mapping-resource-reference` under fields that look like
   snippet references, but those five live in `data/schema-evidence/` with a
   different shape and a different provenance. `renderSnippet` fetched
   `snippets/observation.json`, got a 404, and printed its own error message
   into the page. Fixed with a separate `renderSchema`, because plan section 6
   requires schema evidence to be labelled as not coming from any of the three
   corpora. It now renders with that label, the schema id, the OSCAL version,
   the fetch date and the constraint list.

2. **The fill matrix hit the same bug**, from the slot 2b cells. The set of
   schema-evidence ids is now derived from `six-questions.json` itself rather than
   listed in JavaScript, so a sixth fragment needs no code change.

3. **Two dangling glossary cross-references.** `assessment platform` and
   `assessment asset` both point at `actor`, which was not a term. The right fix
   was to add it rather than to drop the references: `actor` is the site's own
   name for slot 5, and the reason it is the site's own name rather than an
   OSCAL one is exactly the thing evidence register item 8 records as
   unestablished. Added with status not-established and the four constructs in
   use as its other usages.

4. **Heading levels skipped.** The three views rendered as `h4` directly under
   an `h2`, and the slot 6 fills rendered as `h4` under the `h4` that introduces
   6a. Both are invisible in a visual review and both break heading navigation.
   Fixed, and `pagecheck.js` now asserts that heading levels never skip.

5. **`validation component` needs its senses kept distinct.** A proposed
   construct and a shipped assembly are not interchangeable. The glossary must
   identify which meaning the published OSCAL examples actually demonstrate.

### Two fidelity fixes to the harness itself

`dataset.foo = x` writes the attribute in a browser. The first harness stored it
separately, so an element a renderer had just built was invisible to the
`[data-quote]` selector the same renderers use to find their own work, and eleven
checks failed for a reason that did not exist. `dataset` is now a proxy that
writes through.

The inline diagram loader uses `DOMParser`, which the harness did not have, so
every diagram appeared to fail to load. Added.

### Decisions made during the build

1. **The section 2 diagnosis is one paragraph of 109 words**, and it is written
   as an observation with its evidence in front of it rather than as a claim
   being defended. The paragraph distinguishes the views recorded in
   `views.json`; the testable consequence is put as an editorial open question rather
   than as a conclusion. This is the most opinion-adjacent content on the site
   and it is the thing to read twice at the gate.
2. **The automation claim is the weaker one everywhere.** The page states
   "predominantly and increasingly automated", prints the CIS PostgreSQL row of
   144 manual and 0 automated in the same table as the two supporting rows, and
   renders `claim_not_made` from `views.json` under the heading "The claim the
   site does not make". Both figures render from `corpus-stats.json`, so they
   cannot drift from what `--stats` recomputes.
3. **The mapping-collection finding is in the corrected framing only.** The
   three surviving bullets are the whole of what the page claims, and they sit
   under a callout that says plainly that this is not an independent argument
   for any option and that an earlier draft wrongly presented it as one.
   `pagecheck.js` asserts both sentences are present.
4. **The worked side-by-side in slot 6 has an empty left column**, because no
   system security plan exists in any of the three corpora. That is the finding
   rather than an accident of extraction, and the column says so. The right
   column is the one assessment result that does exist, with its publisher's own
   proposed-schema status stated.
5. **Slots 2 and 6 appear twice, and the second time adds only new material.**
   Part 4 gives all six slots the identical four-part structure including the
   per-approach fill. Parts 5 and 6 add the binding times, the cost table, the
   mapping finding, the 6a/6b table and the worked example. Nothing is repeated.
6. **The glossary sorts `rule` first and leaves the rest in file order**, which
   groups the contested terms before the model names. The filter matches the
   term, the usage, and the name of whoever uses it, so searching for a person
   finds the words they use.
7. **`--quotes` also checks two things that are not quotations**: that no page
   contains a `<pre>`, which would mean a hand-typed snippet, and that no page
   contains a long dash. Both are standing rules that had never been machine
   checked, and both belong to the same family as the quotation rule: nothing on
   a page that ought to have come from `data/`.

### Verification added

The page-hygiene checks cover hand-typed code blocks and long dashes. The
current `--quotes` policy prohibits quotation and attribution hooks on pages.

`--pages` shells out to `tools/pagecheck.js` and reports its result.

```
[snippets]  12    [schema]   15    [stats]  20    [data]  18
[css]       62    [a11y]     46    [diagrams] 312
[pages]     1  (384 page checks behind it)
                                              539/539 checks passed
```

### Notes for phase 5 onward

- **Anchors later pages must provide.** `six-questions.html` and `glossary.html`
  already link to them: `index.html#other-options`,
  `questions.html#requirement-level`, `questions.html#mapping-item`,
  `questions.html#evidence-8`, `questions.html#contribute`. Nothing checks
  cross-page anchors yet; `--links` is still registered and unimplemented.
- Use the components rather than writing markup: `data-slot-fill`,
  `data-matrix`, `data-views`, `data-binding-times`, `data-tie-cost`,
  `data-criterion`, `data-slot-question`, `data-stat`, `data-glossary`,
  `data-working-definition`, `data-automation`, `data-six-questions-finding`.
  `pagecheck.js` fails on a hook that `boot()` does not wire.
- Corpus figures go in with `<span data-stat="key">`, never typed. Schema
  fragments go in with `data-schema`, never `data-snippet`.
- The approach pages must state which reading of a rule each structure uses,
  distinguishing analysis from the evidence in published OSCAL examples.
- Every first use of a contested term should be a
  `<button class="dfn" data-term="...">`, which pulls the card from the same
  `glossary.json` the glossary page renders.

### Open for Gate 4

1. **The section 2 diagnosis, read cold.** One paragraph, 109 words.
   Does it read as an observation or as an
   argument? If the latter, the fallback in the plan is to state the three views
   without the diagnosis and let readers draw it.
2. **The mapping-collection section.** It now says three things and explicitly
   disclaims a fourth. Read the callout and the three bullets together and say
   whether the disclaimer is doing enough work.
3. **The empty left column in the slot 6 worked example.** It is the same
   absence for all three approaches and the page says so twice. Confirm it does
   not read as a criticism of the one approach whose assessment result is shown
   opposite.
4. **The new glossary term `actor`.** Status, wording, and whether the four
   other usages are the right four.
5. **`data/glossary.json` generally**, since it now renders in full for the
   first time. Thirty-three terms, and the statuses are load-bearing: settled,
   contested and not-established mean three different things and the page says
   which.
6. **Gate 3 items are still open**, in particular the 7.7 framing question, and
   that figure now has a page built around it.

---

## Gate 4 decisions

_(Pirooz: record corrections here. Phase 5 reads this section first.)_

**Phase 5 note:** this section was empty when phase 5 began, so phase 5 proceeded
on the phase 4 defaults. The section 2 diagnosis wording and the new `actor`
glossary term both shipped as written, and both remain open.

---

## Phase 5: the primer

**Date:** 2026-08-12
**Scope:** `primer.html` per plan section 4.2, the four components it needs, and
the reading-level checks its success test implies
**Result:** complete. 545 of 545 verification checks pass, up from 539, behind
them 465 page checks, up from 384.

### What was built

```
primer.html             eight sections, 3 snippets, 2 tables,
                        3 figures, 1,911 words of prose
assets/site.js          renderModels, renderReaders, renderCitedFigures,
                        renderSc28; term cards rebuilt on delegation
assets/site.css         .models__layer, .models__list
tools/pagecheck.js      checkPrimer, and a prose measurement
```

### The page has a stated success test, so parts of it are machine checked

The brief gives this page a test the others do not have: someone with no
background reads it and can restate the problem correctly. Most of that is a
human judgement. Some of it is not, and the parts that are not are now assertions
so that the human review can spend itself on the part it cannot delegate.

- The tier 1 gist is 70 to 95 words, and **contains no OSCAL vocabulary at all**.
  A blocklist of fifteen terms is checked against it. A reader who has never
  opened one of these files has to get through the first paragraph.
- No sentence in the gist runs past 32 words.
- "What OSCAL is" is five sentences or fewer, mentions seven models, three
  layers and an exchange format, and says it is not a database.
- Across the page's own prose, the average sentence stays under 25 words and no
  sentence runs past 40.

The prose measurement excludes navigation, the table of contents, tables, inline
SVG and snippet bodies. Tables hold labels rather than sentences. Measured
that way the primer is 1,911 words, average sentence 17.7, reading grade 9.3.
The six-questions page is 15.6 and 10.2, the glossary 16.3 and 11.3.

Two of those checks failed on the first run and both were right to. The gist had
a 35-word sentence and the slot 2 cross-reference had a 57-word one. Both were
split.

### Content renders from data rather than being written

Same principle as phase 4, applied to places on this page where the
primer would otherwise restate something that already exists.

1. **The seven models.** Each one line of purpose is the glossary's own text,
   with the layer prefix stripped because the heading above already says it.
   `pagecheck.js` asserts each definition equals the glossary's, and that each
   model sits under the layer its own glossary entry names. The primer and the
   glossary cannot drift apart, in either direction.
2. **The three readers.** Same, from the `publisher`, `implementer` and
   `assessor` entries.
3. **The running example.** The three-row SC-28 table reads every identifier out
   of the snippet that row names. `V-270747` and its `sc-28`, `sc-28.1`,
   `sc-28.3`; `CloudTrail.2` and its absence of any framework control;
   `cos_encryption_hyperprotect_key_configured` and its `sc-28`. Nothing in the
   table is typed. `pagecheck.js` then asserts that every identifier printed
   really occurs in the snippet, and that exactly two of the three reach
   `sc-28`, which is the claim the section makes in prose.

### A real bug in the term cards, found by building this page

The primer is the first page whose `.dfn` term buttons are created by a renderer
rather than written into the markup. `initGlossary` bound a listener per button
at boot, so it wired only the buttons already present and silently missed every
one a renderer produced afterwards. Every model name and every reader name on
this page would have had a dead hover card.

Rebuilt on event delegation at the document level, so a card works whenever its
button appears. This also fixes the same latent problem on the six-questions page,
where the matrix and the slot fills create content after boot.

### Decisions made during the build

1. **The gist says "regulation", never "control".** The word control is OSCAL
   vocabulary and the gist has none. It appears for the first time in section 4,
   with a term card.
2. **Section 6 states the three-views disagreement and stops.** Two sentences,
   the diagram, and a link. The argument itself is on the six-questions page and is
   not repeated here, per the brief. The primer's job is to tell a reader the
   disagreement exists, because it changes how they read everything after it.
3. **The AWS row of the running example is stated as a property of the shipped
   content**, at the time it was published, with a link to slot 2 for the
   distinction between an empty tie and a deficiency. The callout says plainly
   that a rendering which scored it as a deficiency would be making an argument.
4. **"77 groups, one group per service"** rather than the plan's "77 services".
   `corpus-stats.json` counts groups, and the AWS catalog groups are per
   service. The phrasing keeps the number honest to what is recomputed while
   saying what it means.
5. **The nine-page map is checked against the nav.** `pagecheck.js` asserts the
   map's links and the navigation's links are the same list in the same order,
   so the two cannot disagree about what the site contains.
6. **A harness bug was fixed while adding these checks.** The selector engine
   parsed `h3` as the tag `h`, because its tag pattern stopped at the digit.
   Every `querySelectorAll("h3")` had been returning nothing.

### Verification added

`--pages` now runs 465
checks, of which 82 are the primer's.

```
[snippets]  12    [schema]   15    [stats]  20    [data]  18
[css]       62    [a11y]     46    [diagrams] 312
[pages]     1  (465 page checks behind it)
                                              545/545 checks passed
```

### Notes for phase 6

- Four pages exist: index (still the phase 1 placeholder), primer, six questions,
  glossary. Five remain.
- The three approach pages are the phase the plan says must happen in one
  sitting. `data-slot-fill` renders one slot across all three approaches, which
  is the wrong shape for a single-approach page. A per-approach equivalent will
  be needed, and it should be one function over the eight slot rows so that the
  three pages cannot diverge in structure.
- Cross-page anchors are still unchecked. The list of anchors later pages owe is
  in the phase 4 notes, and `questions.html#evidence-8` now has a second caller.

### Open for Gate 5

The build guide's gate here is a cold read, and it is the one gate a machine
cannot stand in for.

1. **Give the primer to someone with no compliance background and no OSCAL.**
   Ask them to say back what the argument is about. If they can name the gap
   between the regulation and the configuration, and say that three groups filled
   it differently, the page has done its work.
2. **The gist specifically.** Ninety words, no OSCAL vocabulary, and it is the
   only thing a hurried reader will read.
3. **The three reasons in "Why this is hard".** They are the load-bearing
   explanation for why this is not a matter of taste. Check that the third one,
   about altitude, lands, because it is the least concrete of the three.
4. **The running example table.** Every identifier in it is read from a file,
   but whether SC-28 is the right example to carry the whole site is a judgement
   the plan flagged for you at section 12.5, including whether to raise the AWS
   row with Fritz before publication rather than after.

---

## Gate 5 decisions

**Recorded by Pirooz, 2026-08-12. Binding on every later session.**

### 1. The register changes, and the plan's audience with it

The prose was too essayistic. The model to write in is the OSCAL Foundation
focus group discussion thread, specifically
[Component-Definition-Focus-Group discussion 2](https://github.com/OSCAL-Foundation/Component-Definition-Focus-Group/discussions/2).

**This supersedes the plan on audience.** Plan section 1.3 gives the audience as
"anyone, including someone who has never opened an OSCAL file", and verification
step 8 is a cold-read comprehension test by a reader with no OSCAL background.
Both are withdrawn.

- **Audience** is the working group and OSCAL-literate readers. Assume fluency
  with the seven models, the layer names, and ordinary field vocabulary.
- **Do not define OSCAL.** The primer's "What OSCAL is" section is deleted and
  must not come back. Neither must one-line definitions of the seven models.
- **Verification step 8 is replaced.** Instead of a cold read by a non-OSCAL
  reader, a practitioner who knows OSCAL but has not followed this argument
  reads the site and restates the disagreement.
- **Everything else in the plan stands**, including all thirteen editorial rules,
   the six-slot spine, the fifteen criteria, and equal budget by
  construction.

### 2. The house style, as it now stands

Written down because four pages remain and they have to match the three that
exist.

| Do | Do not |
|---|---|
| Number every section, and say what is in it: `### 2.2 Versioning: benchmarks change when the product changes` | Aphoristic headings: "Three. They sit at an altitude nothing was designed for" |
| Bold lead-in labels: `**Volume.**`, `**Claim not made.**` | Spelled-out ordinals as headings: "One.", "Two." |
| Headings a newcomer can parse: "OSCAL has no field for shall, should or may" | Headings that name an abstraction the reader has not met: "Where the gap falls", "The crux", "The placement problem" |
| `<code>` for every field, model and enum name | `<span class="mono">` for identifiers, which is now reserved for file paths |
| Declarative sentences that state a fact and stop | Rhetorical closers: "That is the problem.", "and that is the finding" |
| Tables and schema fragments carrying the argument | Prose carrying what a table would carry better |
| Name the constraint, then its consequence | Building to a consequence across a paragraph |

Retained from earlier phases and unaffected: no long dash anywhere; every
snippet from `data/snippets/`;
schema fragments labelled separately from corpus content; no recommendation.

The boxed summary at the top of each page **stays**, and is now written in OSCAL
terms rather than avoiding them. It aids scanning, which is the reason it
existed. The plan's tier 1 rule about plain language does not survive the
audience change.

---

## Phase 5b: the tone pass

**Date:** 2026-08-12
**Scope:** rewrite `primer.html`, `six-questions.html` and `glossary.html` in the Gate
5 register; retarget the checks; close the term-card bug
**Result:** complete. 549 of 549 verification checks pass, behind them 455 page
checks.

### What changed

`primer.html` was rebuilt rather than edited. The old section 2, "What OSCAL is"
in five sentences, is gone, and so are the seven one-line model purposes. The
page now opens on where the gap falls, which for an OSCAL-literate reader is the
first thing worth saying. Six numbered sections replace the eight it had. Prose
fell from 1,911 words to 1,588 and average sentence length from 17.7 to 15.0.

`six-questions.html` kept its structure and its evidence order. Every heading is
numbered, the aphoristic ones are gone, 56 `<span class="mono">` identifiers
became `<code>`, and the essayistic cadence was removed sentence by sentence.
The section 1 diagnosis keeps its evidence-first construction, which was the
part that was working, and loses the build-up: it now opens on
"Two facts combine into a mechanism" and states the mechanism.

`glossary.html` gained numbered sections. The three status definitions were
pulled out of a paragraph into three bold lead-in lines, which is what they
should have been.

`assets/site.js` renderer prose was tightened in the same direction, since the
components emit sentences onto every page that uses them.

### The register is now machine checked

Three new assertions, on every page:

- every section heading is numbered, `1.` at h2 and `1.1` at h3
- no heading is a spelled-out ordinal, which is the exact pattern that was
  called out
- headings inside a rendered component are exempt, because they name a term, an
  approach or a reader rather than a section

That last exemption is the interesting one. It needed a rule for what counts as
a section heading, which is now: any h2 or h3 that is not inside `.card`,
`.glossary__item`, `.slot-fill`, `.worked`, `.models__layer`, or one of the six
render hooks.

The prose measurement also learned that a heading ends a sentence. Without a
full stop, a heading ran into the paragraph after it and the check blamed the
wrong text for a long sentence.

### The term-card bug is closed

Reported at the end of phase 5, fixed in the same session by rebuilding
`initGlossary` on event delegation. It is now covered by a regression test in
`tools/pagecheck.js` that clicks one term button written into the markup and one
created by a renderer, and asserts the card opened and carries the right term.

**The test was verified against the bug.** Reverting the delegation fix makes
three checks fail: the renderer-made card on the primer, and the markup card on
both the primer and the six-questions page. Restoring it makes them pass. A test that
has never been seen to fail is not evidence of anything, so it was made to fail
on purpose once.

Two supporting changes to the harness were needed and are worth recording,
because both were places where the harness was quietly lying:

- `document.addEventListener` was a stub. Any code binding by delegation was
  therefore untestable, and appeared to work.
- events did not bubble to the document. Now they do.

### Decisions made during the build

1. **`renderModels` is kept although no page now calls it.** It renders the
   seven models with purposes from the glossary, which the index page may want
   as orientation. If index does not use it, delete it there rather than
   carrying it further.
2. **`<code>` replaces `<span class="mono">` for identifiers**, matching the
   backtick convention of the discussion threads. `mono` is now reserved for
   file paths and document names, where it reads as a path rather than as a
   field.
3. **The gist component keeps its class name.** Its label changed from "In plain
   language" to "Summary" on all three pages. Renaming the CSS class would have
   touched the kitchen sink and the shell for no reader benefit.
4. **The primer's reading-level checks stay**, at average sentence under 25 and
   nothing past 40. The register is denser but those bounds are about
   comprehensibility rather than simplicity, and all three pages are inside them
   with room.

### Heading pass, same session

The first tone pass fixed the register and left the headings abstract. "The
placement problem", "Where the gap falls", "Why the placement is contested" and
"The crux" all name an abstraction the reader has not been introduced to yet.
Numbering a heading does not make it informative.

Every section heading on the three pages now states what is in the section, in
terms someone meeting the problem for the first time can parse. The pattern that
works, and that the rest of the site should follow, is either a plain statement
of fact or a label followed by one:

- `1. No OSCAL model was designed for this content`
- `2.2 Versioning: benchmarks change when the product changes`
- `1.2 OSCAL has no field for shall, should or may`
- `3.4 Subject: what exactly is tested`
- `4.2 What you lose by leaving the tie empty`

The slot subsections in section 3 of the six-questions page gained their plain
question after the slot name, so the heading alone now says what the slot is
for. The primer's h1 changed from "The placement problem" to "Where hardening
guidance goes in OSCAL", and its lede states the decision rather than naming it.

This is a judgement a check cannot make. The numbering and the ordinal ban are
enforced; whether a heading is informative is a reading.

### Open for Gate 6

1. **Read the primer first.** It changed most, and it is the page the audience
   decision affects most directly. If it still reads as an explainer rather than
   as a reference, say so.
2. **Section 1 of the six-questions page.** The diagnosis paragraph was the most
   opinion-adjacent prose on the site before this pass and still is. It now
   states the mechanism up front rather than arriving at it.
3. **Whether the plan file itself should be amended.** This log records the
   audience change and is binding on later sessions, which is the protocol the
   standing rules describe. The plan document still says "anyone, including
   someone who has never opened an OSCAL file". Say if you want the plan edited
   to match, since it is your document.
4. **The three approach pages are next**, and the plan requires them in one
   sitting. They will be built in this register.

---

## Gate 6 decisions

_(Pirooz: record corrections here. Phase 7 reads this section first.)_

**Phase 6 note:** this section was empty when phase 6 began, so phase 6 proceeded
on the Gate 5 register. The one item carried forward is whether the plan document
itself should be amended to match the audience decision recorded at Gate 5.

---

## Gate 7 decisions

**Recorded by Pirooz, 2026-08-12. Binding on every later session.**

### The site carries no quotations and names nobody

Three decisions, taken together:

1. **No quotations anywhere.** Every blockquote comes off every page. The
   In their words section is deleted from the approach template.
2. **No personal names and no proponent organizations.** Structural names and
   option letters identify the approaches consistently across the analysis.
3. **The three empty slot states survive.** Where a state depends on a reason
   rather than published content, the site identifies that reason as analysis
   rather than presenting it as a source-backed fact.

**This supersedes plan editorial rules 1, 3, 10 and 11 in part.** Rule 1's
"option letter and organization second" loses the organization. Rule 3's "a
proponent's own words" is withdrawn, leaving the other half: every
characterization of published content traces to a JSON pointer into a shipped
OSCAL file. Editorial interpretation is not source evidence. Rule 11's settled
items keep their marking and lose their attribution. **The current criteria
policy is the maintenance note above: 15 criteria maintained as analysis content,
with structural verification rather than source-wording checks.**

---

## Phase 6b: removing quotations and attribution

**Date:** 2026-08-12
**Scope:** every page, the shared renderers, the approach template, and the
checks
**Result:** complete. 536 of 536 verification checks pass, behind them 546 page
checks. Zero blockquotes site-wide, zero personal names, zero proponent
organizations outside file paths.

### What came out

| Page | Quotations removed |
|---|---|
| `six-questions.html` | 8 |
| `assessment-first.html` | 7 |
| `catalog-first.html` | 9 |
| `component-first.html` | 9 |
| `primer.html` | 2 |
| **Total** | **35** |

The approach template dropped from nine sections to eight. In their words is
gone, and every other section moved up one. Word counts after the cut:
assessment-first 2,066, catalog-first 1,977, component-first 2,097, spread
6.1 per cent.

Three boxes in section 7 had to be re-cut. Removing names shortened the
questions-raised box on all three pages, which pushed the pair out of the
15 per cent tolerance, so the case box was trimmed to match rather than the
questions box padded back out.

### Technical distinctions retained

- **Catalog-first control links.** No mapping document is published in the
   corpus; an available mechanism and a shipped artifact are different claims.
- **Rule and check are separate.** One rule can be associated with check
   identifiers in Ansible, Terraform, OPA and OpenSCAP; identity and execution
   convention need not be the same thing.
- **Criterion 3.** Requirement level has no dedicated core OSCAL field.
   Namespaced properties in published examples do not make it a core field.
- **The 6a and 6b distinction.** A system security plan records an implementation
   claim; assessment results record observations and findings. Neither alone
   demonstrates a complete lifecycle.

### The rule is enforced, not remembered

Three new checks, and they are the reason this is safe to leave to later
sessions:

- **`verify.py --quotes` inverted.** The flag keeps its name because the subject
  is the same; the answer changed. No page may carry a blockquote or a
   `data-quote` reference, and no page may present personal attribution.
- **`pagecheck.js` checks the rendered prose**, which is where a name could
  arrive from a data file rather than from markup. It also checks proponent
  organizations, which `verify.py` cannot: a snippet's source path legitimately
  begins with `AWS/`, `IBM/` or `Easy Dynamics/`, and stripping that would break
  the provenance the whole site rests on. The rendered check excludes elements
  marked as paths and checks the prose only.
- **`approach_pages.py` refuses to write** a page containing a blockquote, a
  personal name or a proponent organization.

The path exemption needed one code change: the source column of the SC-28 table
was plain prose to the checker, so it now carries a `path` class. Marking what
is provenance is what makes it possible to be strict about everything else.

### Decisions made during the build

1. **Product and standard names stay.** AWS Config, Security Hub, DISA STIG, CIS
   Benchmark, CISA SCuBA and OpenSCAP are the names of things in the content,
   not attributions of who proposed an approach. Removing them would make the
   site unable to say what it is describing. The line drawn is: no person, no
   proponent organization, no who-proposed-this; product and standard names and
   file paths stay.
2. **The three views table lost its On the record column.** The three readings
   keep their definition, their implied layer and their implied model, which is
   what makes them comparable. Who holds each one is no longer shown.
3. **A criterion no longer says who raised it.** The criteria are now maintained
   as analysis content; editorial review must assess their wording and fairness.
4. **Unreproducible scale claims are not evidence.** Figures need a derivation
   from published OSCAL examples before they can support the comparison.
5. **The glossary's who-uses-this fields were rewritten** to name the approach
   rather than the person or organization, for example "Catalog-first, Option A"
   in place of a person and an employer. The contested terms still show every
   sense in use and where each comes from.

### Open for Gate 8

1. **Read a slot with an empty state.** Slot 2 on the catalog-first page is the
   one to read. Without the publisher's own words, does the reason still land as
   a stated decision rather than as the site's inference?
2. **Criterion wording.** Check that each criterion fairly addresses all three
   approaches without implying a preferred answer.
3. **The case boxes in section 7.** They were re-cut to hold the budget after
   the names came out. Confirm none of the three lost something it needed.
4. **Two gates still open:** whether the plan document should be amended to
   match the Gate 5 audience decision, and the Gate 6 items on proponent review.

---

## Phase 6: the three approach pages

**Date:** 2026-08-12
**Scope:** `assessment-first.html`, `catalog-first.html`, `component-first.html`,
built in one sitting from one template
**Result:** complete. 660 of 660 verification checks pass, behind them 656 page
checks. Word counts are within 6.3 per cent.

### The pages are generated, and that is the whole point

Plan section 3 rule 5 requires equal budget "enforced by construction, not by
judgement". Three hand-written pages cannot deliver that. Whichever is written
first sets the shape, the second is written against it, and the third is written
against both. The drift is invisible to the author and obvious to a proponent
reading only their own page.

`tools/approach_pages.py` emits all three from one function. The template fixes
the nine sections, their order, their heading text, and every count that
repeats. A page supplies only what has to differ: the gist, the per-slot prose,
the strongest case, the hardest questions, and the specifics that go into the
three status sentences.

The generator refuses to write a page that breaks the budget. Assertions
run before any file is opened:

- the gist is 75 to 85 words
- the two boxes in section 8 are within 15 per cent of each other
- the three page totals are within 10 per cent
- no comparative language appears in the authored prose

Budget failures during the build were fixed by cutting the
longer text, never by padding the shorter.

### Final word counts, prose only

Snippets render from `data/` at load time, so the static markup
holds exactly the authored prose. That is what is counted.

| Page | Words | Against the mean |
|---|---|---|
| `assessment-first.html` | 2,117 | +2.3% |
| `catalog-first.html` | 2,000 | -3.3% |
| `component-first.html` | 2,126 | +2.8% |

Spread between the longest and the shortest is **6.3 per cent**, inside the ten
per cent the brief allows. Every page carries
six slot subsections, one layer-map variant, one slot strip and the
same three status sentences.

Catalog-first is the shortest, and the reason is structural rather than
editorial: four of its slots carry nothing, and an empty slot needs a sentence
saying which of the three empty states applies and why, where a filled slot needs
a paragraph describing a construct. The alternative would have been to pad it,
which the brief forbids.

### No comparative language, checked

Editorial rule 6 asks for consequences rather than verdicts, and a comparison
made on an approach page is a verdict delivered where the other two columns are
not visible. The generator rejects `unlike`, `whereas`, `better than`,
`worse than`, `more than`, `fewer than`, `only approach`, `superior`,
`inferior` and their neighbours, and `tools/pagecheck.js` re-checks the rendered
pages.

One phrase needed rewriting under this rule. The component-first page had said
that IBM ships the only assessment result in the three corpora. It now reads
that this is the corpus on this site that contains an assessment result, which
is the permitted form of factual uniqueness.

### Data additions to keep counts out of the prose

**Five counts** were missing from `corpus-stats.json` and would otherwise have
been typed into the artifact inventories: `aws_catalog_files`, `ez_files`,
`ibm_cdef_files`, `ibm_ap_files`, `ibm_ar_files`. All five are now recomputed
from the corpora by `verify.py --stats`.

### The status annotation is data, not markup

Plan section 7 requires the three status annotations to be applied
symmetrically: same shape, same weight, same placement. The wording now lives in
`data/six-questions.json` on the approach, `renderSnippet` reads it from
`data-status`, and `pagecheck.js` asserts that every snippet on a page carries
that approach's annotation and no other. Annotating one approach and not another
is now a failing check rather than an oversight.

### Decisions made during the build

1. **Extra blocks attach to the slot they concern.** The first draft had a fixed
   "slot 6 extra" slot, which put the catalog-first callout about the empty
   control tie underneath slot 6 instead of slot 2. Extras are now keyed by slot
   number, so each page attaches its block where it belongs: assessment-first at
   3 and 6, catalog-first at 2 and 3, component-first at 3 and 6. Two each.
2. **`rule-groups` is named as specification-only in prose**, with an explicit
   statement that there is no snippet because there is no content, so no reader
   goes looking for one.
3. **Repository links are rendered where one exists** and their absence is
   stated in the same sentence on the two pages that lack one. Only the AWS
   content has a public repository on the record.

### Verification added

`--pages` grew by 45 checks, all in a new `checkApproach`:

- the nine template sections, in order, with the exact heading text
- six slot subsections
- every snippet carries this approach's status annotation
- section 8 has two boxes and they are within 15 per cent
- section 9 uses the three shared frames
- no comparative language in authored prose
- the alphabetical ordering is stated on the page
- the page carries its own layer-map variant and its own slot strip

```
[snippets]  12    [schema]   15    [stats]  25    [data]  18
[css]       62    [a11y]     46    [diagrams] 312
[pages]     1  (656 page checks behind it)
                                              660/660 checks passed
```

### Open for Gate 7

1. **Read your own page first.** Proponent review is the strongest neutrality
   instrument available: correct
   anything about your approach that is wrong. The section to read hardest is
   8.1, which is written as the advocates would write it and is therefore the
   place where putting words in someone's mouth is easiest.
2. **The word counts are equal by construction, which is not the same as fair.**
   Catalog-first is shortest because four of its slots are empty and an empty
   slot takes fewer words to describe honestly. Say if that reads as short
   measure rather than as an accurate account.
3. **Proposed versus shipped constructs.** Confirm the examples support the
   distinction rather than treating a planned feature as published content.
4. **Section 9 on all three pages.** The three sentences are the same frames
   with different specifics, which is the rule. Read them side by side and
   confirm none of the three reads as a criticism where the others read as a
   description.
5. **Gate 5 item still open:** whether the plan document should be amended to
   match the audience decision recorded there.

### Addendum: the site has to be served, and now says so

Reported during Gate 6 review: pages were showing
`corpus-stats.json could not be loaded` and similar messages in several blocks
at once.

**The data was fine.** Every file parses, and `verify.py --stats` recomputes
every figure in it. The cause was that the pages were open from the file system.
Every page here is markup plus data, per plan section 8, and a browser gives a
`file://` page an opaque origin and blocks `fetch()` for local files. So every
data-driven block fails at once, and every diagram is missing. Confirmed by
serving the same files over HTTP, where all of them return 200 with the right
content type and parse correctly.

This was a real gap in the build rather than a misuse. Every gate in the build
guide asks a person to open the site and look at it, and nothing anywhere said
how. Three changes:

1. **`tools/serve.py`.** A local static server on the standard library, nothing
   installed, nothing written, `Cache-Control: no-store` so that regenerating
   data between refreshes shows the new data, and only 4xx and 5xx logged so a
   missing file is visible.
2. **The page says so once, not a dozen times.** `site.js` detects
   `file://` and puts a single banner at the top of `main` explaining the cause
   and giving the command. Each component's own failure message gains one
   sentence pointing at that banner rather than repeating the explanation.
3. **README.** A "Viewing the site" section immediately under Status, stating
   plainly that opening a page from the file system does not work and why.

GitHub Pages serves over HTTP, so a published copy was never affected. The
audience for the fix is every reviewer between now and publication, which is the
audience the gates depend on.

The README also now records which files are generated and must not be
hand-edited: everything in `assets/diagrams/`, and the three approach pages.

---

## Phase 7: compare.html

Seven sections, per plan section 4.6. The page compares and does not rank, and
it stops at section 7 rather than summing up, because a summary of a comparison
is a recommendation wearing a different hat. Both of those are now assertions in
`tools/pagecheck.js` rather than intentions.

### What the published OSCAL files establish

The comparison answered fifteen analysis criteria from the published files.
For requirement level, the three CISA assessment plans carry a `criticality`
prop in the `http://cisa.gov/ns/oscal` namespace, valued `SHALL` or `SHOULD`,
on every step: 73 and 55 respectively in each of the three files. This is a
namespaced property, not a dedicated field in the core schema.

Other evidence retained its limits: the component-first observation names a
subject typed `inventory-item`; its assessment result records no finding; all
three approaches carry a description of what the check does. No corpus at this
phase contained a system security plan, so SSP impact remained an open question
rather than a measured scale claim.

### Model coverage must follow the examples

Component definitions, an assessment plan and an assessment result are present
in the component-first examples. A fourth model, the system security plan, is
not demonstrated by that corpus. Describing a proposed lifecycle is not evidence
that all of its models have been published.

### Decisions

1. **Cells live in a data file, not in markup.** `data/criteria-fill.json`, 45
   cells, generated by `tools/criteria_fill.py`, which refuses to write if the
   grid is incomplete, a pair is duplicated, a name appears, or a long dash gets
   in. The alternative was typing 45 cells into a table by hand, which the
   standing rule against hand-typed JSON exists to prevent.
2. **Thirteen new figures, all recomputed.** Every number the page cites is now
   a key in `corpus-stats.json` with a derivation, and `--stats` recomputes it
   from the corpora. `ez_props` 55,155, `aws_props` 6,094, `ibm_cdef_props` 0 is
   criterion 14 as an arithmetic fact rather than an impression.
3. **The SC-28 marks are matched, not listed.** Section 3 marks the lines doing
   three jobs in each encoding. Which lines those are is decided by matching
   tokens against the raw extract and marking the same line numbers in the
   highlighted output, so a re-extraction cannot slide the marks off the text.
   A job a file does not do at all is stated in that pane rather than left as an
   absence to notice. Two of the three panes have one.
4. **The marks reuse the slot palette.** The three jobs are slots 1, 2 and 3, so
   the legend is the vocabulary from the six slots page rather than a fourth
   colour scheme. No new tokens, and `--css` still passes with no raw hex below
   the token block.
5. **One deliberate departure from alphabetical order.** Sections 1, 2 and 3 are
   alphabetical by structural name, as everywhere else. Section 4 puts the three
   join diagrams in option-letter order, so that no approach
   leads every table on the site. The departure is stated on the page and both
   halves are asserted.
6. **Organization names stripped at render time, not from the data.** A stat's
   label in `corpus-stats.json` names the corpus it was counted from, which is
   correct provenance and reads properly on a page about one approach. In this
   table the column already says which corpus a cell belongs to, so the name is
   redundant and Gate 7 applies. `corpusFreeLabel()` strips it on the way out
   rather than weakening the labels the rest of the site depends on.

### A harness bug this phase exposed

`pagecheck.js` stored assigned `innerHTML` as a string and never parsed it. Any
markup a renderer built by assignment was therefore invisible to every check on
the page, which is why the SC-28 marks came back as zero the first time a check
asked for them. The setter now parses into real child nodes and keeps the string
for the getter. Reverting the fix turns the mark check red and nothing else,
which is the evidence that it was the fix and not a coincidence.

That is the fourth harness fidelity bug found by writing a check that should
have passed and did not: `dataset` not writing through, the missing `DOMParser`,
`h3` parsing as tag `h`, and now this.

### tools/verify.py --criteria

The comparison checked fifteen analysis criteria numbered 1 to 15, with no gap,
and 45 cells answering each exactly three times. Evidence pointers resolved to
existing snippets or recomputed figures. The DOM checks confirmed the table's
row count and column order. The current `--criteria` check validates the criteria
and their question mappings structurally; it does not establish source wording.

Six mutations were run against the finished page to confirm the checks bite. A
sixteenth criterion, a fact cell stripped of its evidence, the join diagrams
reordered to lead with the alphabetically first approach, an "on balance" added
to the lede, a closing summary added after section 7, and the harness fix
reverted. Each turns exactly the check that names it red.

### Totals

```
verify.py --all       582/582        (was 536)
pagecheck.js          916/916        (was 546)
```

### Open for Gate 8

1. **Read the evidence-bearing cells.** If a cell mischaracterizes a file,
   the correction is more valuable than the cell. Criterion 3 in
   particular: `criticality` is a namespaced prop, not core schema, and the
   question is whether that counts as OSCAL representing requirement level.
2. **The local-defintions misspelling in criterion 15.** The IBM assessment plan
   spells `local-definitions` without the second `i`, so it does not validate.
   Stated because the other two columns carry a comparable incompleteness fact
   in the same cell, `PLACEHOLDER` in 9 of 14 and 29 controls with no check
   component. Say if it reads as a gotcha rather than as the same kind of fact.
3. **Section 6 claims exactly four agreements.** Four is asserted, but whether
   these are the right four is a judgement no check can make. The fourth, that
   nobody has built the end-to-end example the group chose as its decision
   instrument, is the only statement on the page that applies equally to every
   column.
4. **Options D and E in section 7.** Both are stated from the record with the
   advocates' names removed, which is the site rule, and both have no content to
   show. Whether the core claim is fairly stated is a proponent review question
   and there is no proponent in the room for option D.
5. **Gate 5 item still open:** whether the plan document should be amended to
   match the audience decision recorded there.
6. **Gate 7 item still open:** proponent review of the three approach pages, now
   including the corrected model count in section 6 of component-first.html.

---

## Phase 7b: the six questions, and a shorter way in

Two changes, both from review of compare.html.

### The framework is now the six questions

"The six slots" was ambiguous. Slot is a word the site invented, it has no
meaning to a reader arriving from the working group, and the name says six
while the matrix has eight rows. The framework is now **the six questions**,
which is what the six-questions page's own lede had been calling it all along:
"six questions have to be answered somewhere."

The vocabulary moves with it, and the states read better for it:

| Was | Is |
| --- | --- |
| the six slots | the six questions |
| slot 6a | question 6a |
| Filled, Partly filled | Answered, Partly answered |
| Deliberately not asserted | Deliberately not answered |
| Absent, no stated position | Unanswered, no stated position |
| the slot strip | the strip |

**The identifiers deliberately did not move.** `.slot-chip`, `.slot-strip`,
`--slot-1` through `--slot-6`, `data-slot-fill`, `data-slot-question` and the
`slot` keys in `data/` still say slot. They are machine identifiers that no
reader ever sees, and renaming them would churn the stylesheet, the diagram
library, nineteen SVG files and every anchor on the site to no reader's
benefit. The split is documented where a maintainer will hit it first: a note
in the token block of `site.css`, and one in `pagecheck.js`.

What a reader does see is now checked. `pagecheck.js` walks the rendered text
of every page, exempting source paths and code, and fails on `six slots` or
`slot N`. That check found three leaks the search had missed: the accessible
`<title>` and `<desc>` of the generated SVGs, a second copy of the state labels
inside `assets/diagrams/74-slot-strip.js`, and three definitions in
`glossary.json`. All three were invisible to a grep of the HTML because they
are generated or rendered.

### The six-questions page now opens on its own subject

It ran 917 words across two full sections before the reader reached the list
the page is named for. The first section is the definitional dispute about what
a rule is; the second is why the rule and the check are kept apart. Both are
load-bearing, so neither was cut.

They moved below the list instead. The order is now the questions, the two that
need a section of their own, the matrix, and then the two arguments underneath.
64 words of prose to the first question, down from 917. Nothing was deleted.

The argument for the old order was that the questions presume a definition of
rule that is contested, so the dispute should come first. The argument against
is that the questions are readable without it, and that a reader who has not yet
seen the questions has no idea why the dispute matters. The page now says so in
the section itself: it is placed after them because it explains why the answers
differ rather than what they are.

### A new check, because section numbers moved

Five places on four pages cite a section of the six-questions page by number, and
every one of those numbers changed. A number written into prose on one page and
owned by a heading on another rots the first time a section moves, silently.

`pagecheck.js` now parses every rendered page, finds every link of the form
`./page.html#anchor` whose text says "section N of the ... page", resolves the
anchor on the target page, and compares the number the prose claims against the
number the heading actually carries. Getting it right required fixing the
number-extracting regex, which read `2.2 What you lose` as `2`, so the check
found its own bug before it found anyone else's.

### Verification

Three mutations, each turning red only the check that names it:

1. The retired name reintroduced into six questions prose.
2. A cited section number left stale at 4.2 after the heading moved to 2.2.
3. The six questions sections shuffled back to the old order, which turns the cited
   number red on all four citing pages at once.

```
verify.py --all       582/582
pagecheck.js          939/939        (was 916; 23 of the new ones are the
                                      retired-vocabulary and section-number
                                      checks across every page)
```

### Open for Gate 8

1. **The two moved sections.** The definitional dispute now arrives at section 6.
   Read the page cold and say whether it lands too late, or whether the forward
   pointer in the lede is enough.
2. **Question, not slot, in the matrix header.** The column header is now
   "Question" and the row header carries the question text. Confirm that reads
   as one grid rather than two.
3. **The identifier split.** A maintainer will see `slot` in the CSS and
   `question` on the page. Two comments explain it. Say if that is worse than
   the churn a full rename would have cost.

---

## Gate 8 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

Two decisions, taken before phase 8 began. Gate 7's no-quotation and
no-personal-attribution policy continues to apply to the open questions.

### 1. Gate 7 holds. The register is deidentified

The eleven items keep their substance, their dates and their statuses. The
requester column names the occasion rather than the person: *agreed by the
group, 20 March*, *requested 19 June*. Nothing on the site names anybody, and
the existing name check stands unchanged with no exemption for this page.

### 2. Extracts and editorial questions are different content types

Published OSCAL JSON is extracted through `tools/extract.py` and rendered as a
snippet with provenance. Criteria and open questions are maintained as analysis
content, not reproductions. No blockquote returns to the site.

---

## Phase 8: open questions, the data-quality appendix, and the start page

**Date:** 2026-08-14
**Scope:** `questions.html` per plan section 4.7, `data-quality.html` per plan
section 9, `index.html` per plan section 4.1, the data layer all three need, and
the three verification phases that were registered and never implemented
**Result:** complete. 1,007 of 1,007 verification checks pass, up from 582,
behind them 1,182 page checks, up from 939.

### What was built

```
questions.html          nine sections, 1,247 words of prose in markup
data-quality.html       five sections, 566 words, twelve items
index.html              seven sections, 1,257 words, no concluding paragraph
data/questions.json     the register and framed questions
data/data-quality.json  twelve items, four per approach, every denominator
data/six-questions.json       one_line per approach; other_options for D and E
data/corpus-stats.json  31 figures added, 69 total, all recomputed
assets/site.js          eighteen renderers added
assets/site.css         .register, .two-up, .dq, .orientation, .position-group
tools/verify.py         --questions, --appendix and --links implemented
tools/pagecheck.js      checkQuestions, checkAppendix, checkIndex
```

### Structural verification of analysis content

The 15 criteria and open questions are now maintained as analysis content.
Checks cover identifiers, meaningful question text, mappings and reasoning.
They do not establish that wording was reproduced or that another party agrees
with the framing. Published OSCAL extracts retain their separate file-and-pointer
provenance checks.

### Equal budget on a page made entirely of defects

`data-quality.html` is the page where a thumb on the scale would do the most
damage and be the hardest to see, because its whole content is things that are
wrong with somebody's files. Three properties are counted rather than intended.

**Four items per approach.** The number is a property of the page, not a finding
about the corpora, and the page says so in its own framing: the three sections
do not add up and a total would mean nothing. `--appendix` asserts the counts
are equal and `pagecheck.js` asserts they rendered equal.

**Every item carries its denominator.** Not in prose, where it can be forgotten,
but as a stat key beside the numerator, rendered as one unit. Editorial rule 8
is carried by the layout. Thirty-one figures were added to
`corpus-stats.json` for this, every one recomputed from the corpora by
`--stats`, including all the denominators.

**Every set is read against that publisher's own statement**, stated first in
each section, and the check requires all three sections to have one rather than
two of them.

One further check earns its place: no figure may appear in an item's prose that
is not also a rendered figure. It caught two things. A bare `29` in a sentence
that passed only because 29 happens to be the value of an unrelated stat used
elsewhere on the page, which is exactly the accident the rule exists to prevent.
And `800-53`, which is a standard's name rather than a figure, so the check now
strips standard names before scanning instead of allowing any number that
happens to match something.

### The index has no conclusion, and that is asserted

Plan section 4.1 and the brief both say the index is the page most likely to
acquire a thesis by accident. Four assertions exist for that reason and nothing
else on the site needs them:

- the last section is the scope box, and nothing follows it
- no element after it, so a closing paragraph cannot be appended without failing
- the page contains none of *our view*, *we think*, *we believe*, *this site holds*
- the sixty-second orientation is labelled as orientation and says in terms that
  it is a routing aid

The orientation was the risky part of the brief, because three questions that
route a reader to a page are one edit away from three questions that route a
reader to a conclusion. It is written so that each of the three answers points
at exactly one page and none of them mentions an approach, and both of those are
checked.

### Decisions made during the build

1. **The three readers paragraph is verbatim from the plan except for two
   words.** The plan's wording is "which slots each one fills, for which reader,
   and what it costs to fill the rest". The phase 7b vocabulary decision retired
   the word slot from anything a reader sees, and `pagecheck.js` fails on it. It
   now reads "which questions each one answers ... and what it costs to answer
   the rest". This is the one place where two binding instructions were in
   direct conflict and the later one won.
2. **Open questions are editorial content.** Their wording and reasoning are
   maintained in the analysis data rather than imported as snippets.
3. **A snippet's JSON pointer is part of its address and is displayed.**
   A source filename alone is insufficient to locate the evidence in a document.
4. **The two sides of the mapping-item question are held within fifteen per cent
   by a check**, the same tolerance the approach pages use for their two boxes,
   and are laid out in two columns of equal width. Length is the argument in
   that one place on the site: a case at 300 words against a counter-argument at
   80 is a recommendation whatever the words say. Currently 145 against 129.
5. **The evidence register's state chip drops a duplicate lead-in.** Several
   status descriptions are the state and nothing more, so the chip and the
   text printed the same words twice. The chip stays, because it is what carries
   the state to a reader scanning the column, and the duplicated lead-in is
   dropped from the text.
6. **Supporting figures render label first, value second.** The headline pair
   reads better as "67 component definition files referencing role-id owner",
   but a list of counts reads better the other way round, and it stays
   grammatical when a count is one. Seventeen stat labels were reworded so that
   none embeds its own denominator, because the layout prints the denominator
   beside it and the two read twice. A check now enforces that.
7. **Options D and E render from one data file on both pages.** The panel was
   hand-written prose on `compare.html` and the brief asks for it on the index
   too. Two copies of a characterization of somebody's unpublished position is
   two things to keep in step, so it moved into `six-questions.json` and both pages
   render it. The section number is passed in, so the headings stay numbered in
   the house style on both.
8. **The three one-line summaries on the index cards carry no figures and are
   within ten per cent of each other**, 37, 36 and 39 words. A card is the most
   quotable thing on the site and the shortest, which makes it the easiest place
   to be unfair by a clause.
9. **Assessment-result evidence keeps its qualifier.** The published
   component-first assessment result exists and records no finding. Presence of
   that file does not demonstrate a complete assessment lifecycle.

### Three registered checks were implemented, and one found a real defect

`--questions`, `--appendix` and `--links` had been registered since phase 1 and
printed a note saying they were not implemented. All three now run. `--budget`
is the only one left.

`--links` was overdue and it found what it was always going to find. Every page
carried a footer link to `methodology.html`, which does not exist and never did,
and all three approach pages linked to `compare.html#data-quality`, an anchor
that does not exist on that page. Both are now fixed: the footers point at the
provenance file and the new appendix, and the approach pages point at the
appendix, which is the page they were describing all along.

`--links` also resolves the glossary's anchors, which no static check could see:
they are produced by a renderer at load time, so they are derived here from
`glossary.json` using the same rule `termAnchor()` uses. Five cross-page links
into the glossary were previously unchecked.

### Mutation checks on the finished pages

The checks were exercised by padding the mapping-item case, softening the
distribution note, giving one approach a fifth appendix item, breaking an
appendix denominator, removing one publisher's statement, lengthening a card
summary, adding a concluding section to the index, removing the orientation's
label, breaking a cross-page anchor, and dropping the design-choice statement
from the strip caption.

The script is not committed. The point of recording the edits and reverts
against the data files and `index.html` here is that the checks
were seen to fail rather than assumed to work.

### Totals

```
verify.py --all       1007/1007      (was 582)
pagecheck.js          1182/1182      (was 939)

[snippets] 12   [schema] 15   [stats] 71   [data] 18
[css]      64   [a11y]   46   [diagrams] 312
[appendix] 74  [links] 108
```

### Open for Gate 9

The remaining gates are readings a machine cannot stand in for, and the site is
now complete enough to be read end to end.

1. **The open questions, item by item.** Review their wording and reasoning for
   fairness; structural checks cannot establish agreement with the framing.
2. **The mapping-item question, both sides.** They are the same length by
   construction, which is not the same as being equally strong. Read the case
   against it cold and say whether it is the argument its holders would actually
   make, or a version of it written by someone who does not hold it. This is the
   one place on the site where the site has something close to a proposal, and
   the counter-argument is the only thing keeping it a question.
3. **The index, read cold, looking for a thesis.** Four checks say there is no
   conclusion and no view. None of them can tell you whether the seven sections
   in order add up to one anyway. Section 2, the satisfaction split, is the most
   opinion-adjacent thing on the page, because deciding that this is the
   distinction a reader most needs is itself an editorial judgement.
4. **The sixty-second orientation.** Three questions, three pages, no approach
   named. Say whether it routes or whether it steers.
5. **The appendix, read as a proponent.** Four items about your content, with
   four about each of the other two beside them. The question is not whether the
   items are true, which is checked, but whether four is the right number and
   whether the four chosen are the four that matter. A wrong item is a
   correction; a wrong selection is a bias no check can see.
6. **Whether the plan document should be amended.** Still open from Gate 5, and
   now larger: the plan's section 4 gives nine pages and the site has ten, its
   section 3 rules 1, 3, 10 and 11 were superseded at Gate 7, and its audience
   statement was superseded at Gate 5. This log is authoritative and the plan is
   not, which is the protocol, but the gap is now wide enough to mislead someone
   reading only the plan.
7. **`methodology.html` does not exist.** Every footer pointed at it for six
   phases. Plan section 12.8 suggests publishing a short note on how the site was
   checked for bias, which is what that link wanted to be. The footers now point
   somewhere real; whether to write the page is your call.
8. **Proponent review has not happened.** It is the strongest neutrality
   instrument the site has, it is flagged at three earlier gates, and the
   post-review question count on `questions.html` renders as zero until it does.
   That zero is on the page deliberately, so the omission is visible rather than
   silent.

---

## Gate 8 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

Three decisions, taken before the verification phase began, on conflicts between
the brief for that phase and the state of the project.

### 1. corrections.html is held until review actually runs

The brief asked for a published corrections page. No request for corrections has
been sent to any publisher, so there is nothing to publish and nobody has
declined to respond. An empty corrections page would imply a review that did not
happen.

So the page is not built. `CORRECTIONS.md` is committed empty, with the entry
shape a later session should follow and the text of the request that would be
sent. `verify.py --methodology` asserts the two states cannot be confused: while
that file has no entries the page must not exist, and the moment it gains one the
page must.

### 2. Response status is reported by approach, not by person

Gate 7 removed every personal name and every proponent organization from the
site, and it still holds. A non-response will be recorded as *Catalog-first,
option A: asked 14 August, no response as of 30 September*. Silence is published
and dated. It is attached to the approach rather than to a person.

### 3. A check that cannot run says so, and a skip is not a pass

Four of the checks the brief asks for need something the build environment does
not have: an OSCAL validator, a headless browser, and network access to reach the
published NIST schemas and the external links. They are implemented for real and
run in CI. Locally each prints `SKIP` with the reason and the exact command it
would have run, and the summary reports skips on a separate line from the passes.

---

## Phase 9: the verification harness, the methodology page, and publication prep

**Date:** 2026-08-14
**Scope:** complete `tools/verify.py`, wire CI, build `methodology.html`, make the
site open from a folder, publication metadata, and the report
**Result:** complete. 1,327 of 1,327 verification checks pass, up from 1,007, with
9 skipped and reported. Behind them 1,280 page checks, up from 1,182.

### What was built

```
tools/verify.py          --slots --budget --conformance --methodology --bundle
                         added; --schema --links --a11y gained network halves
tools/bundle.py          builds assets/bundle.js from data/
tools/extract.py         idempotent timestamps
tools/axe_run.mjs        serves the site and runs axe-core over every page
tools/pagecheck.js       checkOffline: every page run the way a browser does
                         under file://
.github/workflows/verify.yml   three jobs: offline, strict, publication
methodology.html         six sections, the eleventh page
data/methodology.json    thirteen rules parsed from the plan, 18 checks, 6 audits
CORRECTIONS.md           empty, with the entry shape and the unsent request
corrections.html         NOT built, per the Gate 8 decision
assets/bundle.js         generated, 63 files
README.md                rewritten for publication
```

### Every check, as of the final run

```
python tools/verify.py --all        1327 passed, 0 failed, 9 skipped
node tools/pagecheck.js            1280 passed, 0 failed
```

| Check | Pass | Fail | Skip |
|---|---|---|---|
| `--snippets` | 12 | 0 | 0 |
| `--schema` | 15 | 0 | 5 |
| `--stats` | 71 | 0 | 0 |
| `--data` | 18 | 0 | 0 |
| `--css` | 62 | 0 | 0 |
| `--a11y` | 46 | 0 | 1 |
| `--diagrams` | 312 | 0 | 0 |
| `--appendix` | 145 | 0 | 0 |
| `--slots` | 110 | 0 | 0 |
| `--budget` | 27 | 0 | 0 |
| `--conformance` | 4 | 0 | 2 |
| `--methodology` | 58 | 0 | 0 |
| `--bundle` | 16 | 0 | 0 |
| `--links` | 233 | 0 | 1 |
| `--pages` | 1 | 0 | 0 |

### The nine skipped checks, and what each one needs

Every one of these runs in the `strict` job of the workflow, where a skip is a
failure. None of them is skipped by choice.

| Skipped | Needs | Command |
|---|---|---|
| Five stored schema fragments still match the published NIST 1.2.1 schemas | Network | `curl` the schema, compare each fragment |
| axe-core over all eleven pages | axe-core, puppeteer | `npm install --no-save axe-core puppeteer && node tools/axe_run.mjs` |
| Every conformant extract validates | An OSCAL validator | `pip install compliance-trestle` |
| Every proposed extract fails validation | The same validator | as above |
| Every external link is reachable | Network | `curl -o /dev/null -w '%{http_code}'` per link, four links |

The offline half of `--conformance` does run and is worth having on its own. It
establishes the structural reason the labels differ: the component-first corpus
uses `rules`, `checks`, `implementing-rules`, `assessment-check-id` and
`target-component-uuid`, none of which OSCAL 1.2.1 defines, and the other two
corpora use no undefined assembly at all. That is why one is labelled proposed
schema and the other two are not, and it is checked by reading the field names in
every file of all three corpora.

### The checks found four real defects

Three of them had been live for one or more phases and none was visible by
reading.

1. **One approach page shipped without its own join diagram.** `--budget` counts
   figures and diagrams per page and found 1 against 2 against 2. The
   assessment-first page had no `73-join-assessment` while the other two showed
   theirs, because the join figure had been hand-placed in two pages' extras
   blocks rather than held in the shared template. That is editorial rule 7
   exactly: a difference in treatment arguing in a channel no word count can see.
   The figure now belongs to the template, so all three get one by construction.

2. **Question 2b was on no approach page at all, and nothing said so.** The
   template renders six questions and the matrix has eight rows. The missing row
   is late binding, which is the single most asymmetric claim in the comparison,
   and its absence from the approach pages is defensible: stating "late binding:
   available" on one page, where the other two columns are not visible, is a
   verdict delivered out of context. But it was undocumented. All three pages now
   carry the same paragraph saying the question is answered once, where all three
   columns are visible, and pointing at both places it is treated.

3. **Every footer pointed at `methodology.html`, which did not exist**, and the
   three approach pages pointed at `compare.html#data-quality`, an anchor that
   does not exist. Both found by `--links` in the previous phase, both now
   resolved, and the page the footers wanted is the one built here.

4. **The criteria-fill generator still emitted the retired vocabulary.** Phase 7b
   retired the word slot from anything a reader sees and checked every page for
   it. `tools/criteria_fill.py` had one cell reading "Slot 6a is empty by design",
   and regenerating the file reintroduced it. This is the failure mode the
   workflow's regenerate-and-diff step exists for: a generated file can be
   corrected by hand and pass every check until somebody runs the generator.

### The harness had two more fidelity bugs, and the second was serious

Both were found the same way as the four before them: by writing a check that
should have passed and watching it fail.

**`location` was a stub carrying only `hash`.** Anything reading
`location.pathname` or `location.protocol` threw. That is why the navigation's
current-page marking had been an inline script on three pages and absent from the
other eight, and why the `file://` path had never been tested.

**The HTML parser dropped all trailing text after the last tag, and all text in a
string with no tags.** `"a <b>B</b> c"` parsed as `"a B"`. `"plain only"` parsed
as `""`. Every check that reads `textContent` off markup a renderer built by
assignment was therefore reading a truncated version of it: the name check, the
organization check, the retired-vocabulary check and the no-recommendation check
among them. They were weaker than they looked rather than failing outright, which
is the worse of the two failure modes.

Fixing it turned one check red immediately. The primer's running-example check
collects every `<code>` in the table and asserts each string occurs in the
snippet it names; with the parser fixed, the `<code>` elements inside the
rendered extract bodies stopped being empty and the whole JSON document started
matching as an identifier. The check now excludes extract bodies, which is what
it always meant.

### The site now opens from a folder

The brief asks that the site open from `file://` and serve from Pages unchanged.
Until now it did not, and the site's answer was a banner telling the reader to
start a server. That is a reasonable answer for a contributor and a poor one for
the audience: someone handed a zip should be able to open `index.html`.

`tools/bundle.py` writes `assets/bundle.js`, containing every file under `data/`
and every diagram, keyed by the path `site.js` would have fetched. `site.js`
consults it only when the protocol is `file:` or a fetch fails, so a served copy
never touches it. Three properties make this safe rather than a second source of
truth:

- `data/` remains authoritative. The bundle is a mirror.
- `--bundle` regenerates it and fails on any difference, so a stale mirror is a
  build failure rather than a page quietly showing old content.
- A page reading the mirror says so, in a line at the top, naming the file and the
  generator.

`pagecheck.js` now runs every page a second time with the protocol set to `file:`
and `fetch` rejecting on every call, and asserts zero fetches, zero renderer
failures, every extract rendered, every diagram drawn, and the provenance line
stamped. All eleven pages pass.

### The editorial rules and the plan

**The thirteen editorial rules.** Parsed out of section 3 of the plan by a script,
not retyped, and each one asserted to occur in that document.

### Decisions made during the build

1. **Rule 5's snippet-count clause is unreachable, and the site says so rather
   than meeting a weaker version quietly.** The rule asks for the same number of
   extracts on each approach page. One corpus offers six distinct constructs and
   another offers fourteen, so equality means padding a page with extracts that
   illustrate nothing or deleting extracts a reader needs. Both are heavier thumbs
   on the scale than an unequal count. Every other clause of the rule is enforced
   and re-measured from the shipped HTML. Each page now states its own extract
   count and the reason, in wording the build asserts is identical across the
   three, and the departure is published on the methodology page. This settles the
   snippet-count asymmetry that has been open since Gate 1.
2. **The `--quotes` check keeps its inverted sense.** Gate 7 removed all
   quotations, so the check asserts that no
   page carries a blockquote, no page carries a `data-quote` reference, and no
   page presents personal attribution. The flag keeps its name because the
   subject is the same. Applying the Gate 8 precedent rather than asking again.
3. **The thirteen rules are published in full, including the seven superseded in
   part.** Each carries its status and, where something changed, what changed and
   where that decision is recorded. Redacting an editorial policy would defeat the
   purpose of publishing one, and a rule that was quietly dropped is more
   interesting than one that held.
4. **Reproduced source text is exempt from the no-organization rule, and the
   exemption is narrow and counted.** Three of the thirteen rules name the
   publishing organizations, because they are rules about how those organizations
   are treated. The rule text renders with a `verbatim` marker, the same mechanism
   that already exempts file paths as provenance. `--methodology` asserts the
   marker is applied in exactly one place in `site.js` and appears in no page's
   markup, and that the organizations appear nowhere in `methodology.json` outside
   the reproduced rules.
5. **The methodology page states what an audit cannot establish.** Word counts,
   annotation counts and figure derivations are all countable and all counted, and
   the choice of what to count is editorial. The two things most likely to be
   wrong are not countable: which four data-quality items were chosen for each
   approach out of those available, and whether the case stated for each approach
   is the case its proponents would make. Both are named on the page as the reason
   proponent review matters more than the harness.
6. **The navigation's current-page marking moved into `site.js`.** It had been an
   inline script on the three generated pages and absent from the other eight, so
   the navigation announced the current page on three pages out of eleven.
7. **The provenance line is rendered from `provenance.json`** rather than stamped
   by a per-page script, so a page cannot claim a freshness it does not have. It
   carries the build time, the extract count and the corpora root.
8. **The workflow has three jobs, and the split is the point.** `offline` is
   exactly what a contributor can reproduce on a laptop. `strict` runs the same
   harness with `--strict` on a runner with network and the validators, so a
   skipped check cannot stay skipped. `pages-build` checks the publication
   requirements that are not checks: `.nojekyll` present, no absolute paths, Open
   Graph and Twitter tags on every page, a provenance line on every page. The
   offline job also regenerates every generated file and fails if the result
   differs from what was committed, which is what would have caught defect 4 above.

9. **Every generator is idempotent, which is what makes regenerate-and-diff a
   real check.** `extract.py` stamped a fresh `extracted_at` on every snippet and
   a fresh `generated_at` on `provenance.json`, and `bundle.py` stamped a fresh
   build time, on every run. So the workflow step that regenerates everything and
   diffs it against what was committed could never have been clean, and the
   check would have been disabled the first time somebody hit it. All three now
   keep the previous timestamp when the content has not changed, so a build time
   is a statement about the content rather than about when the command was last
   typed. Three consecutive full regenerations now reproduce every generated file
   byte for byte.
10. **`CORRECTIONS.md` is committed empty and its emptiness is checked.** The file
   carries the entry shape a later session should follow, the two Gate 8
   decisions that govern it, and the text of the request that has not been sent.
   `--methodology` asserts that while it has no entries `corrections.html` must
   not exist, and that the moment it gains one the page must. That is what keeps
   absent-by-decision distinguishable from absent-by-oversight.
### More mutations, each caught by the check that names it

A reworded editorial rule, a dropped rule, a check advertised that the harness
does not have, an audit round missing what changed, a scope section that stops
admitting review has not happened, a matrix cell with an invented state, an
unanswered cell stripped of its reason, an approach page missing a figure, an
approach page that stops explaining its extract count, a stale offline bundle, a
denominator label that
embeds its own figure, and a weakened conformance mitigation.

These mutations turned red only the checks named for them.

### What could not be verified

Stated plainly, because the point of the harness is to make this list short and
explicit rather than absent.

1. **Nothing has been read by anyone whose work it describes.** No request for
   corrections has been sent. This is the largest unverified thing about the site
   and it is not a technical gap. It is stated on the methodology page in those
   terms.
2. **The five schema fragments have not been re-checked against NIST since
   2026-08-12.** Each fragment records its own fetch date and the check runs in
   CI. If a definition changed in the meantime, the site's question 2 argument
   would be stale and the build would say so on the next CI run.
3. **No content has been put through an OSCAL validator in this environment.**
   The labels are supported by a structural argument about field names, which is
   checked, and by the misspelled key in one file, which is checked. The
   validation itself runs in CI.
4. **No accessibility audit has been run, only contrast arithmetic.** Forty-six
   contrast and palette assertions pass. axe-core over the eleven rendered pages
   has never run, so landmark structure, accessible names on renderer-built
   controls, and the tab order through the disclosures are unverified.
5. **The four external links have not been requested.** They are three in markup
   and one rendered from data.
6. **Whether an extract is the right fragment to show is not checkable.** Every
   extract is provably what the file says at the pointer declared. Whether the
   pointer is aimed at a representative fragment is a judgement.
7. **Whether the case stated for each approach is the case its proponents would
   make is not checkable.** The two boxes are held to the same length and the
   lengths are checked. Their content is a reading.
8. **The grayscale contact sheet has not been looked at by a person** since phase
   3. It is regenerated on every `--diagrams` run and Gate 3 asked for a human
   pass over it, which remains open.
9. **The site has not been opened in a browser.** Every page has been run through
   the harness, served and from a folder, and the harness is a test double rather
   than a browser. Six fidelity bugs have been found in it so far, which is the
   reason to say this out loud.

### Open for Gate 9

The site is ready to publish and is not published, which is where the brief said
to stop. Six things want a person.

1. **Send the review request.** It is written out in `CORRECTIONS.md` and it is
   the one item on this list that changes what the site is: until it goes out, the
   honest description is one participant's reading of other people's files,
   checked against those files by a machine and by nobody else.
2. **Open the site in a browser, both themes, served and from a folder.** Nine
   verification phases and 1,280 page checks have never put a pixel on a screen.
3. **Read the methodology page cold.** It is the strongest credibility asset the
   site has and it is the page most likely to read as a defence. It was written to
   state and not to argue; say if it does the second.
4. **Rule 5.** The snippet-count clause of your own editorial policy could not be
   met and the site now says so publicly, on the methodology page, with the
   reason. Confirm that is the resolution you want rather than a quieter one.
5. **Whether the plan document should be amended.** Open since Gate 5 and now
   wider: the plan gives nine pages and the site has eleven, four of its thirteen
   rules were superseded at Gate 7, one more at this gate, and its audience
   statement was superseded at Gate 5. This log is authoritative and the plan is
   not, which is the protocol, but someone reading only the plan would now be
   misled.
6. **Push once and read the CI output.** The strict job is the only thing that has
   ever run the four network checks, and it has never run.

---

## Gate 9 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

The site was reviewed as a reader rather than as a build. Three findings, all
about the reading experience rather than the content.

1. **The layout wastes a third of a wide viewport.** `main` was capped at 1180px
   with prose at 72ch inside it.
2. **Every page is too long.** Landing on one gives no sense of what it holds.
   The reader should see the page's own structure first and open what they want.
3. **The material is dense and should be visual where it can be**, so that the
   concepts assemble for a reader rather than having to be built out of prose.

### The three decisions taken

1. **Sticky rail plus wide visuals.** The container widens to 1440px. Prose keeps
   a readable measure and the freed column becomes a rail. Anything that is a
   picture rather than a sentence spans the full width.
2. **Board first, one insight visible.** A page lands as a board of its top-level
   units plus the one figure or paragraph it exists to convey. Everything else
   opens in place.
3. **Pattern on three pages first**, then roll out. `index.html`,
   `six-questions.html` and `compare.html` in this pass.

---

## Phase 10: the overview-first layout

**Date:** 2026-08-14
**Scope:** the page grid, the board and panel components, and the three pages the
gate named
**Result:** complete. 1,327 of 1,327 verification checks pass, unchanged. Page
checks rise from 1,280 to 1,392, all passing.

### What the reader now lands on

| Page | Words visible on arrival | Words one click away |
|---|---|---|
| `index.html` | 2,666 | 638 |
| `six-questions.html` | 2,556 | 15,044 |
| `compare.html` | 1,498 | 21,631 |

The six questions page was a single scroll of about 17,600 words. It now opens on
six cards that carry, closed, all twenty-one primary answers on the page: the
question, and what each of the three approaches does about it. That is the
framework on one screen, which is what the page is for and what a reader
previously had to assemble by scrolling.

### Two decisions that shaped the mechanism

**Disclosure, not a modal.** Every collapsible thing is a native `<details>`.
Three properties of this site decided that rather than taste. Plan section 8
requires a stable id on every section and claim so that a discussion comment can
address exactly one of them, and a modal has no address. The print stylesheet
forces every disclosure open, so a printed page is still the whole document. And
a native disclosure is keyboard reachable and announced without any script, so
nothing became unreachable with scripting off.

**The rail is the table of contents, moved.** Every page already carried a `.toc`
nav. On a wide screen CSS places it in the second column and makes it sticky, so
the rail needed no new markup, works with scripting off, and prints in document
order. The only script is which entry you are currently reading.

### Section numbers and anchors did not move

Fourteen places on other pages cite a section of the six questions page by number
or by anchor, and `pagecheck.js` checks the number against the heading it names.
So the restructure kept every section number and every id where it was: section 1
became the board, sections 2, 3, 4, 6 and 7 became panels that open in place, and
the matrix stayed section 5. Nothing that cites this page had to change.

### The board is six cards from eight matrix rows

The matrix has eight rows and the page is called the six questions, which is not
a contradiction but does need handling. Row 2b is a property of OSCAL rather than
a question an approach answers, and it has its own treatment. Rows 6a and 6b are
two forms of one question.

The first attempt rendered seven cards, and the check written to catch that
compared the count against the number of matrix rows, so it passed while being
wrong. The renderer now groups rows by their base number and derives the card
name from the part of the row name before the colon, and the check derives the
expected grouping the same way from the same data, so the two cannot drift. Six
cards: 1, 2, 3, 4, 5, and one carrying 6a and 6b.

### Four defects found, three of them pre-existing

1. **Every question heading on two pages read "(Option C, undefined)".** Gate 7
   removed the organization from `data/six-questions.json` and `renderSlotFill` kept
   reading it. Visible to any reader, invisible to every check, because
   "undefined" is neither a name nor an organization. There is now a check that
   no page renders a missing value as the word undefined.

2. **A deep link into a panel landed on a closed panel.** The cited anchor is the
   section's, and the panel holding its body is a child of that section rather
   than an ancestor, so walking up from the target never reached it. A reader
   arriving at a cited claim would have seen a heading and nothing else, with no
   reason to think anything was missing. Opening now works in both directions.

3. **A link naming a card resolved before the card existed.** The board is built
   asynchronously. The hash is now resolved again once the board and the
   two-options panel have rendered.

4. **The harness was missing four more browser facilities.** `location` carried
   only `hash`, so anything reading `pathname` or `protocol` threw.
   `requestAnimationFrame`, `history` and `scrollIntoView` did not exist, and the
   script runs against an explicit parameter list rather than a real global, so
   each one had to be named there too. That is nine fidelity gaps found in this
   harness across the build, every one of them by writing a check that should
   have passed and watching it fail.

### Verification added

`pagecheck.js` gains 112 checks in three groups.

**The disclosure layer, on every page.** Every collapsible block can be linked
to, its ids are unique, it has exactly one summary of its own rather than
counting the extracts nested inside it, every panel keeps its heading in its
summary where the numbering check can see it, and every panel says what is inside
it before you open it.

**The board, on the six questions page.** Six cards in question order, each
naming its question, each carrying a swatch and a verdict and the evidence as a
tooltip on every answer, all closed on arrival, and the closed board showing
every primary answer in the matrix. That last one is the check that matters: it
is what stops the landing view from quietly losing an answer.

**Arrival, on all three pages.** Thirty-one anchors, each loaded with that hash
in the address, asserting that what it names is actually open. This is the check
that caught defects 2 and 3, and it is the one that keeps the restructure honest,
because the whole risk of collapsing content is that a link stops working and
nobody notices.

### Decisions made during the build

1. **Card colour is a class, not an inline style.** The first version set custom
   properties on the element. Colour on this site lives in the stylesheet where
   `--css` can see it, so there is one rule per question instead, drawing on the
   same palette every diagram and every strip uses.
2. **Question 6's card shows six answers rather than choosing one.** Both 6a and
   6b are named on the card and both sets of three are shown, because picking one
   would be the conflation the page exists to separate.
3. **The panels state what is inside them before they are opened.** A summary
   that is only a heading gives a reader no reason to open it, which turns
   collapsing into hiding. Every panel carries a one-line description and the
   check requires it.
4. **The index collapsed least.** Two panels, 638 words behind them. It is the
   front door and almost all of its content is either the required verbatim
   framing or a figure, so the gain there is the width and the visuals rather
   than the folding.
5. **`main > *` is capped at the measure and named exceptions are not.** Figures,
   tables, boards and anything marked `.wide` span both columns. That keeps the
   default safe: a new block reads at a comfortable width unless it asks not to.

### Open for Gate 10

1. **Look at the three pages in a browser, both themes, and at a narrow width.**
   The rail appears above 1120px and the board reflows to one column below about
   19rem per card. Neither has been seen.
2. **Eight pages still have the old shape.** The pattern is on index, the six
   questions and side by side. `questions.html` is now the longest page on the
   site at 4,311 words visible, and the appendix, the approach pages, the primer,
   the glossary and the methodology page are all unchanged.
3. **The board is the one place a reader meets all three approaches at once
   without the comparison page's framing.** Read the six cards cold and say
   whether the states read as a scorecard. If they do, that is the most
   consequential thing this pass got wrong, and the fix is in the card rather
   than in the prose.
4. **Whether the panels should remember what you opened.** They do not. Every
   arrival is a fresh page with everything closed except what the address names.

---

## Phase 7c: finishing the rename, and a check that was too narrow

Asked to check the build after the rename, on the suspicion that more screens
needed it. The build was green. The suspicion was right anyway, which is the
useful part of this entry.

### The check was passing because it was asking the wrong question

The retired-vocabulary check from 7b matched `six slots`, `slot N` and
`slots N`. It did not match the bare word. So it walked straight past
`the implementation slot expects a narrative one` on index.html, and past
`the six-slot strip is the measure of completeness` in the accessible
description of five generated SVGs.

Slot was never an English word on this site. It was always the framework's
name for a question. So the pattern is now the bare word, `/\bslots?\b/i`,
over the rendered text of every page, exempting source paths and code. That
turned eight pages red immediately.

### What it found, all of it invisible to a search of the HTML

| Where | What |
| --- | --- |
| `tools/diagrams.py` | thirteen strings inside SVG `<title>`, `<desc>` and legend text, which is what a screen reader announces |
| `assets/diagrams/74-slot-strip.js` | a second copy of the state labels, so the strip tooltips still said "Filled" |
| `index.html` | two prose sentences |
| `methodology.html` | rule 5, reproduced verbatim from the plan |

The pattern in every case is that the text is generated or data-driven. A
grep of the pages could not have found any of it. The check that runs the
renderers and reads the result could, once it was asking for the right thing.

### The plan is amended, and the correction log is not

`methodology.html` publishes the plan's thirteen editorial rules verbatim, and
`--methodology` asserts the match against section 3 of
`TFG-Rules-and-Checks-Site-Plan.md`. Rule 5 said "same six-slot template", so
the page could not be corrected without correcting the plan.

The plan is amended. Sixty-seven lines across the forward-looking sections,
plus a Rev. 6 note in the revision history recording the rename and its reason.

**Two parts of the plan were deliberately left in the old words.** The revision
history paragraph and section 13, the correction log, are dated records of what
was decided when. Rewriting them would be editing the record to match the
present, which is the opposite of what a correction log is for. Rev. 6 says so
explicitly.

Code spans in the plan were also left alone: they name machine identifiers,
which keep the old name for the reason 7b recorded.

### A phase flag had to move

The answer-matrix phase was `--slots`. `--questions` was already taken by the
open-questions page phase, so the matrix phase is now **`--matrix`**, which
says what it checks and collides with nothing. `methodology.json` publishes the
flag list and `--methodology` asserts it equals the harness's own phase list in
order, so the page and the harness moved together or neither would have passed.

### Maintainer-facing text moved too

Nineteen printed check names and comments across `verify.py`, `pagecheck.js`,
`site.js`, `site.css`, `74-slot-strip.js`, `diagrams.py` and `svgrender.py`. A
reviewer running the build reads those check names; two vocabularies in one
console output is the same failure as two on one page.

The identifiers still say slot, unchanged and on purpose: `.slot-chip`,
`--slot-1`, `data-slot-fill`, the `slot` keys in `data/`, the `#slot-2-full`
anchors. The split is documented in three places a maintainer will hit first.

### Verification

Two mutations, each turning red only what it should:

1. The bare word reintroduced into index.html prose.
2. The bare word reintroduced into one SVG description in the generator, which
   turns four pages red at once because four pages embed that diagram.

```
verify.py --all       1327/1327     (6 skipped: no network for the NIST schema,
                                     axe-core, the OSCAL validator, external links)
pagecheck.js          1392/1392
```

### Open for Gate 8

1. **The plan amendment.** Sixty-seven lines changed. The substance of every
   rule is unchanged and rule 5 is the only one whose wording moved. Confirm
   that leaving the revision history and the correction log in the old words is
   the right call rather than an inconsistency.
2. **`--matrix` as a flag name.** It is published on the methodology page as
   one of the eighteen checks a reader can run. Say if `--answers` reads better.

---

## Phase 7d: every page was rendering in one grid cell

Reported with a screenshot of index.html: sections stacked on top of one
another, strips over prose, diagrams over both.

### One word

The page grid introduced with the panels placed children with
`main > * { grid-area: content }`. A named area resolves to a row AND a
column, and the grid has one explicit row, so every child of main on every
page was placed into the same cell. Grid items in one cell overlap. That is
the entire screenshot.

The fix is the named-lines form: columns declared as
`[content-start] minmax(0,1fr) [content-end rail-start] 15rem [rail-end]`,
children placed with `grid-column: content`, which pins the column and leaves
the row to auto-placement, so sections flow downward. The toc takes
`grid-column: rail; grid-row: 1 / span 999` and stays sticky for the page's
whole height.

One intent changed rather than restored: the old sheet sent wide items across
both columns with `grid-column: 1 / -1`. With the rail occupied top to bottom
by the toc, a full-span item overlaps it, which is the same bug wearing the
fix's clothes. Wide items now take the full reading column, about 1140px on a
1440 viewport, and stop at the rail.

### Why nothing caught it

Every check this site has reads structure: the DOM harness has no layout
engine, and the CSS phase read tokens and class presence, not placement. A
person caught it, which is the failure mode the harness exists to prevent.

Three assertions added to `--css`, and the first proven by reverting the fix:
`main > *` must place by grid-column and never grid-area; the rail likewise;
and nothing may span `1 / -1` under the sticky rail. Narrow protection,
honestly named: it pins this bug class, not layout in general. Visual review
at the gates remains the real check, which is what this phase demonstrates.

```
verify.py --all       1330/1330
pagecheck.js          1392/1392
```

---

## Phase 7e: the space the screen offers, and two sticky elements fighting

Reported with screenshots after 7d: scrolling cuts off the right-hand table of
contents, a diagram is cut off with a scrollbar under it while empty space
sits beside it, and the pages waste the width of the screen.

All three symptoms trace to two rules.

### The header and the toc are both sticky, and neither knew about the other

The site header is `position: sticky; top: 0`. The toc rail stuck at 24px, so
on every scroll the header simply covered the top of the list. Worse, and
unreported: every same-page anchor on the site landed its target under the
header, because nothing set `scroll-padding-top`.

The header now publishes its real height. `site.js` measures it on load and
resize into `--header-h`, since the header wraps to different heights at
different widths and a constant would either waste space or fail. The toc
sticks below it and `html { scroll-padding-top }` keeps anchor jumps clear.
The stylesheet carries a close-enough fallback for the moment before the
script runs.

### The measure was applied to the page instead of to prose

Every child of `main` was capped at the 72ch measure. So every figure, table
and board on a non-wide section lived in a 600px box, and every diagram
carries a 720px floor below which its smallest label drops under 12px, so
each one grew a horizontal scrollbar with a column of empty space beside it.
That is the cut-off image and the wasted white space in one rule.

Sections now take the full reading column, and only things made of sentences
are held to the measure, by kind, wherever they sit: ledes, gists, tier2
blocks, callouts, the methodology rules, orientation items, captions, and
bare paragraphs. Figures, tables, code extracts, boards and strips take the
column. The frame narrows from 1440px to 1280px so the prose-only stretches
do not gape, and the `.wide` class in the markup is now inert, which is
harmless.

### The three-up diagram row could never have worked as drawn

Three diagrams side by side, each with a 720px readability floor, is 2160px
of floor. No viewport supplies it. As shipped, each of the three panes had
its own horizontal scrollbar showing about 40% of a diagram. The row is now
one shared scroller holding three equal 720px panes: about one and a half are
in view at once and one swipe reads across all three. The panes stay at one
size, which is the constraint the plan actually states. Dropping the floor
was rejected because it puts labels under 12px, which --diagrams exists to
forbid.

### Checks

Three additions to --css, the blanket-cap one proven by mutation. The first
version of that check failed on the clean stylesheet: it read the whole file
and matched the print block's `max-width: none !important`, which is print
UNDOING a cap. Scoped to the screen rules. A check that cannot tell the cure
from the disease is the usual price of a textual check on CSS, and it is why
these are labelled as pinning bug classes rather than layout.

```
verify.py --all       1333/1333
pagecheck.js          1392/1392
```

### Open for Gate 8

1. **The joins filmstrip.** Three equal panes in one scroller is the honest
   reading of "side by side at equal size" under the 720px floor, but confirm
   it on screen, since it is a compromise however drawn.
2. **1280px frame.** Chosen so prose pages do not gape and table pages still
   breathe. The criteria table (900px minimum) fits with room; say if the
   matrix or the SC-28 panes feel cramped and it can go to 1360.

---

## Gate 10 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

### 1. The rail indicator was drawing over the list number

Reported from a screenshot. Fixed, and the cause is recorded below.

### 2. The three approaches appear in option-letter order

Catalog-first is option A, Component-first is B, Assessment-first is C, and that
is now the order everywhere on the site: navigation, cards, strips, matrix
columns, criteria columns, appendix sections, question blocks, join diagrams,
tabs and page maps.

**This supersedes editorial rule 2**, which asked for alphabetical order by
structural name. The reason rule 2 existed is unchanged and is still met: an
order a reader can verify from the record rather than one that looks chosen.
Option letters are the working group's own labelling, so they satisfy the same
requirement without implying a ranking.

---

## Phase 11: the order, and the rail

**Date:** 2026-08-14
**Result:** complete. 1,264 of 1,264 verification checks pass with 12 skipped and
reported. Page checks rise from 1,392 to 1,418, all passing.

### The rail indicator

The active entry in the rail was marked with `box-shadow: -0.6rem 0 0`, which
paints a solid block to the left of the anchor. In an ordered list the list
number sits in the `ol`'s padding, which is exactly where that block landed, so
the current entry appeared to have a blue rectangle stamped over its number.

The marker now sits inside the anchor's own box: a tinted background with a small
radius and matching negative margin, so it cannot collide with anything the list
puts beside it.

### The reorder touched sixteen places

The order was expressed in more places than a search for the word alphabetical
found, which is the interesting part. Six of them were only found by writing a
check that asserts the order on every page and for every construct that carries
the three:

- two lists hard-coded inside renderers, for the SC-28 table and the SC-28 panes,
  which declared their rows starting with Assessment-first
- three sets of cards written directly into markup, on the start page, the six
  questions page and the data-quality page
- the primer's page map, which the existing check compares against the navigation

Both renderer lists now sort through one function rather than carrying their own
order, so a declaration order cannot become a display order again.

The remaining ten were the constant in `site.js`, the constant in
`pagecheck.js`, a new constant in `verify.py`, the navigation in eleven pages and
in two templates, the diagram generator's own list, the appendix section order and
numbering, the data files, and the prose on five pages that states which order is
used and why.

### The colour each approach carries did not move

The three approach hues were assigned mechanically in alphabetical order when the
palette was built. They stayed where they were. A hue that changed hands would
invalidate every published figure and every association a reader had already
formed, and it would buy nothing, because the three are equal-lightness and carry
no valence by design, so which hue an approach has means nothing. The comment in
`site.css` now records the assignment as what it is: a fixed mapping made once,
not a rule that tracks the display order.

### Verification added

26 page checks, in one group: the order, asserted on every page for every
construct that carries the three approaches. Strips, appendix sections, approach
cards, question blocks and the navigation itself, with each run of three checked
separately so a page that repeats the set cannot get one run wrong.

Mutation tested by putting one page's strips back into alphabetical order, which
turns red exactly the two checks that name it and nothing else.

### Open for Gate 11

1. **Look at the rail again**, and at a page scrolled to the middle, since the
   indicator moves with the reader and only the resting state has been reasoned
   about.
2. **Eight pages still have the old shape**, unchanged from Gate 10. The
   overview-first pattern is on the start page, the six questions and side by
   side. `questions.html` is the longest page on the site.
3. **The order is now by option letter and the site says so in five places.** Read
   one of them and confirm it states the reason rather than just the fact.

---

## Gate 11 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

Four findings from reading the six questions page as a reader.

1. **The three corpora are published examples, not official releases**, so the
   counts in them do not matter and should not be presented as if they answer
   anything. Question 1 is about where a rule resides.
2. **"Control tie" is not enough on its own.** The question is how a rule
   satisfies a control. Go through the site and replace labels like it with
   descriptors that say what is being asked.
3. **A source path should link to the file**, and the extract should open large
   enough to read.
4. **The small boxes with numbers in them are hard to follow.**

---

## Phase 12: names that say what they ask

**Date:** 2026-08-14
**Result:** complete. 1,301 of 1,301 verification checks pass with 12 skipped and
reported. Page checks rise from 1,418 to 2,395, all passing.

### The eight questions were renamed

Every name is now a phrase a reader can act on. The short form is what appears in
a strip cell, where there is room for one or two words and nothing more, and the
full name is what appears everywhere there is room for it.

| Was | Is | Short |
|---|---|---|
| Rule | The rule itself | Rule |
| Control tie | How the rule links to a control | Control link |
| Late binding available | Whether someone else can add that link later | Later link |
| Check | How the rule is tested | Check |
| Subject | What the check runs against | Subject |
| Actor | What performs the check | Runner |
| Satisfaction: implementation claim | How the system claims it meets the rule | Claim |
| Satisfaction: assessment result | How an assessment records the outcome | Result |

The questions themselves were rewritten in the same pass, because several were
as terse as the labels. Question 2 was "Which regulatory requirement does this
serve?" and is now "How does this rule help satisfy a regulatory control, and
which one?", which is the question that was actually being asked.

The two-part question needed a name for the pair, since the card had been
deriving one from the part of a member's name before a colon and the new names
have no colon. Both halves now carry the same `group_name`.

The machine identifiers did not move, for the reason recorded at phase 7b:
`--slot-N`, `.slot-chip` and the `slot` keys in `data/` are names no reader ever
sees, and renaming them would churn the stylesheet, the diagram library and
nineteen SVG files for nobody's benefit.

### Counts stopped standing in for descriptions

The corpora are published samples. A count in them describes what somebody chose
to publish and says nothing about how much content an approach could carry, so a
count is not an answer to where a rule lives.

Question 1 for the catalog approach read "452 controls across 77 groups, no
nesting and no enhancements". It now reads "One control per rule, in a flat
catalog: no nested groups and no control enhancements". The same pass rewrote six
other answers and seven criteria cells that led with a figure.

A statement of what the three corpora are now renders from `six-questions.json` in
four places: the six questions board, the comparison matrix, and the artifact
inventory on each approach page. It says they are published samples, that a count
describes the sample rather than the approach, and that counts appear in one
place on this site for one purpose, which is the data-quality appendix, where
every figure carries its denominator because maturity of the sample is what that
page is about.

Editorial rule 8 is unaffected. It requires a denominator wherever a
data-quality item carries a figure, and that is still enforced.

### Extracts carry their address

The source path is now a link to the published file, for the one corpus with a
public repository on the record. The other two are supplied to the working group
with no repository, so their paths stay as text: a link that goes nowhere is
worse than no link, and the check asserts both halves of that rather than only
the first.

Each extract also gained an explicit control reading "View JSON" in place of a
bare disclosure triangle, and opens in a dialog at the width of the viewport
rather than expanding inside a column narrowed to a reading measure.

**The markup did not change.** Every extract is still a `<details>` carrying its
own body, which is what keeps the print stylesheet working, keeps every extract
addressable by id, and keeps the content reachable with scripting off. The dialog
moves that body in and out rather than copying it, so there is never a second
copy of an extract in the page to fall out of step with the first.

### The number boxes say what they are

A chip reading `1` in a coloured box is a reference to a scheme the reader has to
have memorized. Every chip now carries the question's short name beside its
number, and its full name in the tooltip. Three places rendered them: extracts,
the criteria table's question column, and the SC-28 legend. All three were bare
digits, and the check that found the second and third was written for the first.

### Verification added

Eight checks in `--matrix`: every question name is at least three words, none is
one of the retired labels, every question has a short form, every question is
phrased as a question, the two-part question carries one name for the pair, the
statement about the corpora exists and says what it has to say, and no answer
opens with a count instead of a description.

977 page checks, most of them per extract and per chip: every extract shows where
it came from, links to the published file where a repository exists, does not
link where none does, and offers an obvious way to open it; every chip is
labelled rather than a bare digit; and the pages that show counts carry the
statement about what the corpora are.

Two mutations confirm the pair that matter. Renaming question 2 back to "Control
tie" turns red both the three-word check and the retired-label check. Putting a
count back at the front of an answer turns red the check that names it. The
first mutation was run once against a weaker version of the check, which passed
it, because "Control tie" has a space in it and the check only asked for a
phrase. The bar is three words for that reason.

### Open for Gate 12

1. **Read the six cards again with the new names.** They were the thing to read
   cold at the last gate and the names have changed since.
2. **The dialog has not been opened in a browser.** It is a native `<dialog>`,
   so focus handling and Escape are the browser's, but the moving of the body in
   and out is this site's and has only been exercised by the harness.
3. **Eight pages still have the old shape.** Unchanged from the last two gates.
4. **"Subject" and "Check" survive as short forms** because no shorter phrase
   fits a strip cell. If either still reads as jargon in the strip, the fix is a
   wider cell rather than a longer word.

---

## Gate 12 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

**The answer boxes are very difficult to understand. Find a better way to
visualize this.** Reported from two screenshots: the eight-cell row on the start
page and the same row inside each approach card.

---

## Phase 13: the answer list

**Date:** 2026-08-14
**Result:** complete. 1,301 of 1,301 verification checks pass with 12 skipped and
reported. Page checks rise from 2,395 to 2,456, all passing.

### What was wrong with it

The row asked a reader to decode two encodings at once and wrote neither down.

The tint said which question, from a six-hue palette. The border and fill said
which of five answer states, using solid, dashed, hollow, hollow-with-a-dot and
hollow-with-a-dotted-fill. Both were documented on other pages and neither was
legible where it was used, so a reader who had not memorised both saw eight
coloured squares with numbers in them.

**The second problem is worse than the first, and it is the reason this was not
just a legibility fix.** The three unanswered states were drawn as three
different geometries. Three different renderings of the same fact read as three
degrees of it, and a hollow box with a dotted fill reads as emptier than a plain
hollow box. They are not degrees. They are one fact, not answered, with three
different reasons behind it, and one of those reasons is that the approach
answers the question deliberately by not answering it. Encoding that as a fainter
box is close to the opposite of what the site says about it in prose.

### What it is now

One labelled row per question: the question's number as a tinted chip, its short
name, and the answer in words.

```
1   Rule           Answered
2   Control link   Not answered · reason on record
2b  Later link     Answered
3   Check          Answered
4   Subject        Not answered · no position stated
5   Runner         Not answered · no position stated
6a  Claim          Partly answered
6b  Result         Not answered · no position stated
```

**The three unanswered kinds now share their words and differ only in the reason
after them.** A reader learns the fact first and the reason second, which is the
order they matter in, and no reading of the three as degrees is available.

The palette survives on the number chip, which is what a palette is for:
reinforcing a label rather than standing in for one. The five geometries survive
on a small swatch, so grayscale and print still separate the states. Neither is
load-bearing any more, because the words are, and that is asserted rather than
intended.

On the start page the three lists now sit side by side under one legend, which is
the comparison, and it needs no key.

### Decisions made during the build

1. **The five state wordings live in `data/six-questions.json`** under a new
   `answer_states`, each with a label, a reason and a meaning. They were split
   between a constant in the strip component and the `empty_states` list, so two
   files had to agree. Now one file says it and the component reads it.
2. **The component keeps its name, its hook and its file.**
   `assets/diagrams/74-slot-strip.js` still owns it and `data-strip` still
   summons it, for the reason recorded at phase 7b: those are machine
   identifiers no reader sees, and renaming them churns the stylesheet, the
   generator and every page for nobody's benefit.
3. **The legend renders from the same data.** It was a hand-kept list of five
   labels.
4. **The old caption is gone rather than rewritten.** It explained how to read
   the boxes, which is a caption a component needs only when it is illegible.
   What replaced it is the one thing that still needs saying: that an unanswered
   question is not a defect, with the clearest instance named.

### Verification added

60 page checks, per approach per page: every list answers all eight questions,
names every question rather than numbering it only, states every answer in words
drawn from a closed set, gives a reason on every unanswered row, and carries its
evidence as a tooltip on every row.

Mutation tested by deleting the state words from the component, leaving only the
swatch, which is exactly the old failure mode. It turns red the check that names
it, on every page, for every approach, and nothing else.

### Open for Gate 13

1. **Look at the three lists side by side on the start page.** They are the
   comparison now, and they are the thing to read cold for whether they land as a
   scorecard. Every earlier gate asked this of the boxes and the boxes hid it.
2. **The row is taller than the box was.** Eight rows is a block rather than a
   strip, and it appears on the start page, on all three approach pages and in
   three cards on the six questions page. Say if it is too heavy in the cards,
   where the small size is used.
3. **Eight pages still have the old shape**, unchanged since Gate 10.

---

## Gate 13 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

**The control link for the catalog approach uses the OSCAL mapping model.**

The site had described question 2 for that approach as if an inline framework
prop had been the plan and had been stripped pending a decision by the group. The
mechanism is `mapping-collection`: the tie to a framework control is made in a
separate OSCAL mapping document, authored independently of the catalog and able
to be authored after it is published. That is why the inline props came out.

---

## Phase 14: naming the catalog approach's mechanism

**Date:** 2026-08-14
**Result:** complete. 1,301 of 1,301 verification checks pass with 12 skipped and
reported. Page checks hold at 2,456.

### What changed, and what deliberately did not

**The mechanism is now named** wherever the site describes the catalog approach's
control link: the answer matrix, the approach page, the criteria table, section
2.1 of the six questions page, and the mapping-item question on the open
questions page.

**The answer state did not change, and could not.** It stays "Not answered,
reason on record". No `mapping-collection` document exists in that corpus: the
repository holds one catalog and 230 component definitions and nothing else, and
no file in it mentions a mapping. The site's foundational rule is that a cell
reports what the published files contain, so naming a mechanism that ships no
content cannot make the question answered. What changed is the reason: it was
"props removed pending a decision" and is now "the tie is made by a separate
mapping document, and none is published".

That distinction is the whole of this change and it is worth being exact about,
because the two readings differ in what they imply. The old text implied the
approach had not decided how to make the tie. The new text says it has decided,
the decision is the mapping model, and the artifact has not been published. The
evidence register already recorded the second reading at item 5, so the site was
inconsistent with itself.

### The neutrality risk this runs, and what holds it

Rev. 4 of the plan called the reachability of `mapping-collection` an advantage
for this approach. Rev. 5 corrected that: the constraint rewards whichever view
of a rule already matches the schema's assumption, which restates the
disagreement one level down rather than resolving it. Naming the mapping model as
this approach's mechanism runs straight at that correction, because it makes the
one approach that can reach the mechanism the one that depends on it.

Three things hold the line, and all three are asserted.

- **Question 2b keeps its disclaimer verbatim.** "Not an independent advantage:
  it follows from the view of a rule that this approach already holds." A check
  requires that sentence to be present.
- **Section 2.3 of the six questions page is untouched.** It still says in terms
  that this is not an independent argument for any option, that an earlier draft
  presented it as one and was wrong, and that the gap is in OSCAL rather than in
  any approach.
- **The open questions page gained a statement of fact rather than a case.** It
  records that one approach depends on this mechanism, that the question is
  therefore not hypothetical for it, and that the asymmetry is a property of
  OSCAL rather than a merit of any approach. It sits outside the two boxes whose
  lengths the build holds equal, so it cannot tilt the balance that check
  enforces.

### Verification added

Four checks in `--matrix`: the catalog approach's control link names the mapping
model, says the tie is made by it rather than inline, keeps the state unanswered
with the reason that no mapping document is published, and leaves the
late-binding disclaimer in place.

Mutation tested by reverting the construct to "None in the content", which turns
red the check that names it and nothing else.

### Open for Gate 14

1. **This is a correction about somebody else's approach, made by someone who is
   not its proponent.** The analysis names the mapping model as the mechanism,
   but no mapping document is published in the corpus. It is exactly the class
   of interpretation `CORRECTIONS.md` exists
   to route through the publisher, and proponent review has not happened.
2. **Whether question 2 and question 2b should stay separate for this approach.**
   They are now one mechanism described in two rows, which reads as duplication
   on the approach page. The rows are separate because 2b is a property of OSCAL
   that applies to all three, and merging them for one approach would break the
   matrix. Worth a look at whether the page says that clearly enough.

---

## Gate 14 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

**The primer uses question numbers that mean nothing to a reader.** The numbers
are introduced in a section that uses 6b before any context for them exists.

---

## Phase 15: a number with nothing behind it

**Date:** 2026-08-14
**Result:** complete. 1,301 of 1,301 verification checks pass with 12 skipped and
reported. Page checks rise from 2,456 to 2,460, all passing.

### What was wrong, in three places

**The primer.** It referred to "question 2" twice. The primer shows no list of
the questions and never introduces the framework, because it is deliberately the
page a reader meets before the framework exists for them. Both references are now
the question's name, linked to where it is worked out.

**The start page.** Section 2 was the satisfaction split, whose figure renders
chips reading 6a and 6b, and section 3 was the six questions. So the numbering
appeared one section before the section that introduces it. The two sections are
swapped: the six questions are now section 2 and the split is section 3. That is
the natural reading order anyway, and the new section 2 states in terms that the
numbers are shorthand for those six questions and nothing else, that 2b is the
second part of the link to a control, and that 6a and 6b are the two halves of
the sixth, for the reason in the section that follows.

This departs from plan section 4.1, which puts the satisfaction figure before the
strips. The plan predates both the numbering being visible on the answer lists
and the figure carrying 6a and 6b chips of its own.

**Five more pages, found by the check rather than by reading.** The comparison
page, the glossary, the methodology page, the appendix and the open questions
page all used a bare number somewhere. Three of them were fine in context and two
were not.

### The rule, and why it is that rule rather than a stricter one

A page may use a question number only where a reader can find out what it means:
either the page shows the list, or the number is accompanied by the question's
name.

The first draft of the check required a formal introduction of the numbering.
That failed five pages, and reading them showed three of the five were perfectly
clear: the comparison page uses "questions 1 to 3" beside the matrix that lists
all of them, the glossary writes "question 5, whatever or whoever performs a
check", and the open questions page writes "Question 4: what exactly is being
tested". A check that fails those is measuring the wrong thing.

The check also matched too literally at first. "The link to a control" is the
name of question 2 even though the canonical name reads "how the rule links to a
control", so the match is now on the distinctive words of the name, compared by
four-character prefix, which tolerates a plural or a tense. Two of the fixes
failed the check after being written correctly, which is what exposed that.

### The retired label had survived in the prose

Renaming the questions at phase 12 changed the names and left every sentence that
used the old label. "Control tie" was still in the primer, on all three approach
pages, in the glossary, in the appendix, in the diagram generator and in the
one-line summaries on the start page: which is to say, in most of the places a
reader actually meets it.

That is the failure the phase 12 check was written to prevent, and it did not,
because it only inspected `slots[].name`. It now inspects the four data files the
prose is written into as well.

Three consequences worth recording, because each one was caught by an existing
check rather than by reading:

- The one-line summaries grew past the ten per cent budget when the longer phrase
  went in, so all three were rewritten.
- A primer sentence went past forty words, which its reading-level check caught.
- A diagram node label overflowed its column. The generator asserts that text
  fits before it writes, so it refused to build rather than shipping a drawing
  with text over the edge. Four node labels now carry the questions' short names.

### Verification added

Four checks in `--matrix`, one per data file the prose lives in, asserting the
retired phrase is absent.

One page check, on every page: no question number appears without its name,
unless the page shows the list. Mutation tested by putting the bare phrasing back
on the methodology page, which turns red the check that names it and nothing
else.

### Open for Gate 15

1. **Read the start page in its new order.** Six questions, then the split, then
   the approaches. The satisfaction split was placed second on purpose by the
   plan and is now third.
2. **The primer names questions and never numbers them.** Confirm that reads as
   deliberate rather than as an omission, since every other page numbers them.
3. **Eight pages still have the old shape**, unchanged since Gate 10.

---

## Gate 15 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

Three changes to the answer list.

1. **Line the numbering up** across the three lists.
2. **Include a legend that describes what the dotted lines are.**
3. **Drop the reason from the row.** Move it to something that shows on hover.

---

## Phase 16: three lists that line up

**Date:** 2026-08-14
**Result:** complete. 1,301 of 1,301 verification checks pass with 12 skipped and
reported. Page checks rise from 2,460 to 2,510, all passing.

### The reason was what broke the alignment

A row read `2  Control link  Not answered · no position stated`, and a row that
answered read `1  Rule  Answered`. So rows had different widths and different
heights, the three lists drifted against each other, and a reader comparing them
had to find question 4 three times rather than reading across one line.

The reason is now in the row's tooltip and in the legend. Every row is the same
shape: a number, a name, a mark and a state word. The number chip is a fixed
width rather than content-sized, because 1 and 2b are different widths and the
names beside them were starting at different places down the column. The state
column is fixed too. Three lists placed side by side now line up rank for rank.

### The legend says what the marks mean

There was one, on the start page only, and it named the states without naming
their geometry. Taking the reason off the row makes the mark the only thing
carrying which of the three kinds of unanswered a row is, so the legend now names
the geometry as well:

```
Answered                            (solid)
Partly answered                     (dashed outline)
Not answered · by design            (plain outline)
Not answered · reason on record     (outline with a dot)
Not answered · no position stated   (dotted fill)
```

It is a component of its own now, `data-answers-legend`, so it appears wherever
the lists do: the start page's comparison and its three cards, the six questions
page's three cards, and each approach page. It was on one of those five before.

### Verification added

50 page checks. Every row keeps the reason off it and carries it on its tooltip
instead; every row is the same shape; every page showing lists shows a legend;
every legend covers all five states, names the geometry of each mark, and gives
the reason for each of the three unanswered kinds.

Mutation tested by putting the reason back on the rows, which turns red the check
that names it on every list on every page and nothing else.

### Open for Gate 16

1. **Hover is the only route to the reason for a mouse user, and there is none
   on a touch screen.** The tooltip is the browser's own, from the `title`
   attribute, so it is keyboard reachable but not tappable. The reason is in the
   legend, which is on the page, so nothing is unreachable. Say if a tap target
   is wanted.
2. **The state column is a fixed 10.5rem.** That fits "Partly answered" with
   room. If a longer state word is ever added it will need widening rather than
   wrapping, since a wrapped row would break the alignment this phase bought.
3. **Eight pages still have the old shape**, unchanged since Gate 10.

---

## Gate 16 decisions

**Recorded by Pirooz, 2026-08-14. Binding on every later session.**

Three findings from the three cards on the start page.

1. **The lists do not start at the same height.** Assessment-first sits higher
   than the other two.
2. **The question names are missing from the cards.** Add them.
3. **Sections 2 and 3 carry redundant material.**

---

## Phase 17: the dead stylesheet underneath

**Date:** 2026-08-14
**Result:** complete. 1,304 of 1,304 verification checks pass with 12 skipped and
reported. Page checks hold at 2,510.

### The names were being hidden by the design they replaced

The cards showed a number, a blank column and a state. The name was in the
markup the whole time. One rule was hiding it:

```css
.slot-strip--sm .slot-strip__name { display: none; }
```

That rule was correct when it was written. The component was a row of eight
small boxes, and at the small size a box was too narrow for a word, so the name
came off and the number carried it. When the boxes became a list at phase 13 the
rule stayed, and it is more specific than anything the new component sets, so at
small size the list lost the column that is the whole point of it.

It was not alone. The old block was still styling the list that replaced it: a
flex row fighting the grid, a centred column layout, a minimum cell height, and
`.is-partial` and `.is-empty-absent` painting a dashed border and a dotted fill
onto whatever wore the class. The row wears the class, so every row carried a
coloured border restating the state its own swatch already showed. That is the
double encoding phase 13 set out to remove, still in the stylesheet after the
markup that needed it was gone.

The block is deleted. The five state classes now set variables and nothing else,
and each thing that wears one decides what to draw: `.state-swatch` and
`.answers__swatch` carry the geometry, the row carries none.

### Why the lists did not line up

The one-line summaries are held within ten per cent of each other in length,
which is a budget rule and not a layout guarantee. At a given column width one
wrapped to four lines and another to three, so the lists underneath started at
different heights.

The card is a flex column now and the list is pushed to the bottom of it. The
grid row already stretches all three cards to one height, and every list has the
same eight rows at the same height, so pinning the bottoms lines up every rank.
The same rule covers any card carrying a list, which is the three on the six
questions page as well.

### What was redundant in sections 2 and 3

Three things, all of them the same thing said twice.

- Section 2 enumerated the six questions in prose immediately above three lists
  that name them.
- Section 2 then explained which mark means what, immediately below the legend
  that exists to say exactly that.
- Section 3's figure caption restated the paragraph above it, author for author
  and form for form.

Each is cut to what only that place can say. The caption now says what the
figure shows and links to the full treatment, which is a caption's job.

### Verification added

Three checks in `--css`: no rule hides a question name at any size, the answer
row's number column is a fixed width, and a card carrying a list pins it to the
bottom. The first is the one that matters, and it exists because the defect it
catches was invisible for four phases: the markup was right, the check that the
name rendered was passing, and a stylesheet rule from a deleted design was
hiding it on three cards.

Mutation tested by adding the hiding rule back, which turns red the check that
names it.

### Open for Gate 17

1. **This was found by looking at the site, not by any check.** A rule that
   hides content is invisible to a harness that inspects the DOM, because the
   content is in the DOM. The new check reads the stylesheet for the pattern,
   which catches this one and any repeat of it, and would not catch the same
   thing done with visibility, opacity or a zero width.
2. **`.card:has(.answers)` uses `:has`.** Supported in current browsers and
   ignored by older ones, where those three cards would go back to unaligned
   lists rather than breaking.
3. **Eight pages still have the old shape**, unchanged since Gate 10.

## Phase 18: the marks nobody defined, and the split told twice

Asked for a quality check on the primer, with three specifics: the six questions
are never defined, sections 2 and 4 say almost the same thing, and the dotted
boxes are undefined.

### The dotted boxes were undefined, and worse than reported

The primer has no marks at all, so the boxes come from elsewhere on the site.
Auditing every page for a mark and its legend found four defects:

- `compare.html` draws 24 marks in its matrix and never loads
  `assets/diagrams/74-slot-strip.js`, which is what renders the legend. In a
  browser its legend host finds no `TFGSlotStrip` and draws nothing.
- `questions.html` draws 6 marks in its slot fills and has no legend host at all.
- `six-questions.html` and `index.html` each drew the legend twice, once from a host
  and once appended by a renderer.

So on two of the eleven pages, a reader met a solid box, a dashed outline, a
plain outline, an outline with a dot and a dotted fill with nothing anywhere
saying which was which. The user reported this from looking at the site.

**Why no check caught it.** Two independent reasons, both worth recording.

First, the harness lied. `checkPage` loaded `74-slot-strip.js` into every page's
window regardless of whether the page declared it. Every legend assertion on
`compare.html` passed against a window no browser produces, because the harness
had supplied the missing file itself. `runDeclared` now reads `<script src>` off
the parsed document and loads exactly that, in order. This is the third time in
this build a check has passed while the thing it names was broken, and all three
had the same shape: the check and the subject were fed from the same place.

Second, the gate was wrong. The existing block was gated on `.answers__row`,
which is the answer list, so the two pages that draw marks through a different
renderer were never asked the question. The gate is now the mark itself.

Fixed: both pages load the renderer and carry one legend host; the two
self-appended legends are gone, so the host is the only thing that draws one;
and `renderAnswersLegend` now calls `fail()` when `TFGSlotStrip` is absent
instead of returning silently, so this cannot recur as an empty space again.

### The primer never defined the six questions

The page's own summary promised "six questions any of them has to answer" and
then never named them. Rule, Control link, Check, Subject, Runner, Claim and
Result were first met as column headings on the next page.

New section 2 defines all six, rendered by `renderQuestionList` from
`data/six-questions.json`. Grouping matches the board exactly, so the two cannot
disagree about what "the six" are. Where a question has a follow-on, 2b under 2
and 6a and 6b under 6, the follow-on gets its own line rather than being
dropped, so all eight matrix rows are accounted for on the page that introduces
them. The definition is the question itself, which is the shortest honest gloss
and is already the wording every other page uses.

### Sections 3 and 4 were the same three-way split

Not 2 and 4 as reported, though the report was right that a section was
redundant. Section 3 was "three readers who want different things" and section 4
was "disagreement about what a hardening rule is", and they map one to one: the
publisher wants it as a requirement, the implementer as a statement of how a
component may be configured, the assessor as a procedure. Same three, once by
who is reading and once by what they read it as, with a diagram apiece. A reader
who spotted the correspondence learned nothing from the second telling; one who
did not went looking for a fourth party.

Merged into one section 4, rendered by `renderReadings` from `data/views.json`
joined to `data/glossary.json`. The join is made in the data: each view now
names the reader it serves. Each card carries the reading, its definition, the
reader in the glossary's own words, and the model it implies. Diagram
`75-three-readers` is dropped from the primer and still used on `index.html`, so
nothing is orphaned. The framing callout and the Gate 7 suppression of advocates
and quotations are both unchanged.

Sections renumbered, subsection numbers with them. No link anywhere pointed at
the removed anchors.

### Verification added

Thirty-four page checks. Every page drawing a mark shows a legend, and shows it
once. The primer lists six questions, names each short name, and puts each
beside its own question text. The three readings render in `views.json` order,
each carrying its definition, its reader in the glossary's words, the model it
implies, and no advocate. The readers do not also get a section of their own.

One correction to an existing check: the sentence-length walker ended a sentence
after `h1` to `h6` but not after `dt`, so the definition list read as one run-on
per question and reported three sentences over forty words when none was. A `dt`
is a heading for its `dd`.

Mutation tested. Dropping the strip script from `compare.html` turns red the
legend check; a second host turns red the once check; removing the question list
turns red its check; restoring the readers section turns red the check that it
is gone.

Mutating `six-questions.json` and `views.json` turns nothing red, which is correct and
worth stating. These checks assert that the page faithfully reflects the data,
so mutating the data moves both sides together. The current `--questions` and
`--criteria` checks validate analysis structure, not the truth or fairness of
editorial wording. Published OSCAL extracts have separate corpus-backed checks.
Mutating the renderers, which is what these checks do guard, turns red nine of them.

`1307/1307` verify checks pass with 12 skips, `2549/2549` page checks pass.

### Open for Gate 18

1. **The silent-`if` pattern is probably not unique to the legend.**
   `if (window.TFGSlotStrip)` with no else rendered nothing and said nothing on
   two pages for several phases. The same construct appears wherever a renderer
   depends on an optional file. Only the legend one was fixed here.
2. **Editorial wording still needs review.** Structural validity is not
   agreement with a question's framing.
3. **Eight pages still have the old shape**, unchanged since Gate 10.
4. **Proponent review has still never been sent.** `CORRECTIONS.md` is empty by
   decision, not by response.

## Phase 19: three removals

Instructed to remove the two further options and every reference to them, to
remove section 6 from the primer, and to remove the footer.

### Options D and E

Options D and E had no published OSCAL content and were removed on instruction.
Gone from `data/six-questions.json`, from
`renderOtherOptions` in `site.js`, from section 5 of `index.html` and section 7
of `compare.html`, from the two tables of contents, and from the pointer
sentences on `six-questions.html`, `compare.html` and the primer.

`index.html` renumbered 6 and 7 down to 5 and 6. `compare.html` needed no
renumbering because the removed section was its last, which changed what its own
closing check was about: it asserted the page ends on section 7 rather than on a
summary, and a summary of a comparison is a recommendation wearing a different
hat. The check now names the section that is last and still asserts the absence
of a closing argument.

### Section 6 of the primer

"How to read this site", with the three tiers and the eleven-page map.
Removed on instruction, with its table of
contents entry. The primer is five sections now.

The page map had a check worth naming before it went: it asserted the map listed
every page in the site navigation and no others, with the count derived from the
nav rather than written down, so adding a page could not leave it asserting a
stale number. Nothing replaces it, because nothing else on the site claims to
list the pages. The navigation is now the only page list.

### The footer

Asked whether to remove the footer from all eleven pages or the primer alone,
and whether to keep the licence or the no-recommendation statement, the
instruction was: all eleven pages, keep the no-recommendation line, drop the
licence.

So the footer is one paragraph now. Gone: the provenance and sources paragraph,
the links to `provenance.json` and the data-quality appendix, the four source
attributions, the CC BY 4.0 licence, and the build date. `renderGenerated` and
every `data-generated` hook are gone with them, including the inline stamping
script on three pages and the same script in `assets/shell.html`, the page
template, which was updated so new pages come off it in the new shape.

**The CI workflow would have failed on the next push.** It looped over every
page and failed the build if `data-generated` was absent, which after this
change is every page. Removed. Nothing in the local harness would have caught
it, because the harness does not read the workflow.

### Verification

Fourteen checks removed with the content they asserted, two rewritten, two
added. The two added are the ones the removal made necessary: every page carries
the footer exactly once, and it states that the site makes no recommendation.
That statement is a standing rule of the build rather than a piece of copy, and
after this phase the footer is the only place on the site that says it, so it is
asserted per page rather than assumed.

Mutation tested. Changing the wording on one page turns red that page's check;
putting a `data-other-options` hook back turns red the unwired-hook check.

Swept for leftovers by rendering all eleven pages and resolving every internal
anchor link against the ids that actually exist: no dangling anchors.

`1287/1287` verify checks pass with 12 skips, `2545/2545` page checks pass.

### Open for Gate 19

1. **The site no longer states its licence or its publication terms.** Removed
   by decision. Nothing on the site now says under what terms it may be reused,
   and `data/provenance.json` is no longer linked from anywhere a reader would
   find it.
2. **The extraction claim is no longer made on the page.** "Every code block is
   extracted from a published file at a declared JSON pointer, never
   transcribed" was in the footer. It is still true, still enforced by
   `--snippets`, and still described on the methodology page, but a reader who
   does not open that page is no longer told.
3. **The primer no longer explains the three tiers.** The tier structure is
   still in the markup on every page and is still checked; nothing now describes
   it to a reader.
4. Items 1 to 4 of Gate 18 all stand.

## Phase 20: titles that say what the section contains

Instructed that section titles must make sense and explain the section, with
"The distinction most readers arrive without" given as the example of what not
to do.

Swept every h2 and h3 on the eleven pages. Most were already plain. Five were
not, in two different ways: some described the reader's state rather than the
content, and some named a thing without saying what about it.

| Was | Is |
| --- | --- |
| index 3. The distinction most readers arrive without | 3. Why question 6 splits: a claim is not a result |
| index 5. A sixty-second orientation | 5. Where to start, depending on what you need |
| questions 8. capability, and Discussion #2 | 8. What capability means, and where that is being settled |
| questions 1.1 Why this list is the shortest path to a decision | 1.1 What it would take to close these items |
| methodology 2.1 The checks were made to fail on purpose | 2.1 How the checks were tested: each one made to fail |

The first said what a reader lacks rather than what the section holds. The
second named a duration. The third was a term and a thread number. The fourth
made a claim about the list instead of describing it. The fifth described the
method obliquely.

The title of section 8 also lives in `data/questions.json` as
`discussion_2.title`, so both were changed together.

### A numbering error that had already shipped

The index carried a subsection numbered **7.1 under a section numbered 6**. It
was left behind by phase 19, when two sections above it were removed and
everything below renumbered. Nothing caught it, because each half of the page
was internally consistent: the contents list said 6, the heading said 6, and the
subsection number underneath was simply wrong.

### Verification added

**Every entry in a page's contents list has to match the heading it points at,
word for word.** Sixty-nine checks, one per entry across the eleven pages.

This is the check that would have caught the 7.1 error, and it is the check this
phase needed for itself: every title lives in two places, and each of the five
renames had to be made twice. Renumbering is worse, because it touches both
halves of every section below the change.

The comparison is on rendered text, so a heading assembled from a question chip
plus a title still has to match what the contents claims it says. The chip is
dropped before comparing, being a marker rather than part of the title.

Mutation tested both ways it can fail: drifting the contents entry from its
heading on the index, and renaming a chip-carrying heading on the six questions
page without touching its contents entry. Both turn red, and the failure message
prints the two strings against each other.

`1287/1287` verify checks pass with 12 skips, `2614/2614` page checks pass.

### Open for Gate 20

1. **A title can still be accurate and useless, and no check can tell.** The new
   check asserts the contents and the heading agree, not that either says
   anything. The five titles in this phase were found by reading them.
2. Items 1 to 4 of Gate 19 and 1 to 4 of Gate 18 all stand.

## Phase 21: the legend was decorative

Three things reported: the partly-answered mark is dashed in the option lists
but not in the legend, the contents list numbers every entry twice, and sections
5 and 6 should come off the start page. Plus a correction: removing section 6
from the primer last phase was probably a slip.

### The legend drew nothing, on every page that had one

Reported as one state. It was all five.

Every geometry rule was written as `.answers__row.is-X .answers__swatch`, which
needs the row ancestor that carries the state class. The legend has no row: its
renderer puts the state class on the swatch itself. So no geometry rule matched
a legend swatch at all, and all five drew as the same plain outline while the
lists beside them drew five different shapes. A reader comparing a dashed mark
in a list against five identical marks in the legend is being told the mark
means nothing.

This is worse than the missing legends of phase 18. That was an absence, which
looks like an absence. This was a legend that looked complete and was wrong.

Each rule is now written for both places a mark is drawn.

**Why `--css` passed while this was broken, which is the part worth recording.**
The check existed. It searched for `.answers__swatch.is-X` inside

    css.replace(".answers__row.is-X .answers__swatch", ".answers__swatch.is-X")

so it substituted the row-scoped selector into the swatch-scoped form in the
string it was about to search, and then found it. The check rewrote the evidence
into the shape of its own assertion. It could not have failed.

That is the fourth check in this build to pass while the thing it named was
broken, and the worst of the four. The others were fed from the same source as
their subject; this one manufactured its subject.

Replaced with a check that names all three selectors literally, for all five
states, and asserts the paint is in the matched rule. Mutation tested by
reverting the fix for one state: it turns red and names the missing selector.

Writing it honestly found a second thing. `.state-swatch.is-filled` has no rule,
because the inline mark paints filled from the `--cell-bg` token that
`.is-filled` sets rather than from a rule naming the state. That is legitimate
and is how one mark carries a question's hue, so filled is checked separately
against both mechanisms rather than forced into the table.

The legend's own text ran together for a screen reader: "Answeredsolid", "Not
answeredby designplain outline". Separators are real text nodes now, the same
fix and the same reason as the definition list in phase 18. The shape names
carry their article so the sentence reads.

### The contents list numbered everything twice

`.toc ol` kept the browser's list marker while the link text carries its own
number, so every entry read "1. 1. Three readers". The marker is off. The number
stays in the text, because it has to match the number in the heading and phase
20's check asserts that it does. The element stays an `ol`: the order is
meaningful.

### Sections 5 and 6 off the start page

"Where to start, depending on what you need" and "What this site does not cover".
Removed with their contents entries and their checks.

The check that the page ends without a concluding argument had named the scope
box by id. That id has now changed twice in three phases, so it is derived from
the declared section list instead: the invariant is that the page stops at the
last of its own sections, not that any particular one is last.

**What came off with the scope box.** It was the only place stating that the
site does not resolve `capability`, does not cover the mapping models beyond
question 2, and does not recommend. That is recorded here rather than asserted
anywhere.

### Section 6 of the primer, restored

Restored whole from a copy taken during phase 18's mutation testing. There is no
version control on this directory, so that copy in `/tmp` was the only thing
standing between a removal and a rewrite from memory. Worth fixing.

Two rows of its eleven-page table were stale on arrival, because the table
describes pages that changed after the copy was taken: the start page row still
cited options D and E, removed in phase 19, and the primer row predated section
2. Both corrected. The page-map check is back with it.

`1297/1297` verify checks pass with 12 skips, `2593/2593` page checks pass. No
dangling anchors.

### Open for Gate 21

1. **This directory is not under version control.** A removal is unrecoverable
   except by whatever copy happens to be lying around. This phase got lucky.
2. **No check can see a stylesheet the way a browser does.** `--css` reads text.
   It now reads it honestly, but the thing that was actually wrong, a selector
   matching nothing, is only visible to something that resolves selectors
   against a document. The axe run would not have caught this either.
3. **The scope statements have no home.** See above.
4. Items 1 to 4 of Gate 19 and 1 to 4 of Gate 18 stand, except the primer's
   section 6, which is back.

---

## Revision: review comments after the first full read

**Date:** 2026-08-18
**Scope:** terminology, the index's structure, one figure, the answer rows, page width
**Result:** 1299 of 1299 verify checks, 2570 of 2570 page checks.

### 1. Readers became stakeholders

The publisher, the implementer and the assessor are roles in the process, not
audiences for a document, and "reader" collided with the site's own frequent use
of the word for the person reading a page. Renamed throughout, with an explicit
phrase list rather than a blind replace, so that the roughly ninety genuine uses
of "reader" survived untouched.

Changed: the heading, the section id, the `#stakeholders` anchor, the field
`serves_reader_first` to `serves_stakeholder_first`, the `reader` key in
`views.json` to `stakeholder`, the glossary entries, the four diagram files
`75-three-readers*.svg` to `75-stakeholders*.svg`, and every reference in
`site.js`, `approach_pages.py`, `diagrams.py`, `verify.py` and `pagecheck.js`.

### 2. A rule is a requirement or a recommendation, never just one

Most of the content in question recommends rather than compels. A CIS Benchmark
and a Security Technical Implementation Guide are guidance; an organization
decides what to adopt. Calling the thing a requirement assumed the answer to the
question the site exists to lay out, which is what kind of thing a rule is.

Section 1 now says "a requirement or recommendation" and carries a short
paragraph on why both words are used, pointing at the three readings on the
primer rather than settling it. The figure's centre node reads "one requirement
or recommendation", and the publisher's first step reads "a requirement or
recommendation, written once". The glossary entries for publisher and implementer
follow. `pagecheck.js` now asserts both the phrase and the explanation, so the
single word cannot creep back.

### 3. The stakeholders figure was a third air

Rows sat 192 units apart against a 96-unit node, so the figure stood 922 units
tall on a page where nothing else passed 640. Rows now sit 140 apart against an
88-unit node and the legend prose is shorter: **922 to 730**, a 21 per cent cut,
with the same reading order and nothing dropped. At the current column width it
renders about 651px tall instead of 886px.

### 4. The Easy Dynamics pull quote is gone

The satisfaction figure ended with a quotation from `Where-does-desired-state-go.pptx`
and a line marking it as advocacy. It made the same point the six-differences
table above it already makes from the OSCAL schemas. Sourcing a structural fact
to the site author's own slide invited a reader to discount the fact along with
the source. Removed from the generator, so it is gone from `six-questions.html` too,
not only from the index. The figure lost 74 units of height with it.

### 5. The index showed the three approaches twice

Section 2 carried the three answer lists and section 4 carried three cards with
the same three answer lists inside them. A reader met the same three things twice
on one page. Section 2 is gone; its two paragraphs that were doing work, the one
explaining the numbering and the one saying an unanswered question is not a
defect, moved into section 3 around the cards, where the three sit side by side.

Four sections became three, renumbered, with the table of contents, the
`ARRIVALS` anchor list and the `INDEX_SECTIONS` list in `pagecheck.js` all
updated. The strip assertions now look in `#approaches`.

### 6. The answer rows were losing their names

`Control link` rendered as `Contr...`. The state column was a fixed 10.5rem, so
in a three-up card about 270px wide the name column got whatever was left.

Three changes, because right-aligning alone was measurably not enough:

- the state column is content-sized and pushed to the right edge
- the compact list has a tighter gutter and a narrower number chip
- two question names were shortened in `six-questions.json`: `Control link` to
  `Control`, `Later link` to `Later`

Measured against the row's real geometry, the tightest row now has **9px of
slack** and the rest have 16 to 28px. The full question name is still on the
row's `title` and in its screen-reader text, and in full on the six questions
page. Rows still line up rank for rank across the three cards, because the row
height and the chip width are fixed; only the internal boundary moves.

### 7. The interior gap between prose and the rail

The page was 1280 wide with a 3rem gutter and a 15rem rail, which left the
reading column about 930px against a 700px measure. The 230px that fell between
the end of a paragraph and the start of the table of contents read as a hole
rather than as margin, because it was bounded on both sides.

| | Was | Now |
|---|---|---|
| `main` max-width | 1280px | 1160px |
| column gap | 3rem | 2rem |
| rail | 15rem | 13.5rem |
| `--measure` | 72ch | 78ch |

At a 1269px viewport the gap falls from about 233px to about 107px, and the
reading column is 864px so figures and tables gained room rather than losing it.

### Caught while doing the above

**`approach_pages.py` had drifted from `shell.html`.** Regenerating the three
approach pages reintroduced a four-paragraph footer carrying provenance, sources
and a `data-generated` stamp that `site.js` no longer wires, because the shell
had since been cut back to the single "no recommendation" line. The generator now
carries the same footer as the shell, with a comment saying so. Worth noting as a
class of bug: a generator and a template that both hold a copy of the same markup
will drift, and only regenerating reveals it.

### For local cleanup

The sandbox could not delete inside the mounted folder. Two things to remove by
hand, both under `build/`, which is gitignored and regenerated:

- `build/grayscale/75-three-readers*.png`, eight files carrying the retired name
- `build/review/`, one throwaway render

Then `python tools/verify.py --diagrams` rewrites the grayscale set.

---

## Revision: catalog against component, with assessment separable

**Date:** 2026-08-18
**Scope:** one new index section, one paragraph on each approach page, a note on
the comparison page, plus the fixes three cold audits found
**Result:** 1322 of 1322 verify checks, 2602 of 2602 page checks.

### The change

The site treated the three as one choice among three. The observation put to it
was that catalog-first and component-first compete for the same job while the
assessment layer is separable, because the implementer and the auditor are
different people. The record supports that: one participant is on record that
treating these as competing approaches is a mistake, another that pieces of this
belong in different layers, and the group has already settled that both flows
converge at the assessment results layer.

Two corrections were needed before it could be written down.

**The axis is not the implementation layer.** A catalog is the Control layer and
a component definition is the Implementation layer. What unites them is that both
are authored once and reused before any assessment exists.

**Assessment-first does not abstain from the first question.** The material
proposing it states that catalogs and profiles are eliminated, which is a third
answer to where guidance lives, not an orthogonal position. Exempting it would
have handed one approach a free pass in a contest the other two were in, which is
the failure mode two earlier audits already caught on this site.

So the section is titled **"One question, or two?"** and sets out two candidate
questions without deciding whether the group should split the decision:

- **question A**, where reusable guidance lives
- **question B**, how an assessment is carried out and recorded

Question B is grounded in the models rather than in an argument: an outcome can be
recorded only in the assessment layer, and every assessment result is required to
declare the controls it reviewed. Three new schema fragments back that, and the
sentence links to each one.

### Three cold audits, and what each found

The section relocates the author's own approach out of a contest, so it was
audited three times by reviewers given the pages cold.

| | Author preference detected | Defects found |
|---|---|---|
| First audit | assessment-first, 85% | 11 |
| After rev. 1 fixes | assessment-first, 60 to 65% | 5 new, all factual |
| After rev. 2 fixes | assessment-first, 62% | 6, three of them mine |

**Fixed across the three rounds:**

- **A false schema claim.** "Observations and findings exist in no other model" is
  wrong: the POA&M root assembly carries both. Restated as the assessment *layer*,
  which is true, with `data/schema-evidence/poam-outcomes.json` behind it.
- **Catalog-first was unexamined on question B** while the section asserted that
  everyone owes an answer. All three positions are now stated.
- **IBM's assessment plan was deleted from the description**, which made the only
  corpus publishing both halves of the lifecycle look result-only. Corrected.
- **The nine `PLACEHOLDER` values were used as evidence of reuse and never as a
  cost**, although the site's own appendix calls the unresolved reference the
  mechanical reason that corpus has no assessment result. Both readings now sit in
  the same sentence.
- **"The other five name a system" was false.** Three point at a back-matter
  resource titled `[System Name] SSP` whose files are not published. The sentence
  now says none of the fourteen resolves to a system and gives the three shapes.
- **"On B has published nothing" contradicted the matrix**, which gives
  catalog-first the only non-empty 6a cell. Corrected to what the cell says.
- **`six-questions.json`'s finding contradicted its own matrix** and nothing caught it.
  The finding is now derived from the cells and `verify.py --data` recomputes it.
- **Two pages claimed the ordering was alphabetical by structural name** while the
  code renders option-letter order. The order was right and the claim was wrong.
- **The unevidenced caveat** that a result may satisfy `reviewed-controls` with
  `include-all`. `data/schema-evidence/reviewed-controls.json` added.
- **`plan-of-action-and-milestones` was missing from `NIST_SCHEMAS`**, so its
  fragment was skipped in silence, including in CI. The local skip list is now
  driven by the directory rather than a hand-kept tuple, so a new fragment cannot
  again produce a check that never runs.
- **`callout--settled` on the assessment-first page.** Everywhere else that class
  means settled by the working group. It was dressing one proponent's unsettled
  claim in the site's own consensus styling, on the only approach page that had it.

### Assertions added, so none of this can quietly revert

`pagecheck.js` now requires the section to name both questions, to ground B in
the models, to say that the Assessment layer answer is an answer to A rather than
an abstention, to name all three positions on B, to qualify the one existing
result rather than counting it whole, to state where A and B share a model, and to
leave the shape of the decision open. It also forbids the two sentences the first
audit found false.

### Still open, and not mine to settle

**The props double standard.** The third audit put this as the sharpest fairness
objection on the site, and it is pre-existing rather than introduced here.

The assessment-first page says the approach *"changes no schema: every construct
used is released OSCAL, with content carried in props where the released model has
no field."* Section 3 says of component-first *"fields that are proposed rather
than released."* Both extend OSCAL. One extends it through 55,155 undeclared
props; the other through zero props and a written specification. The first is
credited with changing no schema and the second is debited for proposing one.

Either that asymmetry is defensible or the two need one vocabulary. It is a
judgement about how to characterise two ways of extending a standard, it favours
the author's own approach, and it should not be resolved by the author alone.

**Also worth a decision:** the fourteen-of-fourteen and one-of-one figures now sit
in section 3, while `six-questions.json` states that counts live in the data-quality
appendix with their denominators. The figures carry denominators inline, but
`aws_ap_files` and `aws_ar_files` have no appendix item, so the appendix cannot
currently be the single home the policy describes.

---

## Revision: section 3 as two pillars, and a table that was not aligned

**Date:** 2026-08-18
**Result:** 1322 of 1322 verify checks, 2605 of 2605 page checks.

### 1. Section 3 is now two pillars with a bridge

Six paragraphs of prose became a three-column layout: question A on the left,
question B on the right, and the thing that joins them in a narrow channel
between. 470 words to 397, and the drop understates it, because most of what
remains is now a scannable list rather than a paragraph.

The bridge is the point of the component. **The check and its runner are not
decided by the left-hand choice.** A rule names a check, something runs it, and
the same check and the same runner serve whichever model holds the guidance. That
was the observation behind the change and it had no visual expression before.

Two things the layout had to get right or it would have misled:

- **The assessment plan appears in the left column too**, marked with a doubled
  border, because placing guidance there is an answer to question A rather than an
  abstention from it. A reader who took the left column as "not the assessment
  plan" would have the division backwards, and the approach whose model it is
  would have been lifted out of a contest the other two are in.
- **Equal width by construction**, 1fr against 1fr, so neither side can be given
  more room by editing prose.

Every neutrality assertion the section carried survives the rewrite and two were
added: that the bridge names the check and the runner, and that it says neither is
decided by the left-hand choice.

### 2. Titles now describe their sections

`3. One question, or two?` asked a question instead of naming its content. It is
now `3. Where guidance lives, and how it is assessed`, which says what is in the
section. The three column titles are not `h3` elements: every `h3` on this site is
a numbered subsection, and these are column headings, so they carry the same
weight through `.pillar__title` without claiming to be sections.

### 3. The six-differences table was genuinely misaligned

The comment above it claimed the columns matched the panels above and were of
equal width. Neither was true. The widths were **250 and 408**, so the 6b column
wrapped at a measure half as wide again as 6a and the two read as ragged rather
than as a pair.

A table beneath two panels cannot align to them in any case: the panels start at
the drawing's left edge and the table needs a label gutter first. So the table is
now internally symmetrical instead, which is what the eye reads as aligned:

```
 40 ..240   label   200 wide
260 ..580   6a      320 wide
600 ..920   6b      320 wide
```

Equal widths, equal gaps, flush with the rules at x=920. The misleading comment is
replaced by the geometry and the reason for it.

---

## Revision: two paths, a reordered index, and a diagram that overlapped itself

**Date:** 2026-08-19
**Result:** 1317 of 1317 verify checks, 2603 of 2603 page checks.

### 1. The stakeholders diagram

Three defects, all real.

- **The trunk ran through the centre box.** The vertical the three paths branch
  from sat at `RX[0] - 40 = 228`. The box's right edge is at `34 + 196 = 230`, so
  the line was two units *inside* the box. It now sits at `RX[0] - 28 = 240`, ten
  clear. Recorded as `TRUNK_GAP` with the arithmetic in a comment, because the
  next person to move either the box or the first column will need it.
- **"one requirement or recommendation" became "one recommendation"**, on two
  lines, because one line at that weight is wider than the 196-unit box and spilled
  out of both sides. The publisher's first step follows to "a recommendation,
  written once", since a centre box reading *recommendation* beside a step reading
  *requirement or recommendation* was inconsistent.
- **Legend and note removed.** The two shapes are a box and an arrow, both obvious
  in context, and the note repeated a sentence the surrounding prose already
  carried. Everything the legend said survives in the `<desc>`, which is what a
  screen reader gets and what a caption cannot replace. 730 units tall to **452**.

### 2. The index was explaining question 6 before saying there were six

`Why question 6 splits` sat at section 2 and the six questions are introduced in
the approach-cards section. So the page named question 6, and the 6a and 6b split,
before a reader had been told there were six of anything. Reordered:

1. Three stakeholders considered
2. Two paths for a hardening recommendation
3. The three approaches, and what each answers
4. Why question 6 splits: a claim is not a result

Section 4 now opens by saying which question it is about, and section 3's forward
reference points at 4 rather than backwards at 2.

Two assertions were dropped rather than repaired. Section 1 was rewritten by hand
into a shorter form that no longer carries "all three needs are real and can be
true at once" or "not which approach is correct". Both sentiments moved to section
2, where both paths are called viable and the site declines to choose, and that is
where they are now asserted.

### 3. Section 2 is two paths, not two questions

The question A and question B framing is gone. It was an accurate division but an
abstract one, and it never said what an implementer would actually do.

**Path 1, shift left.** The recommendation and its rule are written before any
assessment exists, so an implementer can use them, and the record of what was
applied belongs in the implementation layer. Two approaches take this path:

- catalog plus component definition, the rule as a control in a product-specific
  catalog and a component definition carrying the Config rule identifier and a
  control-implementation that satisfies it
- component definition plus validating component definition, the target state
  written once with several validation components standing for different runner
  engines, so one rule can be enforced through OPA, Kyverno, Azure Policy or
  another engine

**Path 2, write the rule and the check in the assessment**, with the outcome in
assessment results. Two models rather than three, and the rule and its check in one
document instead of two.

**The bridge is the check and the runner**, shared by both. The same automation can
serve an implementer analysing an environment and recording its state, or an
assessor producing a result, and neither is decided by which path is taken.

Vocabulary: **hardening recommendations**, not guidance, and "reusable" is dropped
throughout the section.

### On "much more straightforward"

Path 2 was described to me as much more straightforward than path 1. That is a
judgement, it favours the author's own approach, and the site does not carry it.
What the site carries instead is the fact underneath it: **two models rather than
three, and the rule and its check in one document instead of two.** A reader can
price that.

### Neither path is finished, and the section says so for both

Stated symmetrically, and the arrangement is deliberate:

- **Path 1**: neither approach publishes a system security plan, so the
  implementation-layer record the path depends on is not shown anywhere.
- **Path 2**: fourteen assessment plans, no assessment result beside them.
- **The only assessment result** in any of the three bodies of content belongs to
  an approach on **path 1**, and it carries one observation, no findings, and fields
  that are proposed rather than released.

That last fact is the one worth keeping. The assessment path has no assessment
result, and the only one that exists sits on the other path. A framing that put the
assessment layer on one side and left it there would have hidden it.

### Assertions added

Twelve, replacing the twelve that tracked the retired vocabulary: both paths named
and both called viable, path 1 identified as written before an assessment exists,
path 2 as rule and check in the plan, all three approaches placed on a path, the
reason a validating component definition is repeated per engine, the check and
runner named as shared and not decided by the path, the same automation serving
implementer and assessor, what each path is missing stated for both, the one
existing result placed on path 1 and qualified, and the choice left open.

---

## Revision: each option as a three-step chain

**Date:** 2026-08-19
**Result:** 1317 of 1317 verify checks, 2612 of 2612 page checks.

Section 2 described the two paths but not the pattern inside them. Every option
answers the same three questions in the same order, and the section now renders
that rather than describing it:

| | Rule | Check | Response |
|---|---|---|---|
| **A** | a control in a product-specific catalog | a component definition | the system security plan |
| **B** | one component definition | a second, of type validation | the system security plan |
| **C** | an activity and a step in the assessment plan, in prose | a step beneath that activity | assessment results |

Three rows rather than three columns: at a pillar's width three side-by-side boxes
leave about 90px each and the model names do not fit. The row accent reuses the
question palette, so the rule is question 1, the check is question 3 and the
response is question 6, and a reader who has met those chips elsewhere meets the
same three colours here.

Option B carries the worked example: one component definition of Ubuntu hardening
rules, then one validation component definition for OPA and another for Ansible,
with the target state written once and each validation component standing for a
different runner engine.

### The response step is unpublished for all three, and every row says so

This is what the chain made visible, and it is the reason the pattern was worth
rendering. No system security plan exists in any of the three bodies of content, so
neither path 1 option has published the artifact its response step names. No
assessment result exists in the path 2 corpus either. Every response row carries
the same dashed annotation, because marking one and not the others would be an
argument made in a channel a prose review does not read.

The fact that survives from the previous revision still holds and still cuts across
the paths: the only assessment result anywhere belongs to an approach on path 1.

### Equal shape, checked rather than trusted

Option A's check row originally carried a clause the other two carried in their
example note, so its chain read twice as long as theirs. The clause moved to a note
and all three now have the same shape: a label, a three-row chain, an example note.
Chain rows are 6/6/10, 3/9/10 and 11/9/10 words.

`pagecheck.js` now asserts the structure rather than the prose, because here the
structure is the content. It requires three options, each with exactly three rows
labelled Rule, Check and Response in that order, and each response row carrying the
unpublished annotation. A rewritten sentence can no longer drop a step.

---

## Revision: retitled, and the guidance read as input is now on the page

**Date:** 2026-08-19
**Result:** 1334 of 1334 verify checks, 2625 of 2625 page checks.

### The corpora moved, and eight extractions broke

Before anything else: the working copy was reorganised into publisher folders,
`Easy Dynamics/DISA/...` and `Easy Dynamics/Center for Internet Security/...`, and
a `Hardening Guides/` tree was added carrying the publishers' own source material.
Eight snippet sources and four hardcoded globs broke at once.

The paths are remapped, but the durable fix is that **corpus discovery is now by
OSCAL root key rather than by folder name**. `oscal_files()` and `ez_plans()` walk
the tree and keep documents whose single root key matches, so the next
reorganisation costs nothing. That also keeps non-OSCAL material out: the CIS
benchmarks ship as XCCDF-derived JSON with a `Benchmark` root and sit in the same
tree, and a path-based glob had begun counting them as assessment plans.

### Retitled

**Automating Technical Hardening Guidance with OSCAL**, across 14 files: every
`<title>`, the header, `og:site_name`, the Twitter card, the shell template, the
page generator and the README.

### The guidance read as input

A table in the introduction, one row per publisher, rendered from
`data/sources.json`:

| Publisher | Guidance | Source form held | Read as OSCAL |
|---|---|---|---|
| Center for Internet Security | Ubuntu 24.04 LTS and PostgreSQL 18 Benchmarks | XCCDF-derived JSON, and the PDF | two assessment plans |
| DISA | Nine STIGs: Ubuntu 22.04 and 24.04, RHEL 8 and 9, Windows Server 2019, 2022 and 2025, PostgreSQL 16, EPAS | XCCDF XML | nine assessment plans |
| CISA | BOD 25-01, the SCuBA baselines | none held in this working copy | three assessment plans |
| AWS | Security Hub security best-practice controls | published as OSCAL by the publisher | one catalog of 452 controls across 77 groups, and 230 component definitions |

Naming these four is consistent with the no-organization rule, which bans the two
approach proponents that are not guidance publishers. CIS, DISA, CISA and AWS were
already named on six pages between them.

**`verify.py --sources` recomputes every count**, sixteen checks. A row claiming
two assessment plans must have two. The CISA row claims no source material is held,
so if a file ever appears the row is wrong rather than the corpus. And every plan
in the corpus must be accounted for by some row, so a publisher cannot appear in
the tree without appearing in the table. `--sources` is listed on the methodology
page in the same position it occupies in `PHASES`, because the page prints that
list and a check compares the two.

### Repairs to hand edits in section 2

- **Three response rows had lost their closing tags.** `<span class="chain__where">`
  and its `<li>` were left open and the `<ul>` closed over them, which swallowed the
  rest of each row. Clearly mid-edit breakage, now closed.
- Two typos: "corresponding c heck is put it in front of" and "environemtns".
- The OPA and Ansible example was restored on Option B, since it was the worked
  example asked for two revisions ago.

### One thing restored deliberately, and it is reversible

The closing paragraph carrying **neither path has been carried through end to end**
and **this site does not choose between them** had been removed. Those are not
decoration: three of the thirteen editorial rules require them, the methodology
page publishes those rules, and `verify.py` enforces them. Removing them silently
would have made the site's own published policy false.

It is back as **one** paragraph rather than the previous two. If it should go, the
rule it serves should be amended on the methodology page in the same change, so the
site and its stated policy stay in step.

The per-row "unpublished" markers were not restored. They were mine, they were
clutter, and the fact they carried is in that paragraph for both paths at once.
Their assertions moved rather than the markers coming back.

### Open, and not mine to settle

Option C's example note now reads, in the site's own voice: *"assessors do not rely
on system owner defined hardening guidance to conduct assessments. They will bring
their own assessment capabilities, independent of any features available through
the system."*

That is an argument for path 2, unsourced, on a site whose rule is consequences
rather than verdicts, and path 2 is the author's own approach. It is exactly the
pattern three cold audits flagged. Either it wants a source, or it wants rewriting
as a consequence, or the note belongs on the assessment-first page as a proponent
claim rather than in the site's voice. Left as written, flagged here.

---

## Revision: the source documents are in the site, linked with media-type icons

**Date:** 2026-08-19
**Result:** 1343 of 1343 verify checks, 2634 of 2634 page checks.

`sources/` now holds **31 documents, about 48 MB**, and every row of the table in
the introduction links its own files with an icon per media type.

| Publisher | Files | Types |
|---|---|---|
| Center for Internet Security | 6 | 4 JSON, 2 PDF |
| DISA | 22 | 9 XML, 9 JSON, 4 PDF |
| CISA | 3 | 3 JSON |
| AWS | linked, not copied | one outbound link |

Each publisher's cell groups its files as **Source** then **OSCAL**, so a reader can
see what the publisher wrote and what was read from it without reading the paths.

### On the CIS material

I first split the copy and held CIS back, because the Benchmark's own Agreed Terms
of Use say a user may download and print a Benchmark but may not redistribute one or
post it, or any component of one, on any website, internal or external. That text is
in the Benchmark JSON and it is unambiguous on its face.

You then confirmed that CIS is a stakeholder receiving this brief, that the work is
being done with them on how their guides should sit in OSCAL, and that copying and
linking infringes nothing. So the material is in, and the terms line on those files
records the basis rather than implying a general grant: *"Reproduced here with the
publisher's participation in this review. The Benchmarks carry CIS's own Agreed
Terms of Use; consult the publisher before reusing them elsewhere."*

Worth keeping in view: the basis is that relationship, not the printed terms. If the
site is ever mirrored or forked by someone outside the conversation, that sentence
is what tells them to ask first.

### The icons

Four glyphs, drawn as inline SVG markup with the type lettered on the page outline:
XML, PDF, JSON, and an arrow leaving a box for the one outbound link. No font, no
request, `currentColor` so they theme automatically.

Two things learned building them.

**Created SVG nodes render nowhere in the page-check harness.** The first version
used `document.createElementNS`, which the shim does not implement, so the renderer
threw and the whole table vanished while reporting only a generic load failure. Every
other SVG on this site is injected as a string; these are too now.

**The icon's letters land in `textContent`.** Because the type is SVG text inside the
link, the accessible name concatenated to `…v1.0.0.jsonJSON, 1.0 MB` and no word
boundary survived, which is why the first version of the assertion failed on all 31
links at once. The icon is `aria-hidden`, the anchor carries its own `aria-label`, the
type and size are in a `.filelink__meta` span the assertion now reads, and the icon
is `user-select: none` so a copied selection does not pick up the prefix.

### Verification

`--sources` grew from 16 checks to 24, and the two that matter run in both
directions: **every link resolves to a file on disk**, and **every file under
`sources/` is linked by some row**. A document sitting there that no row reaches is
worse than a missing one, because nothing on the page admits it exists. Sizes, media
types and SHA-256 digests are read from disk by `tools/sources_files.py`, and
`--check` makes regeneration a no-op so a stale figure cannot reach the page. A
publisher with no files must carry a stated reason, which is what keeps the AWS cell
from reading as an oversight.

`tools/sources_files.py` refuses to run if `sources/` holds a folder or an extension
it cannot label, rather than emitting a link with no media type and no terms.

---

## Revision: the table lists inputs only

**Date:** 2026-08-19
**Result:** 1348 of 1348 verify checks, 2638 of 2638 page checks.

The OSCAL representations are published elsewhere, so the introduction lists only
the documents read as input. 31 files became **17 documents, about 29 MB**.

| Publisher | Documents read | Types |
|---|---|---|
| Center for Internet Security | 4 | 2 JSON, 2 PDF |
| DISA | 13 | 9 XML, 4 PDF |
| CISA | none held | reason stated |
| AWS | none held | reason stated, with a link |

The per-publisher grouping into Source and OSCAL is gone with it; the list is flat
because there is only one kind of thing in it now. The column reads **Documents
read**, and the fourth column is **Read into OSCAL as** rather than **Read as
OSCAL**, which was starting to imply a link the table deliberately does not carry.

### Excluded rather than merely unlisted

`sources/oscal/` is named in `EXCLUDE` in `tools/sources_files.py`, with the reason
recorded in `data/source-files.json`, and it is in `.gitignore` so it cannot ship
even if a working copy still holds it. Three checks enforce the distinction:

- every exclusion states why it is excluded
- no excluded path is linked from the table
- every listed document has kind `source`, so an output could not appear as an input

An unlisted folder would have looked like an oversight. A declared one is a decision
that the harness can hold.

### Two publishers now have no documents, and both say why

Removing the OSCAL left CISA with nothing, because no copy of the SCuBA baselines
themselves is held here. AWS has nothing for a different reason: that publisher
ships its guidance as OSCAL already, so there is no separate source document to
hold, and the published content is linked rather than copied.

Both appear as **Not held here** with the reason in the cell. The check that every
publisher has either documents or a stated reason is what stops either from reading
as an oversight.

### An inaccuracy this caught

The introduction had said *"every extract on this site comes from one of these files
at a declared pointer."* That was never true and is now plainly false: the extracts
come from the OSCAL, not from the PDFs and XCCDF. It now says the opposite in terms,
and three assertions hold it there, because a table of documents on a site full of
OSCAL extracts otherwise reads as the source of those extracts.

### For local cleanup

The sandbox cannot delete inside the mounted folder. `sources/oscal/` is still on
disk, 14 files and about 18 MB. It is excluded from the build and from git, so it is
harmless, but it is dead weight in the working copy and can be deleted by hand.

## Revision: one row per benchmark, and the documents as icons

The table listed one row per publisher, which put nine STIGs behind the word
**DISA** and made the reader open nine files to find the RHEL 9 one. Four changes,
all of them the same change: make the table describe the corpus at the granularity
a reader recognises, and keep a row to one line.

### One row per benchmark or guide

`data/sources.json` now has thirteen rows: two CIS Benchmarks, nine DISA STIGs,
CISA BOD 25-01, and the AWS Security Hub controls. Each row names its publisher,
the guidance, the release read, and what form of it is held.

Counts are per publisher and rows are per benchmark, so the two are held apart in
the data. `rows` is what the reader sees; `publishers` carries the source counts,
the OSCAL form, the OSCAL counts and the derivation, which is what
`verify.py --sources` recomputes against the corpora. Nothing was dropped to
remove the column, and the arithmetic still runs on the same numbers.

### Center for Internet Security is CIS

Everywhere else on the site the publisher is CIS. The full name is kept in
`publishers.cis.full_name` and rides on the cell as its `title`, so shortening it
stays a display choice rather than a lost fact. Two assertions: the table says CIS
and not the full name, and the full name is still on the cell.

### The release, beside the name

A row that says **Ubuntu 24.04 LTS STIG** names a moving target. V1R5 is not the
same document as the same STIG a year later, and the row would still look correct.
Each row now carries the release, and `verify.py` fails if a row's release does not
appear in the filename of a file that row links. That is the one error in this
table a reader cannot catch, because both look right.

### Read into OSCAL as, removed

The column is gone from `columns` and no row carries an `oscal_form`. Two checks
hold it out: the column is not in the declared columns, and no row carries the
field. The OSCAL written from this guidance is published separately, which is what
the footnote says.

### Filenames off the page, icons on it

A file link is now its media-type icon and nothing else. Nine STIG filenames
stacked in a cell were what made rows three lines deep. The filename, media type
and size ride on the link instead: `title` for a pointer, `aria-label` for a
screen reader, and both carry the same three facts, so nothing a sighted reader
can hover for is withheld from anyone else. `download` is what makes the icon do
what it looks like it does, rather than opening a 10 MB PDF over the page.

On paper an icon cannot be clicked, so the print stylesheet prints
`content: attr(title)` in place of the glyph.

### One line per row, asserted in two places

`white-space: nowrap` on the cells is only half of it: white-space does not govern
flex items, so a squeezed column would have wrapped four icons onto two lines and
put the row back where it started. `.filelist` is `flex-wrap: nowrap` as well, and
`verify.py --css` asserts both. `.table-wrap` scrolls rather than letting a cell
reflow, and the print stylesheet reflows rather than scrolling, because nothing
scrolls on paper.

Two cells were trimmed to keep the table inside the reading column: the CISA row
reads **BOD 25-01, the SCuBA baselines**, with the full name in the note directly
below it, and the Ubuntu 24.04 row reads **three release notes**.

### What could not go in a row

Two kinds of thing need a sentence, and a sentence does not go in a one-line row.
Both moved under the table:

- `U_Readme_SRG_and_STIG.pdf` is about the STIG and SRG packages as a set, not
  about any one guide. Filed into a row it would have to be repeated across nine
  of them or put in one arbitrarily, and both would misdescribe it. It is declared
  in `general` in the data, and `verify.py` requires it to be linked and to belong
  to no row.
- The CISA and AWS reasons for holding nothing. Their rows say **See below**, and
  `pagecheck.js` asserts the reason is under the table and not in a row.

### Every file reaches its own row

`tools/sources_files.py` now assigns each file a row by filename, from an explicit
`GUIDANCE` list, and a file matching zero patterns or two is a build error rather
than a silent choice about which row it lands in. Five checks: every file names a
row, every row exists, no file is filed under another publisher's row, every row
with no documents belongs to an excused publisher, and, in `pagecheck.js`, every
row links exactly the number of documents the data gives it.

## Revision: the table closes, the notes go, and the icons get big enough to read

Five changes to the introduction's table, from one review.

### The block under the table is gone

Under the table sat a run of small grey paragraphs: what the STIG readme was, why
CISA's baselines are not held here, why AWS's are not, and two footnotes. It
followed no format the rest of the site uses, it repeated what the row already
said, and it was the first thing on the page after the lede. All of it is
removed. What it carried is now carried by the table:

- the STIG and SRG readme has a row of its own, because it was read as input and
  a row is the only home a document has now
- the CISA and AWS rows say **None held here** and **Published as OSCAL, and
  linked** in the source column, and link the publisher instead of explaining

`data/sources.json` lost `general`, `caption` and `footnote`. `pagecheck.js`
asserts that no `.sources__aside` survives and that the table holds every link in
the block, so the notes cannot come back by accident.

### The publishers' own pages, linked

Two rows had nothing to download, and a row with nothing in its last cell is a
claim with nothing behind it. Both now link the publisher:

- CISA: the BOD 25-01 page at cisa.gov
- AWS: the Security Hub guidance at aws.github.io, and the same controls as OSCAL
  in the awslabs repository, which is what was actually read

`verify.py --sources` asserts every row carries a document or a link, that every
link is https with a label, and that those two publishers' rows link the
publisher rather than explaining an absence.

### Closed until it is wanted

Fourteen rows of provenance is reference material, not the argument, and open by
default it pushed the argument below the fold on the one page a newcomer arrives
at. The table is now a `<details>` closed on load, in the same visual grammar as
`.panel`: a caret, a title, a line saying what is inside, and an Open hint that
becomes a minus.

Two things follow from choosing `<details>` rather than a script. It is keyboard
reachable and announced with no code of ours, and the print stylesheet opens every
disclosure on this site, so a printed page is still the whole document. There is a
check for the second, because a disclosure print leaves closed would drop the
whole provenance table from the one thing this site prints for.

The `<caption>` is gone, since the summary names the table; the table keeps an
`aria-label` so it still has a name of its own when open.

### The icons were too small to read

They were 19px, with the type lettered inside the page outline: three characters
in about 11 units of a 20 unit box, which at that size was a grey smudge. The
drawing now reverses the type out of a filled badge that overhangs the page on
both sides, which buys about 70% more width for the same icon and reads as a
shape before the letters resolve. The icon is drawn at 27px in a 40px hit area,
because it is the whole link and there is no text beside it.

`.micon__badge` fills with currentColor and `.micon__label` fills with `--bg`, so
the pair inverts cleanly in both themes and its contrast is the accent-on-page
pair that `--a11y` already checks. A check asserts the two rules stay a pair: a
badge with no fill, or a label the same colour as the badge, and the icon says
nothing at all.

### A globe for a link, drawn in straight lines

Guidance that is a page rather than a document gets a globe rather than a file.
The first drawing used two bezier meridians, and `tools/svgrender.py` does not
implement `c`, so the rasteriser drew a wedge: the glyph would have rendered
correctly in a browser and been unverifiable here forever. The meridians are now
a diamond of straight segments, which reads the same at this size and keeps the
icon inside the subset that can be rasterised and looked at.

`verify.py --sources` now asserts every icon path uses only `M L H V Z`, so the
next bezier fails the build rather than quietly leaving the icons uncheckable.

### Every link opens in a new tab

A reader following a source is not done with the page they left. Every link in
the table carries `target="_blank"` and `rel="noopener"`, and every web link tells
a screen reader that it opens in a new tab. Both are asserted.

## Revision: four removals, a table that sits straight, and sixteen retired checks

### The legend under diagram 76 is gone

It named the 6a and 6b chips, the assembly box and the resolved reference, and
then added a sentence of argument. The drawing labels all four in place: the
chips carry "6a" and "6b" beside the words Implementation claim and Assessment
result, the boxes carry the assembly names, and the table underneath states the
six differences in words. A legend that renames what the drawing has already
said in full is a second thing to read for no more meaning, and it was the
longest block in the section. The drawing is 278 units shorter for it.

### The six differences table sits straight now

Every line is centred between the rule above it and the rule below. It was not,
and that was the whole of what looked wrong: a row advanced by `20n + 10` and set
its first baseline at the top of its band, so the ink sat hard against the rule
above with about fifteen units of space below it. Six rows of that and every line
looks to have slipped upward out of its box.

Text set at a fixed offset from one edge of a variable-height band is never
centred in it. The offset has to be computed from the height, which is what the
loop does now: `LEAD` between baselines, `ASC` and `DESC` for the ink around a
baseline at 16px, and `PAD` for what is left, applied equally above and below. A
cell with fewer lines than the tallest cell in its row is centred on its own, so
"fails when" lands between the two lines beside it rather than beside the first.

### Two sentences removed

The figure caption under diagram 76, which said what the drawing's own labels
say, and the note under the three approach cards about
option-letter order. Each card carries its own option letter, so the order is
visible rather than asserted, and the same sentence still appears on five other
pages. Six statements of one convention is five more than it needs.

### Sixteen checks retired

The page was rewritten in the author's own voice between builds, and sixteen
assertions no longer matched it. They were retired by decision rather than
worked around, and each is recorded in `tools/pagecheck.js` at the point where it
stood, with what it required and why it was there. The four groups:

- **The introduction's provenance, three checks.** That three publishers ship a
  document and the fourth ships OSCAL, that the OSCAL is published separately,
  and that the extracts elsewhere on the site come from that OSCAL rather than
  from the documents linked here. An earlier revision had claimed the opposite in
  terms, and these existed to stop it coming back.
- **Section 2's neutrality, seven checks.** That both paths are named, that
  neither has been carried through end to end, what each is missing, that the one
  published result belongs to an approach on the implementation side, that the
  site does not choose, and the worked example of one Ubuntu rule set with an OPA
  validation component and an Ansible one. Three cold audits of this section
  found the same failure mode each time, and this group was the answer to it.
- **Section 1's wording, two checks.** That the statement is called a requirement
  or a recommendation, never one alone, and that the page says why both words are
  used.
- **Section 3's empty cells, four checks.** That an unanswered question is not a
  defect, the clearest instance of one, that the rows do not add up, and that the
  three kinds of unanswered are one fact with three reasons rather than three
  degrees of severity.

What still holds on that page: nobody is named, no proponent organization is
named, both paths are called viable, the three chains each run rule then check
then response, the bridge is shared, the strips are in option-letter order at one
size with a legend naming every state, and no page claims an alphabetical
ordering it does not use.

### Three repairs alongside

- The contents list and the section 2 heading had drifted apart. The list now
  carries the heading verbatim, which is what the check compares.
- `</strong><em>whether</em></strong>` in section 4 was missing its opening tag.
- Two typos in `data/six-questions.json`: "in a a software component" and "validation
  component component definition". Fixing the second brought the three one-line
  summaries to 18, 18 and 17 words, inside the ten per cent equal-budget rule
  they had fallen outside of at 19, 20 and 17.

## Revision: three pages removed, and the six questions moved to the start page

The primer duplicated the start page. It opened with the same problem statement,
introduced the same three stakeholders, and routed to the same places, and a
reader arriving at the site had to read two pages to learn one thing. It is
removed. The methodology page and the data-quality page are removed with it.

Eleven pages, now eight.

### The six questions moved, and are now listed where they are promised

The primer's part 1 was the only place on the site that listed all six questions
with their definitions. Every other page used the names as column headings. So
the site promised "six questions any of them has to answer" and then let a reader
meet Rule, Control link, Check, Subject, Runner, Claim and Result for the first
time as table headers, with nothing having introduced them.

That list is now section 3 of the start page, between the two layers and the
three approaches, which is where the page first names the six and where it used
to name them twice without listing them once. Sections 3 and 4 became 4 and 5.
`data-question-list` and the `.qlist` styles moved with it unchanged, so the list
is still one render from `data/six-questions.json`.

`pagecheck.js` asserts it: one term per question, six of them, every one numbered
and named, no question missing from the list, and the section still says why two
of the six have a follow-on, because the eight-row comparison table comes later.

### What went with the pages

- **Twelve renderers** in `assets/site.js`, about 450 lines: the primer's cited
  figures and SC-28 walkthrough, the four appendix renderers with their
  `statSpan` helper, and the six methodology renderers. Their boot dispatch lines
  went with them. `renderSc28Panes` stays, which is the comparison page's own
  component and a different thing.
- **Two CSS blocks**, `.dq*` and the methodology block, and `main .rules` from
  the reading-measure selector list.
- **Two data files**, `data/methodology.json` and `data/data-quality.json`,
  26 KB and 16 KB. Both were exclusive to their page.
- **Two verify phases.** `--appendix` recomputed the data-quality page's
  arithmetic; `--methodology` held the thirteen editorial rules against the
  development plan and checked the correction log. Seventeen phases now.
- **Two pagecheck functions**, `checkPrimer` and `checkAppendix`. `sentences()`
  was declared for the primer and stays, because `checkCompare` counts sentences
  too.
- **Three nav entries**, on every page, in `assets/shell.html`, and in the `NAV`
  list in `tools/approach_pages.py`.

### Coupling the removals exposed

The methodology page published `PHASES` in order, and `check_methodology`
compared the page against the dict, so reordering the phases silently made the
page wrong. That coupling is gone with the page, and the comment recording it is
replaced by one recording that it existed.

The `verbatim` class had exactly one user, the methodology page's reproduced
rules, and `check_methodology` asserted that. The exemption it carries is a rule
about markup rather than about that page, so the branch in `pagecheck.js` stays
and says why it is now unreachable.

### Claims left dangling, and repaired

Deleting a page leaves sentences elsewhere that describe it. Each was rewritten
rather than left:

- `data/six-questions.json` said counts appear "in one place and for one purpose: the
  data-quality appendix". Now: a count is only reported beside its denominator.
- `data/views.json` explained a merge by reference to what "the primer used to
  state separately".
- `questions.html` and the three approach pages each carried a paragraph pointing
  at the appendix. The approach-page one was generated, so the generator was
  fixed rather than the three pages.
- `CORRECTIONS.md` offered proponents three things to correct, the third being
  their four appendix items.
- The `README` phase list, data inventory, editorial-policy section, rule 5
  departure note, contribution steps, page count and check count.

The one thing genuinely lost rather than moved: the editorial rules are no longer
published on the site. They remain in section 3 of the development plan, and the
README says so.

## Revision: question 2b removed

The framework asked eight things in six questions. Two had a follow-on: question
2 had 2b, whether a third party can add the control link after publication
without touching the rule, and question 6 splits into a claim and a result.

2b is gone. Six questions, seven rows.

### Why it was there, and why that was not enough

2b existed to separate "can be tied to a control" from "can be tied by someone
else, later, without cooperation". The distinction is real and it matters to the
requirement the site was built around: the tie must be available and must not be
mandatory. Only late, external binding delivers that in the strict sense, because
a tie authored with the rule is a cost of publishing borne by a publisher who may
have no framework in view.

What made it a bad row is that its answer follows from the contested premise
rather than from anything an approach chose. `mapping-item.type` is closed by
`allOf` to `control` and `statement`, and `mapping-item` carries no `uuid` and no
`href`, so late binding reaches a rule only where the rule is already modelled as
a control. Catalog-first therefore scored filled and the other two scored absent,
and the site had to print a disclaimer under its own cell saying the point was not
an advantage. A row that needs a disclaimer to be read correctly is doing its work
in the wrong place: it was scoring a property of the OSCAL mapping model as though
it were something an approach answers.

### What was kept

The analysis, all of it. It was never dependent on the row:

- Section 2.3 of the six questions page, what `mapping-collection` can and cannot
  reach, with the six-home reachability table and the schema extracts.
- The three claims that hold under all three readings: the mapping model encodes a
  position on what a rule is; if rules are not controls, OSCAL has no late-binding
  mechanism at all; and the remedy is small and requires no content to move.
- Section 4 of the open questions page, which puts the remedy to the group as a
  question with the counter-argument beside it.
- The third column of diagram 77, three binding times and who can use each.

The availability the 2b cells carried moved onto question 2's own binding-times
entry in `data/six-questions.json`, as `available_to` plus the reason. Diagram 77 reads
it from there. That is the same fact attached to the mechanism it is a fact about
rather than to a row in a matrix that scores approaches.

`verify.py` now asserts the disclaimer where it actually lives, on the page, along
with the binding-times record and the reason the other two readings cannot reach
late binding. The check that used to require each approach page to carry a pointer
to the 2b row went with the callout that pointed at it.

### The count, in eleven places

Seven rows rather than eight, and one question splits rather than two. The
matrix caption, the answer-strip note on the three approach pages, the board's
grouping comment, the question-list heading logic, the manifest's slot vocabulary,
the `--slot-2b` palette tokens in both themes, three diagram descriptions, the
kitchen sink's slot list, and the assertions in `verify.py` and `pagecheck.js`.

Two of the counts in `pagecheck.js` are now derived from `data/six-questions.json`
rather than written down: the matrix had eight rows and twenty-four cells hard
coded in two places, which is exactly the kind of number that survives a change
like this one and starts lying.

## Revision: the glossary page removed

Seven pages now. The vocabulary is not gone: `data/glossary.json` still drives
every term card on the site, and a card carries the whole of what the page held
for one term, which is why removing the page cost nothing a reader could use.

### What a term card already had

The `.dfn` component renders a term, its status, the usage this site adopts, and
the other usages in play, on hover and on focus, wherever the term appears. The
card used to end with a link reading "Full entry", pointing at the term's anchor
on the glossary page. There was no fuller entry: the page rendered the same four
fields from the same file, plus a filter box. So the link went from a card to a
longer copy of itself, and it is gone.

### The four prose links

Four sentences pointed a reader at a term anchor on the page. Each now names the
term as a card instead, so the definition arrives where the sentence is rather
than one navigation away:

- the six questions page, on assessment platform and on rule
- the comparison page, on rule
- the open questions page, on capability

`verify.py --links` used to synthesise the page's anchors from `glossary.json`,
because a renderer produced them at load time and they were never in the markup.
Nothing links to a term anchor now, so that synthesis is gone with the check that
needed it.

### Removed with the page

`renderGlossaryList` and `termAnchor` in `assets/site.js`, 147 lines, and the
`.glossary*` block in the stylesheet, 23 lines. `checkGlossary` in
`tools/pagecheck.js`, 67 lines, and its dispatch entry. The `.dfn` and
`.dfn-card` component stays, and `pagecheck.js` still asserts on every page that
every term card names a term the data defines and that a renderer-made card fills
when it is clicked.

## Revision: the JSON in the matrix, at the lines that answer the question

The matrix said what each approach does about each question. It now shows it, in
a file, on the lines where it happens.

### The construct and the note are no longer behind a link

They are the answer, so they are read without opening anything. Only the JSON is
behind the link, and the link now says what it opens: "Show the JSON". Three
columns of JSON open at once is the one thing that makes this table unreadable,
which is why that stayed collapsed and the prose did not.

### Line numbers are computed, never typed

`tools/example_pointers.py` carries one entry per question per approach: a file,
a JSON pointer, and one sentence saying what the reader is looking at. The line
span is not in that entry. It is computed by re-serialising the document and
walking it, recording the first and last line of every pointer as it goes, and
the walk asserts that what it produced is byte-identical to the file on disk. If
the two ever diverge the tool exits rather than emitting numbers that describe a
document nobody has.

`verify.py --example` then slices each file at the recorded span and parses the
slice back. A span off by one line stops parsing, which is exactly the failure a
hand-maintained line number produces silently.

### What question 1 shows

- catalog-first, `catalog.json` lines 23 to 74: the rule is a control, with an
  id, a title, a statement part, and a parameter for the value.
- component-first, `component-definition.json` lines 42 to 87: the rule is an
  implemented requirement on the component, with the rule identity and the
  desired state as props.
- assessment-first, `assessment-plan.json` lines 23 to 111: the rule is an
  activity, in prose, with steps carrying the work.

### What question 2 shows, and what it cost

- catalog-first, a document of its own: `mapping-collection.json`. The rules are
  controls, so the tie is control to control, which is what
  `mapping-collection` does and the only thing it does. One document per control
  framework: this one says nothing about any framework other than 800-53.
- component-first, no extra document. The `source` names the framework catalog
  and each implemented requirement names the control by id, so the tie is the
  requirement.
- assessment-first, `related-controls` on the activity, beside the rule.

Adding the mapping document made the sets six, five and two, and that asymmetry
is now what question 2 costs rather than a sentence claiming it.

Getting `mapping-collection` to validate took four passes and taught three
things the schema does not advertise: `mappings` is a single object rather than a
list, `relationship` is a token rather than an object, and `provenance` is
required with `method` closed to human, automation or hybrid, `status` closed to
complete, not-complete, draft, deprecated or superseded, plus a
`mapping-description` and a `matching-rationale`. A mapping that does not say who
made it and how is not a mapping this model accepts, which is a point in its
favour and a cost of using it.

### The code surface does not follow the theme

Five new tokens, `--code-bg`, `--code-fg`, `--code-dim`, `--code-focus` and
`--code-rule`, with identical values in both theme blocks. The JSON is an
artifact rather than page content, and a code block that inverts when the reader
flips the theme reads as prose. They are written twice rather than inherited
because `--a11y` resolves tokens per theme and a token defined in one block only
is missing from the other; a check asserts the two definitions stay identical.

Contrast is measured against `--code-bg` rather than `--bg`, since nothing here
is ever drawn on the page. Lit lines 15.3:1, dimmed context lines 5.7:1, lit
lines on the lifted background 12.7:1. The dimmed lines are held to AA rather
than to the 3.0 a decorative rule would take, because they are still lines a
reader reads.

### Asserted rather than intended

`pagecheck.js` now checks, on every page carrying the matrix: every cell shows
its construct and its note outside the part that opens, the link says it opens
the JSON, there is one view per cell, every view names its file and its pointer
and says which lines, every view numbers its lines and lights the ones it points
at and dims the ones around them, every view says the example is authored rather
than published, and no view is a dialog. Plus the three files question 1 lands
in, in order, and that question 2 lands in a mapping document for catalog-first.

## Revision: the JSON leaves the table

The JSON was rendered inside a matrix cell. A cell is a quarter of a four-column
table, so every line wrapped or scrolled sideways and a reader saw about thirty
characters of a document whose lines run to eighty. No amount of styling fixes
that. The container was the problem.

So the JSON came out of the table. One panel, below it, taking the whole reading
column, aimed by whichever cell link is pressed.

### Why one panel and not one per cell

Three columns of JSON open at once is three narrow columns again. So the panel
carries its own row of approach buttons, each labelled with that approach's
construct, and a reader comparing the three on one question switches between
them in place at full width. That is the drill-down: the table says what each
approach does, the panel shows one at a time in enough width to read it.

The cell link and the panel are two views of one state. The link carries
`aria-controls` and a pressed state rather than `aria-expanded`, because what it
opens is shared and only one cell can own it. The owning cell is outlined, its
link reads "Showing the JSON", and pressing it again closes the panel. Focus
moves to the panel's heading on open, because the content appeared somewhere
other than where the reader clicked.

The published extracts stayed in the cell. They are a different claim: what a
publisher shipped, rather than what this example makes of it.

### A mistake worth recording

Two edits in this revision were made by scripted string slicing rather than
through a bounded replacement, and both went wrong.

In the stylesheet the end boundary sorted before the start, so instead of
replacing a block the script duplicated a hundred lines. That was caught by
counting selectors and repaired.

In `tools/pagecheck.js` the end boundary was `"  }\n\n  const two = textOf("`,
which first occurs several hundred lines further down the file, inside
`checkIndex`. The deletion ran all the way there and took `checkApproach`,
`checkSixQuestions`, `checkQuestions`, `checkIndex`, the `sentences` helper and three
section-list constants with it, about four hundred lines. The file still parsed,
so `node --check` reported nothing.

The per-page functions are not being rebuilt: the pages they checked are being
rewritten, and assertions written from memory of the old shape would either fail
on the new one or pass while checking nothing. What holds the site now is every
check inside `checkPage`, which runs on every page, plus the matrix and panel
checks, plus seventeen verify phases that were never touched.

The lesson is mechanical and worth stating: a bounded replacement in a source
file goes through an edit that fails loudly on an ambiguous match. A script that
computes its own boundaries by searching for a string will happily delete the
wrong range, and a file that still parses afterwards hides it.

## Revision: the JSON gets a page

Third attempt at the same problem, and the first one that is not fighting the
layout.

The JSON was in a matrix cell, where it had about thirty characters of width. It
moved to a panel under the table, where it had the column but pushed the table
around every time a link was pressed, and carried a row of approach buttons that
restated constructs the table had already said one scroll above. Neither is a
place to read a document.

So the document has a page. `example.html`, in the navigation as "Worked
example", one section per question, three anchored blocks per section, each with
the file, the pointer, the line range, one sentence of what to look at, and the
code at the full width of the column.

### The cell is a link now

Nothing in a matrix cell opens. The cell shows the state, the construct and the
note, and then one link, "See the JSON", pointing at
`example.html#q{question}-{approach}`. The reader lands on the lines. Nothing
moves, nothing expands, and the address bar carries where they were, which the
panel could not do.

The link text is identical in twenty one cells, so the accessible name carries
the question, the approach, the file and the line range. Without that a screen
reader hears "See the JSON" twenty one times.

### What the page does not do

It does not restate the matrix. The table already says what each approach does
about each question, and repeating the constructs on the walkthrough would be a
second copy of the same claim, one page apart, with nothing keeping them in step.
The page carries the JSON and the sentence saying what to look at, and that is
all. The approach buttons from the panel version are gone with it.

### Numbering, which the site's own checks required

Sections are numbered in sequence, one to seven, and each keeps its question
identifier on its chip. The two part company at 6a and 6b, which are the sixth
question and the sixth and seventh sections. Subsections are `n.1`, `n.2`, `n.3`
for the three approaches. Both are required by `pagecheck`, which asserts every
section heading is numbered, every subsection heading is numbered, and the
contents list says what the heading says.

### Asserted

`checkExample` walks the data and the page together: one section per question,
three blocks per question, every anchor a matrix link can name exists, every
block with a pointer shows the code and names its file and lines and lights
exactly the number of lines the pointer covers, and every block without one says
that nothing is written there. On compare.html: nothing expands, no JSON is
rendered anywhere on the page, every cell either links or says there is no JSON,
every link points at `./example.html#q...`, and questions 1 and 2 link all three
approaches in option-letter order.

## Revision: the six questions page is the grid and nothing else

The page had eight sections. Seven are gone. What remains is section 1, and
section 1 is now the grid: six questions down the side, three approaches across,
and in every cell what that approach does with a link to the example document
where it is done.

Section 5 was the reason. It carried the matrix, and section 1 carried a board of
six cards showing the same per-question answers a different way. One page, two
renderings of one thing, and a reader had to work out that they were the same.
The cards are gone and the matrix moved into section 1, which is what the page
was for.

### The link is named after the document

The cell link used to read "See the JSON", which was identical in twenty one
cells: nothing about where it went, and twenty one identical names for a screen
reader. It now reads the document's own file name, `catalog.json`,
`mapping-collection.json`, `assessment-plan.json`, with the file, the lines, the
question and the approach on the accessible name. The document name is the one
thing the cell does not already carry.

### What left the site with those seven sections

Recorded because some of it exists nowhere else now, and re-homing it is a
decision rather than an oversight:

- **The binding-times table**, three moments the tie to a control can be made
  and by whom, rendered from `data-binding-times`.
- **The cost of an empty tie**, the schema facts about what an observation can
  record and what a finding requires, from `data-tie-cost`.
- **The mapping-collection reachability analysis**, the six-homes table, and its
  disclaimer that the constraint is a gap in OSCAL rather than an argument for
  the one approach it happens to suit. The question survives on the open
  questions page, put to the group with both sides at the same length. The
  analysis does not.
- **SC-28 followed end to end**, the one control traced through all three
  corpora.
- **Questions 4 and 5 in detail**, the six constructs in use across the three.
- **The three readings of what a rule is**, from `data-views`, and the working
  definition the site declared. Each approach page still states the reading it
  rests on, in full, since it no longer has a section to point at.
- **The automation argument**, from `data-automation`.

Ten renderers now have no page carrying their hook: `data-views`,
`data-binding-times`, `data-tie-cost`, `data-working-definition`,
`data-automation`, `data-board`, `data-models`, `data-readings`, `data-readers`
and `data-answers-row`. Ten diagrams are generated and shown nowhere: the three
72-six-questions drawings, the three 75-stakeholders variants, 71-layer-map-base,
77-optional-tie, 78-three-views and 79-scale. All of it is still built and still
checked; none of it is on a page.

### Repairs the deletion forced

Six sentences on four pages cited the removed sections. Each stated a fact and
then pointed at where the fact was set out in full, so each was rewritten to
state the fact and stop:

- the three approach pages, on the reading each one rests on
- catalog-first, on why an unanswered control link is a position
- component-first, on what an empty tie costs
- the comparison page, on the evidence for treating question 2 as optional
- the open questions page, twice, on the subject inventory and on the mapping
  consequence

Two verify checks were retired with the analysis they guarded, and the note in
their place says they come back if it is ever re-homed. The arrival-anchor list
for the page went from fifteen anchors to one.

## Revision: the corpora come out of the walkthrough

The three approach pages still argued from the published corpora. Catalog-first
carried a figure drawn from ACM.2 and an AWS Config rule, with a subsection
explaining the name match between a TechnicalControlId and a component title,
directly above encodings of two Ubuntu rules. A reader following the two rules
across the three pages met a different publisher's identifiers on each one.

### Four removals

**The join figure, all three pages.** It was drawn from whichever identifiers
each publisher shipped: ACM.2 and a Config rule on one page, a STIG V-number on
another. A figure whose labels change with the publisher shows the reader the
corpus when the point is the modelling. The three still sit together on the
comparison page, in one panel, framed as real identifiers from published files,
which is where a comparison of the join mechanics belongs.

**Section 5, "SC-28 followed end to end".** The first of the two rules the site
walks IS protection of data at rest, sc-28, so section 4 now follows it end to
end in all three shapes. The old section followed it through each publisher's own
content instead, which made the same point twice and dragged CloudTrail.2 and a
Config rule name into it. Seven sections now, not eight, and the subsection
numbers in sections 6 and 7 moved with them.

**The three 4.3.1 subsections.** One per page, each a description of a
publisher's own shipped content: the AWS name match and its two recomputed
figures, the three step conventions across the STIG, CIS and CISA plans, and the
component-first chain "in published content". All three are what the artifacts
page is for.

**Three dangling references.** Each removal left a sentence pointing at
something no longer there: "both are shown below" for the figure, "they are set
out below" for a subsection, and one that now points at the open questions page
where the four proposal questions actually are.

### One reordering, which was the real problem

Removing the figure exposed a contradiction the page had been putting side by
side without labelling it. Two different things get said about every question.
Our encoding says what this shape looks like when the two rules are written out
in it. The matrix cell says what this group's published content does about the
question, which for several questions is nothing. Both are true and they answer
different questions. Unlabelled and adjacent they read as one claim disagreeing
with itself: an encoding that models a subject, directly above a cell reading
"not modelled".

So the encoding now comes first, because it is what the page walks, and the
published position follows it inside a block headed "In the published content".
The per-question prose moved into that block too, unchanged: it was always a
description of what a group shipped, and it names publisher-specific things
because that is what it is about. Nothing was rewritten to achieve this. It was
moved and labelled, and every publisher-specific identifier inside section 4 now
sits inside one of seven labelled blocks per page.

### Two repairs to the harness, from data that changed under it

The STIG and SRG package readme no longer has a row in the sources table, so the
file had no home and two checks failed. It is now excluded by file rather than by
folder, with the reason stated in the data: it is about the packages as a set,
and a table of one row per guide has nowhere to put it. `verify.py` learned to
read exclusions at both granularities. The DISA row count went from ten to nine
with it, and the summary sentence check with that.

---

## Session: the claim and the result, from a published assessment result

**Date:** 2026-08-21
**Scope:** questions 6a and 6b for the assessment-first column, and the answer
state vocabulary that changed under them
**Result:** complete. 1137 verification checks and 927 page checks pass.

### What the published result actually says

A CISA BOD 25-01 assessment result was added to the corpus, so both halves of
question 6 were re-read against it rather than against an assumption.

It contains **no claim**. There is no by-component response, no implemented
requirement, no import of a system security plan: counts of all of them are
zero. It contains 128 findings, every one targeting an `objective-id`, 114
satisfied and 14 not; 128 observations, each naming the assessment activity that
produced it, the method and the time it was collected; and three risks. That
answers 6b, not 6a.

The claim is addressed in the **plans**, not the result, and by pointing rather
than asserting. `import-ssp` resolves to a back-matter resource, and the
published plans carry two shapes of that resource: one naming an OSCAL system
security plan, and one, marked `no-oscal-ssp`, holding a prose description of
the system for the case where no OSCAL one exists.

### Three cells moved

- **6a assessment-first**, from "not applicable by design" with no encoding, to
  partly answered. The encoding is the real pointer pattern, both resources
  included. Partly, because elsewhere in the corpus the same pointer is left
  unresolved, and that placeholder stays on the page as the evidence for the
  qualifier.
- **6b assessment-first**, from "absent, no stated position" to answered. The
  finding was retargeted from `statement-id` to `objective-id`, which is what
  the publisher's own result does for all 128 of its findings, and the
  observation the finding rests on is now shown in the same block, because the
  cell names both assemblies and a reader should not have to take the join on
  trust.
- **6b component-first**, wording only. It said it was the one corpus reaching
  an assessment result, which stopped being true when this one arrived.

### The vocabulary shrank, and three places had hardcoded it

6a assessment-first was the only cell using `empty-by-design`, so the state was
dropped, leaving one live empty state. The repo already had a check for exactly
this ("every declared empty state is used by at least one cell, or dropped"),
and it caught it. What it did not catch is that the state list was also written
out by hand in three other places: the stylesheet, two scripts, and the
verifier's own check. So the check demanded the presence of rules that nothing
could ever match.

All four now read `answer_states` from the data. The stylesheet carries a rule
only for a live state and `verify.py --css` fails if it carries one for a
retired state. The diagram legend draws a row per live state, on a question that
actually carries it. Geometry definitions for retired states are kept, keyed by
name, so a state coming back finds its geometry waiting, and a live state with
no geometry is a failure rather than a silent pass.

### One structural change to how a block may be shaped

Question 6a is answered once per rule by two approaches and once per document by
the third, because one pointer covers both rules. Printing it twice would assert
a difference that is not there. The comparability check, in both the verifier and
the page harness, previously demanded that all three columns carry the same rule
blocks. It now demands that each column be one of two shapes, both rules in order
or a single shared block, that the per-rule columns agree with each other, and
that a shared block say what it covers.

---

## Session: pros and cons at the top of every approach page

**Date:** 2026-08-22
**Scope:** section 1 of the three approach pages
**Result:** complete. 1375 verification checks and 954 page checks pass.

### What was built

Four gains and four costs per approach, in `data/tradeoffs.json`, rendered as the
opening section of each approach page. The section that used to carry this
argument, section 6, two boxes at the foot of the page, is gone rather than
duplicated: a reader met a thousand words of description before being told what
the thing is good and bad at. Each entry is analysis: claims about published
content need OSCAL example evidence, and claims about a model's constraints need
schema evidence. Neither kind of evidence establishes agreement with a strength
or risk as framed by the analysis.

### The block is where an asymmetry does the most damage

It opens all three pages and it is the only place on the site where the
approaches are weighed rather than described. So the shape is enforced rather
than reviewed. Exactly four of each, identical on all three pages. The two
columns within a page within 15 per cent of each other by word count, and the
three sections within 10 per cent of each other, both checked at build time and
again on the rendered page, because what a reader compares is what is on the
page.

The first draft failed its own check. All three pages argued their costs about a
fifth longer than their gains. That is a position taken in the word count, in a
place no reader would think to look for one, so the gains were argued out to the
same length rather than the costs cut back.

### What the fact-check found

Review of the draft against the three corpora and the OSCAL schemas found four
things worth recording.

**A claim can only be made against a component.** In a system security plan the
response is `by-component`, keyed by `component-uuid`, and it carries no subject
of any kind. The plan describes inventory items elsewhere, but nothing can
respond to a control against one, so two hosts of one component inside a
boundary share a single response. An assessment subject, by contrast, is typed,
and the vocabulary includes `inventory-item`. Both halves are now stored as
schema fragments and checked, along with the shared `metadata` assembly behind
the claim that a guide published as a catalog is versioned and citable.

**Three claims were wrong and two were backwards.** The catalog encoding
declared the password length as a parameter and then wrote fifteen into the
requirement text, so a profile could have set sixteen and left the statement
still saying fifteen; it now inserts the parameter. The component approach was
charged with skipping the assessment plan, which its own proposal addresses and
its sample ships. Its rule assembly was said to have no fidelity fields, when
the proposal defines `audit-procedure` and `remediation-procedure` and the
shipped rules simply do not use them. The published result was credited with a
lifecycle that does not resolve: its `import-ap` names a plan no file here
carries, and its observations type their subject as an assessment activity,
which is not a subject type.

**Six derivations described a corpus that had moved.** `ez_ar_files` was
recomputed over the assessment plans, so a list of plans was being asked how
many results it held, and could only ever answer none. It answered none for as
long as a result existed. Six derivation strings still said fourteen plans when
there were fifteen, and one label carried a denominator that had moved by eight.
A derivation is prose and nothing had ever checked it; a corpus size stated in
one now has to match a figure the same file declares.

**Four sentences ranked the approaches rather than describing one.** The
strongest of them read that the difference was between an approach that can be
adopted and one that has to be agreed first. Comparisons belong on the side by
side page, where all three columns are visible at once.

### The tone pass, which was the point

A second reading found the block scoring three axes rather than describing them.
Tailoring was a headline cost on one page, absent from another, and a trailing
clause on the third. The same structural limitation must receive the same
treatment wherever it applies. The by-component limitation was a cost on one page, the mirror
gain on another, and not charged at all on the third, whose own claim mechanism
is a by-component response. Plan-of-record growth was framed as a cost in one
place and as desired state arriving in another, without a consistent derivation. Two pages
softened their corpus shortfalls with a line saying the shortfall is the files
rather than the model; the third had no such line. All four are levelled now.

---

## Session: the block restructured in place, and a page overwritten

**Date:** 2026-08-23
**Scope:** section 1 and 2 of the approach pages, and a guard against the way
this session destroyed work
**Result:** complete. 1262 verification checks and 960 page checks pass.

### The overwrite

The three approach pages are generated. `catalog-first.html` was edited by hand
after being generated, and the next run of `tools/approach_pages.py` rewrote it
from the data. The edits were gone, and there was no copy: the repository is not
under version control here, so recovery came from OneDrive file history.

The failure was silent by design. A generated file that someone has edited looks
exactly like a generated file. So the generator now records the sha256 of every
page it writes, in `data/generated-pages.json`, and compares the page on disk
against that record before overwriting. A page that has moved since it was
generated stops the run, names itself, and says where the edit belongs instead.
`--force` writes anyway, which is right once the edit is in the data.

### What the edit changed, and what was kept

The published inventory now comes first, as **1. How this approach is
published**, and the argument second, as **2. Strengths and risks with this
approach**. The block is three strengths and three risks rather than four and
four, and the other two pages were cut to match, both in count and in length: a
block that ran a fifth longer on one page would be an argument made in the
layout.

The block no longer carries citation chips or a source list on the page.
The entries are editorial analysis, not attributed statements. Where an entry
turns on what a model can express, the
schema fragment behind it is still named in `data/tradeoffs.json` and still
checked, without being rendered.

### Green and red, which the site had avoided until now

Colour carries meaning in this block, which it does nowhere else on the site.
Three conditions make that safe, and all three are checked rather than intended.

Each entry carries a mark: a box with a tick, or the same box with a cross. Same
size, same weight, same shape, and only the glyph inside differs, so the two are
still apart in grayscale and for a reader who cannot separate the colours. The
columns keep the solid and dashed edges they had before any colour arrived. And
each column is headed with the word.

The two colours are matched in contrast to within a hundredth, 6.53 against 6.54
in light and 7.97 against 7.98 in dark, and both clear 4.5:1 on both surfaces
they are drawn on. A red that shouted louder than the green would be an argument
in a block whose whole point is that the two sides get equal weight.

### One more guard, for a mistake made twice

Two edits this session replaced a span of a file by computing the end offset
before the start, appending the tail back, and leaving a second copy of three
functions behind. Python and node accept that in silence, the later definition
winning, so the file keeps working while carrying a stale copy of itself. It
happened once in `assets/site.js` and once in `tools/verify.py`.
`verify.py --source` now checks every tool and script for a name defined twice,
and compiles every Python file.

### The summary block and the one-of-three callout, removed

The lede is the summary now. Above it sat a Summary box restating the same thing
at seventy-five words, and below that a callout explaining how the three pages
are constructed, in what order they are presented and why they are named rather
than lettered. That is a note about the site, addressed to a reader who came for
the approach, and it ran on all three pages ahead of anything about the
approach itself.

Both are gone. Each page now opens with its name, one short paragraph naming
what carries the rule, what carries the check and what each of the two states,
and then the contents. The lede is held to between 25 and 60 words by the build,
where the gist was held to 75 to 85, and `h1_tail`, which fed the sentence the
lede replaced, went with it.

---

## Session: one scenario, modelled three ways

**Date:** 2026-08-23
**Scope:** section 3 of the approach pages, and the figures behind it
**Result:** complete. 1397 verification checks and 966 page checks pass.

### Why a scenario

The three approaches are hard to weigh against each other in the abstract,
because each of them can express everything the others can. What separates them
is how many documents it takes and what the plan of record ends up holding, and
neither of those is visible until the same task is put to all three.

So the task is fixed once, in `data/scenario.json`: a system under NIST SP
800-53 Revision 5 at the High baseline, running Ubuntu, PostgreSQL and Microsoft
365, hardened against a published guide for each. Every OSCAL model except the
plan of action and milestones, which is excluded because it is the same document
in all three approaches and therefore separates none of them.

### Every number is derived

The framework is 370 controls, 188 base and 182 enhancements across 18 families.
That is the length of the id list in the published HIGH baseline profile, stored
in `data/scenario-evidence/nist-high-baseline.json` and counted rather than
quoted.

The three guides come to 547 requirements: 308 for CIS Ubuntu 24.04, counted as
the steps titled "Audit for" in its plan; 111 for the DISA PostgreSQL STIG,
counted as the props marked step-type check; and 128 for CISA SCuBA, counted as
the steps in its agnostic plan. Each records the file and the counting rule, and
`verify.py --scenario` recomputes all three from the corpus rather than trusting
them.

### Four of the counts are not a choice

`import-profile` on a system security plan is a single required object, so
several baselines have to be merged into one profile before a plan can import
them. `imports` on a profile is an array, which is what makes the merge possible
and the resolution a tool problem. `import-ssp` on a plan and `import-ap` on a
result are both single and required, so a separate plan produces a separate
result rather than another section of one. Those four facts do most of the
arithmetic, and they apply to all three approaches equally.

The result is 18 files for the catalog approach across all seven models, and 11
each for the other two, across six and five.

### The figure is the argument

One tile is one file, and the tile is the same size in all three drawings, so
the comparison is area rather than a number to be believed. The three share a
width and a grid, and the verifier fails if they stop sharing them or if the
tiles stop matching the inventory.

A model an approach does not use is drawn as a dashed rule and labelled none,
not as a hollow tile. The first draft drew a hollow tile, and at that size an
outline the same shape as a file reads as a file: the approach that uses five
models looked like it used seven.

### The tie to section 2

Every consequence the scenario states names a strength or a risk from section 2
of the same page, and the verifier fails if it names one that page does not
carry, or if two consequences name the same one. Without that, section 3 would
be a second argument sitting under the first rather than the first one made
concrete.

---

## Session: the comparison page removed

**Date:** 2026-08-23
**Scope:** compare.html and everything that existed only to serve it
**Result:** complete. 1331 verification checks and 530 page checks pass.

### What it had, and what happened to each

Six sections. The matrix, one control in three encodings, and the model map
overlay all said what the six questions page says, arranged all at once rather
than one question at a time, so they went with the page.

The rule-to-check figures did not. Each approach page now carries its own, next
to the model map, which is the other structural figure on those pages.

The fifteen criteria table and the four agreements were both unique to the page
and both dropped, on the call recorded in the conversation. `criteria-fill.json`
went with the table. `criteria.json` stays as the 15 evaluation criteria
maintained as analysis content, with structural checks on the criteria and their
question mappings.

### What came back from the dead

`nothingBlock` renders the evidence behind a cell that shows nothing: what was
searched for and what turned up instead. It ran only on the comparison page, so
removing that page would have left question 5 of the catalog approach saying
"nothing is encoded here" with the evidence for it unpublished. It now runs in
the question stack, and the harness accepts either shape.

It had also been borrowing the `carrier` class for its layout. That class means
the model-and-assemblies block, which is checked for naming the model first, so
the borrowed one failed the check the moment it appeared on a page that runs it.
Two different things, two classes.

### One repair, from the same mistake as before

Removing the composite builders took a span from a comment to `def build():`,
and six tables lived in between: BUILDERS, SHOWS, PER_RULE, SHARED_LABEL,
SHARED_CELLS and EXTRA. This is the third time this session an edit has computed
a span wrong.

They were rebuilt from `data/pattern-examples.json`, which is the generator's
own last good output and holds every label, every "shows" string and every
block, so what went back is what was there rather than what was remembered.
The one thing the output could not supply was a uuid seed, which was recovered
by search. The regenerated file is byte-identical to the one committed before
the cut, which is the proof that the reconstruction is exact.

`verify.py --source`, added earlier today for the duplicate-definition version
of this mistake, does not catch the deletion version. What catches this one is
that the generator's output is committed and compared.

---

## Session: one scenario, on one page

**Date:** 2026-08-23
**Scope:** the scenario moves off the approach pages onto a page of its own, and
every figure goes with it
**Result:** complete. 1374 verification checks and 552 page checks pass.

### The rule

The site describes one scenario, and every count on the site is a count of that
scenario, on the page built for it. A figure anywhere else is a second scenario,
implied and never introduced, and a reader comparing two pages would be
comparing two systems without being told.

So `scenario.html` carries the lot: 370 framework controls, 547 hardening
requirements, 917 together, and the file inventory for all three approaches with
their three figures. The approach pages carry none. `verify.py --scenario` fails
the build if any other page renders a figure, and separately if any other page
retypes one of the scenario's counts into prose, which is how the rule would
actually be broken: a `data-stat` span is obvious, a sentence saying "917
controls" is not.

### What section 1 lost, and where it went

"How this approach is published" counted things: 452 controls, 230 component
definitions, 2,425 activities. It now describes the same content without
counting it and points at the OSCAL artifacts page, which already carried the
full inventory file by file. Nothing was lost; it was being said twice.

Three strengths and risks and one status sentence also carried figures. They now
make the same point structurally, which is what an approach page is for: the
join between a control and its check is by name rather than by reference, and
whether it holds in 429 cases out of 429 is a fact about one corpus rather than
about the approach.

### What the page is

Four sections. The inputs, with a disclosure listing where every figure was
counted from. The file sets, as a table of all three approaches by model and
then one figure each. The four facts the schemas force, which do most of the
arithmetic. And the consequences, grouped by approach, each naming the strength
or risk on that approach's page which it makes concrete.

`tools/scenario_page.py` builds it from `data/scenario.json`, so the numbers on
the page are the numbers in the data and neither can drift from the other.

### Two things went dead with the move

`renderCited` and the `.cited` marker were removed. The scenario page generates
its figures from scenario data with declared derivations; it does not inherit
unsupported scale claims.

### Every tile now names its file, and a component definition says which kind

**Date:** 2026-08-23

Six identical blank tiles under `component-definition` said nothing about which
three hold the thing being configured and which three hold the checks that test
it, which is the distinction the whole component approach rests on and the one
thing a file count cannot show. So every tile carries the name of the file it
stands for, shortened to fit, and a component definition carries its kind
underneath: software or validation.

The names are in `data/scenario.json`, one entry per file, and they are rendered
three times from that one place: on the tile, in the list under each figure, and
in the figure's description for a reader who gets the description rather than
the drawing. `verify.py --scenario` fails if the count and the number of names
disagree, if two files in one model share a name, if a name is too long for a
tile, if a component definition does not say which kind it is, or if a name in
the data is not drawn in the figure.

Sizing it took two passes. The first drew the names at 13px, which broke the
site's own floor: a diagram is displayed at three quarters of its authoring
width, so 16px is the smallest text that still renders at 12px on the page, and
`verify.py --diagrams` failed every diagram at once because the two new classes
had gone into the shared style block. The tile is sized around the text now
rather than the text shrunk to fit the tile, which is the right way round.

### Sections 3 and 4 removed from the scenario page

**Date:** 2026-08-23

The page is the inputs and the file sets, and nothing else. "What the model
decides for you" and "What follows, approach by approach" are gone, and so are
the two data blocks that only those sections read, `forced_by_the_model` and
`consequences`.

Neither argument was lost, because neither had to live in a section of its own.

What the schemas force was already stated on the file rows it explains: the
profile row says the merge is needed because a plan reaches everything through
one `import-profile`, and the results row says four results rather than four
sections of one because `import-ap` is neither an array nor optional. Three rows
only implied it and now say it, and `verify.py --scenario` fails if a row whose
count is forced by a cardinality stops naming the field that forces it. That is
a stronger check than the one it replaces: the reason now has to sit next to the
number it explains rather than in a list further down the page.

The consequences tied each count to a strength or a risk on an approach page.
Those strengths and risks are still on those pages, argued there, which is where
a reader deciding between approaches is reading. The tie was a convenience for a
reader going the other way, and the page is 1,084 words rather than 1,455
without it.

### The corpora note removed from the approach pages

**Date:** 2026-08-23

"What these three bodies of content are" ran on all three approach pages: a
callout saying the corpora are published samples rather than official releases,
that a count in an answer describes the sample somebody chose to publish, and
that a count is only ever reported beside its denominator.

Its second half had already stopped being true of these pages. The figures moved
to the scenario page, so there are no counts left on an approach page for a
denominator to accompany, and a rule about how counts are reported was being
stated on the three pages that no longer report any.

The first half was worth saying once and is now said where the counts are: the
OSCAL artifacts page is the inventory of what each group published, and the
scenario page states plainly that its figures describe one modelled system
rather than any group's maturity.

Gone with it: `renderCorporaNote`, the `corpora_note` block in
`data/six-questions.json`, and the three checks that asserted the block existed
and said what it said. Nothing else read any of them.

### The answer legend reduced to three words

**Date:** 2026-08-23

The legend read "Answered. Drawn as a solid mark." and "Not answered, no
position stated. Drawn as a dotted fill." Both halves after the label described
the drawing, which is sitting next to the label where a reader can see it, and
between them they turned three short states into three sentences.

It is three labels and three marks now: Answered, Partly answered, Not answered.
The meaning of each stays on the title attribute for anyone who wants it, and
the tooltip on a row carries the cell's own note, which is the evidence and says
more than a stock phrase.

The `reason` field went out of `data/six-questions.json` with it, along with the
two places that concatenated it into a tooltip, and two CSS rules for spans
nothing renders. The page harness now asserts the opposite of what it did: that
neither the geometry nor the reason is written out, and that each item is one
label standing alone.

One repair on the way. The regex that removed `.answers__why` from the
stylesheet matched the line above it as well and took `.answers__q` with it,
which is the rule that keeps a long question name from pushing the state column
out of alignment. Restored, and the two rules for that selector merged into one.

### Section 1's heading is now per approach

The heading was fixed across the three pages, and it is the one heading where
the three genuinely differ, because what each publishes is the subject of the
section. Catalog-first now reads "How this approach leverages controls as
technical requirements", edited in the page and folded back into the generator
along with the marked-up lede and the shorter body. The other six headings stay
identical on all three pages, which is what the equal-budget rule is for.

The hand edit had changed the heading but not the table of contents entry above
it. The generator keeps the two in step, so regenerating fixed a mismatch the
edit had introduced rather than losing anything.

### Prose now fills the reading column

**Date:** 2026-08-23

Body text stopped about 215px short of the rail on every page. The reading
column is 864px once main's padding, the column gap and the 13.5rem rail come
off 1160px, and `--measure` was 78ch, about 650px. Bounded on both sides, that
gap reads as a hole rather than as margin.

An earlier pass had already narrowed the page and the gutter and widened the
measure to close it, and closed about half. The reason it kept reappearing is
that the two numbers were set independently: a character count on one side and
four layout values on the other, with nothing relating them.

`--measure` is now `54rem`, which is the column exactly, and `verify.py --css`
recomputes the column from the same four values and fails if they drift. The cap
is still worth having for two cases it now handles correctly. Below 1120px there
is no rail, so the column is the full width and the cap holds a line to the
length it has on a wide screen. And for a reader who has raised their browser's
font size, the rem scales with it, the cap stops binding, and the column
governs, which is the right way round.

Writing the check found a second bug in the check itself: `main`'s padding is
the three-value shorthand, top then horizontal then bottom, and a greedy match
took the third value. That put the computed column 80px out and would have
enshrined the wrong number.

### The other two section 1s follow the catalog page

Folding the hand edit into the generator left catalog-first with a much shorter
section 1 than the other two, and the page budget went to 10.4 per cent against
a 10 per cent limit. Rather than pad it back, component-first and
assessment-first were given the same treatment: a heading naming what the
approach leverages, and one clause on the primary-model sentence saying how it
expresses a technical requirement. The repository link went with the paragraphs;
it is on the OSCAL artifacts page, which is the inventory of who published what.

### Two sections become the stakeholder mapping

**Date:** 2026-08-23

"What kind of thing a rule is here" and "Which stakeholder this serves first"
were answering the same question at two resolutions, and the second answered it
badly. Three stakeholders, publisher and implementer and assessor, and a verdict
about all three in three words: this approach serves the publisher first.

Six parties actually touch a hardening rule between the body that writes it and
the auditor who reads the outcome:

    Regulatory control providers
    Technical hardening guidance providers
    Software providers
    System owners
    Policy engine providers
    Independent auditors

Section 3 now names all six, on every page, in one order, with one line per
party saying what the approach asks of them and what it gives them. That is the
same argument at a resolution a reader can disagree with: "the vendor describes
its own product once and every system that runs it inherits the description" is
a claim someone can push back on, where "serves the publisher first" is not.

Naming all six matters most where an approach asks nothing. Two of the three
change nothing at all for the regulatory body, and saying so is a fact about
those approaches rather than an omission, so the entry says it and says why.

The reading survives as the section's opening sentence, because it is the reason
the six land differently: an approach that reads a rule as a requirement asks
the benchmark body to publish controls, and one that reads it as a procedure
asks them to publish a plan. `views.json` is still what supplies it.

`verify.py --stakeholders` fails if a party is missing from a page, if the six
are rendered out of the declared order, if a line runs under fifteen words, or
if the three pages spend more than twenty per cent apart on their six.

Two fields went dead with the merge and are gone: `view_note` and `reader_note`
in the generator, and `view_of_rule` in the data. `serves_stakeholder_first`
stays, because diagram 7.5 on the start page still draws from it.

### The stakeholder mapping reduced to a table

**Date:** 2026-08-23

Six paragraphs became six rows. The section named the six parties and argued in
prose what each approach asks of them, which is the same information at a length
nobody reads twice. Each party works in an OSCAL model, and which model is the
whole of what an approach asks of them, so the section is a mapping now: party
in one column, model in the other.

    Regulatory control providers              catalog, profile
    Technical hardening guidance providers    the model that approach puts the rule in
    Software providers                        the same
    System owners                             system-security-plan
    Policy engine providers                   what it reads, what it writes
    Independent auditors                      what it reads

The engine is the one row with two sides, because it consumes a model to know
what to check and produces another to record what it found, and the three
approaches differ most there. Catalog-first reads the catalog and the component
definition and writes the plan of record, because no assessment result is
published. Assessment-first reads the plan and writes the result.
Component-first has two flows rather than one, the component definition feeding
the claim and the assessment plan feeding the result, so its row is drawn as
two.

`verify.py --stakeholders` checks that every party appears on every page in one
order, that every model named is one of the seven the scenario page enumerates,
that the engine row names both a model it reads and one it writes, and that
where an approach declares flows there is one per model it consumes.

The reading of what a rule is stays as one sentence above the table, shortened
to the clause that decides it: this approach reads a rule as a requirement,
which puts it in the control layer, and that is what decides the table.

### Five sections, reordered, and the strip joined to the questions

**Date:** 2026-08-23

The order is the stakeholder mapping, then the strengths and risks, then how
the approach leverages its model. Which party works in which model comes before
the argument about the approach, and the argument comes before the detail it
generalises.

The bigger change is that the answer strip and the six questions are one section
now. They were two: an inventory section carrying the strip, and the questions
two screens below it. That is one subject split in half, and it left the strip
doing half a job. A reader who learned from it that question 3 is partly
answered had no way to act on that except to scroll and hunt.

Every row is a link now, to the subsection that answers it. The two halves of
question six point at the same subsection, because there is one. The strip is
still a list when nothing links: the start page shows three of them side by
side and has no per-question section to point at, so `data-link` is what turns
the rows into anchors and its absence leaves them as list items with the list
semantics they had.

`pagecheck` gained a check on the strip: seven rows, every one a link, every
target an id that exists on the page, the two halves of question six sharing
one, and the strip inside the section it summarises.

It also gained a real fix. The hook check read only `site.js` to learn which
`data-` attributes a script handles, so the ones the strip script reads had to
be hand-listed as exceptions, and `data-link` failed the moment it appeared. It
reads both scripts now, and the attributes read through `getAttribute` as well
as those selected on, so the exception list is doing less work.

### The mapping gets the scenario's file tiles, and two rows change hands

**Date:** 2026-08-23

The models in the stakeholder mapping are drawn as the same file tiles the
worked scenario uses: a page with a folded corner, the model name beside it, and
the component type beneath where a component definition has one. The two pages
talk about the same seven models and a reader moving between them was looking at
a drawing on one and a code span on the other. The engine's row is a flow, with
an arrow between what it reads and what it writes; the arrow is aria-hidden and
the word "produces" sits beside it, because an arrow read aloud is silence.

Two rows changed hands, and both are now checked rather than reviewed.

**The profile is the system owner's, in the catalog approach.** It had been sat
with the bodies that publish catalogs. The selection of what a system is held
to, and the merge of four catalogs into the one a plan can import, are decisions
about one system, so they belong to whoever runs it. The build fails if the
profile appears in any other party's row on that page.

**The component definition holding the checks is the policy engine
provider's.** It had been sat with the software provider, which is right for the
component definition describing a product and wrong for the one describing what
tests it, because a check is the thing that triggers an engine to run. It is a
component of type software in the catalog approach and of type validation in the
component approach, which is the same model doing two jobs for two parties, so
every component definition in the table now names its type and the build fails
if the check one is not the engine's.

### The encodings on the two pages are now checked against each other

**Date:** 2026-08-23

Asked whether the JSON examples are the same on the six questions page and the
three approach pages. They are: all 32 blocks, character for character. Both
routes read `data/pattern-examples.json` through the same renderer.

But they get there differently, and that is worth a check rather than an
assurance. An approach page names a block in a `data-pattern` hook the page
carries, one hook per block, written by the generator. The six questions page
builds all 32 in one pass from the data. A block added to one route and not the
other, or a hook naming a rule that no longer exists, would show a reader two
different answers to the same question on two pages, and neither page would look
wrong on its own.

`pagecheck` now renders both and compares them: every encoding an approach page
shows must be on the six questions page, character for character, and every
encoding the six questions page draws for an approach must be on that approach's
page. Both directions, because a block missing from one side is as wrong as a
block that differs.

Tested by making the two disagree. Pointing one hook at a rule that does not
exist failed both directions at once, naming the hook and the orphaned block.
Changing the data does not fail it, correctly: both routes read the same file,
so the two still agree, and what is being checked is that they agree rather than
that any particular value is right.

What does differ between the two pages, deliberately, is the prose around the
block. An approach page carries the "shows" sentence describing the encoding; the
six questions page does not, because three sentences already sit above every
encoding there and a fourth was a paraphrase of the one below it, three times
per question and eighteen times down the page.

### The encodings leave the approach pages, and the join takes their place

**Date:** 2026-08-23

The JSON was on the approach pages and on the six questions page, byte for byte
the same in both, which the harness had just been made to prove. Proving two
copies identical is a good reason to keep one. They are on the six questions
page now, where all three columns sit together and the comparison a reader is
making is possible; an approach page has one column, so the block there was the
same block twice.

What came back in its place is what was being suppressed. The published extracts
had been hidden on any question our own encoding covered, which was most of
them, because two code blocks on one question read as one claim made twice. The
block they sit in is headed "In the published content", and now that is what it
holds.

The harness check inverted with the change. It compared the two copies; it now
asserts that the six questions page draws every block the data declares and that
no other page draws one. That is the stronger check: the six questions page
builds them in a loop, so a block dropped from the data would disappear from the
site without anything looking wrong.

### Section 4 carries the connecting tissue

The six questions are answered one at a time, which hides the thing that decides
whether the set works: what joins one answer to the next. A rule is only useful
if something can get from it to the check that tests it, from the check to the
control it serves, and from the result back again.

Section 4.1 is those hops, in a table. Each row is a field on one side, a field
on the other, and how it resolves, with both ends linking to the question they
belong to. The ways of joining are a closed set of six, and the glossary under
the table lists only the ones that page uses, so a page joining three ways does
not explain five.

The way it resolves is the argument. Catalog-first joins its control to its
check by matching a prop against a component title, which is a name match: it
holds where the two agree and no schema can tell you when they stop.
Assessment-first reaches its runner through a uuid held inside a JSON string in
a prop value, which resolves and which the schema knows nothing about.
Component-first uses two composite keys, and its result never states the control
at all. Those three sentences are the difference between the approaches, and
until now they were spread across six subsections that each looked fine alone.

The join figure follows the table, drawing the same hops with the real values
read out of the shipped files, so a reader can take either one and check it
against the other.

### Section 3 comes off the approach pages

**Date:** 2026-08-23

The section walked the six questions one at a time for a single approach: an
answer strip, then a subsection per question carrying that approach's position,
its carrier vocabulary and the published extracts. It is gone, and the pages
drop from about 2,050 words to about 1,190.

The reason is that six-questions.html answers the same seven rows with all three
columns visible. A reader deciding between catalog-first and component-first is
making a comparison, and one column of that comparison on its own page is the
same content read twice with nothing beside it to compare against. The encodings
had already moved there for the same reason; this is the rest of the same move.

The answer strip went with it. A scorecard for one approach is a row of a table
whose other rows are the point.

**What was lost, deliberately.** The published extracts, thirty-one blocks of
real shipped OSCAL, were inside those subsections and are now displayed nowhere.
That was a decision, taken knowing it: the matrix still declares them per cell
as snippet_ids and verify.py still checks every id resolves to a file in
data/snippets, so they remain as provenance, the record of which shipped file
evidences which answer. What a page still shows is the evidence under its status
section, which is the publisher's own statement about its content rather than an
answer to a question.

**What moved rather than went.**

The joins table in section 3.1 linked its hops to `#slot-N` on the same page.
Those links now cross to `./six-questions.html#q{slot}-{approach}`, landing on
that approach's column of the question named, which is a better destination than
the one they had: the reader arrives where all three answers are. Every hop end
also names its question now, "Question 5, the runner" rather than "Question 5",
because the strip that used to tell a reader what the numbers meant is gone.

The completeness sentence in the status section enumerated question numbers for
the same reason and now names them too: "The rule and the check are filled"
rather than "Questions 1 and 3 are filled".

The extract-count note went. It stated how many extracts the page showed and
explained why the three pages showed different numbers; with the extracts gone,
the count is one or two pieces of status evidence and the explanation explains
nothing.

**Checks.** Four in verify.py were asserting the old arrangement and were
retargeted rather than deleted:

- the joins links, to the cross-page anchors
- the section order, from "before the questions" to "before the models"
- the evidence rule, which required every answered question to show an extract
  or an encoding on its approach page. It asserts the data now: an answered cell
  declares a published extract, or an encoding of the two running rules exists
  for it. An answer resting on neither is what the rule was written to catch.
- the three extract-count checks, removed with the note

In tools/pagecheck.js checkAnswerStrip became checkApproachShape, which asserts
the opposite of what it used to: no strip, no per-question walk, every join link
crossing to the six questions page and into this approach's own column. Two more
were added: checkJoinTargets resolves those anchors against the rendered six
questions page, because it builds its answers in JavaScript and a cross-page
anchor that rots does not 404, it lands at the top of the page; and
checkExtractsAreStatusOnly holds the deletion in place by rule rather than by
memory, no extract outside the status section.

Dead code removed with the section: SLOT_HEADINGS, chip(), and the per-approach
exists_heading, exists_tail, slot_notes and slot_extras keys, about 10,600
characters of tools/approach_pages.py. The page template no longer loads
assets/diagrams/74-slot-strip.js, having no strip to render.

### The join figures become one chain, drawn from the six questions examples

**Date:** 2026-08-23

The three join figures each drew two joins out of whichever corpus that
approach's proponent had published. Catalog-first showed an ACM.2 control and an
AWS Config rule; component-first showed a COS component and an Ansible runner;
assessment-first showed a STIG activity and a CISA context prop. Three pages,
three subjects. A reader comparing the figures was comparing the corpora, which
is the one comparison this site exists to avoid making.

They draw one chain now, from one rule. Every value is rule 1, data at rest, as
data/pattern-examples.json encodes it for that approach, which is the rule all
three columns of the six questions page already walk. What changes between the
three figures is only what a reader is being asked to compare: how many
relationships it takes to get from the rule to the check, and what each one is
made of.

**The chain, not a list of joins.** It starts where the rule is introduced and
runs to the claim and the result, through the runtime. Each step is drawn as one
row per relationship, the field holding the pointer on the left and the field it
resolves to on the right, so a step made of two rows costs two things to follow.
That geometry is the finding:

- catalog-first: 5 steps, 9 relationships. Getting from the rule to the check
  takes two, pointing opposite ways, and one of them is a name match. Check to
  runtime is a no-join: a prop names the rule the engine runs and the engine is
  nowhere in the content.
- component-first: 6 steps, 10 relationships. Rule to check is a composite key
  with both halves on the check side. Check to runtime is containment, because
  the checks sit inside the component that runs them. Result to control is a
  no-join: the result never states the control.
- assessment-first: 6 steps, 7 relationships. Rule to check is containment, the
  check being the first step of the activity. Result to control resolves,
  because the finding targets the control objective and needs no plan of record
  to do it.

**data/joins.json** carries all of it: stages, the vocabulary of five ways to
join, and per approach a list of steps each holding one or more foreign-to-
primary pairs with the literal value on each side. The section 3.1 table renders
the fields and the figure renders the values, which keeps the old division of
labour: the table is the chain in words, the figure is the chain with the
quotations.

Authoring the chain surfaced what the six questions encodings do not show, which
is worth recording because it is not a defect. Three references point at
documents no question draws: the SSP's own component inventory, its inventory
items, and the observation a catalog-first finding relates to. They are real
cross-document references and the chain names them as such rather than drawing
them as broken.

**The check moved with the figures.** Every literal used to be matched back to
data/snippets to prove it had not been typed by hand. It is matched against
data/pattern-examples.json now, which is the file the figures are built from,
and the assertion is stronger than it was: every value the data declares has to
be in that encoding, and every value has to be on the figure.

### The runtime gets an icon

Every other party in the stakeholder mapping writes a document, so a file tile
says what they do. The policy engine is not a document. It is the thing that
reads OSCAL, executes, and writes OSCAL back, and putting it in the same shape
as the five parties that produce documents said it was one of them.

So it has a glyph: something arrives, a machine runs, something leaves. Both
arrowheads are part of the icon, which is why the engine's row does not also
carry the flow arrow the other rows use. The same mark is drawn beside every
step of the chain figure that involves the runtime, at a fixed column so it
lands in the same place on all three pages.

The mapping now reads, for catalog-first: the engine writes a component
definition of type software, and then catalog plus that component definition go
in, the runtime runs, and a system security plan comes out. For component-first
the type is validation and there are two flows. For assessment-first there is no
component definition of its own and the engine is named inside the plan.

### The stakeholder mapping gains a party, a group and a narrower engine

**Date:** 2026-08-23

Three corrections, all of them about who actually does what.

**The mapping is nobody's by default.** The hardening guidance provider used to
hold both the catalog and the mapping-collection, which said that whoever writes
a guide also ties it to a framework. They often do not. A STIG carries CCIs and
it is DISA's separate CCI list that names the 800-53 controls; third parties
publish mappings of their own through NIST's OLIR programme, the Secure Controls
Framework among them. So the mapping-collection comes off the guidance row and
the mapping provider is a party of its own, seventh in the table.

It writes a document in one approach and nothing in the other two, which is the
finding rather than a hole: catalog-first needs a separate mapping document that
no publisher has shipped, while component-first ties the rule to the control
inside the control implementation and assessment-first ties it on the activity.
Where the party writes nothing the row says why, and the harness fails a row
that is empty without an explanation.

**Two of the seven are one role.** A benchmark body writes hardening guidance
for a product it does not own; a vendor writes it for its own. Same objective,
same model, two kinds of organisation. They were two rows saying the same thing
and a reader had no way to tell that was deliberate, so a group heading spans
them and they indent under it.

**The policy engine writes the component definition and nothing else.** Its row
in catalog-first used to show the catalog going into the runtime alongside the
check component definition, which read as though the engine had a hand in the
catalog. It does not: the catalog is the guidance authors', above. The flow is
the component definition into the plan of record, and what it produces there is
the control-implementation responses.

**The equal-budget rule now counts prose rather than payload.** The rule exists
so that no approach is argued at greater length than another. Since the chain
table arrived, a large part of each page is generated from data whose size is
set by how many relationships that approach has, and counting it made the rule
push the wrong way: it would have had me shorten the argument of whichever
approach turned out to have the most to join. Field names, model tiles and the
vocabulary glossary come out of the count and every sentence stays in. The
spread went from 9.6 per cent, which was nearly a build failure caused by
component-first having ten relationships to catalog-first's nine and
assessment-first's seven, to 3.5 per cent.

Two chain notes were trimmed and two were extended while this was being sorted
out, all four for their own reasons. Component-first lost a clause in three
places that repeated the row above it. Assessment-first gained the consequence
its notes had stopped short of: that a plan naming its platforms once cannot say
which engine ran which check, and that pointing at a prose resource instead of a
plan of record is what makes the route usable before an SSP exists and also what
makes the tie unreadable to a machine.

### A provider builds a tool; the system owner and the auditor run it

**Date:** 2026-08-23

The policy engine row said the engine reads a component definition and writes a
plan of record, which put the provider in the position of doing something it
does not do. OPA, Kyverno, ScubaGear and OpenSCAP are tools. Somebody else runs
them, and which somebody decides what comes out.

So the run moved onto the row of whoever performs it. The policy engine provider
writes the component definition and has no flow at all: it builds the tool and
ships the checks in it. The system owner's row carries the run that makes the
control-implementation responses in the plan of record, and the auditor's row
carries the run that makes the result. The same checks, two rows, two outputs.

Assessment-first is the exception and says so: both runs produce the same
artifact, because there is no path from a check to a claim to take instead, so
the two parties differ only in whose signature is on the outcome.

The harness holds the distinction rather than trusting it. The engine may have
no flow. The parties with a run must be exactly the system owner and the
auditor. Every run must say what it produces. An auditor's run must end in a
result, and an owner's run must end in the plan of record on the two routes that
have a path from a check to a claim and in a result on the one that does not,
where the row has to explain why.

**One group, not a second concept.** The system owner and the independent
auditor were grouped on their own as "automation tool users", which invented a
category: it said the automation was one thing and the policy engine another.
They are the same thing. The group is the tool and the two parties that run it,
so the policy engine provider sits inside it rather than above it, and the
heading says what the three rows are: automation tools and who runs them.

A group heading spanning rows needs them adjacent, so the harness checks that a
group's parties are contiguous.

**The mark is defined where it is used.** The runtime glyph was defined only in
the legend of the chain figure, two sections below the table that first draws
it. A line under the table now says what it means and carries the distinction:
the party in the row builds the tool, the party named on each flow runs it.

One line had to change to stay true. The auditor was described as "reading the
outcome without having run any of it", which was the assumption this correction
removes. They run the same checks independently of the system owner.

### In, runtime, out is one line

**Date:** 2026-08-23

The run was rendering as three flex items sitting beside its label, so the label
took the first line, the input and the mark took the rest of it, and what the
run produces wrapped onto a third line on its own. It read as two statements
rather than one.

The label takes a row of its own now, and the input, the mark and the output are
wrapped together in a element that does not wrap. That only works if the widest
of them fits the cell, and the widest, a validation component definition through
the runtime to a plan of record, needed about 540px against the 540 the cell had
at a 32 per cent party column: it fitted or it did not depending on the reader's
font size. The party column is 28 per cent now and the mark is 2.75em rather
than 3.05, which leaves 37px of slack on the worst row.

A measurement that close should not be left to inspection, so verify.py computes
it: it reads the font sizes, the spacing tokens, the column percentage and the
mark's width out of the stylesheet, adds up the tiles each run draws from
data/stakeholders.json, and fails if any of them no longer fits. A longer model
name or a wider spacing token starts it wrapping again, and the build says so
rather than the reader finding out.

### The chain table goes; the figure stays

**Date:** 2026-08-23

Section 3.1 was a four-column table, a row for every foreign-to-primary
relationship, with the models, the fields, the question each belonged to and how
it resolved, and then the figure drawing the same chain underneath it. A screen
and a half of table sitting directly above a picture of itself.

The figure carries the fields and the values and the way each relationship
resolves, and it carries them better, because a drawing can put the two ends
side by side and a table has to name them twice. So the table is gone.

What a drawing cannot say is why a step costs what it costs, so the notes stay,
one per step, as a list above the figure. Each keeps the two links the table's
cells carried, on the stage names, which is where a reader reaches for them: the
step reads "Rule to Control" and each end links to that question on the six
questions page.

The vocabulary glossary went with the table. It listed the ways this approach
joins things and the figure's own legend already does, three lines apart.

The harness moved with it: it checked the table's row count against the number
of relationships and the glossary against the kinds in use, and now checks that
no table is there, that a note survives for every step, and that both ends of
every step still resolve to an answer on the six questions page.

### Section 1 is the branch, not the parties

**Date:** 2026-08-24

The section was called "Three stakeholders considered" and defined publisher,
implementer and assessor in three bullets. That detail now lives on each
approach page, in the stakeholder mapping, seven parties deep and joined to the
model each one works in. Two resolutions of the same subject, and the shallower
one came first.

What the section is actually for is the branch: one recommendation goes down
three paths rather than along one of them, which is the premise the whole site
rests on. So it is called that, the three bullets are one sentence, and
`id="stakeholders"` is `id="paths"` to match. Only the page's own table of
contents cited that anchor.

"Recommendation" rather than "requirement", on the call recorded in the
conversation and for the reason already in `tools/diagrams.py`: a CIS Benchmark
and a STIG both recommend and neither compels, so calling it a requirement here
would pre-answer the question the site exists to lay out.

The figure is unchanged, deliberately. The second new sentence says the
assessor's path can be run independently of the implementer's, and the drawing
already shows it: all three paths branch from the same trunk and none passes
through another, so the independence is in the geometry rather than something
the geometry has to be changed to assert. Stated as what can happen rather than
what should, which keeps it a description of the process and not a case for the
assessment layer. Section 2 carries the same fact at length, that assessors
bring their own capabilities, and `data/stakeholders.json` has the auditor
running the same checks independently of the system owner.

### Two legends become one, above the answers

**Date:** 2026-08-24

Section 1.1, "How each capability is enabled", is gone as a section. Its legend
is now the second group of the answer legend, and the legend sits above the
question stack rather than below it.

Three things were wrong with the old arrangement. The two vocabularies were two
blocks in two places, which reads as two subjects when they are two axes of one
reading: every answer carries a mark from the first and, where it is answered at
all, one or more badges from the second. The mechanism key sat two screens below
the first badge it decoded. And both keys sat under the thing they explain, so a
reader met three swatches and twenty badge rows with nothing yet to read them
by, and had to scroll past all seven questions to find out what they meant.

**The second group is opt-in, per page.** `data-answers-legend="mechanisms"`
asks for it. index.html and questions.html draw marks and no badges, so a
mechanism vocabulary there would define a mark that never appears on the page. A
renderer that looked for badges instead of being told would be racing them: the
legend renders before the answers do.

**The asymmetry is deliberate.** The answer states are three words with the
meaning on a title attribute, which is the shape they were reduced to earlier
today. The mechanisms keep a sentence each. Answered, partly answered and not
answered mean what they say; "Proposed" does not tell a reader that no tool can
read the content until the schema lands, and that is the sentence the page turns
on. Both reasons are in `data/six-questions.json` under `legend`, next to the
two group titles, rather than in the renderer.

**Two checks, both tested by breaking them.** The mechanism block in
`pagecheck.js` only ran where a legend already existed, so the one failure it was
written to catch, badges drawn and no key to read them by, was the one it could
not see; a page drawing `.mech-row` now has to carry the group. And a check that
the legend precedes the stack in source order holds the move in place. Dropping
the opt-in fails the first with "20 badge row(s), 0 legend group(s)"; putting the
legend back under the stack fails the second.

**One repair on the way.** The group title spanned the items grid with
`grid-column: 1 / -1`, and `verify.py --css` bans that string outright, because a
full-span child of `main` overlaps the sticky rail the table of contents sits in
and the ban is a plain string search that cannot tell a nested grid from that
one. The title is a sibling of the items grid now. The guard is worth more than
the one element it cost.

Gone with the merge: `renderMechanismLegend` in both `assets/site.js` and
`assets/diagrams/74-slot-strip.js`, the `data-mechanism-legend` hook, and the
`1.1` heading and its `id="mechanism"`, which nothing linked to.

### One icon per OSCAL model

**Date:** 2026-08-24

Eight drawings arrived in `assets/images`, one per model, colour-coded by layer:
blue for control, green for implementation, amber for assessment. They are on
the stakeholder mapping tiles and the scenario page file lists now.

**The tiles are where they earn their place.** Every tile drew the same
page-with-a-folded-corner. In a table whose entire subject is which model each
party works in, that said "this is a file" seven times and distinguished
nothing: a reader had to read the name to learn what the drawing was there to
tell them.

**Colour is in the tokens, not in the SVG.** An icon loaded through `<img src>`
is a separate document and cannot see the page's custom properties, so a
token-driven icon has to be inline. `tools/model_icons.py` does the conversion
once into `data/model-icons.json`: the ink becomes `currentColor`, the second
tone becomes a class, the chip is dropped because a rounded rect with a fill is
a CSS box, and `<line>` becomes `<path>`. Three new token trios carry the
layers, in both themes, so the coding survives the conversion rather than being
discarded by it. Both tones clear the 3.0 non-text ratio against their own chip
in both themes, which is the standard for a graphical object.

**Two icons were redrawn.** The catalog and the system security plan were drawn
with cubic curves, and `tools/svgrender.py` implements `M L H V Z` and nothing
else, so a curve would render as a straight line to the last control point and
the grayscale review would show a shape nobody drew. Both are straight segments
now, following the same silhouette. The generator refuses to run if a curve
appears in an icon that is not on the redrawn list, so a replacement drawing
cannot reintroduce one quietly.

**A bug the checks caught, not a person.** The profile's markers are stroked in
the second tone and filled with the chip colour to hide the rule running behind
them. The emitter wrote those as two `class` attributes on one element, which is
invalid and drops the second without complaint, so every marker shipped with its
knockout silently gone. Classes are collected and written once now, and
`verify.py --icons` fails on any element carrying two.

`--icons` is 30 checks: the data is current with its generator, every model the
site names has one, no icon carries a literal colour, every path is in the
subset svgrender can draw, every icon is filed under exactly one layer, both
tones clear contrast in both themes, and the stylesheet defines every class the
markup uses.

**Not done, and deliberately.** The file tiles inside the generated scenario
figures still draw the plain rectangle. Those are SVGs subject to the
token-colour rule and the path-subset rule at once, and putting a glyph in them
means teaching the diagram library three more classes. It is the next surface,
not a forgotten one.

### A span replacement ate two constants, for the fourth time

Moving `model_icon` out of `tools/approach_pages.py` used a scripted slice from
a comment to `def model_tile`, and `RUNTIME_GLYPH` and `RUNTIME` were inside it.
The build log already records this mistake three times. It is now four.

Recovered from `catalog-first.html`, which had been generated successfully a
minute earlier and carried both the glyph and the visually-hidden sentence that
travels with it, byte for byte. `RUNTIME` turned out not to be the glyph alone:
it is the glyph plus " is read by the policy engine, which runs and writes ",
which a screen reader needs because the glyph is aria-hidden and without it the
row is two model names and silence between them.

Proved rather than asserted: the three pages were copied before the repair and
regenerated after it, and all three came back identical.

The rule that keeps being broken is simple enough to state. Use the Edit tool
for a bounded replacement. A computed span is only safe when the end boundary is
unique in the file, and in a file of 40,000 characters written in one house
style it usually is not.

### The icons were tiny because three reductions were multiplied

**Date:** 2026-08-24

Reported as unreadable at 16px, and correctly diagnosed: a shaded rounded square
with something very small inside it. The cause was three reductions applied in
series, none of them wrong on its own.

    the drawing occupies ~52% of its authored 64-unit canvas
    the SVG was inset to 78% inside the chip
    the chip is 1.3em, about 21px

21 x 0.78 x 0.52 is about 8px of actual ink. The outer shape had taken the room
and the inner one was carrying all of the information.

**The fix is cropping, and it costs nothing.** The viewBox is computed from what
is actually drawn, squared around the centre, and given one 9 per cent margin.
Nothing is redrawn and no proportion inside an icon changes; the drawing is
simply no longer surrounded by nothing. The CSS inset goes, because the margin
now lives in the viewBox once, where it can be measured. Seven of the eight
icons roughly doubled: 8.1 to 8.9px before, 19.7px after, between 2.2x and 2.4x.

**Stroke weight is normalised, not left to the crop.** Cropping scales strokes
with everything else, which is most of why this reads better. But the POA&M
crops less than the rest, its tick marks reaching further out, so it would have
come out finer than its neighbours. Every icon is now 5.5% of its own box, up
from 3.1%, with the weights inside an icon held in proportion: the clock hand
drawn at 1.5 against a body of 2 is still three quarters of it.

**A collision, found while measuring.** The class was `.micon`, which was
already the media icon in the sources table, the one with the PDF badge. Two
rules, the later one winning, so every media icon on the start page was being
resized by a stylesheet block about model icons. Nothing caught it because the
download links set their own width, and the only marks that actually moved were
the web-link globes, which got bigger and looked fine. Renamed to `.model-icon`
throughout, and `verify.py --icons` now fails if `.micon` picks up a second
width rule.

`--icons` is 40 checks now. The four added here assert the crop against the
authored canvas per icon, that the glyph fills its chip rather than being inset,
and that the two icon families keep two names.

**Levers left, if 16px is still too small.** Dropping the chip would give the
glyph the whole box, another 1.2x, at the cost of the layer tint that is doing
the colour coding. Below that, the honest answer is a second lower-detail set
for small sizes: the assessment plan is a clipboard with a clock on it and the
mapping collection is three circles and three connectors, and there is a size
past which no amount of scaling makes those two readable.

### Section 3 goes; the join chain takes its number

**Date:** 2026-08-24

"Which OSCAL models this touches" is gone from the three approach pages. It was
a paragraph naming the models the approach's content lives in and the
seven-model map with those models outlined.

It was saying something already said twice above it. The stakeholder mapping
directly above is a table of which model each of seven parties works in, which
is the same fact at a resolution a reader can act on, and every answer on the
six questions page names the model it lives in. The section also had to
disclaim itself in its own caption, that a footprint records where content lives
and is not a measure of how complete it is, which is a fair warning and also an
admission that the figure invites a reading it cannot support.

3.1, the join chain, was nested under it and is section 3 now, keeping its
`id="joins"` so the links from the six questions page still land. That section
is the one carrying the difference between the approaches: a name match no
schema can check, two composite keys and a result that never states the control,
a uuid inside a JSON string in a prop value.

Pages drop from about 1,460 words to about 1,390.

Gone with it: the three `touches` blocks in the generator and the figure and
caption around the layer map. One check moved rather than went: the strengths
and risks block was asserted to sit between the stakeholder mapping and the
models section, and now sits between the stakeholder mapping and the joins,
which is the same rule about order with the section that follows renamed.

**Three diagrams are now drawn on no page.** `71-layer-map-assessment`,
`71-layer-map-catalog` and `71-layer-map-component` are still generated and
still grayscale-rendered, and nothing references them. Left in place rather than
deleted, because the seven-model map is a drawing that may want a home rather
than a mistake to clean up, and deleting a builder is the kind of edit that has
gone wrong twice today. Nothing in the harness fails on an unused diagram, which
is itself worth knowing.

### The chain starts where the rule is defined

**Date:** 2026-08-24

Section 3 is "Tracing rules and checks from implementation to assessment", and
it now runs in the order OSCAL actually moves information.

**The chain opened in the wrong place.** Its first step was rule to control,
which in catalog-first meant the first document a reader met was the mapping
collection: the file that ties a rule to a regulation, named before the catalog
that defines the rule. The figure had always started at the definition. The
notes beside it had not, so the two told the story in different orders on the
same screen.

Two changes fix it, both in `data/joins.json`.

A block before the steps says where the rule is introduced, from the
`introduced` entry the figure already drew: the model, the field, and one
sentence per approach on what it means to define a rule there. Catalog-first
puts it in a product catalog in the same shape a regulatory control has;
component-first puts it inside the document describing the thing being hardened;
assessment-first puts it in the plan that assesses it, and it never enters the
implementation layer at all.

Then rule to check moves ahead of rule to control, in all three. The rule, then
the thing that tests it, then what runs it, then the claim and the result, with
the tie to a control beside them rather than ahead of them. The order is the
same in every column, which is what makes the three comparable.

**Three checks moved with it,** and the new one is the one worth having:
`verify.py --joins` now fails if any chain reaches the control before the check,
which is the arrangement this was written to correct rather than a count that
happens to be right today. Tested by putting catalog-first back the way it was:
one failure, naming the order it found.

The other two were counts that assumed one block per hop. The step list is one
longer now, and its first block has one end rather than two, so the link count
is odd by exactly one where the parity used to be the check.

**One repair.** The step count in `pagecheck.js` used `.joins__steps > li`, and
the DOM shim in that file implements descendant and attribute selectors but not
the child combinator, and returns nothing rather than erroring on one it does
not know. It read zero steps on all three pages. Descendant selector now, with a
note, since the list has no nested lists and the two would select the same
elements regardless.

### Three properties off the catalog control

**Date:** 2026-08-24

`SeverityLabel`, `TriggerType` and `EvaluatedServices` are gone from the
catalog-first encoding of question 1, on the call recorded in the conversation.
Both rules, so both blocks on the six questions page.

None of the three answers what question 1 asks. The question is where the rule
is written down and what it says must be true, and that is the id, the
statement, and the part naming the check. `Periodic` and `Ubuntu24` are facts
about how one publisher's engine schedules and scopes a run rather than about
the requirement, and the severity is already carried on the assessment-first
encoding of the same rule, from the publisher's own STIG properties, where a
reader comparing the columns will meet it.

This is a deliberate departure from the published shape, which does carry all
three on the control. The generator's docstring says so rather than continuing
to claim the encoding is what AWS publishes.

The cell still declares `prop` as one of its mechanisms and is still right to:
`TechnicalControlId` on the assessment-method part remains, and it is the whole
of how a control reaches its check in this approach. Removing it would have
made the badge false, which is the thing to watch when trimming an encoding.

Nothing else read the three. The composite panes are built from the same
function and lost them too, and nothing has rendered those since the
side-by-side page was removed.

### Every encoding lights the part that answers the question

**Date:** 2026-08-24

A block is a whole document, deliberately, because what is absent from one is
often the finding. The cost is that the lines a reader is being sent to look at
arrive wrapped in metadata, and on a page putting one question to three
approaches the part that differs is the part worth seeing first.

**The spans are computed, not typed.** `tools/pattern_examples.py` carries a
`FOCUS` table naming, per question and approach, the key whose value answers
that question. It scans the serialised block, balancing brackets and skipping
strings, and commits the line spans into `data/pattern-examples.json`. Every
match is lit rather than the first: two activities each carrying a
`related-controls` is two answers to one question, not one answer and some
noise. The generator fails outright if a key is no longer in the block, which is
what catches an encoding reshaped under a focus written for its old form.

**Two channels.** The lit lines take the lift `--code-focus` was added for, plus
a rule down their left edge. The rest drop to `--code-dim`, which is the token
named for context lines and is 5.9:1 on the code surface: dimmed, not disabled,
so a reader who wants the whole document can still read every line. The dimming
has to reach the syntax colours too, or a key on a context line sits at full
strength inside a line meant to have receded.

**What is lit, per question.** Catalog-first: the `TechnicalControlId` props,
the `maps`, the `ConfigRuleId` props, `assessment-subjects`, `by-components`,
`findings`. Component-first: `rules`, `implemented-requirements`, `checks`,
`assessment-subjects`, the validation `type`, `implementing-rules`, the proposed
`result`. Assessment-first: the STIG props, `related-controls`, `steps`,
`assessment-subjects`, `assessment-platforms`, `import-ssp`, `findings`.

Question 1 of the assessment column was `activities` first, which lit fifty
lines of fifty-six and therefore pointed at nothing. Narrowed to the properties,
which is where that rule's identity is written and is the same answer the
catalog column gives one line above it. A check now fails any focus covering
more than three quarters of its block, so that mistake cannot come back
unnoticed.

**Checked on both sides.** `verify.py --example` asserts every block names a
focus, that every span lands inside the block, that the first lit line carries
the key it was computed from, and the three-quarters rule. `pagecheck.js`
asserts the renderer applies them: every line wrapped and exactly the declared
count lit, per block, counted rather than sampled, because a renderer lighting
the first line of everything would pass a spot check and tell a reader nothing.
Tested by making the renderer ignore the spans: 64 failures.

### The lit lines were double-spaced, and the harness could not see it

**Date:** 2026-08-24

Reported from the page: a blank line between every line of every encoding.

Each line is wrapped in a block element so the lit ones can carry a background
across the full width. The lines were then joined with a newline, which inside a
`<pre>` is a text node in preserved white-space: the block already starts a line
and the newline starts another, so every line rendered twice as tall. Joined
with nothing now. The line breaks live in the layout rather than in the text.

The clipboard is unaffected. The Copy button writes the block's own content, and
a browser puts newlines back between block elements on a manual selection.

**The interesting part is why 591 checks passed with it.** Two of them counted
the lines and the lit lines, and both totals were right: the bug added no lines,
it made each one taller. So a third was added, comparing the text read back off
the rendered block against the source.

It also passed. Putting the newline back into the join and rerunning gave a
clean run, which is the point at which a check is worse than no check.

The reason is the DOM shim in `pagecheck.js`: it drops a whitespace-only text
node, so the newlines between the lines were invisible to `textContent` and both
sides of the comparison came out newline-free. A browser does not drop them,
which is exactly why the page was double-spaced and the harness was green.

So the assertion reads the markup rather than the tree: no newline anywhere
inside the rendered code element. Retested the same way, and this time putting
the newline back fails 32 blocks, naming the count in each.

Both checks are kept. The text comparison catches a character being lost or
duplicated, which the newline rule would not.

### Question 1 was answering question 2

**Date:** 2026-08-24

Reported as an `implemented-requirements` showing under question 1. It was, in
the component-first column rather than the catalog one: of the six encodings
under that question, only component-first's parameterised rule carried it. The
catalog control has no control tie in it at all.

It was there to show where a parameter's value is set. Setting a value means a
control implementation, a control implementation requires an implemented
requirement, and an implemented requirement names a control and the rule that
implements it. So the block answering "where is the rule written down" was also
answering "how does it reach a control", one question before that was put, and a
reader met `control-id` and `implementing-rules` with no framing for either.

Split along the line the questions already draw. The declaration stays on
question 1, which is that column's whole answer for a rule carrying a value: the
rule names its parameter and gives it a label. The value moves to question 2,
onto the control implementation that was already there, which is the construct
that scopes it. Question 2 had the tie and not the value; it has both now, which
is a better answer than it was giving.

`verify.py --example` fails any question-1 encoding containing
`implemented-requirements`, `control-id`, `implementing-rules`,
`related-controls` or `mapping-collection`. That is the rule rather than the one
instance: a question answers itself and not the one after it. Tested by putting
the control implementation back, which fails and names both terms it found.

### Six properties off the rule, and two questions on the record

**Date:** 2026-08-24

The assessment-first encoding of question 1 carried method, three STIG
identifiers, severity and category. They were two thirds of the block: a reader
looking for where the rule is written down read a namespace six times before
reaching the requirement. They are gone, and what is left is an activity with an
identifier and a title, the title being the requirement itself.

Two of the six had a further problem, worth recording. **Category is severity,
spelled differently.** The XCCDF rule carries a severity attribute and no
category: CAT I, II and III are DISA's presentation of the same value, so the
block stated one fact in two vocabularies. And **method is core OSCAL** rather
than an extension, so of the six it is the one that already has a home.

The focus moved with them. It was `props`, which after the removal would have
lit the check property on the step beneath, and that is question 3's answer
arriving under question 1 again. It is the activity's own title now, which
needed a way to say "this key, not the one nested under it": a key ending in `^`
takes only its shallowest occurrences, with depth read off the indent that
`json.dumps` sets rather than a number written in the table.

### What the guides carry, counted

Dropping metadata from an example is not deciding it needs no home, so both
questions go on the open questions page with the corpus behind them.

**The Ubuntu 24.04 STIG, 194 rules.** Every one has a severity, a weight, a
version string that is the STIG identifier, a title, a fix, a fixtext, a check,
and a packed description holding eleven named sub-fields: VulnDiscussion,
FalsePositives, FalseNegatives, Documentable, Mitigations,
SeverityOverrideGuidance, PotentialImpacts, ThirdPartyTools, MitigationControl,
Responsibility, IAControls. 318 CCI identifiers across the 194, so 1.6 each.

**The CIS Ubuntu 24.04 Benchmark, 312 recommendations.** Every one has a title,
a description, a rationale, a weight, a remediation, an audit procedure, and a
status saying whether it is automated, 291, or manual, 21. 309 carry identifiers
into CCE and the CIS Controls; 289 carry safeguard metadata with implementation
groups, asset type and security function.

**Section 5, where the metadata goes.** Some of it has a home: method is core, a
title and a description are fields on almost everything, and an identifier can
be a property. Some does not. No released model has a field for the severity or
priority of a rule, so AWS carries SeverityLabel in its own namespace on all 452
controls and the STIG conversion carries it in DISA's. Nothing says whether a
check is automated or manual, which is a distinction CIS draws on every one of
its 312. Rationale, where it is separate from description, has no field either.

**Section 6, where remediation lands.** Not a corner case: 194 of 194 STIG rules
carry a fixtext and a fix element with an identifier, and 312 of 312 CIS
recommendations carry a remediation. The three approaches answer it three ways
and none of them with a field. Catalog-first points at it, and this is
systematic rather than incidental: all 452 AWS controls carry a link with rel
remediation to the publisher's documentation. Assessment-first inlines it as a
second step marked with a step-type property whose value is remediate.
Component-first does not carry it; the proposal covers the rule, the check and
the result.

OSCAL does have a remediation construct, in the plan of action and milestones,
where a risk takes a response. That is a different thing: the POA&M answers what
to do about this finding on this system, and the guide answers how anyone fixes
this condition anywhere, written once, before any assessment has run. Whether
those are two constructs or one is the question.

The page is eleven sections now, five of them questions put to the group. The
numbering, the table of contents and the three meta descriptions were rebuilt
from the section ids rather than edited by hand, after a first attempt renumbered
sequentially and collided with itself: 6 became 8, and the next pass looking for
8 found the one just written.

### In the assessment approach the rule and the check are one thing

**Date:** 2026-08-24

Question 1 of the assessment column lights the check property now, not the
activity's title.

That looks wrong until the reason is stated, which is why the cell's note states
it. The activity's title is the requirement and the step's check property names
the test, and no construct in this approach holds one without the other: there
is no rule here that is not already a check. Lighting the title said the rule
was the sentence, which is the half of it that is prose. This is a real
difference from the other two, where the rule and the check are separate
objects: a control and a software component in one, a rules entry and a checks
entry on two components in the other.

The note carries the consequence as well. A value has nowhere of its own to go.
The fifteen in the second rule is inside the title text rather than in a
parameter, so tailoring it means editing the sentence. That is the same finding
the approach page already records as a risk, now stated where a reader meets the
encoding rather than only where the argument is made.

**A mechanism left without a user.** The shallowest-only focus selector was
added an hour earlier for exactly this cell and is now unused. It stays, because
the problem it solves returns the moment a focus names a key that also appears
nested under itself, and a title or a props is that kind of key. But an unused
mechanism with no test is one that rots without anybody noticing, so it is now
exercised directly against a document written in the check rather than against
whatever the encodings happen to contain: a key at two depths, two spans for the
plain form and one for the shallowest.

### The parameter gap is an open question, not a mark

**Date:** 2026-08-24

Assessment-first has no parameter on an activity or a step, so a rule that
carries a value has to write the value into the requirement text. Where that
belongs took three attempts and the third is the right one.

It was first a clause inside a cell note, which changed nothing about what the
matrix said. It was then a mark: question 1 assessment-first set to Partly
answered, plus a paragraph above the three tabs comparing all three columns.
Both are gone. The paragraph said at length what the cells say in place, and the
mark was wrong for a reason worth recording: **the approach is not failing to
use a construct, it is being asked to use a construct that does not exist.** A
column marked partial reads as content somebody did not write. Nobody could have
written it.

So the cell is Answered and its note states the fact plainly, that an activity
and a step have no parameter and the value goes into the rule itself. The
argument moved to section 7 of the open questions page, which asks whether an
activity or a step should be able to declare a parameter, or whether a
tailorable value belongs elsewhere with the plan pointing at it.

The evidence is the same either way and is still checked: catalog-first declares
a param on the control and inserts it into the statement, component-first
declares a param on the rule and sets the value through set-parameters, and
assessment-first has neither, with the literal fifteen still in its activity
title. What changed is which of the site's surfaces carries the conclusion.

Two consequences are stated in the question rather than in the cell, because
they are the reason it matters beyond one rule. Tailoring means editing the
requirement text, so an organisation setting its own minimum is rewriting the
guide rather than setting a value against it. And a profile has nothing to
tailor, because set-parameters needs a parameter to point at.

The open questions page is twelve sections now, six of them questions put to the
group. The `across` slot field added for the removed paragraph went with it,
along with its renderer, its style rule and its two checks.

### One property on the check component

**Date:** 2026-08-24

`asset-type` and `ResourceType` came off the catalog-first encoding of question
3. What is left is `ConfigRuleId`, which is the identifier the engine is handed.

Both removed properties are in the published component and neither answers the
question. Question 3 asks what the test is and how it is reached from the rule,
and the answer is the component title matching the control's
`TechnicalControlId` and this value being the thing that runs. An asset-type of
automated-inspection and a ResourceType naming what is inspected are facts about
the subject, which is question 4.

That is the third encoding trimmed on the same rule this session, and the rule
is worth stating once: a block answers its own question. The three properties on
the catalog control, the six on the assessment activity and these two were all
real, all published, and all describing something the question above them was
not asking.

**One allowance withdrawn.** `asset-type` had been added to the list of property
names exempt from the "every property carries a namespace" check, because OSCAL
defines it and the publishers' own files therefore give it none. It appears in
no encoding now, so it is off the list. An exception for a property that appears
nowhere is permission granted for nothing, and if it comes back it should have to
be argued for rather than arriving under a standing allowance.

### Question 3 asks about the runtime, not about the hop

**Date:** 2026-08-24

The question was "What is the test, and how is it reached from the rule?" It is
"What check executes the rule within a runtime environment?" now. The question
mark is added, because the other six slots carry one and this is a question like
they are.

The catalog-first cell went with it. It read "Two parallel joins. The normative
one is a control-id hop through source and back-matter. Alongside it, the control
names its check by title and a software component carries that same title, which
is a match on a string rather than a reference the schema can check." It now
reads "The check is the bridge to the machine runtime environment. This
identifier executes a machine check or automated test."

The two changes go together. The old question asked how the check is reached
from the rule, so the cell answered with the reaching: two joins, one of them a
string match. The new question asks what executes, so the cell answers with the
identifier that does.

**The join finding is not lost, and it is worth saying where it went.** It was
never only in that cell. `data/joins.json` carries it as a step of the chain,
typed `name-match` in a closed vocabulary of five, and it renders in section 3 of
the catalog-first page: "Two relationships pointing opposite ways. The control
names its check by title, which no schema can validate, and the check names its
control by id, which resolves through the control implementation's source and
back-matter." That is where a claim about how something resolves belongs now
that the cell is about what runs.

### The prop that carries the check was not named
**Date:** 2026-08-24

Reported against catalog-first, question 3, on the six questions page: the
assemblies had to show that a prop carries the `ConfigRuleId`.

The cell already declared the right mechanism. `mechanisms` was
`["assembly", "prop"]`, so the badge row said PROP. What it never said was
which prop. The carrier block rendered `Model: component-definition` and
`Assemblies: component, implemented-requirement`, and a reader looking for the
thing that reaches the runtime check found a box reading "component".

`ConfigRuleId` is in the cell's own extract already, on the component at
`/component-definition/components/2`, with `ns: http://aws.amazon.com/ns/oscal`
and value `ACM_CERTIFICATE_RSA_CHECK`. Nothing needed extracting; it needed
showing.

**Where the box goes, and why not in a row of its own.** First attempt gave it a
`Properties` row under the assemblies. Corrected from the page: a proposed
assembly is already drawn as a dashed box inside the assemblies row, so a prop
belongs in that row too, as a box carrying its own name. One row lists what
carries the answer and the border says which kind each one is: solid for a
released assembly, dashed for proposed, dotted for a prop. Those are the three
borders the mechanism badges already use, so the box repeats what its badge
declared rather than starting a second vocabulary.

The namespace is on the box's title rather than in the row, because the row has
to stay scannable across three columns, and it is the namespace that makes the
value unreadable to a tool that does not know it.

The row's label follows what is in it. It was fixed to `Assembly`/`Assemblies`
off the assembly count; a cell whose answer lives in a prop with no assembly
around it now reads `Prop`/`Props`. Calling a prop an assembly is the exact
mislabelling this block was built to prevent.

**Verification.** Three checks in `--example`, and the first two are the ones
worth having because they hold the page against the extract rather than against
prose: a named prop has to appear as a prop of that name somewhere in the cell's
own encoding, and it has to carry the namespace the cell claims for it. The
third refuses a prop box on a cell that does not declare the mechanism. Two in
`--pages`: a prop box names a prop, and its title says it is a prop rather than
leaving a dotted border to be decoded.

Mutation tested three ways. Renaming the prop to one the file does not carry
turns both evidence checks red. Changing the claimed namespace turns the second
red and prints what the encoding actually has. Dropping `prop` from the cell's
mechanisms turns the declaration check red alongside the existing
under-declaration check.

`2338/2338` verify checks pass with 18 skips, `667/667` page checks pass.

**Four cells still declare the prop mechanism and name no prop.**
`q1/catalog-first`, `q1/assessment-first`, `q3/assessment-first` and
`q6a/assessment-first`. Their encodings carry candidates, but which prop is
load-bearing for a given question is a judgement about the content and not
something to infer from a prop list, so they are left alone and recorded here.
Until they are filled the row is asymmetric: catalog-first names its prop at
question 3 and assessment-first names none anywhere, which reads as a
difference in the content rather than a difference in what has been written
down.

### The prop box was styled like the badge, and read like neither
**Date:** 2026-08-24

Reported from the page: the `ConfigRuleId` box should look like the dotted box
the PROP badge sits in, and should carry a colour.

It already carried the badge's colour. `--slot-5-border` and `--slot-5-fg`, the
same two tokens `.mech--prop` uses. What it did not carry was the badge's border
weight. `.mech` is `2px`; every box in the carrier row is `1px`, inherited from
`.carrier code`. **A 1px dotted border at text size is nearly a solid line**, so
the box read as an ordinary assembly with an odd tint. Dashes survive 1px, which
is why the proposed box has looked right all along and the prop box did not.

Both boxes are 2px now, on the page background rather than the subtle one, so
each matches the badge that declares it. The prop box is also set at the badge's
weight, 650, because at 2px the dots crowd a light glyph.

**A check, because this is two places saying one thing.** A box and its badge
have to agree on border style and on hue token, asserted per pair. Weight is
asserted separately, since weight is what was wrong rather than colour.

**The check failed first time for a reason worth keeping.** It read the *first*
rule matching a selector, and after this change each selector appears in two: a
shared rule setting weight and background, then one each for style and hue. It
found the shared rule, saw no `border-style`, and reported the border style as
missing on both pairs. Now it collects every rule whose selector list contains
the selector and reads them together, which is what the cascade does. A
one-rule-per-selector assumption is wrong in any stylesheet that groups.

Mutation tested three ways: drifting the prop box's hue off its badge, drawing
it dashed instead of dotted, and putting the weight back to 1px. Each turns red,
and the weight one turns both pairs red because they share that rule.

`2344/2344` verify checks pass with 18 skips, `667/667` page checks pass.

### The prop box on the other three cells
**Date:** 2026-08-24

Reported from question 1 of catalog-first: the PROP badge was there, the box was
not, and the prop is `TechnicalControlId`. Correct, and the same omission was on
two more cells.

Which prop answers a question is a judgement about content, so the previous
entry left these unfilled rather than guessing. It did not need guessing. The
site already records the answer: `data/pattern-examples.json` carries a
`focus_key` and a lit span per block, which is the site's own statement of which
lines answer that question. Reading them:

| Cell | `focus_key` | Prop, from the lit span |
| --- | --- | --- |
| q1 catalog-first | `props` | `TechnicalControlId`, `http://aws.amazon.com/ns/oscal` |
| q1 assessment-first | `props` | `check`, `http://comply0.com/ns/oscal` |
| q3 assessment-first | `steps` | `check`, `http://comply0.com/ns/oscal` |
| q6a assessment-first | `import-ssp` | none |

The first two light a props array directly. The third lights `steps`, and its
own `shows` text says "the steps are the check, and a check prop names it", so
the prop is load-bearing there even though the lit span is the assembly around
it. Names and namespaces were read out of each cell's own blocks rather than
typed, and the existing evidence check then holds them against the same blocks.

**q6a of assessment-first still names no prop, and that is the right answer
rather than an omission.** What carries the claim there is `import-ssp` and a
back-matter resource. The cell declares the prop mechanism because `observed()`
derives it from the document and the document does contain namespaced props, but
none of them carries this answer. The only prop named `type` in those blocks has
no namespace at all, so it is core OSCAL rather than a publisher extension.
Naming it would put a box on the page for a prop that answers nothing.

Worth stating plainly: the prop mechanism being declared on a cell and no prop
being named are now two different claims, and the second is not a gap. Four
cells name a prop, one declares the mechanism without one, and the reason is
here rather than inferable from the page.

`2353/2353` verify checks pass with 18 skips, `667/667` page checks pass.

### The prop box was never dotted, and the check could not have known
**Date:** 2026-08-24

Reported: the border is not dotted when the box shows `TechnicalControlId`.

Correct, and it was never dotted on any cell. Nor was it 2px, nor on the page
background. **Only the colour and the font weight ever reached the page**, which
is why the last two entries read as if the styling worked: the box was tinted,
and a tint was the thing being asked for.

`.carrier code` is `(0,1,1)` and sets the whole `border` shorthand. A bare
`.carrier__prop` is `(0,1,0)`. Specificity beats source order, so the shorthand
won `border-style`, `border-width` and `background`, and the three declarations
underneath it were discarded before a browser ever drew them.

`.carrier__assembly.is-proposed` escaped this by accident, being `(0,2,0)`,
which is the whole reason the proposed box has looked right since the day it was
written and the prop box never did. The comparison that was supposed to prove
the two matched was comparing a rule that applied against a rule that did not.

**It also hit a rule nobody was looking at.** `.carrier__model` sets
`border-color: var(--border-strong)` at `(0,1,0)` and has been losing it to the
same shorthand for as long as it has existed. The model box has been drawn in
the ordinary border colour the entire time. Fixed with the others.

All three are qualified `.carrier code.<class>` now.

**The check could not have caught this, and that is the part worth fixing.** It
read declarations as text. A stylesheet can contain `border-style: dotted` and
draw a solid line, and every text-matching check in this file would call that a
pass. This is the third time in the log that `--css` has certified something the
browser was ignoring.

So the border declarations are now resolved instead of searched. For each box,
every rule that could match an element with those classes is collected, ranked
by specificity with source order breaking ties, and the winner is asserted to be
the intended one. When it fails it names the thief:

    the prop box's border style survives the cascade
      | 'dotted' expected, '1px solid var(--border)' wins from '.carrier code'

Comments are stripped before either helper scans, because these read selector
blocks with a regex and a comment mentioning a border would otherwise be read as
a declaration, letting a note satisfy the check it was describing.

Mutation tested by putting the shipped bug back. Unqualifying both prop rules
turns four checks red, two of them naming `.carrier code` as the winner.
Unqualifying only the width turns the width check red and leaves the style check
green, which is the discrimination the old check never had.

Swept the rest of the row: every `.carrier` rule touching a border is now at
`(0,2,1)` or higher, so none of them loses to the shorthand.

`2357/2357` verify checks pass with 18 skips, `667/667` page checks pass.

### The bulk block lights the check, and says so in its title

**Date:** 2026-08-24

Reported from question 3 of assessment-first: on the block showing the check at
the activity level, the lit lines should be the check, and the title should say
what the arrangement is.

Both were wrong for the same reason. The block was labelled "Either placement,
one runner at a time", which names the choice rather than what is being shown,
and it inherited the cell's focus key of `steps`. That key is right for the two
blocks where each step holds its own check and exactly wrong here: the whole
point of this block is that the check has moved off the steps and onto the
activity above them, so lighting the steps lit everything except the thing it
was drawn to show.

It is titled "Multiple tests, with the check at the activity level" now, and it
lights the activity's `props`, which is where the check went.

**Focus can be overridden per block.** It is keyed on the question and the
approach because the two rules in a cell are the same shape and the same part of
each answers the question. An extra block exists to show that answer arranged
differently, so it can declare its own key beside its label and its prose, which
is where the rest of what makes it different already lives.

The lit span covers `method` as well as `check`, both being in the one props
array. Left as is: an array is the unit the focus mechanism addresses, and
splitting it would mean targeting an object by one of its own values, which is a
different mechanism for one line of gain.

**Checked as a difference, not as a literal.** An override that stopped being
applied would fall back to the cell's key, light the wrong lines, and break
nothing else, so the assertion is that a block declaring its own arrangement
does not light what its siblings light. Tested by deleting the override:
`'steps' against ['steps']`.

`2367/2367` verify checks and `667/667` page checks pass.

### Lighting one element of an array

**Date:** 2026-08-24

The bulk block lit its whole props array, which meant lighting a `method` of
TEST that nothing was asking about beside the `check` that was the point. Only
the check is lit now.

An array element has no key above it to name it by, so it is addressed by a
value it carries: `name=check`. Two selectors existed before this, a plain key
and a key marked shallowest-only, and both find a keyed value. This finds an
object.

**Found by indentation, not by counting brackets.** A value can contain a brace.
The catalog statement holds an insert directive written with them, and a scanner
balancing braces without tracking string boundaries would close the wrong
object. `json.dumps` lays out an indent deterministically, so an element opens on
the nearest line above at two spaces less and closes on the next line at that
indent, and neither line can be inside a string.

The self-test carries that case rather than describing it: the sample array has
a brace inside a string value on the element that must not be selected, so a
bracket-counting implementation fails it.

**The evidence check changed shape with the selector.** It asserted that the
first lit line carries the focus key, which is true of a keyed value and false
of an object, whose first line is a brace. For this form it asserts instead that
the value is somewhere inside the span, and that the span is a whole object,
opening on `{` and closing on `}`. Without that second half a span could drift
by a line and still contain the value.

Mutation tested by pointing the selector at `name=method`, which moves the lit
span from lines 13 to 17 onto lines 9 to 12, the other object in the same array.

`2370/2370` verify checks and `667/667` page checks pass.

### Question 4 answers from the plan of record, and one block answers from the assessor's

**Date:** 2026-08-24

The question is unchanged and right: what exactly is being tested. What changed
is where the two implementation approaches answer it from.

Both answered with `assessment-subjects` in an assessment plan, which is the
assessment layer answering a question about implementation. They answer from the
plan of record now, and they answer it identically, because OSCAL gives them one
way to answer. **A control response is a by-component.** It names a component and
takes no subject of its own, so a response covers every machine the component
stands for and cannot say which one it was true of. That is a limitation of the
model rather than of either approach, and both cells state it.

The difference between the two columns is elsewhere and is one line:
component-first adds the proposed `implementing-rules`, so its response says
which rule it rests on. Catalog-first has nothing that does. Adding that line
also made the cell rest on a proposed assembly, which the under-declaration
check caught immediately: declared `assembly`, encoding also uses `proposed`.

**The assessor's copy.** Component-first gains a second block showing the
component definition carried into an assessment plan as an assessment asset,
with the checks travelling on the component that runs them and each check naming
what it tests through `target-component-uuid`. That is the shape the
component-first corpus already publishes, so the block is evidenced rather than
invented, and `ibm-validation-ansible` is now the cell's extract.

It matters because hardening guidance publishers and software vendors publish
secure configuration guidance openly, so the definition an assessor needs can be
a public document rather than something the system owner hands over. **The
catalog approach has no equivalent**, and the reason is stated in its cell: an
assessor cannot introduce a catalog into an assessment, so what is assessed is
whatever the plan of record already selected. Recorded as the answer rather than
raised as a section, on the call in the conversation.

**Two mechanisms in the generator, both small.** An extra block can now name its
own wrapper as well as its own focus, because an extra exists to show an answer
arranged differently and that sometimes means a different document. And the
check holding every block to its cell's model now applies to the cell's own
blocks; an extra has to open with an OSCAL model, and which one is its own
business. Holding all of them to one model said the second document was the
wrong document.

`2379/2379` verify checks and `668/668` page checks pass.

**Left alone, and worth a decision.** The two cells keep their answer states,
`empty-absent` for catalog-first and `partial` for component-first. Those states
describe published content, and neither corpus publishes a system security plan,
so on the new framing both would be `empty-absent`. Changing a headline state is
a claim about the corpora rather than about the encodings, so it is flagged here
rather than made.

### The by-component limitation is a risk on both implementation approaches

**Date:** 2026-08-24

A control response in a system security plan is a `by-component`, so it names a
component and never an instance. One Ubuntu component can stand for a hundred
Ubuntu instances whose configurations differ with the applications they run, and
nothing can record that ninety-nine apply a rule and one carries an exception.

Catalog-first had a version of this already, worded loosely and carrying a typo.
It is rewritten around the inventory case. Component-first did not have it and
now does, with the one thing that approach adds: the proposed
`implementing-rules` names the rule a response rests on, so an exception reaches
a rule but still not an instance.

**The equal-count rule is gone.** Every page carried three strengths and three
risks, enforced in three places, so that the shape of the block could not itself
be an argument. Component-first has four risks now. The rule was doing real work
and it was also the reason this risk had to displace another one to be said at
all, and a rule that decides what can be stated about one approach because of
what was stated about another is deciding the content rather than protecting it.

Removed from `data/tradeoffs.json`, from the generator's build guard, and from
both harnesses. What replaces it is weaker and honest: every page states at
least one of each, and the page renders exactly the count its own data declares
rather than a shared number, which would have asserted the retired rule.

**The length budgets stayed, and one of them moved.** The strengths and risks
block is still held across the three pages, at 20 per cent rather than 10,
because an approach with a fourth risk cannot come within 10 per cent of one
with three unless its entries are cut to a length that says nothing. The whole
page budget is untouched at 10 per cent and is the one doing the real work: it
bounds the total a reader compares and says nothing about which side of the
block it falls on. The two columns within a page are still held within 20 per
cent of each other, and that rule earned its keep immediately, failing on
catalog-first at 126 against 169 because the rewritten entry was too long. Cut,
rather than the rule relaxed.

    catalog-first     pros 129  cons 154   total 283
    component-first   pros 147  cons 174   total 321
    assessment-first  pros 141  cons 130   total 271

`2385/2385` verify checks and `668/668` page checks pass.

### The assessment walkthrough, read against the six questions

**Date:** 2026-08-24

Fifteen slides showing the Easy Dynamics approach end to end, sequenced by the
number in each corner. They open on the assessment plan skeleton and four
framing questions: what tools, what system, which controls, how orchestrated.
Three of the four map onto the six questions. Read against the matrix, three
cells were showing one level of a two-level answer.

**Question 2 was showing the inner level only.** `reviewed-controls` at plan
level says which controls the assessment may touch; `related-controls` on the
activity names the ones that activity is for, read against that scope. The cell
named the second and not the first.

The distinction matters for what the site says elsewhere. The tie from a rule to
a control is optional here and an activity can carry none, which is the site's
position on question 2. The plan's declaration of controls under review is not
optional: it is `[1]` on the model and present in 15 of 15 published Easy
Dynamics plans. So an approach that puts rules in an assessment plan is
committed to naming a control scope whether or not any rule is tied to anything,
and that was nowhere on the site.

**Question 4 was showing one part of three, across one model of two.** The plan
scopes with `assessment-subjects`, each activity targets within that scope
through its task's `associated-activities`, and the thing itself is an
`inventory-item` in the plan of record carrying the identifier a runner needs to
reach it.

This is the counterpart to the risk added an hour earlier. Both implementation
approaches respond by-component and cannot reach an instance; this reaches one of
the hundred machines the component stands for. The site had the limitation and
not the contrast. The instance is a second block on the cell, in the system
security plan rather than the assessment plan, which is what the per-block
wrapper added earlier is for.

**Question 5 was one assembly where the corpus has a chain.** A platform, a
component beneath it holding what the platform needs to find and invoke the
plugin, and a property on the task naming which platform a given run uses. The
cell now declares the prop mechanism it always rested on.

**machine-context is not a new label.** It appears on the check, on the subject
and on the runner, and the site does not name it as a construct: it is how this
approach reaches a machine, and the check is what it is reaching for. Recorded
on the call in the conversation.

**Orchestration became a strength rather than a question.** Tasks carry
`timing.at-frequency`, the platform that runs and the activity that is run, and
no other approach expresses when an assessment happens at all. It is a fourth
strength on the assessment-first page rather than a seventh question.

**Which meant relaxing one more bound, and it is worth naming the pattern.** The
two columns on a page were held within 20 per cent of each other. With counts
following content a page can carry four of one and three of the other, and a
tight bound then makes prose length compensate for count, which is the
distortion the count rule was retired for: it would have meant writing the
fourth entry short enough not to unbalance the column rather than long enough to
say the thing. The bound is 30 per cent.

That is the third guard loosened today, so the reasoning should be checkable
rather than taken on trust. What each approach spends in total is the number
that matters, it is still held across the three pages, and it is closer than it
was before any of this: 283, 321 and 309 words.

`2404/2404` verify checks and `672/672` page checks pass.

### The cell notes are notes again

**Date:** 2026-08-24

Two notes were held up as the pattern: "One control per rule. Existing
assemblies capture context around the rule's intent." and "Rules sits on the
component as a sibling of control-implementations." Both name the construct and
stop. Eleven others had grown to two and three times that, most of them written
today, and they had stopped naming constructs and started arguing.

Longest to shortest across the twenty-one: 71 words down to 10, mean 32.
Afterwards: 32 down to 10, mean 22. The eleven rewritten ones lost 60 to 70 per
cent of their length and none of them lost a fact.

What went was consistently the same thing. A sentence explaining the consequence
of the construct just named, which is what the strengths and risks block on each
approach page is for. Question 4 of the catalog approach said a by-component
"covers every machine the component stands for and cannot say which one it was
true of"; the risk on that page says exactly that, at length, where a reader
weighing approaches is looking. The cell now says it names a component and not
an instance, which is the construct.

Three notes are held by checks and were written around them: question 2 of the
catalog approach has to say the tie is made by the mapping model, not inline,
and that no publisher has shipped one, and question 1 of the assessment approach
has to name the parameter and the value. All three still do.

A rule for next time, since this is the second batch of prose trimmed today. A
cell note says what the construct is. If a sentence in one would still be true
with the construct removed, it belongs on the approach page or in an open
question, not in the cell.

`2404/2404` verify checks and `672/672` page checks pass.

### A property that came off a slide, and the block built on it

**Date:** 2026-08-24

Reported from the page: question 4 of the assessment column showed a PROP badge
above a block with no property in it. Then, on being asked where
`machine-context` came from, the answer turned out to be worse than the badge.

**It came off a slide.** Slides 6, 9 and 17 of the walkthrough use that name.
Checked against the files:

    q5, the plugin component   the published prop is named context, not
                               machine-context, in ap-cisa-scuba-scubagear.json
                               at /assessment-assets/components[0]/props[0],
                               and the site already quotes it as
                               ez-cisa-assessment-assets

    q4, the inventory item     machine-context is real, exactly once, in
                               Pattern-Library-main/summit/system-security-plan/
                               summit_system_ssp.json, a body of content this
                               site declares nowhere: not in provenance.json,
                               not in sources.json, not in any snippet

So one encoding used an invented name where the right one was already in
`data/snippets`, and the other rested on a corpus the site does not admit
holding. Both were written from a picture rather than from a file, in a session
whose whole subject is where content lives.

**What changed.** The block is gone, with its builder and its focus. The
property on the plugin component is named `context`, which is what the shipped
file calls it. Question 4 of the assessment column no longer declares the prop
mechanism, because the property was in the block that was removed, so the badge
comes off the page with it.

**The badge was the visible symptom and is worth fixing on its own terms.**
Mechanisms are declared per cell and blocks are per rule, so a cell can show a
badge that the block a reader is looking at does not support. The
under-declaration check only runs one way: it catches a cell using a mechanism
it did not declare, never a cell declaring one no visible block demonstrates.
Left as a gap rather than patched over, and recorded here.

`2395/2395` verify checks and `668/668` page checks pass.

### Question 5 shows what the runner sits between

**Date:** 2026-08-24

Question 5 is the only one of the seven whose answer is a step rather than a
place. The other six ask where something is written down. This one asks what
performs the check, and a runner is legible only as the thing between an input
and an output. The cell showed the runner alone.

Each approach now carries a lineage strip under its note: the document that goes
in, the in-machine-out mark, and the document or documents that come out.

**It is a link, not a third copy.** Both ends are already on the page. The input
is the document at question 3, because the check is what a runner takes, and the
output is the claim at 6a, the result at 6b, or both. Each tile is an anchor into
the question that holds it, and a line under the strip says so, because the
alternative was printing the same JSON a third time under a different heading.

    catalog-first     component-definition  ->  system-security-plan
    component-first   component-definition  ->  system-security-plan or
                                                assessment-results
    assessment-first  assessment-plan       ->  assessment-results

Catalog-first gains the strip and keeps its evidence block. Its cell says no
construct names an executor, and that stays true: the strip shows the two ends
and the mark between them is what OSCAL does not name here. Both ends were read
off its stakeholder mapping rather than chosen.

**Named by question, not by model.** The lineage declares `in: "3"` and
`out: ["6a"]`, and the labels are read off the cells at those questions. A model
renamed in one place cannot leave the strip saying the old name, because the
strip has no name of its own.

**The mark is borrowed, and that is the point.** The same glyph the stakeholder
mapping draws on every approach page for exactly this. A reader moving between
the two pages meets one vocabulary rather than two. It is a copy of a string
that also lives in `tools/approach_pages.py`, which is the one thing here worth
watching: a Python constant and a JavaScript one drawing the same picture.

**Checked against the mapping rather than trusted.** Two places now say what a
run produces, so `verify.py --example` compares them: an output named in the
lineage has to be one the stakeholder mapping draws for that approach. Tested by
giving assessment-first a claim as well as a result, which its mapping does not
draw, and by pointing an input at question 1: both fail and name the values.
`pagecheck.js` asserts the strip renders, names the right number of ends, draws
the mark, and that every end resolves to an anchor the page actually has.

`2412/2412` verify checks and `680/680` page checks pass.

### Removing what nothing points at, and making that a rule

**Date:** 2026-08-24

Three kinds of rot, all of the same shape: something was generated or defined,
the thing that used it was deleted, and nothing failed.

**The layer maps.** Three figures, `71-layer-map-{catalog,component,assessment}`,
sat in assets/diagrams after section 3 of the approach pages was replaced by the
chain. They were built on every run, published to the directory, rendered to
grayscale for review and asserted against by four checks. No page had linked to
them for weeks. One of those four assertions read "all four layer maps share
byte-identical geometry" and had said four since two of the five were dropped,
which is what a check nobody reads looks like from the inside.

Gone: the three files, `diagram_71` and the eight symbols only it used
(`_map_body`, `_rings`, `LAYERS`, `MODELS`, `BAND_H`, `FOOTPRINTS`,
`FOOTPRINT_RULE`, `LAYER_DESC`), the entry in `BUILDERS`, the three names in
`PUBLISHED`, the phase in verify.py, and the two paragraphs of module prose that
still described five maps sharing one geometry. tools/diagrams.py loses 9,047
bytes.

**Eighty-eight stylesheet classes.** Whole families left by three deleted pages:
`exview__*` from the example walkthrough, `qcard__*`, `matrix__*`, `fill-cell__*`
and `diff-key*` from the comparison page, `reading__*`, `orientation*` and
`filter-bar*` from the component gallery, plus singletons like `published__label`
and `slot-strip__legend` from sections removed in the last few days. 134 rules,
15,508 bytes.

Two things had to be got right to do this safely. A class can be built rather
than written, `"slot-chip slot-" + slot.number`, so a prefix that something
concatenates or interpolates counts as a use; without that rescue the six
question colours and the two media badges all read as dead. And a rule this tool
does not change has to be emitted byte for byte: the first attempt reflowed
every selector list it kept, which broke four assertions that match the
stylesheet by exact string.

**Thirty-six grayscale renders** for figures whose source SVG no longer exists,
including families deleted long enough ago that their builders are gone too.

**And two guards, so this is the last time.** Both invert the direction the old
checks ran in. Every published figure has to be referenced by a page, because
the old checks all ran from the directory outward and so could never notice that
nothing pointed in. Every class the stylesheet defines has to be reachable from
markup, a script, a generator or a data file. 215 classes, 8 figures, all
accounted for.

Two things were found and left alone. `diagram_72`, `77`, `78`, `79` and the
three stakeholder variants are still built and then filtered out by `PUBLISHED`,
which is deliberate and commented: the builders cost nothing and hold the drawing
code in one place. And `scenario.html` has no "is current with its generator"
assertion, unlike every other generated page, so a hand edit to it would not stop
the build.

### Question 5 is answered by path, not by document

**Date:** 2026-08-24

The runner question showed one block per approach and the blocks were not
answering the same question. Component-first showed a validation component;
assessment-first showed an assessment platform; catalog-first showed nothing.
Three shapes, and no way to see that two of them are the same thing reached by
different parties.

The answer is a path. One recommendation is run by an implementer, to build the
responses in a plan of record, and by an assessor, to produce a result, and the
two runs read different documents. So question 5 is answered once per path:

- component-first has both. Its implementor's path is the runner as a component
  of the system, type validation. Its assessor's path is the same definition
  carried into an assessment plan as an asset, with the checks travelling with
  the component that runs them, which is the shape its corpus already publishes.
  Neither run needs anything from the other party.
- assessment-first has the assessor's path only: an assessment platform and the
  plugin it uses, in a plan the assessor owns.
- catalog-first has the implementor's path only, and it carries no block.

Neither JSON block is a plan of record or a result. What each shows is where the
runner is declared for that path, because the document the run produces is
question 6 and showing it here would answer that question twice.

**Why catalog-first has no block, having been asked for one.** Its cell says the
published content answers nothing here, and that is a claim about the corpus:
230 component definitions, 429 software components carrying a ConfigRuleId, no
component of type validation, no assessment platform, no prop naming an
executor. An encoding beside that would show a shape the content does not have,
next to a sentence saying it has nothing, which is the one contradiction this
page exists to avoid, and the harness refuses it: a cell showing JSON may not
also claim an absence.

So the path went into the note, where it is true without a shape to back it: the
implementor's path is a component definition into the plan of record, there is
no assessor's path because a catalog cannot be introduced into an assessment by
someone who did not write that plan, and what is named is the rule the engine is
handed, never the engine.

### The runner's answer is drawn as two paths

**Date:** 2026-08-24

Question 5 showed one lineage row: the check going into the runtime and out the
other side to "the claim, the result, or both". That "or" was doing too much
work. The two outputs are not alternatives off one run. They are two runs, by
two parties, reading two different documents.

So the cell is two sections now, each headed by whose path it is, each one file
in and one file out with the runtime between them, and each carrying the
encoding for that path directly underneath:

- **Implementor's path**: component-definition, runtime, system-security-plan.
- **Assessor's path**: the component definition is copied into an assessment
  plan, and the plan is what the runtime reads, producing the result. The two
  files of this path are the plan and the result; the definition sits in front
  of them with a copy mark, because that is where the assessor's plan got its
  checks.

Which paths an approach has is the finding. Catalog-first has the implementor's
only, and no assessor's, because a catalog cannot be introduced into an
assessment by someone who did not write the plan of record. Assessment-first has
the assessor's only. Component-first has both, and the harness asserts that it
is the only one that does.

**A copy mark, not an arrow.** Everywhere else on the site an arrow means
produced from. The assessment plan does not derive anything from the component
definition; it holds it, checks and all. So the mark between them is two
overlapping sheets and an arrowhead, and it is aria-hidden with "is copied into"
spoken beside it.

**A third shape for a cell.** Both harnesses knew two shapes for a column's
encodings, per rule or once for the whole document, and rejected anything else.
Question 5 is answered once per path, so the block keys are the path keys and
both harnesses learned the shape rather than having the rule relaxed: a column
answering by path has to carry exactly the paths its cell declares, no more and
no fewer, and each block still has to say what it shows.

The input of the assessor's path is named directly rather than read off question
4. That cell answers the subject question from the plan of record for
component-first, so its model is the plan of record, and borrowing it drew the
assessor reading an SSP. A document that means something different in the cell
you took it from is worse than one typed out.

### The runner is what happens between the checks and the assertion

**Date:** 2026-08-24

The two path sections were showing the wrong thing. Each drew a file flow and
then one encoding, and the encoding identified the runner: here is the component
of type validation, here is the assessment platform. That answers "which thing
is the engine", which is not the question. What performs the check is only
legible as a run, and a run is checks in and an assertion out.

So each path carries two encodings now, what the run reads and what it writes,
and component-first has four in total because it has both paths:

- **Implementor's path.** In: the validation component carrying the checks, each
  naming the rule it tests and the component it tests it against, so what the
  engine is handed is complete. Out: the response in the plan of record,
  carrying the proposed implementing-rules, which is what makes it an assertion
  traceable to the check rather than prose about the check.
- **Assessor's path.** In: the same definition taken into an assessment plan as
  an asset, the checks travelling with the component that runs them. Out: the
  observation, whose assessment-check-id is the same string the validation
  component gave the check, so it resolves back to what ran without the assessor
  holding the plan of record, and whose subject is a host rather than a
  component.

Assessment-first has the assessor's path only and now shows both halves of it:
the plan carrying the check on its activity step, the assets naming the platform
and the plugin beneath it, and the task binding one to the other by prop, then
the observation naming the activity that ran.

Two of these encodings also appear at questions 6a and 6b, and that is
deliberate rather than an oversight. There they answer where the claim and the
result are written. Here the same document is the output of a run, which is a
different fact about it, and the section is unreadable without it.

**What the harnesses learned.** A path is a run, so both halves have to be
there: a cell answering by path must carry the key with -in and the key with
-out for each path it declares, and one without the other now fails. The focus
rule needed care too, since two blocks in one cell legitimately light the same
construct: the assessor's input lights target-component-uuid rather than the
checks, because what that arrangement moved is which side names the subject.

### Both rules on both sides, and the carrier split by path

**Date:** 2026-08-24

Four corrections to the runner's two paths, all of them the same mistake:
showing one of something the reader needs two of.

**Both implementing-rules.** The implementor's output showed one implemented
requirement. Two checks ran, so there are two, and the tie back to the rule is
on each of them. That tie is the thing the catalog approach cannot write, so
showing it once undersold it by half.

**Both observations.** Same on the assessor's side, on both approaches that have
one: two checks, two observations.

**The whole checks assembly.** The assessor's input lit target-component-uuid,
which is one field of one check. What the assessor gains is the assembly: every
check, each naming its rule and its subject, in a document they own. So the
focus is the checks, the same construct the implementor's input lights, and the
harness rule that forbade two blocks in a cell lighting the same thing was
scoped rather than dropped. That rule was written for a lone extra block showing
a rearrangement, where lighting what the other blocks light means it has not
said what moved. A block keyed to a path is not a rearrangement, it is one half
of a run, and two runs reading the same checks is the finding.

**Two carrier rows, not one.** The block at the top of the cell listed one set
of assemblies, which said the approach used all of them at once. The
implementer's run touches the component, its checks, the by-component it writes
and the implementing-rules on it; the assessor's touches the component, its
checks, the assets that hold it and the observation it writes. Two rows now, one
per path, each in the order the run goes, with proposed assemblies marked from
the same list that marks them everywhere else. Two of the four on the
implementer's row are proposed, which is visible at a glance and was not before.

The page harness held the old shape: a carrier's second row had to be labelled
Assembly, Assemblies, Prop or Props. It now accepts rows labelled by path, and
requires each of them to carry assemblies, so the labelling cannot quietly
become free text.

### A run is items of one shape

**Date:** 2026-08-24

The marks in a flow row sat low against the tiles beside them, and the reason
was structural rather than a spacing value being wrong. A tile carried two
lines, the box and the question under it; a mark carried one, the glyph. A flex
row centring items of two different heights put the mark at the middle of the
taller neighbour, which is half a caption below the middle of its box.

So every item in a run is the same two-part stack now: a box on a fixed band
with its contents centred, and a line under it. The boxes ride one middle and
the captions sit on one line beneath, left aligned under the box they belong to.

The marks are captioned, which is what the second line gave them somewhere to
be: "copy" under the copy mark and "runtime" under the runtime mark, in small
caps so they read as labels on the drawing rather than as more of the sentence.
It also removes an inference. A reader met a glyph between two documents and had
to work out that the machine was a runtime and the sheets were a copy, when the
answer is two words long.

Both places that draw these rows follow it: question 5 on the six questions
page, and the stakeholder mapping on all three approach pages. A tile in a
stakeholder run takes an empty caption line rather than a word, because the name
is inside the box already and what the second line is doing there is holding the
row's shape.

The page harness now asserts both halves of this, on every page that draws a
run: every item is a box with a line under it, and every mark says what it is.
An unlabelled glyph fails the build.

### The catalog approach's runner answer is written, and it is partial

**Date:** 2026-08-24

Question 5 for catalog-first said nothing was there, and that was a claim about
the wrong thing. It was written against "is the runner named", and the answer to
that is no. But the question is what performs the check, and a run is an input,
a machine and an output. Two of those three are written down in this approach:
the check components the engine is handed, one per rule, each carrying the
identifier in ConfigRuleId, and the responses in the plan of record they end up
in. What is never written down is the machine in between.

So the cell is partly answered now, with both halves of the implementor's path
drawn from the encodings questions 3 and 6a already use. The output is a plain
by-component saying the control is met, with no field naming the check that
produced it, which is the difference between this path and the same path in the
component approach and is the whole of it: the response and the run are joined
by whoever wrote them and by nothing a schema can follow.

There is still no assessor's path, and the note says why: a catalog cannot be
introduced into an assessment by someone who did not write the plan of record.

The evidence of absence came out with the state. The cell had recorded what was
searched for and what turned up instead, 230 component definitions, 429 software
components carrying a ConfigRuleId, no component of type validation and no
assessment platform, which is the right shape for a cell claiming nothing exists
and the wrong one for a cell showing two encodings. What survives of it is the
note, which still says the identifier resolves inside the engine where OSCAL
cannot follow it.

**A check that required the site to stay unfinished.** The page harness asserted
that at least one cell states a gap rather than leaving it blank. That was true
while a gap existed, and this was the last one on the site. A rule requiring a
gap to remain is a rule against finishing, so it counts now: the number of cells
with no encoding has to be the number the data declares, which catches a cell
losing its encodings silently and does not object to there being none.

### Short sentences, and a rule that keeps them short

**Date:** 2026-08-24

The catalog approach's runner note had grown to a hundred words while the note
beside it ran to twelve. That is not just long, it is unfair: the page is a
comparison read across three columns, and an approach whose note has been
rewritten more often ends up looking more complicated than its neighbours. Long
is not neutral here.

Every note a reader meets in a cell, a chain step or a mapping row is two
sentences now, three where a claim needs a qualification:

- the fifteen matrix notes over eighteen words, 461 words down to 326
- the seventeen chain step notes, 582 down to 322
- the eleven stakeholder row notes and the two group notes, 428 down to 229
- the eight lines that describe an encoding on the approach pages, each now
  twelve to eighteen words

Nothing was dropped that was doing work. What went was the second telling: a
sentence naming a construct and then a sentence explaining the construct it had
just named, which is what these grew by.

The rule is now a check rather than an intention, on all four families: between
six and thirty-two words. The floor matters as much as the ceiling, because a
note of four words is not an answer, and the ceiling is set where a third
sentence stops being a qualification and starts being a paragraph.

The tradeoff entries were left alone. They are the argument rather than a label
on a construct, they are authored in the user's own words in places, and they
already have an equal-budget rule of their own that keeps the three approaches
within ten per cent of each other.

### The strengths and risks become one sentence each, and gain three points

**Date:** 2026-08-24

Every entry is a single sentence now, twelve to thirty words. They had grown to
paragraphs, up to sixty-five words in one case, which on a page of six or seven
claims is a wall rather than a list. What went was the elaboration after the
claim; every claim itself survives.

Three points were added:

- **catalog-first, a strength.** The tie to a framework is its own mapping
  collection, so a third party can publish it without owning either catalog.
  That separability is a property of the approach and was not stated anywhere.
- **component-first, a strength.** Vendors are already told to describe how
  their product meets requirements in a component definition, so the rules land
  in the model they are already writing rather than across two.
- **component-first, a risk.** For a claim to reach a host rather than a class,
  implementing-rules would have to be carried by inventory items as well.

**The budget rule moved from the page to the point.** Component-first now
carries nine entries to the others' seven, and measured per page that made it
36 per cent longer, which the rule read as arguing at greater length. It was
not: its points are the same size as everyone's, there are more of them.
Squeezing nine into seven entries' worth of words would have made its sentences
terser than its rivals', which reads as less considered and is a thumb on the
scale of its own.

So both halves of the rule compare points rather than pages: a strength and a
risk on one page within fifteen per cent of each other per point, and a point on
one page within ten per cent of a point on another. How many points an approach
has is a fact about it and is visible in the list; how much room each one gets is
the thing that can be unfair. The three approaches now sit at 27.1, 27.7 and
27.7 words per point, a spread of two per cent.

A second rule came with it: no entry may run past thirty words or hold more than
two sentences, because a claim arriving at three times the length of the claim
beside it is an argument made by volume.

### The assessor's path shows what of it is proposed, and lights both fields

**Date:** 2026-08-24

Two things the assessor's path was understating.

**The proposed fields were invisible.** Its carrier row listed the checks
assembly as proposed and stopped there, but the observation the run writes
carries two fields the proposal adds as well: assessment-check-id, which is the
join back to what ran, and result. Both are in the row now and both draw with
the dotted border every proposed construct on this site draws with, so the row
reads four released constructs and three proposed rather than five and one.
That is the honest count for this path: what it needs from OSCAL is not one
change but three, and two of them are on the result side.

**Only half the answer was lit.** The observation block highlighted
assessment-check-id alone. The answer is the check that ran and what came of it,
and a reader looking at a lit identifier with an unlit outcome beside it is
being shown the question rather than the answer.

So a focus can name more than one field now. The generator resolves each, unions
the spans and records both names, and the verifier holds the pair rather than
being relaxed: every lit line has to open on one of the named fields, and each
of the names has to be lit at least once, so a focus that silently stops
matching one of its keys still fails.

### The runner's files are the files, not copies of them

**Date:** 2026-08-24

Question 5 shows what a run reads and what it writes, and both of those are
answers to other questions: the check at 3, the response at 6a, the result at
6b. They were built separately and had drifted.

- The catalog approach's check component appeared at question 3 with its control
  implementation and at question 5 without it, trimmed when the block was
  written. Same file, two shapes.
- The component approach's validation component carried a description at
  question 3 and a method prop at question 5, neither carrying the other's.

Both are built from one function each now, sliced rather than rewritten:
question 3 shows the component with one check because it is asking how a rule is
tested, question 5 shows it with both because it is asking what the run is
handed. The verifier compares them by field path, so a slice is allowed and a
divergence is not.

**And question 6 had a defect of its own.** The catalog approach's finding
related to an observation uuid that nothing in its column wrote. The uuid
resolved in a neighbouring column, which is worse than dangling: it looked
fine. A result whose related observation resolves nowhere is not a result, so
the observation is in the document now, and what it cannot carry is the finding:
no field on it names the check that ran, so the outcome and the test are joined
outside OSCAL. The assessor's block at question 5 shows the same pair for both
rules rather than the observation alone.

Two checks came with this. Every document question 5 shares with another
question has to have the same fields in both places. And every observation a
finding relates to has to be in the document that carries the finding.

### The chain figure joins the site's vocabulary, and two notes were on the wrong steps

**Date:** 2026-08-24

**One drawing for one model.** The stakeholder mapping and the six questions
page both draw a model as an icon coloured by its layer. The chain figure below
them drew a plain rectangle with the model's name in it, so a reader moving from
the page to the figure met the same seven models twice in two vocabularies. The
figure draws the icons now, emitted from data/model-icons.json, the file those
pages read, with the colour set from the layer tokens rather than written into
the drawing. Control blue, implementation green, assessment amber, in the figure
as on the page, so a step that crosses a layer is visible before the field names
are read.

**And a real defect, found by looking at the drawing.** The first two steps of
every chain are rule to check and then rule to control. An earlier pass had
rewritten the step notes by position while assuming the opposite order, so all
three approaches carried their first two notes on each other's steps. Nothing
failed: each note was true, well written, and about the wrong step. It was
visible the moment the figure was rendered and read, which is the argument for
rendering it.

The guard for this is not a check that a note mentions its own fields. That was
tried and it fails honest notes: the catalog step from check to runtime says
"the prop names the rule the engine runs, and the engine itself is nowhere in
the content", which shares no vocabulary with ConfigRuleId. What is checkable is
the order. All three chains now have to step in one declared sequence, skipping
what they do not have and reordering nothing, which is what makes the three
figures comparable row against row and what makes the file safe to edit by
position.

### The status section comes off the approach pages

**Date:** 2026-08-24

Three sentences closed each page: what the published content conforms to, how
complete it is, and the publisher's own statement about it. All three are facts
about a corpus, and the corpus is what the artifacts page is for. On a page
whose subject is the shape of an approach, they read as a verdict on whoever
published the files, which is the one thing these pages are built not to do.

An approach page is now the stakeholder mapping, the strengths and risks, and
the chain from the rule to the claim and the result. About 940 words each,
against 2,050 a week ago.

What went with it: the three status keys and the status_quote pair for each
approach, and snippet(), which had no caller left. Those two extracts were the
last published content on an approach page, so a page now draws no extract at
all. The matrix still declares them per cell and verify still checks each one
resolves to a file, so they remain as provenance.

The page harness kept the shape rather than losing it: it checked that the
completeness sentence accounted for all seven questions by name, and now checks
that no status section is there at all, and that no approach page draws an
extract.

### The open questions become four lists

**Date:** 2026-08-25

The page was twelve sections and about 3,900 words: an evidence
register of eleven items, six questions each with its own headings and
sub-headings, two question lists, a block on what would settle the
disagreement and a block on how to contribute. A reader arriving to find out
what is unresolved read an essay.

It is four sections of one-line questions now, each opening into the reasoning
behind it. One across all three approaches and one per approach, which is the
shape the questions were always in and the page was not.

    Across all three approaches   8
    Catalog-first                 5
    Component-first               9
    Assessment-first              1

**The distribution is editorial, not a measure of defects.** Section lengths
reflect the selected questions, not the completeness or quality of an approach.

**The new question, and it is the one the reorganisation was for.** Do many
catalogs converge into one profile and one plan of record, or does each catalog
need its own? The working assumption is convergence; what is being seen in
practice is one plan of record per catalog. That is not a matter of taste: it
changes the file count, where a response lives, and whether a benchmark outcome
sits beside a regulatory one. The worked scenario assumes convergence, which is
why its figure is 18 files and not more, and a check now holds the question by
name so it cannot quietly leave the page.

**Questions are maintained as analysis content.** Their wording and reasoning
can be revised through editorial review. Structural checks preserve identifiers
and validate the question structure; they do not establish reproduction or
attribution. Existing anchors remain stable when the prose changes.

**What was dropped, on the call in the conversation.** The evidence register,
the settle block and the contribute block. The register was the longest block
on a page meant to be scannable; open issues now live in the question lists.

**Re-validated against the site as it now is, which mattered.** The platform
semantics question still described questions 4 and 5 as answered by six
constructs across three corpora. Those two questions were rebuilt yesterday:
question 4 is answered from the plan of record by two approaches and question 5
is answered by path. The question underneath is still open and still unanswered
by NIST, so it stays, with the reasoning rewritten against what the site says
today rather than what it said last week.

**The clearing up.** Fourteen renderers had no caller left, 421 lines of
`assets/site.js`, and four hooks no page carries. Eight stylesheet families went
with them, caught by the guard added yesterday that every class the stylesheet
defines has to be reachable from markup, a script, a generator or data. That
guard has now earned itself twice.

`2562/2562` verify checks and `633/633` page checks pass.

### The last exemption from the attribution rule

**Date:** 2026-08-25

No page names a proponent organization now. The artifacts page was the one
exception, exempt by name in the harness on the argument that an inventory
redacting the publisher would be useless.

It was not useless. The inventory is of the same files under the name the rest
of the site uses for them: Catalog-first, Component-first, Assessment-first,
with the option letter beside each. Every other page had been talking about
approaches for weeks while this one talked about companies, which is exactly the
drift the rule exists to catch, and the rule could not catch it because the page
was written out of the rule.

    1. Catalog-first     Option A    1 catalog, 230 component definitions
    2. Component-first   Option B    1 plan, 1 result, 4 component definitions
    3. Assessment-first  Option C    15 plans, 1 result

**Proponent attribution, not source attribution.** The distinction is now
stated in the check rather than implied. The publishers of the guidance being
read stay named wherever they are the source of a document: CIS, DISA, CISA and
NIST, and AWS in its Security Hub role, on the call in the conversation. A
benchmark cannot be cited without citing who wrote it, and the guidance table on
the start page is a list of what was read.

**What stays and is not rendered.** Three things carry a company name in data
and none reaches a page: the directory each corpus is read from, which is a path
on disk; the titles inside the published files, which are read off the documents
rather than written here; and the repository link, which is a location a reader
can go and check the counts against. These are properties of the published OSCAL
examples, not attribution of editorial statements.

**The check now has no branch.** It read "if this is the artifacts page, assert
it does name publishers; otherwise assert it does not". One rule, no exception,
and the comment says what is banned and what is not, because the next person to
add a company name will read that comment rather than this entry.

`2562/2562` verify checks and `633/633` page checks pass.

### The inventory links to the documents it counts

**Date:** 2026-08-25

Every row of the artifacts page named a document and counted what was in it, and
nobody reading the page could open one. The corpora sat beside this directory,
outside anything the site publishes, so a reader had a figure and no way to check
it.

**Two corpora are copied, one is linked.** `tools/copy_examples.py` copies the
component-first and assessment-first corpora into `examples/`, 24 files and 27
MB, and records each with its size and hash in `data/examples.json`. Catalog-
first is not copied: it is published in a public repository under a licence, so
its rows link there. An online document gets an online link, and 231 files and
4.8 MB do not need a second home.

Copied, never moved. The corpora are what the site recomputes its figures from,
and a tool that moved them would break every count on the worked scenario and
this page at once. The tool has a `--check` mode and the build runs it, so a
copy that has drifted from its source is a failure rather than a surprise.

**Two exclusions were lifted, and it is worth being plain about which.** The
repository excluded `sources/oscal/` and `sources/cis/`, the second with a note
that CIS licenses its Benchmarks for internal use and that a public repository is
redistribution. Two of the files now committed are CIS Benchmark content: the
Benchmark itself and an assessment plan derived from it. That was raised before
copying and the call to ship them is recorded here. Both paths are named in
`CIS_DERIVED` in the copier so the question does not have to be reconstructed
from filenames if it is ever revisited.

**The check turned around rather than going.** It asserted that the OSCAL tree
stayed out of the repository. It now asserts that every file the inventory names
is either in the repository or at a public address, that the copy is current with
the corpora, and that every local link resolves to a file that exists. Tested by
pointing one row at a file that is not there.

That last one matters more than it looks. A row with a dead link reads exactly
like a row with a live one, so the failure is found by a reader clicking rather
than by the build, which is the same shape as every other defect this harness has
caught this week.

`2568/2568` verify checks and `633/633` page checks pass.

### The stakeholder table stops describing a reader

**Date:** 2026-08-25

The auditor row on each approach page carried a second line, `reads` followed by
a model tile: the plan of record on catalog-first, the plan and the prior results
on component-first, the results on assessment-first. It described a person
opening a document. This site is about what a machine does with the files, and
every other line in that column is a production: something goes in, a runtime or
an arrow, something comes out.

What the run actually consumes was already on the row, as the input side of the
flow. So the line was not carrying a fact the row lacked; it was carrying a
different kind of fact, in the same shape, which is the worse of the two
problems. A reader comparing three rows had no way to tell that one line meant
"this is produced" and the next meant "somebody looks at this."

Removed from the data rather than hidden in the renderer, and the key is now
asserted out: an entry may carry `writes`, `flows` and `note`, and nothing else.
A key the renderer quietly ignores is a key that gets written again. Tested by
putting one back.

`.mflow__verb` went with it, which the class-reachability guard would have caught
had I left it. The diff of the three regenerated pages is those lines and nothing
else.

`2581/2581` verify checks and `633/633` page checks pass.

### The assessor's route stops depending on the system owner

**Date:** 2026-08-25

The stakeholder table on assessment-first drew the system owner running the
assessment plan and producing results, the same run as the auditor's row below
it. That said the assessor's route runs through the owner's tooling, which is the
opposite of what the approach claims. An assessor works from the plan of record
and nothing else the owner holds. What the owner automates is not visible to
them and is not theirs to answer for.

So the owner row on that page is now the plan of record and no run. The one
approach with one runner is the finding, not a hole: on the two routes with a
path from a check to a claim the same checks make the owner's responses and the
auditor's result, and on this one there is no such path and no owner's run to
draw. The six questions page already said this. Question 5 on assessment-first
carries an assessor's path and no implementor's path, and had done for some time
while the table beside it said otherwise.

**The engine row gained the document it was missing.** It read "no document of
its own." On this approach the policy engine provider writes the assessment plan
and puts the checks in it; the guidance and software authors write the activity
and its steps. Three rows now write `assessment-plan`, each saying which slice is
theirs, which is the substance rather than a duplication.

That made a rule sharper rather than looser. The harness asserted the engine
writes only a component definition, which was a claim about a model. It now
asserts the engine writes only the document that holds the checks, which is a
claim about ownership and is what was meant: a component definition in two of the
three, the assessment plan in the third.

Four rules were retargeted, each with a negative test: who runs the tool, what
the owner's run makes, what the engine writes, and a new one, that a row with no
run has to say why in words. A reader cannot tell an argument from an oversight
by looking at an empty cell.

The automation group's note said "the two parties below run it." One page now has
one. Reworded to hold on all three rather than split per approach.

`2577/2577` verify checks and `633/633` page checks pass.

### One way to draw a model, on the page that draws them most

**Date:** 2026-08-25

The approach pages set every OSCAL model as a chip: its icon, its name in mono,
a light border. The worked scenario named the same seven models eleven times
over as bare `<code>`. Same set of things, two vocabularies, one site.

Section 2 now uses the chip in all three places it names a model: the first
column of the files table, the terms in each approach's list, and the label above
each group in the three figures. The icon carries the layer colour, so the three
bands the table is ordered by are now visible in the first column rather than
only stated in the caption.

**The chip moved to where the icon lives.** It was defined inside
`approach_pages.py`, which was fine while one generator drew it. Two generators
copying the same markup is a tile that drifts, and the string carrying the
runtime mark has already done exactly that. It is now in `model_icons.py`, beside
the icon it wraps, and both generators call it.

Three smaller decisions, each of which is a trade:

The count in the lists moved into a column of its own, right aligned. Two things
are scanned down those lists and they want different treatment: counts are
compared between the three approaches, so they line up; models are recognised
rather than read, so they are the chip.

`.mtile__name` sets its weight rather than inheriting. The chip sits in a table
cell on one page and a row heading on another, and a row heading is 600, so the
same model name was coming out two weights depending on which cell it landed in.

The figures get the icon and not the chip. A bordered box the width of a short
label, directly above a row of bordered boxes each of which means one file, is a
box a reader can count. That is the same reasoning that already keeps an unused
model as a dashed rule rather than a hollow tile.

**And the rasteriser was drawing the icons wrong.** `tools/svgrender.py` matched
`translate` and `rotate` in a transform and dropped anything else in silence.
Every model icon is placed with translate/scale/translate, so all of them came
out at two to three times their real size, overlapping the labels beside them.
That is not a new fault: the chain figure has drawn model icons for a while and
`build/grayscale/` has been showing them wrong for as long. The sheet exists so a
human can look at the drawings, which makes a plausible wrong picture worse than
a crash.

`scale` is now supported, in points and in the lengths that follow it, and any
other transform raises instead of being skipped. The file's own docstring already
claimed unsupported transforms were asserted against; now they are.

Twelve checks added, each tested by breaking it: the chip counts on all three
surfaces, no model set as bare code, one icon per group in each figure, the icon
size, and both halves of the transform repair. `scenario.html` was backed up to
`backups/2026-08-25-scenario-before-tiles/` with the three generators it depends
on before any of this.

`2589/2589` verify checks and `633/633` page checks pass.

### The figure keeps the inventory to itself

**Date:** 2026-08-25

Under each of the three subsections in section 2 was a list: every model again as
a term, with its count, what it is for, a further sentence of detail, and the
names of its files. The figure directly above it draws all of that already. The
count is the tiles, the names are on the tiles, and what the model is for is the
line under each group. Three approaches, seven models each, so the page said the
same thing twice eighteen times over and the second telling was the longer one.
The three lists are gone. Section 2 is now 484 words of prose where it was 930.

**The screen reader argument is covered where it belongs.** The list was
justified in a comment as the text route for a reader who gets the description
rather than the tiles. Each figure already carries a `<desc>` naming every model,
its count, what it is for and every file in it, wired through `aria-labelledby`.
That is the description of the tiles rather than a second list beneath them.

Which changes what the harness is for. Every file name used to be asserted twice,
once against the page and once against the drawing, and the page copy was doing
the work. The page assertions are gone and three now run against the `<desc>`:
each file named there in full, each component definition's type named with it,
and each model's purpose stated. That path is the only route to these names now,
so it is checked rather than assumed. Tested by emptying the names out of the
description.

**What was lost, plainly.** The `detail` sentences are no longer printed
anywhere. Some are the sharpest lines the page had, including why an assessment
result cannot be one file with four sections. They stay in `data/scenario.json`
and stay checked, which is the same trade this page already made twice, for the
derivations and for the excluded model. Worth knowing they are unprinted rather
than discovering it later.

`.scenario__n` and `.scenario__files` went with the lists; the section 1 inputs
list keeps `.scenario__inputs`. One check was added to hold the removal: section
2 prints no definition list at all. Tested by putting one back.

The backup taken before the tile work was deleted on request.

`2609/2609` verify checks and `633/633` page checks pass.

### A component definition is a world of possibility, not a claim about a system

**Date:** 2026-08-25

The first strength listed on component-first read: "A component definition
already documents how a component meets a control." It does not. It documents
how a component **can** meet a control. That is the whole distinction between a
component definition and a plan of record, and this page turns on it: the risk
listed three bullets away is that desired state entering the plan of record
mixes how a component should be configured with how a system actually is. The
strength was quietly denying the risk.

Now: "A component definition says how a component can meet a control, the world
of possibility for software, and rules inside it make that document drive
automation."

The sibling bullet had the same slip, vendors told to describe how a product
"meets" requirements, and now reads "can meet". One word, same correction, said
here so it can be put back if that one was meant literally.

The rest of the site had this right already. The glossary calls a component
definition "descriptive rather than binding," and question 2's note says "a
definition says how a component would satisfy a control. Only a plan of record
says a system does." The tradeoff block was the outlier.

### The profile is the system owner's on all three

**Date:** 2026-08-25

Component-first and assessment-first drew the profile on the regulatory row.
It belongs to the system owner: a framework body publishes the catalog, and the
baseline an organisation selects out of it is a decision about that
organisation's system.

The site was contradicting itself in the open. Catalog-first's owner row says
"The profile is always the owner's," and the two pages beside it drew it
somewhere else. The harness had the claim, scoped to catalog-first, where the
merge of four catalogs makes it unmissable. A rule scoped to the one case where
a claim is obvious is a rule that lets the claim be wrong everywhere else, and
this one did for as long as the pages have existed.

Both halves now run for every approach: the profile is on the owner's row, and
on nobody else's. Tested by moving it back.

The assessment-first owner note said "The plan of record, and nothing else,"
which stops being true when the row gains a second document. It now reads "The
selection and the plan of record, and nothing beyond them," and keeps the point
that follows it.

`2613/2613` verify checks and `633/633` page checks pass.

### The mapping provider moves up to the framework it maps to

**Date:** 2026-08-25

The seven parties now read: regulatory, mapping, guidance authors, engine
provider, system owner, auditor. The mapping provider was fourth, after the
guidance it maps; it is now second, directly under the row whose framework it
maps back to.

That is the order a rule travels. A framework is published, something ties a
guide back to it, somebody writes the guide, somebody builds the tool that tests
it, and two parties run the tool. Reading the mapping row before the guidance
rows puts the tie next to the thing it points at rather than next to the thing it
points from.

The order is now asserted rather than left to whatever the file happens to say.
It was only held loosely before: the two group headings need their rows adjacent,
so a shuffle inside a group failed, and a shuffle across groups did not.
Tested both ways, since a reorder that moves the data blocks with the parties
list is the one that would otherwise pass in silence.

`2614/2614` verify checks and `633/633` page checks pass.

### The mapping provider works in every approach

**Date:** 2026-08-25

Two of the three stakeholder tables said the mapping provider had "nothing to
write," on the reasoning that an inline tie is written by whoever writes the
thing it sits on. That confuses the tie with its container. Somebody still
decides which framework control a rule serves. In these two approaches they do
it by editing a document another party owns, and editing somebody else's
document is a heavier ask than shipping your own, which the row said nothing
about at all.

- **Catalog-first:** a mapping collection, its own document, the only approach
  where the tie is a file the mapping provider ships.
- **Component-first:** a component definition, edited, not written.
- **Assessment-first:** the assessment plan, edited, where reviewed-controls on
  the activity names the framework controls the check covers.

**Which component definition is genuinely open, so the table says so.** The tie
could sit on the software definition holding the rules, or the validation
definition holding the checks, and those belong to different parties. The type on
that row reads "software or validation."

That marker is not a way out of the rule that every component definition names
its type. It is a claim of its own, and it is held like one: only the mapping
provider's row may carry it, and only while the open questions page carries a
question about it. An unsettled marker with no question behind it is a shrug
printed as a finding. The question is new, in the component-first section.

Whether a document is the party's own is derived rather than read out of the
prose. A document belongs to somebody else exactly when somebody else writes it,
and the table already says who writes what. Checked that way, so rewording a note
cannot flip a structural claim.

Four checks added, tested by removing the question, moving the unsettled marker
to the engine's row, and putting "nothing to write" back.

`2631/2631` verify checks and `633/633` page checks pass.

### The open questions get shorter, and two of them move to where they belong

**Date:** 2026-08-25

Six questions off the page: four from the across-all section and two
catalog-first ones.

- `parameters`, where a rule's parameter goes
- `mapping-item`, whether it can point at something that is not a control
- `platform-semantics`, the difference between a platform, an asset and a component
- `capability`, what the word means here
- `paper-cat-3`, nested profile resolution between two sets of publishers
- `paper-cat-4`, what a benchmark catalog is for if it never reaches the plan

**Requirement level is a catalog question, not an all-three question.** OSCAL
cannot express shall, should and may, so placement is the only channel left for
saying something is required, and this approach *is* placement: a benchmark's
recommendations become controls beside a framework's controls in one merged
profile with nothing on either saying which is which. Its rationale was rewritten
to say that rather than to make the general point.

**And a new one beside it, about kind rather than level.** Should a control
declare its type, so a regulatory control and a technical hardening control can
be told apart? Both end up in the same merged profile and the same plan of
record, and nothing on a control distinguishes them, so a plan cannot report its
regulatory coverage separately from its hardening coverage. Written without
retyping the scenario's counts, which the scenario page derives.

**One removal cost something and it is worth naming.** The parameter question was
tied to question 1 on the six questions page by a check, with a comment saying
that if the question were dropped the cell would be left stating a fact with
nowhere to go. It has been dropped, and the check with it.

What remains is defensible: the cell says the activity is the rule, there is no
parameter field, and a value goes in the text. That is a description of the
encoding, and the encoding is still checked, so it cannot drift. What is gone is
the argument that it ought to be otherwise. The cell is now neutral where it used
to point somewhere, which is arguably the better position for a comparison to
take.

`2615/2615` verify checks and `633/633` page checks pass.

### The deployable cut, and three things the QA found

**Date:** 2026-08-25

`tools/package.py` cuts the copy that ships. One rule: a file goes in if the
browser asks for it. Everything else here is input to the build or evidence for
the harness, and neither is part of a static site. 98 files, 27 MB, of which 26
MB is the examples the artifacts page links to.

Out: `tools/`, `build/`, `sources/` (46 MB of corpora), `.github/`, `serve.cmd`,
every markdown file, `assets/shell.html` (a template that would serve as a broken
page), `assets/images/` (the authored icon sources, consumed at build time), and
the 25 data files no page fetches.

**The QA found three things, in rising order of how long they had been wrong.**

*Every deep link into the six questions page landed at the top.* `boot()` calls
`revealHash` synchronously; the question stack is built from a fetch, so when
`revealHash` ran its targets did not exist and it returned having done nothing.
Eighteen distinct anchors, linked from all three approach pages. It looked fine
because clicking one from the matrix on the same page works: by then the stack is
built and what fires is the hashchange listener. The broken path is the one that
arrives from elsewhere, which is the path the links exist for. The renderer now
reveals when it has finished building.

*The artifacts page's meta description still named AWS, IBM and Easy Dynamics.*
The body was relabelled by approach; the description in the head was not. Gate 7
walks `<main>`, so the head was exempt, and nothing on the page showed it. A
search result and a link preview would have shown it to everyone. Gate 7 now
reads the title and description too.

*The folder-based fallback must match the package.* `assets/bundle.js` mirrors
all of `data/` in the working site, so packaging rebuilds it over the shipped
subset rather than copying it. This keeps the fallback aligned with the files
the package includes.

**What was proved rather than asserted.** The package was served over plain
HTTP with no rewrite rules, the way object storage does, and all 83 URLs the site
asks for returned 200, including the 22 documents with spaces in their keys. No
link depends on a directory index, a redirect, or a case-insensitive filesystem.
The `file://` mirror was checked to hold exactly the 48 entries the site asks for
and no more. Then the zip was unpacked to a clean directory and served again.

Runtime inclusion and verification evidence are separate. An OSCAL extract may
be retained for a declared evidence pointer without being fetched by a page;
packaging selects browser inputs rather than copying all build inputs.

`2619/2619` verify checks and `649/649` page checks pass.
