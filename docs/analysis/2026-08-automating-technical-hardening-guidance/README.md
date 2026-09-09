# Automating Technical Hardening Guidance with OSCAL

A comparison site for the OSCAL Foundation Technical Focus Group on Automated
Assessments.

Three organizations have published OSCAL content addressing the question:
**where does technical hardening guidance live in
OSCAL, and how does an automated check attach to it?** The analysis compares
three approaches against six questions, encodes
the same two rules in all three model structures to isolate modelling
differences, and identifies the join key for each approach.

**The JSON encodings on the question pages were authored for the analysis.**
The published content covers different products: a certificate control, an
object-store rule, and a Linux STIG would compare subject matter rather than
modelling. Instead, `tools/pattern_examples.py` encodes two published Ubuntu
24.04 LTS requirements in each approach's structure, retaining the published
identifiers. Only the encoding is authored; property namespaces come from the
illustrated approaches, not the analysis authors. `oscal-artifacts.html`
inventories the published content separately, one row per document, with
contents counted from each file. Extracts supporting claims retain declared
pointers into published files and are re-derived on every build.

The analysis uses published hardening guidance from CIS, DISA, CISA, and AWS.
The introduction lists one row per benchmark or guide in a collapsed disclosure,
with links to source material. File icons download the 16 documents recorded
under `sources/`, totalling 29.0 MB; hover text gives the filename, type, and
size. Globe icons link to publisher pages for guidance without a downloadable
document. All source links open in new tabs. **Only inputs are listed.** OSCAL
content derived from the guidance is published separately.
`tools/sources_files.py` excludes `sources/oscal/` from the inventory and also
excludes `disa/U_Readme_SRG_and_STIG.pdf`, which describes STIG packages rather
than an individual guide. `verify.py --sources` recomputes counts from the
corpora and checks link resolution, coverage of included files in `sources/`,
and absence of links into the excluded tree. Each file lists publisher terms.

**The basis for including CIS material is recorded.** `sources/cis/` holds two
CIS Benchmarks in JSON and PDF, accounting for 19.7 MB of the 29.0 MB. On their
face, CIS's Agreed Terms of Use prohibit redistributing a Benchmark or posting a
Benchmark on a website. CIS is a stakeholder receiving the brief and confirmed that copying
and linking infringes nothing. `BUILD-LOG.md` records the confirmation. Each of
the four files states the basis for inclusion, not a general grant:
*"Reproduced here with the publisher's participation in this
review. The Benchmarks carry CIS's own Agreed Terms of Use; consult the
publisher before reusing them elsewhere."* **A fork or a mirror made outside
that conversation does not inherit the basis.** The DISA material is a work of
the United States Government, 13 files and 9.3 MB, 12 of them with a row.

**No recommendation is made.** The analysis provides no ranking, score, or
implied recommendation. Costs are stated for readers to evaluate.

## Status

Ready to publish, not published. Eight pages, all built: `index.html`,
`six-questions.html`, the three approach pages, `scenario.html`, `questions.html`
and `oscal-artifacts.html`. Remaining review and verification items:

- **Proponent review has not happened.** No correction requests have been sent
   to the publishers; no corrections have been received, and no publisher has
   declined review. The site states the review status.
- Four checks require network access, skip locally, and run in CI.
- The verbatim portions of `--criteria` and `--questions` skip when the pre-read
   and position paper are absent. The two Word documents reside outside the site
   and are absent from the corpora repository checked out by the workflow, so the
   verbatim checks skip in CI and locally. Place both documents at the corpora
   directory root to enable the checks.

`BUILD-LOG.md` records every phase, every decision, and the open items for each
review gate.

## Viewing the site

The analysis is served within the Pattern Library. The former standalone
`serve.cmd` and `tools/serve.py` have been removed. A server rooted in the
analysis folder would exclude the library landing pages.

From the repository root, serve `docs/` and open the analysis from the analysis
index. Press F5 in VS Code to start the server and open the site:

```
python3 -m http.server --directory docs 4173
npx serve docs
```

Or install the recommended Live Preview extension and click the preview button
on a page; `.vscode/settings.json` sets the server root to `docs/`.
The analysis path is:

```
/analysis/2026-08-automating-technical-hardening-guidance/
```

### Why a server, and what happens without one

Page markup contains hooks populated by `assets/site.js` from `data/` at load
time. Regenerating data leaves markup unchanged. Browsers assign opaque origins
to `file://` pages and block `fetch()`, preventing direct access to data files.

Opening `index.html` directly still works: `assets/bundle.js` contains copies
of every data file and diagram. The page reads the bundle and displays a notice:

> Opened from a folder rather than a server, so this page read its content from
> `assets/bundle.js`, a mirror of `data/` that the build checks byte for byte ...

**The notice identifies the content source, not an error.**
`tools/verify.py --bundle` rebuilds the mirror and fails on any content
difference. Served pages read `data/` directly without the notice. GitHub Pages
serves over HTTP, so published pages do not display the notice.

## Verifying it

Install dependencies and run verification:

```
pip install pyyaml pillow
python tools/verify.py --all
```

Pillow is required: `verify.py` imports `svgrender`, which imports Pillow at
module scope to rasterise diagrams for `--diagrams`.

Verification reads corpora from `TFG_CORPORA`, falling back to `corpora_root`
in `tools/manifest.yaml` when the environment variable is unset. The site resides
under `docs/analysis/`, not beside the corpora. Set `TFG_CORPORA`:

```
export TFG_CORPORA=/path/to/tfg-automated-assessments
```

Eighteen checks report `PASS`, `FAIL`, or `SKIP`. A skipped check reports the
reason and command separately from passed checks. **A skip is never counted as
a pass.**

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

**In CI**, `--strict` treats every skip as a failure on a runner with network
access and validators. See `.github/workflows/verify-2026-08-hardening-guidance.yml`
at the repository root.

### What needs network

| Check | Needs | Command |
|---|---|---|
| `--schema`, second half | The published NIST 1.2.1 schemas | `curl` the schema, compare each stored fragment |
| `--conformance` | An OSCAL validator | `pip install compliance-trestle` |
| `--a11y`, second half | axe-core and a headless browser | `npm install --no-save axe-core puppeteer` |
| `--links`, external half | External link targets | `curl -o /dev/null -w '%{http_code}'` per link |

## How the content is produced

The site generates content rather than transcribing or duplicating source
material. Labels distinguish two content types. An **extract** comes from a
published file at a declared JSON pointer and is re-derived on every build. An
**encoding** comes from generator-held data, is labelled as authored for the
analysis, and is regenerated and diffed on every build to detect hand edits.
Every figure is recomputed from the corpora.

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

The workflow runs generators in the listed dependency order. The bundle runs
last to mirror all preceding output. Four generators accept `--check` to compare
without writing and exit non-zero for stale committed files:
`pattern_examples.py`, `oscal_artifacts.py`, `sources_files.py`, and `bundle.py`.
`approach_pages.py` records generated-page hashes and refuses to overwrite
hand-edited pages. Editing a generated page instead of source data stops the
build rather than losing the edit.

`tools/manifest.yaml` is the declarative source of truth for the extracts. Each
of the 29 entries names a source file, an RFC 6901 pointer, the illustrated
question, and any trimming applied. Trimming is declared and marked in rendered
output; there is no silent truncation.
`data/provenance.json` records the SHA-256 of both the source file and the
extracted content.

`tools/pattern_examples.py` is the source of truth for encodings. Two rules, one
binary and one carrying a value, demonstrate parameter placement. The generator
encodes the rules for each of seven question rows in each approach's structure.
A composite shows one rule's complete chain in three panes. Unanswered questions,
such as assessment-first's 6a, receive no encoding. `--example` checks the same
constraints as extracts: published identifiers, approach namespaces where
required rather than invented namespaces, no named parties, and identical
rule order across columns.

`verify.py` asserts facts against the corpora and recomputes cited figures.
When source documents are available, verification checks verbatim material
against the named sources: fifteen criteria and attributions against the
pre-read, eleven evidence-register items, and ten open questions from the
position paper. Missing documents produce named skips, not passes. The former
`--methodology` phase checked editorial rules against the development plan.
Removal of the methodology page also removed the check; editorial rules are no
longer machine-checked by that phase.

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
```

Eight tools are generators. Do not hand-edit generated files:
`data/snippets/*.json` and `data/provenance.json`,
`data/pattern-examples.json`, `data/oscal-artifacts.json`,
`data/source-files.json`, `assets/diagrams/*.svg`, `data/criteria-fill.json`, the
three approach pages, and `assets/bundle.js`. The workflow regenerates the files
and fails on differences from committed versions.

`tools/diagrams.py` builds 19 diagrams and writes 9. The remaining 10 appeared
only in a removed component gallery, including the base layer map and three
stakeholder variants. The builders remain together in the drawing code.
`PUBLISHED`, at the foot of the file, lists diagrams written to
`assets/diagrams/`. Add a diagram name to `PUBLISHED` to publish the diagram.

## Editorial policy

Thirteen rules govern every page, as recorded in section 3 of the development
plan, `TFG-Rules-and-Checks-Site-Plan.md`. A later decision partly superseded
seven rules. The rules also appeared on the removed methodology page. Key rules:

- **The site authors no evaluation criteria.** The fifteen criteria come from
   the pre-read unchanged. Every build checks arithmetic; builds with access to
   the pre-read also check wording.
- **The site carries no quotations and names nobody.** Every characterization
   traces to a JSON pointer in a published file or a source document. Use
   structural names and option letters only. `tools/pagecheck.js` checks rendered
   prose per page, exempting file paths as provenance.
   **`oscal-artifacts.html` is exempt by name** and must name publishers to
   identify document provenance. The inventory states no position. All other
   pages follow the rule.
- **Equal budget is enforced by construction.** One generator writes the three
   approach pages and rejects word-count differences above ten per cent.
- **Non-verbal encoding counts as editorializing.** Badges, hollow cells, and
   hatch fills convey arguments outside word counts. Every annotation type
   applies to all three approaches or none.
- **Consequences, not verdicts.** State the cost; let the reader price it.
- **Every figure carries its denominator**, and every figure is recomputed from
  the corpora on every build.

Rule 5, requiring equal extract counts on approach pages, could not be met.
Unanswered questions provide no extract; an answer using one construct needs one
extract, while an answer using three constructs needs three. The counts are 1,
1, and 2. Each page discloses the count and reason with otherwise identical
wording, including a warning that extract counts do not measure documentation
quality. Each page states the departure from the rule.

## Contributing a correction

**Report mischaracterizations of an approach through an issue or pull request.**
Corrections are published unedited and attributed to the contributor.

Priority correction types:

1. **Mischaracterization of an approach.** Section 7 of each approach page
   presents the proponents' case. Proponents should report differences from the
   intended argument; automated checks cannot establish agreement.
2. **Incorrect encoding.** The analysis authors encoded two rules in each
   approach's structure for comparison. The build checks structure, published
   identifiers, and absence of invented namespaces, but cannot confirm that
   proponents would use the same encoding.
3. **Unrepresentative extract.** Verification proves the extract matches the
   declared file pointer. Selecting a representative fragment remains an
   editorial judgement by the analysis author.
4. **Outdated figure.** Counts are recomputed from the corpora on each build.
   Report publisher corrections made since the files were read.

For a suspected extract error, run `python tools/verify.py --snippets`. A
passing check with an unrepresentative extract indicates a manifest-pointer
selection defect. Encoding defects belong in `tools/pattern_examples.py`, not
the manifest; run `python tools/verify.py --example` to check encodings.

Editorial rule 4 forbids authoring evaluation criteria for the site. Submit a
sixteenth criterion to the working group before inclusion in the analysis.

## Adding a fourth approach

Adding an approach requires data changes and a page, not a site rewrite.

1. **Add the corpus.** Put the published files where `corpora_root` in
   `tools/manifest.yaml` can reach them.
2. **Declare the extracts.** Add manifest entries with a source file, an RFC 6901
   pointer, and the illustrated question. Run `python tools/extract.py`.
3. **Add the approach to `data/six-questions.json`.** Add an `approaches` entry
   with a structural name, option letter, primary model, proponents' view of a
   rule among the three views, primary reader, and status annotation. Add a
   `matrix` cell for each of the seven question rows, with a state, tooltip note,
   and supporting extracts. Classify unanswered cells using one of the three
   unanswered states.
4. **Encode the two rules in the approach's structure.** Add a fourth column to
   `tools/pattern_examples.py`: the same two rules, in the same order, for every
   answered question row. Each block names the containing OSCAL construct and
   uses the approach's namespace on properties requiring a namespace.
   Unanswered questions receive no block.
5. **Add a one-line summary** to the same `data/six-questions.json` entry, within
   ten per cent of the length of the others.
6. **Add the page content** to `tools/approach_pages.py`: the gist, the per-question
   prose, the case for the approach, questions about the approach, and three
   status sentences. The generator supplies the structure and rejects pages
   exceeding the budget.
7. **Regenerate and verify.** Run the generators in the order given under *How the
   content is produced*, then `python tools/verify.py --all`.

Checks identify omissions: `--matrix` rejects unclassified cells, `--example`
rejects columns with mismatched rules, `--budget` rejects unequal pages, and
`--criteria` requires answers to all fifteen criteria for the added approach.

Add a fourth entry to `PUBLISHERS` in `tools/oscal_artifacts.py`, naming the
corpus directory and option letter. The inventory derives the remaining content
from files rather than hand-authored descriptions. Keep the OSCAL corpus outside
`sources/`, which lists input hardening guidance, not derived OSCAL content.

## License

CC BY 4.0 applies to analysis-authored text, diagrams, and encodings. See
`LICENSE`.

The licence does not cover source material. The three OSCAL corpora belong to
the publishers and are not redistributed; only extracts at declared pointers
are included, with provenance in `data/provenance.json`. Under `sources/`, DISA
material is a work of the United States Government. CIS Benchmarks are included
on the basis of publisher participation in the review, not a grant under the
Agreed Terms of Use. Each CIS file states the basis for inclusion.
`data/source-files.json` records terms for each file.
