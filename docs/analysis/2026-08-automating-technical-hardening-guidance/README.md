# Automating Technical Hardening Guidance with OSCAL

A comparison site for the OSCAL Foundation Technical Focus Group on Automated
Assessments.

Three organizations have published working OSCAL content that answers the same
question three different ways: **where does technical hardening guidance live in
OSCAL, and how does an automated check attach to it?** This site puts the three
side by side against the same six questions, writes the same two rules out in all
three shapes so that the only thing differing between the columns is the
modelling, and names the join key that makes each one work.

**The JSON on the question pages is ours.** The three groups ship content for
different products, so quoting what each one published would set a certificate
control beside an object-store rule beside a Linux STIG, which compares subject
matter rather than modelling. So two rules were chosen once, both published
Ubuntu 24.04 LTS requirements keeping their real identifiers, and written out in
each approach's own shape by `tools/pattern_examples.py`. What is authored is the
encoding and nothing else: every property carries the namespace of the approach
it illustrates and none of them is ours. What the three groups have actually
published is inventoried separately, on `oscal-artifacts.html`, one row per
document with its contents counted from the file rather than described. Extracts
at declared pointers into the published files are still carried where a claim
rests on one, and they are still re-derived on every build.

Published hardening guidance from four publishers was read as input: CIS, DISA,
CISA and AWS. The introduction tabulates it one row per benchmark or guide, in a
disclosure that is closed until it is wanted, and every row carries what stands
behind it. A file icon downloads one of the 16 documents recorded under
`sources/`, 29.0 MB in all, and names the file, its type and its size on
hover; a globe opens
the publisher's own page for guidance that is not a document to hold. Every one
of them opens in a new tab. **Only inputs are listed.** The OSCAL written from
this guidance is published separately, so `sources/oscal/` is in the repository
but carries no row: `tools/sources_files.py` excludes it from the inventory, as
it excludes `disa/U_Readme_SRG_and_STIG.pdf`, which is about the STIG packages
as a set rather than about any one guide. `verify.py --sources` recomputes every
count from the corpora,
confirms every link resolves to a file, confirms no file sits in `sources/` unlinked,
and confirms nothing from the excluded tree is linked. Terms differ by publisher and
each file carries its own.

**The CIS material is here on a recorded basis.** `sources/cis/` holds the two
CIS Benchmarks in both their JSON and PDF form, 19.7 MB of the 29.0 MB. CIS
licenses its Benchmarks under its own Agreed Terms of Use, which on their face
say a Benchmark may not be redistributed or posted on any website. The material
is here because CIS is a stakeholder receiving this brief and confirmed that
copying and linking infringes nothing. That call is recorded in `BUILD-LOG.md`,
and each of the four files carries the basis rather than a general grant in its
own terms line: *"Reproduced here with the publisher's participation in this
review. The Benchmarks carry CIS's own Agreed Terms of Use; consult the
publisher before reusing them elsewhere."* **A fork or a mirror made outside
that conversation does not inherit the basis.** The DISA material is a work of
the United States Government, 13 files and 9.3 MB, 12 of them with a row.

**It makes no recommendation.** There is no ranking, no score, and no summary
that adds up to one. Where an approach carries a cost, the cost is stated and the
reader prices it.

## Status

Ready to publish, not published. Eight pages, all built: `index.html`,
`six-questions.html`, the three approach pages, `scenario.html`, `questions.html`
and `oscal-artifacts.html`. What remains is not a build step:

- **Proponent review has not happened.** No request for corrections has been sent
  to the publishers of the three bodies of content, so none has been received and
  nobody has declined. This is stated on the site rather than left implicit.
- Four checks cannot run without network and are skipped locally. They run in CI.
- Two more skip wherever the pre-read and the position paper are not on disk.
  Both are Word documents, both live beside the site rather than in it, and
  neither is in the corpora repository the workflow checks out, so `--criteria`
  and `--questions` skip their verbatim halves in CI as well as locally. Put the
  two documents at the root of the corpora directory and both run.

`BUILD-LOG.md` records every phase, every decision, and the open items for each
review gate.

## Viewing the site

**Double-click `serve.cmd`.** It starts a local server in this folder, opens the
site, and prints the address. Ctrl-C in that window stops it.

From a terminal, the same thing:

```
python tools/serve.py                    # then open the address it prints
python tools/serve.py --port 8080        # if 8000 is taken
python tools/serve.py --page scenario.html
python tools/serve.py --no-open          # do not launch a browser
```

It needs nothing installed beyond Python, writes nothing, picks the next free
port if yours is busy, and sends `Cache-Control: no-store` so that regenerating
data between refreshes shows the new data. Only 4xx and 5xx responses are logged,
so a missing file is visible and nothing else is noise.

Any other static server works too, run from this folder:

```
python -m http.server 8000               # Python, no extras
npx serve .                              # Node
```

### Why a server, and what happens without one

Every page is markup plus data: the markup carries hooks and `assets/site.js`
fills them from `data/` at load time, so regenerating data never touches markup.
A browser gives a `file://` page an opaque origin and blocks `fetch()`, so a page
opened by double-clicking cannot read its own data files.

Opening `index.html` directly still works. `assets/bundle.js` carries a copy of
every data file and every diagram, and the page reads that instead and says so in
one line at the top:

> Opened from a folder rather than a server, so this page read its content from
> `assets/bundle.js`, a mirror of `data/` that the build checks byte for byte ...

**That line is the site telling you which copy you are reading, not an error.**
The content is identical: `tools/verify.py --bundle` rebuilds the mirror and fails
on any difference. Serving the site reads `data/` directly and the line does not
appear. GitHub Pages serves over HTTP, so a published copy never shows it.

## Verifying it

One command:

```
pip install pyyaml pillow
python tools/verify.py --all
```

Pillow is not optional: `verify.py` imports `svgrender`, which imports it at
module scope to rasterise the diagrams for `--diagrams`.

The corpora are read from `TFG_CORPORA` when it is set, and from the
`corpora_root` in `tools/manifest.yaml` when it is not. This site sits under
`docs/analysis/` in a repository the corpora are not a sibling of, so set it:

```
export TFG_CORPORA=/path/to/tfg-automated-assessments
```

Eighteen checks. Each prints `PASS` or `FAIL` with detail. A check that cannot run
in the current environment prints `SKIP` with the reason and the exact command it
would have run, and is reported separately from the checks that passed. **A skip is
never counted as a pass.**

```
python tools/verify.py --snippets      re-extract every extract and diff
python tools/verify.py --schema        every OSCAL constraint the argument rests on
python tools/verify.py --conformance   labelled conformant validates, proposed fails
python tools/verify.py --example       our own encodings, and what must hold across them
python tools/verify.py --quotes        no page quotes anyone or names anyone
python tools/verify.py --criteria      the fifteen are the group's, verbatim
python tools/verify.py --stats         recompute every cited figure from source
python tools/verify.py --sources       the guidance read as input, recomputed
python tools/verify.py --matrix        every matrix cell resolves and is classified
python tools/verify.py --diagrams      structure, colour, geometry, join literals
python tools/verify.py --css           colour lives only in the token block
python tools/verify.py --links         every internal link, anchor and path
python tools/verify.py --budget        equal budget across the three approach pages
python tools/verify.py --a11y          contrast, then axe-core over every page
python tools/verify.py --bundle        the offline fallback matches data/
python tools/verify.py --questions     the reproduced material matches its source
python tools/verify.py --data          internal consistency of data/
python tools/verify.py --pages         run each page and inspect what it rendered
```

`node tools/pagecheck.js` runs behind `--pages` and can be run alone, including
against one page: `node tools/pagecheck.js six-questions.html`.

**In CI**, `--strict` turns every skip into a failure, on a runner that has the
network and the validators. That is what stops a skipped check from staying
skipped. See `.github/workflows/verify-2026-08-hardening-guidance.yml` at the
root of this repository.

### What needs network

| Check | Needs | Command it would run |
|---|---|---|
| `--schema`, second half | The published NIST 1.2.1 schemas | `curl` the schema, compare each stored fragment |
| `--conformance` | An OSCAL validator | `pip install compliance-trestle` |
| `--a11y`, second half | axe-core and a headless browser | `npm install --no-save axe-core puppeteer` |
| `--links`, external half | The links themselves | `curl -o /dev/null -w '%{http_code}'` per link |

## How the content is produced

Nothing on this site is transcribed, and nothing is typed twice. Content on this
site comes from one of two places and always says which. An **extract** is taken
from a real published file at a declared JSON pointer and is re-derived on every
build. An **encoding** is written by a generator from data held in that
generator, is labelled on its own bar as ours, and is regenerated and diffed on
every build so it cannot be hand-edited. Every figure, in either case, is
recomputed from the corpora rather than stated.

```
python tools/extract.py          # rebuild data/snippets and data/provenance.json
python tools/pattern_examples.py # write the two rules in all three shapes
python tools/oscal_artifacts.py  # inventory what the three groups have published
python tools/sources_files.py    # rebuild data/source-files.json from sources/
python tools/diagrams.py         # rebuild every published SVG in assets/diagrams
python tools/approach_pages.py   # rebuild the three approach pages
python tools/scenario_page.py    # rebuild the worked scenario page
python tools/bundle.py           # rebuild the offline fallback
python tools/verify.py --all     # prove the site says what the files say
```

That is the order the workflow runs them in, and it is the order they depend on
each other in: the bundle mirrors everything upstream of it, so it goes last.
Four of them take `--check`, which compares instead of writing and exits non-zero
if the committed file is stale: `pattern_examples.py`, `oscal_artifacts.py`,
`sources_files.py` and `bundle.py`. `approach_pages.py` does the same job the
other way round: it records the hash of every page it writes and refuses to
overwrite one that has been hand-edited since, so an edit made in the page rather
than in the data stops the build instead of disappearing into it.

`tools/manifest.yaml` is the declarative source of truth for the extracts. Each
of its 29 entries names a source file, an RFC 6901 pointer, the question the
extract illustrates, and any trimming applied. Trimming is always declared and is
marked in the rendered output; there is no silent truncation.
`data/provenance.json` records the SHA-256 of both the source file and the
extracted content.

`tools/pattern_examples.py` is the source of truth for the encodings. Two rules,
one binary and one carrying a value, because the pair is what shows where each
approach puts a parameter. The pair is written into each of the seven question
rows in each approach's shape, plus one composite that puts the whole chain for
one rule in three panes. Where an approach answers a question with nothing, as
assessment-first does for 6a, nothing is encoded and nothing is invented.
`--example` holds the encodings to the disciplines the extracts are held to: real
published identifiers, a real namespace on every property that carries one and
none of them ours, nobody named, and the same rules in the same order in every
column.

`verify.py` does more than diff. It asserts named facts against the corpora,
recomputes every figure the site cites, and, when the two source documents are on
disk, opens them to confirm that everything the site marks verbatim occurs in the
document it names: the fifteen criteria and their attributions against the
pre-read, the eleven evidence-register items, and the position paper's ten open
questions. When they are not on disk it skips those by name rather than passing
them. The editorial rules were checked against the development plan by a
`--methodology` phase, which went when the methodology page it checked was
removed; they are no longer machine-checked.

## Layout

```
data/
  snippets/          29 files, one per extract, never edited by hand
  schema-evidence/   8 verbatim OSCAL 1.2.1 schema fragments with their constraints
  six-questions.json the six questions and the answer matrix, the central claim set
  pattern-examples.json  the two rules, written in all three shapes. Ours
  oscal-artifacts.json   what each of the three groups has published, counted
  criteria.json      the fifteen evaluation criteria, verbatim from the pre-read
  criteria-fill.json the forty-five cells, answered from the files
  sources.json       the guidance read as input, one row per benchmark
  source-files.json  every file under sources/, generated, with size and type
  views.json         the three views of what a rule is
  glossary.json      the vocabulary, including the terms the group has not
                     settled. Rendered as term cards in place; there is no
                     glossary page
  questions.json     the evidence register, the open questions, and their sources
  quotes.json        the record of what was said. Retained, and never rendered
  corpus-stats.json  every figure cited, each with its derivation
  provenance.json    generated
tools/
  manifest.yaml      the declarative extract manifest
  extract.py         builds data/snippets and data/provenance.json
  pattern_examples.py  builds data/pattern-examples.json, the site's own encodings
  oscal_artifacts.py   builds data/oscal-artifacts.json from the three corpora
  sources_files.py   builds data/source-files.json from sources/
  diagrams.py        builds the published SVGs in assets/diagrams from data/
  approach_pages.py  builds the three approach pages from one template
  scenario_page.py   builds scenario.html, the one page that carries figures
  bundle.py          builds assets/bundle.js, the offline fallback
  svgrender.py       rasterises the diagrams for the grayscale contact sheet
  verify.py          the check harness
  pagecheck.js       runs a page's renderers and asserts on the result
  axe_run.mjs        serves the site and runs axe-core over every page
  serve.py           a local static server
serve.cmd            double-click to serve the site on Windows
```

Eight of those are generators and the files they produce must not be edited by
hand: `data/snippets/*.json` and `data/provenance.json`,
`data/pattern-examples.json`, `data/oscal-artifacts.json`,
`data/source-files.json`, `assets/diagrams/*.svg`, `data/criteria-fill.json`, the
three approach pages, and `assets/bundle.js`. The workflow regenerates all of
them and fails if the result differs from what was committed.

`tools/diagrams.py` builds 19 diagrams and writes 9. The other 10, the base layer
map, the three stakeholder variants and the rest, were only ever on a component
gallery that has been removed. The builders are kept, because the drawing code
belongs in one place, and the `PUBLISHED` constant at the foot of the file is the
list of what reaches `assets/diagrams/`. Add a name there to publish one.

## Editorial policy

Thirteen rules govern every page. They live in section 3 of the development
plan, `TFG-Rules-and-Checks-Site-Plan.md`, including the seven that a later
decision superseded in part. They were also published on the site, on a
methodology page that has since been removed. The load-bearing ones:

- **The site authors no evaluation criteria.** The fifteen come from the pre-read
  unchanged. Their arithmetic is checked on every build, and their wording is
  checked against the pre-read on any build that can reach it.
- **The site carries no quotations and names nobody.** Every characterization
  traces to a JSON pointer into a published file, or to the document the claim
  comes from. Structural names and option letters only. `tools/pagecheck.js`
  enforces it per page, over rendered prose rather than markup, with a file path
  exempt because a path is provenance. **`oscal-artifacts.html` is exempt by
  name**, and is required to name publishers rather than merely permitted to: an
  inventory of who published what is useless with the publisher redacted, and
  that page weighs nothing and states no position. Every other page is held to
  the rule.
- **Equal budget is enforced by construction**, not by judgement. One generator
  writes the three approach pages and refuses to write them if their word counts
  differ by more than ten per cent.
- **Non-verbal encoding counts as editorializing.** A badge, a hollow cell or a
  hatch fill argues in a channel a word count cannot see, so every annotation type
  applies to all three approaches or to none.
- **Consequences, not verdicts.** State the cost; let the reader price it.
- **Every figure carries its denominator**, and every figure is recomputed from
  the corpora on every build.

One rule could not be met. Rule 5 asks for the same number of extracts on each
approach page, which is unreachable for a structural reason rather than an
editorial one: an unanswered question has nothing to extract, and a corpus that
answers a question with one construct needs one extract where a corpus that
answers it with three needs three. The counts today are 1, 1 and 2. Each page
states its own count and the reason instead, in identical wording, and says that
the count is not a measure of how well documented an approach is. The departure is
stated on each page rather than quietly met in a weaker form.

## Contributing a correction

**If something about your approach is stated wrongly here, that correction is
more valuable than anything else you could send.** Open an issue or a pull
request. Corrections are published on the site, unedited, with the correction
attributed to whoever made it.

Four kinds are worth more than the others, and none of them is a matter of
opinion:

1. **A characterization of your approach that is wrong.** Section 7 of each
   approach page states the case for that approach as its proponents would state
   it. If it is not the case you would make, say so; that is the one thing no
   check on this site can catch.
2. **An encoding written in the wrong shape.** The JSON on the question pages is
   ours, not yours: two rules written out in each approach's shape so the columns
   are comparable. The build checks that the shape is well formed, uses real
   identifiers and invents no namespace. It cannot check that it is the shape you
   would actually write, and that is the correction worth the most.
3. **An extract that is unrepresentative.** Every extract is provably what the
   file says at the pointer declared. Whether it is the right fragment to show is
   a judgement, and the site's author made it.
4. **A figure that is out of date.** Every count is recomputed from the corpora
   on each build, so a figure here is what the files said when they were read. If
   a publisher has since corrected one, that is worth reporting.

If an extract looks wrong, run `python tools/verify.py --snippets`. If that
passes and it still looks wrong, the manifest pointer is aimed at the wrong
place, which is a real defect. If an encoding looks wrong, the defect is in
`tools/pattern_examples.py` rather than in a pointer, and
`python tools/verify.py --example` is the check that covers it.

A criterion cannot be added here. Editorial rule 4 forbids the site from
authoring evaluation criteria, so a sixteenth goes to the working group and this
site follows.

## Adding a fourth approach

The site is built so that this is a data change and a page, not a rewrite.

1. **Add the corpus.** Put the published files where `corpora_root` in
   `tools/manifest.yaml` can reach them.
2. **Declare the extracts.** Add manifest entries with a source file, an RFC 6901
   pointer, and the question each one illustrates. Run `python tools/extract.py`.
3. **Add the approach to `data/six-questions.json`.** One entry under `approaches` with
   a structural name, an option letter, a primary model, which of the three views
   of a rule its proponents hold, which reader it serves first, and its status
   annotation. Then one `matrix` cell for each of the seven question rows, each
   with a state, a note that becomes its tooltip, and the extracts that evidence
   it. An unanswered cell must say which of the three kinds of unanswered it is.
4. **Write the two rules in your shape.** Add a fourth column to
   `tools/pattern_examples.py`: the same two rules, in the same order, for every
   question row the approach answers, each block naming the OSCAL construct that
   carries it and carrying your own namespace on any property that needs one. A
   question the approach answers with nothing gets no block.
5. **Add a one-line summary** to the same `data/six-questions.json` entry, within
   ten per cent of the length of the others.
6. **Add the page content** to `tools/approach_pages.py`: the gist, the per-question
   prose, the case and the questions against it, and the three status sentences.
   The generator supplies the structure and refuses to write pages that break the
   budget.
7. **Regenerate and verify.** Run the generators in the order given under *How the
   content is produced*, then `python tools/verify.py --all`.

The checks will tell you what is missing. `--matrix` will reject an unclassified
cell, `--example` will reject a column whose rules do not match the others,
`--budget` will reject an unequal page, and `--criteria` will reject a criteria
table that does not answer all fifteen for the new approach.

Two more things. The inventory page needs a fourth entry in the `PUBLISHERS` list
in `tools/oscal_artifacts.py`, naming the corpus directory and the option letter;
everything else on that page is counted off the files and nothing about it is
described by hand. And `sources/` lists the hardening guidance read as input, not
the OSCAL written from it, so a new corpus does not go there.

## License

CC BY 4.0. See `LICENSE`. The site's own text, diagrams and encodings are under
that licence.

Nothing else here is. The three OSCAL corpora belong to their publishers and are
not redistributed; only extracts at declared pointers, with provenance in
`data/provenance.json`. Under `sources/`, the DISA material is a work of the
United States Government; the CIS Benchmarks are here on the publisher's
participation in this review rather than on a grant in their Agreed Terms of
Use, which is why that basis is written on each of those files rather than
assumed. Each file in `data/source-files.json` carries its own terms.
