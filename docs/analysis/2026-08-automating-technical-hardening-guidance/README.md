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

Active analysis with eight built pages: `index.html`,
`six-questions.html`, the three approach pages, `scenario.html`, `questions.html`
and `oscal-artifacts.html`. Strict verification is not fully passing. Remaining
review and verification items:

- **Proponent review has not happened.** No correction requests have been sent
   to the publishers; no corrections have been received, and no publisher has
   declined review. The site states the review status.
- Schema, external-link and browser checks need their dependencies and network
   access; offline skips are not strict passes.
- Four known published assessment-plan schema defects remain, detailed below.
- Full checks require the repository-defined sources: committed examples and
   the verified public AWS cache. Prepare the cache explicitly before working
   offline; CI prepares it before corpus-dependent checks.

The 15 evaluation criteria and the open questions are maintained as analysis
content and verified structurally. They are not reproduced or attributed text.
Published OSCAL example evidence is checked against the locked source inputs.

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

Run these commands from this analysis directory. CI uses Python 3.12, Node.js
20 and the DejaVu fonts (`fonts-dejavu-core` on Ubuntu).

```sh
pip install pyyaml pillow 'jsonschema[format]' regex
node tools/bannercheck.js
test -f tools/test_verify.py && python -m unittest discover -s tools -p 'test_*.py' -v
python tools/verify.py --data --css --quotes --bundle --source --pages --offline
```

This subset checks local content, CSS, absence of quotation and attribution hooks,
bundled data, source-code sanity and page rendering without preparing the public
source cache. Unit discovery includes verifier and source-resolver tests.
`--pages` runs
[tools/pagecheck.js](tools/pagecheck.js); it can also be run directly with Node.
`--example` is not corpus-independent: it invokes the artifact inventory
generator, so it remains in the full pass below.

Pillow is required at import time by [tools/svgrender.py](tools/svgrender.py).
Formal OSCAL validation uses `jsonschema[format]` and `regex`; format dependencies
enforce timestamps and URIs, and `regex` supports Unicode patterns in the NIST schemas.
`compliance-trestle` is not used.
Install dependencies before disconnecting from the network.

### Repository-defined sources

[tools/source-lock.json](tools/source-lock.json) defines the source inventory;
[tools/source_inputs.py](tools/source_inputs.py) resolves it without environment
overrides or implicit downloads. No personal corpus folder, second repository
checkout, source-repository Actions variables, or private corpus upload is
required.

| Source | Authoritative input | JSON files |
|---|---|---:|
| IBM | Committed [examples/component-first/](examples/component-first/) | 6 |
| Easy Dynamics | Committed [examples/assessment-first/](examples/assessment-first/) | 18 |
| AWS | Public [awslabs/oscal-content-for-aws-services](https://github.com/awslabs/oscal-content-for-aws-services/tree/4a1779ffb556c4ab8fb3dad94a19d4d198116803), revision `4a1779ffb556c4ab8fb3dad94a19d4d198116803` | 231 |

The committed local examples are the source of truth. Their inventory, byte
sizes and SHA-256 fingerprints must match [data/examples.json](data/examples.json).
Missing, extra or changed JSON inputs fail validation; regenerating the index
is not a way to bless an unexpected local change. Restore the committed files
and index unless changing the inputs is an explicitly reviewed change.

Fetch once while online, before the full offline pass or regeneration:

```sh
python tools/source_inputs.py --fetch
python tools/source_inputs.py --check
```

Only explicit `--fetch` may download or repair the public AWS cache. The pinned
codeload archive is authenticated against the lock's byte size and SHA-256
before extraction. The cache is rooted at
`.cache/oscal-sources/aws/4a1779ffb556c4ab8fb3dad94a19d4d198116803/` within this
analysis directory, with the authenticated archive retained as
`.source-archive.tar.gz` alongside the selected JSON, LICENSE and NOTICE files.
The cache is ignored by Git; it is not a committed source copy or a runtime
download dependency. The resolver does not upload or read a private/local
corpus outside this repository.

`--check` is offline: it revalidates the local fingerprints, retained archive
and complete cached inventory. Missing or corrupt cached inputs fail; they are
never counted as an empty corpus, skipped, or fetched implicitly. Run `--fetch`
explicitly again to repair the public cache or prepare a changed pin. A valid
cache is reused without downloading.

Changing an input pin is an explicit tracked change to the source lock, not a
branch update or a machine-specific override. Update the archive URL, digest,
size, inventory and pinned link metadata together, and regenerate affected
provenance, example/link indexes and generated outputs, including the bundle.
Intentional local input changes likewise require reviewed updates to the
committed examples and their fingerprint index, and to the lock if inventory
counts change. Do not change published inputs merely to make checks pass.

### Offline and strict passes

After source preparation and dependency installation, run offline:

```sh
python tools/source_inputs.py --check
python tools/verify.py --all --offline
```

`--offline` prevents verifier network access; it does not replace or waive
source checks. Network-dependent checks report `SKIP`, separately from `PASS`
and `FAIL`. **An offline pass is not proof of strict verification.**

With the same locked inputs and network access available, run every check
with every skip treated as a failure:

```sh
npm install --no-save axe-core puppeteer
python tools/source_inputs.py --check
python tools/verify.py --all --strict
```

| Check | Additional requirement for strict verification |
|---|---|
| `--schema`, `--conformance` | Published NIST OSCAL 1.2.1 schemas; `jsonschema` and `regex` installed above |
| `--a11y` | axe-core and Puppeteer's headless browser |
| `--links` | Reachable external link targets |

Schema downloads use the pinned NIST 1.2.1 release assets, not generated-file
paths absent from the source tag. Refresh full schema evidence explicitly with
`python tools/schema_evidence.py assessment-subject by-component metadata`, then
regenerate the bundle. Do not rewrite published OSCAL examples to make validation pass.

The full `--all` pass retains extraction, corpus statistics, source inventory,
scenario, example, schema and conformance checks alongside structural checks.
Individual flags select checks for diagnosis; they do not replace the full pass.

In VS Code, run **analysis 2026-08: prepare sources** once while online before
**analysis 2026-08: verify** or **analysis 2026-08: regenerate**. Preparation is
deliberately not an automatic dependency. Both later tasks begin with
`--check` and never fetch inputs; **verify** runs `--all --offline`.
Use the strict command above when network-dependent verification is required.

### Source blockers

The published assessment plans contain four known schema failures: the Maester
and ScubaGear plans omit required `subjects` on associated activities;
Windows Server 2019 and 2022 activity titles
contain line breaks rejected by OSCAL 1.2.1. The verifier reports these failures.
Original source files and provenance hashes must not be edited to bypass them.
Source preparation does not resolve or suppress these defects. No validation
exceptions or edits to the original inputs have been applied.

### CI source preparation

The [verification workflow](../../../.github/workflows/verify-2026-08-hardening-guidance.yml)
runs banner tests, all verifier/source-resolver/workflow unit tests and the
corpus-independent offline subset in both jobs before source preparation.
Each job then runs `python tools/source_inputs.py --fetch` followed by
`python tools/source_inputs.py --check` before corpus-dependent phases.
Downloads and dependency installation precede `--all --offline`; the verifier
itself does not access the network in that pass. Source preparation or integrity
failure stops the job, with no fallback to an unpinned checkout or missing inputs.
The strict pass retains schema, external-link, browser and accessibility checks,
and treats every skip as a failure. After browser dependencies are installed, a
separate strict accessibility audit runs even if another check fails. Audit
errors and violations fail the job; they are not suppressed.

After the full offline pass, CI regenerates outputs in dependency order and
requires no changes in the generated-output paths, including additions,
deletions and untracked files. Its generation sanity step rechecks sources
offline and runs [tools/copy_examples.py](tools/copy_examples.py) before
[tools/oscal_artifacts.py](tools/oscal_artifacts.py). The existing data diff
covers [data/examples.json](data/examples.json), alongside provenance and other
data, [assets/bundle.js](assets/bundle.js), diagrams and generated pages.
The Pages-build job, publication workflow and organization Pages settings are
unchanged. No private corpus upload, additional credential or runtime network
change is part of this source preparation.

## How the content is produced

Published evidence and authored analysis are distinguished. An **extract** comes
from a published file at a declared JSON pointer and is re-derived on every build. An
**encoding** comes from generator-held data, is labelled as authored for the
analysis, and is regenerated and diffed on every build to detect hand edits.
Every figure is recomputed from the corpora.

```
python tools/source_inputs.py --check # require prepared inputs; never fetch here
python tools/extract.py          # rebuild data/snippets and data/provenance.json
python tools/pattern_examples.py # write the two rules in all three shapes
python tools/copy_examples.py    # rebuild data/examples.json from verified inputs
python tools/oscal_artifacts.py  # inventory what the three groups have published
python tools/sources_files.py    # rebuild data/source-files.json from sources/
python tools/diagrams.py         # rebuild every published SVG in assets/diagrams
python tools/approach_pages.py   # rebuild the three approach pages
python tools/scenario_page.py    # rebuild the worked scenario page
python tools/bundle.py           # rebuild the offline fallback
python tools/verify.py --all --offline # verify offline; run strict separately
```

The workflow runs generators in the listed dependency order. The bundle runs
last to mirror all preceding output. Five generators accept `--check` to compare
without writing and exit non-zero for stale committed files:
`pattern_examples.py`, `copy_examples.py`, `oscal_artifacts.py`, `sources_files.py`,
and `bundle.py`.
`approach_pages.py` records generated-page hashes and refuses to overwrite
hand-edited pages. Editing a generated page instead of source data stops the
build rather than losing the edit.

`tools/manifest.yaml` declares 32 snippets, all JSON. Each entry names a published
OSCAL JSON source file, an RFC 6901 pointer, the illustrated question, and any
trimming applied. Trimming is declared and marked in rendered
output; there is no silent truncation.
`data/provenance.json` records the SHA-256 of both the source file and the
extracted content.

`tools/pattern_examples.py` is the source of truth for encodings. Two rules, one
binary and one carrying a value, demonstrate parameter placement. The generator
encodes the rules for each of seven question rows in each approach's structure.
A composite shows one rule's complete chain in three panes. Unanswered questions
receive no encoding. `--example` checks the same
constraints as extracts: published identifiers, approach namespaces where
required rather than invented namespaces, no named parties, and identical
rule order across columns.

`verify.py` asserts OSCAL example facts against the corpora and recomputes cited
figures. The 15 criteria and open questions are analysis content: `--criteria`
and `--questions` check structure, identifiers, question mappings and reasoning,
not attribution or text reproduction. The former `--methodology` phase checked
editorial rules against the development plan.
Removal of the methodology page also removed the check; editorial rules are no
longer machine-checked by that phase.

## Layout

```
data/
   snippets/          32 JSON files, one per extract, never edited by hand
  schema-evidence/   8 verbatim OSCAL 1.2.1 schema fragments with their constraints
  six-questions.json the six questions and the answer matrix, the central claim set
  pattern-examples.json  the two rules, written in all three shapes. Ours
  oscal-artifacts.json   what each of the three groups has published, counted
   examples.json      committed local fingerprints and pinned public links
   criteria.json      the 15 evaluation criteria, maintained as analysis content
  sources.json       the guidance read as input, one row per benchmark
  source-files.json  every file under sources/, generated, with size and type
  views.json         the three views of what a rule is
  glossary.json      the vocabulary, including the terms the group has not
                     settled. Rendered as term cards in place; there is no
                     glossary page
   questions.json     editorial open questions and their reasoning, in four sections
  corpus-stats.json  every figure cited, each with its derivation
  provenance.json    generated
tools/
   source-lock.json    tracked local inventories and pinned public archive metadata
   source_inputs.py   explicit public fetch and offline input integrity checks
  manifest.yaml      the declarative extract manifest
  extract.py         builds data/snippets and data/provenance.json
  pattern_examples.py  builds data/pattern-examples.json, the site's own encodings
   copy_examples.py   builds data/examples.json from verified source inputs
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

Nine tools run in the regeneration pipeline. Do not hand-edit generated files:
`data/snippets/*.json` and `data/provenance.json`,
`data/pattern-examples.json`, `data/examples.json`, `data/oscal-artifacts.json`,
`data/source-files.json`, `assets/diagrams/*.svg`, the
three approach pages, `scenario.html`, and `assets/bundle.js`. The workflow regenerates the files
and fails on differences from committed versions.
The local files under `examples/` are authoritative inputs, not disposable
generator output; their committed fingerprints must already pass source checks
before regeneration.

`tools/diagrams.py` builds 19 diagrams and writes 9. The remaining 10 appeared
only in a removed component gallery, including the base layer map and three
stakeholder variants. The builders remain together in the drawing code.
`PUBLISHED`, at the foot of the file, lists diagrams written to
`assets/diagrams/`. Add a diagram name to `PUBLISHED` to publish the diagram.

## Editorial policy

Thirteen rules govern every page, as recorded in section 3 of the development
plan, `TFG-Rules-and-Checks-Site-Plan.md`. A later decision partly superseded
seven rules. The rules also appeared on the removed methodology page. Key rules:

- **The 15 criteria and open questions are maintained as analysis content.**
   Checks validate structure and mappings; editorial review assesses the wording
   and whether the questions fairly address each approach.
- **The site carries no quotations and names nobody.** Every characterization
   of published content traces to an OSCAL example at a declared JSON pointer.
   Editorial questions and modelling choices are identified as analysis. Use
   structural names and option letters only. `tools/pagecheck.js` checks rendered
   prose per page, exempting file paths as provenance.
   Guidance publishers and source paths remain identified for provenance;
   the artifact inventory describes published content, not proponent positions.
- **Equal budget is enforced by construction.** One generator writes the three
   approach pages and rejects word-count differences above ten per cent.
- **Non-verbal encoding counts as editorializing.** Badges, hollow cells, and
   hatch fills convey arguments outside word counts. Every annotation type
   applies to all three approaches or none.
- **Consequences, not verdicts.** State the cost; let the reader price it.
- **Every figure carries its denominator**, and every figure is recomputed from
  the corpora on every build.

Equal budgets apply to the authored comparison, not to the volume of evidence
a publisher happens to supply. Published extracts are selected to support claims;
extract counts do not measure documentation quality or rank the approaches.

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

Submit changes to the 15 evaluation criteria or open questions for analysis
review, and update their structural checks when the agreed structure changes.

## Adding a fourth approach

Adding an approach requires data changes and a page, not a site rewrite.

1. **Define the source inputs.** Extend [tools/source-lock.json](tools/source-lock.json)
   and [tools/source_inputs.py](tools/source_inputs.py) together, with tests,
   to authorize the new local inventory or pinned public archive. Record
   fingerprints and publisher terms; never rely on a personal folder or upload
   a private corpus. Prepare public inputs explicitly and check them offline.
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
`--criteria` validates the 15 criteria and their mappings to question rows.

Add a fourth entry to `PUBLISHERS` in `tools/oscal_artifacts.py`, naming the
corpus directory and option letter. The inventory derives the remaining content
from files rather than hand-authored descriptions. Keep the OSCAL corpus outside
`sources/`, which lists input hardening guidance, not derived OSCAL content.

## License

CC BY 4.0 applies to analysis-authored text, diagrams, and encodings. See
`LICENSE`.

The licence does not cover source material. The OSCAL corpora belong to their
publishers. The 6 IBM and 18 Easy Dynamics JSON files already committed under
`examples/` are source inputs; AWS documents are linked at the pinned public
revision and cached only for build-time verification. Extracts retain declared
pointers and provenance in `data/provenance.json`. Source preparation does not
authorize additional redistribution or uploading a private corpus.
Under `sources/`, DISA
material is a work of the United States Government. CIS Benchmarks are included
on the basis of publisher participation in the review, not a grant under the
Agreed Terms of Use. Each CIS file states the basis for inclusion.
`data/source-files.json` records terms for each file.
