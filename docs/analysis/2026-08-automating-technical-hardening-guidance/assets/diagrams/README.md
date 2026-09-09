# The diagram library

Eight SVG files and one small script. `tools/diagrams.py` writes exactly the eight
figures the site shows, listed in its `PUBLISHED` constant. The library also retains
unpublished OSCAL-based builders, whose outputs are not written. Every published
SVG is generated from `data/`, and `tools/verify.py --diagrams` re-derives
it and checks the result. **Do not hand-edit an `.svg` in this folder.** The
next run of the generator will overwrite it, and the verifier will fail in the
meantime.

```
python tools/diagrams.py          rewrite every diagram
python tools/verify.py --diagrams check them, and write build/grayscale/
open build/grayscale/index.html   the contact sheet gate 3 asks you to review
```

---

## Why a generator

Three reasons, and the third is the one that matters most.

1. **Literals cannot drift.** The join diagrams print real identifier strings
   out of the shipped OSCAL files. Typed by hand, those strings can quietly stop
   matching the corpus. Here they are read from `data/snippets/` at generation
   time, and `verify.py --diagrams` checks that every quoted literal on a join
   diagram is a string the extractor actually produced.

2. **Field names cannot be invented.** Every OSCAL field name printed on a node
   passes through `F()` in the generator, which refuses to return a name that is
   not a key in the snippet it claims to come from. A wrong field name stops the
   build.

3. **Equal budget is enforced by construction.** Plan section 3 rule 5 requires
   the three approaches to get the same treatment, and rule 7 says non-verbal
   encoding counts as editorialising. Each three-approach family is emitted from
   one function looping over one list of three, so giving one approach an extra
   node or a heavier outline would take deliberate effort, and the verifier
   counts the results anyway.

---

## The shape vocabulary

Fixed by plan section 7. Use exactly this. Nothing else may be added without
amending the plan first, because a reader who has learned the grammar on one
page has to be able to read it on every other page.

| Mark | Means |
|---|---|
| rounded rect | an OSCAL model, or an assembly inside one |
| solid border | a filled slot |
| dashed border | a partly filled slot |
| hollow | an empty slot, in one of three states, below |
| hexagon | a control |
| labelled arrow | a join, carrying the literal field name on the line |
| solid arrow | a resolved reference |
| dotted gray | a prose-only or inferential link |

Three marks are local extensions, and each is declared in the legend of every
figure that uses them, because none had a place in the vocabulary and none
overloads an existing one:

| Mark | Means | Where |
|---|---|---|
| plain elbow, no head | containment: the child sits inside the parent | 72, 73 |
| socket, hollow with two seating tabs | a slot that may legitimately be published empty | 77 |
| two short bars across a line | a route this approach cannot use | 77 |

The strike is deliberately **not** a dash pattern. Dashed already means "partly
filled" and must not acquire a second sense.

### The empty states

An unanswered question is not a defect, and rendering the kinds of empty
identically would be an argument disguised as a design choice. So each kind gets
a geometry of its own.

| State | Rendering | Token | Live |
|---|---|---|---|
| Absent, no stated position | hollow plus a fine dotted fill | `.sl-empty-absent` | yes |
| Not applicable by design | hollow, plain outline, no marker | `.sl-empty-design` | retired |
| Deliberately not asserted | hollow plus a small open circle | `.sl-empty-notasserted` | retired |

Which of them exists is decided by `answer_states` in
`data/six-questions.json`, not here: a state no cell uses is dropped from the
data, and the legend then stops drawing a row for it. The drawing code for a
retired state is kept so the state can come back without being reinvented, but
the stylesheet carries no rule for one, and `verify.py --css` fails if it does.

None uses colour to carry its meaning, so all survive grayscale and print. They
mirror `.is-empty-*` in `site.css` on purpose: the CSS strips and the SVG
diagrams have to read as one system.

---

## Colour

**Every fill and stroke is `var(--token)`. No literal colour, ever.** The
verifier rejects a hex or an `rgb()` in a style block or in a `fill`/`stroke`
attribute.

Two palettes, and they are governed by opposite rules.

**The slot palette**, `--slot-1` through `--slot-6`, sits on a monotonic
lightness ladder. That ladder is the second discriminating channel that survives
when hue collapses for a dichromat, and `verify.py --a11y` asserts it stays
monotonic. Slot identity is also always written: every slot node carries a
numbered chip, so the palette is never the only channel.

**The approach palette**, `--approach-assessment`, `--approach-catalog`,
`--approach-component`, is held at *one* lightness on purpose. An approach drawn
darker or brighter than the other two would argue in a channel a word count
cannot audit. Equal lightness costs dichromat separation, which is accepted
because approach identity on every figure is carried by

- an outline offset (nested in alphabetical order, innermost first),
- a marker shape (circle, square, triangle, assigned alphabetically), and
- a written label.

`verify.py --diagrams` asserts that any file using an approach colour also
carries a marker shape and a label, so that fallback cannot be removed by
accident.

---

## Sizes and legibility

Every diagram is authored on a **960 unit** viewBox and sets **no text below 16
units**. `site.css` gives `.diagram > svg` a `min-width: 720px`, and
960 x 12/16 = 720, so the smallest label is at least 12 CSS px at every width
the wrapper allows. The wrapper scrolls below that rather than shrinking.

`verify.py --diagrams` re-derives that arithmetic from the CSS and the file
rather than trusting the comment. If you change the canvas width or the minimum
font size, change the `min-width` too or the check fails.

---

## Using a diagram on a page

```html
<figure>
   <div class="diagram" data-diagram="76-satisfaction-6a-6b"></div>
  <figcaption>
      How a requirement is satisfied and whether it was satisfied.
  </figcaption>
</figure>
```

`site.js` fetches the file and injects it **inline**. It is not an `<img src>`,
and that is not a preference. An external SVG in an `<img>` is an isolated
document: it cannot see the page's custom properties, so it would not theme, and
its `<title>` and `<desc>` would never reach the page's accessibility tree.

Because the SVG is inlined, its `<style>` block is not scoped by the browser.
Every rule in every file is therefore written as `#<root-id> .class { }`, and
the verifier rejects any rule that is not. Root ids are unique across the
library for the same reason.

### The scripted component

`74-slot-strip.js` renders the six-slot strip from `data/six-questions.json`, at two
sizes, with the tooltip on each cell taken verbatim from the matrix cell's own
`note`. It is the one implementation; `site.js` delegates to it.

```html
<div class="slot-strip" data-strip="catalog-first" data-size="lg"></div>
```

---

## Adding a diagram without breaking the grammar

1. **Put the facts in `data/` first.** If the figure needs a literal from a
   corpus, add a snippet to `tools/manifest.yaml` and run `tools/extract.py`.
   Nothing in this folder may read a corpus file directly, and nothing in it may
   contain a typed identifier.

2. **Write a `diagram_NN(c)` function** in `tools/diagrams.py` returning
   `{"NN-slug.svg": svg(...)}`, and add it to `BUILDERS`. Take every literal
   from the `Corpus` object, and put every field name through `F()`. Add the file
   to `PUBLISHED` only when a page references it; unreferenced outputs are not
   published.

3. **Reuse the primitives.** `node`, `elbow`, `socket`, `hexagon`, `plate`,
   `slot_chip`, `legend`, `LI`. They carry the vocabulary. A new primitive means
   a new mark, and a new mark means amending plan section 7 first.

4. **Size the canvas from the content.** Compute the height from where the
   content actually ends and add `legend_h(items)`. Do not hard-code a height;
   a legend that grows past the viewBox is invisible, not wrong-looking.

5. **Write the `<desc>` for someone who will never see the picture.** It must
   convey the same information, not describe the appearance. It is the longest
   thing you will write for the figure, and on this site it is also the version
   a screen reader user reads instead of the diagram, so it carries the same
   evidential weight as the drawing.

6. **Run the checks.**

   ```
   python tools/diagrams.py
   python tools/verify.py --diagrams
   ```

7. **Look at the grayscale.** Open `build/grayscale/index.html`. If a
   distinction disappears there, the figure is making its point in colour alone
   and has to be redrawn.

---

## The renderer

`tools/svgrender.py` rasterises the restricted subset of SVG this generator
emits, so that a grayscale contact sheet can be produced with no browser and no
cairo. It is not a general SVG renderer, it refuses elements outside that
subset, and it must not be used as one. It exists because gate 3 of the build
guide asks a person to look at the grayscale, and looking needs a picture.

---

## Published files

| File | Plan | What it carries |
|---|---|---|
| `73-join-assessment.svg` | 7.3 | containment, and the CISA context prop |
| `73-join-catalog.svg` | 7.3 | control-id in two hops, and the name match |
| `73-join-component.svg` | 7.3 | the composite key, and the return path |
| `74-slot-strip.js` | 7.4 | the six-slot strip, two sizes |
| `75-stakeholders.svg` | 7.5 | one requirement, three paths |
| `76-satisfaction-6a-6b.svg` | 7.6 | how it is satisfied against whether it was |
| `710-scenario-catalog.svg` | 7.10 | Catalog-first scenario file set |
| `710-scenario-component.svg` | 7.10 | Component-first scenario file set |
| `710-scenario-assessment.svg` | 7.10 | Assessment-first scenario file set |
