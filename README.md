# OSCAL Foundation — Pattern Library

A collection of [OSCAL](https://pages.nist.gov/OSCAL/) example artifacts published by the **OSCAL Foundation** as community patterns and practices.

## About OSCAL Foundation

The Open Security Controls Assessment Language (OSCAL) is a machine-readable language for simplifying and standardizing information system security assessments through automated information exchange.

Developed by the National Institute of Standards and Technology (NIST) with FedRAMP and industry, OSCAL aims to improve the efficiency, timeliness, accuracy, and consistency of system security assessments.

The **OSCAL Foundation** supports the development and adoption of OSCAL standards. The Foundation is a nonprofit organization seeking recognition of 501(c)(3) tax-exempt status.

## Purpose

The repository collects OSCAL compliance-package examples and design analyses.

The repository is published as a website: **<https://oscal-foundation.github.io/Pattern-Library/>**

Three areas have separate lifecycles.

| Area | Contents |
|---|---|
| [**Patterns**](docs/patterns/summit/) | Model office examples covering the seven OSCAL models, published as machine-readable files |
| [**Analyses**](docs/analysis/) | Comparisons of OSCAL approaches, retained in separate areas after conclusion |
| [**Recommendations**](docs/recommendations/) | Foundation recommendations citing the supporting analyses |

## Examples

| System | Organization | Description |
|--------|-------------|-------------|
| [**Summit**](docs/patterns/summit/) | Oscalate Systems | A complete model office example covering all 7 OSCAL models |

## Analyses

Each analysis has a dated area, never renamed, moved, or deleted. Concluded analyses are not rewritten to match later views. A replacement analysis receives a new area; the earlier analysis is marked as superseded to preserve the record.

| Opened | Analysis | Status |
|---|---|---|
| 2026-08 | [Automating Technical Hardening Guidance with OSCAL](docs/analysis/2026-08-automating-technical-hardening-guidance/) | active |

Each analysis has an `analysis.json` beside `index.html` and an entry in [docs/analysis/analyses.json](docs/analysis/analyses.json), the registry rendered by the analysis index. Adding an analysis requires a new area and registry entry, not an index-page edit.

## OSCAL Models Covered

Each library example aims to include artifacts for all seven OSCAL models:

1. **Catalog** — Security control definitions
2. **Profile** — Baseline selection and tailoring
3. **Component Definition** — Component-level security capabilities
4. **System Security Plan (SSP)** — System security documentation
5. **Assessment Plan (SAP)** — Security assessment planning
6. **Assessment Results (SAR)** — Assessment findings
7. **Plan of Action & Milestones (POA&M)** — Remediation tracking

## Repository Structure

`docs/` is published unchanged, with no build or generation step at deployment.

```
Pattern-Library/
├── README.md
├── .github/workflows/
│   ├── pages.yml                     # publishes docs/
│   └── verify-2026-08-*.yml          # one analysis's own harness
└── docs/
    ├── index.html                    # landing: the three areas
    ├── assets/
    ├── patterns/
    │   ├── index.html
    │   └── summit/                   # Model Office: Summit by Oscalate Systems
    │       ├── diagrams/                 # Architecture and system diagrams
    │       ├── catalog/                  # OSCAL Catalog artifacts
    │       ├── profile/                  # OSCAL Profile (Baseline) artifacts
    │       ├── component-definition/     # OSCAL Component Definition artifacts
    │       ├── system-security-plan/     # OSCAL SSP artifacts
    │       ├── assessment-plan/          # OSCAL SAP artifacts
    │       ├── assessment-results/       # OSCAL SAR artifacts
    │       └── poam/                     # OSCAL POA&M artifacts
    ├── analysis/
    │   ├── index.html
    │   ├── analyses.json             # the registry the index renders from
    │   └── 2026-08-…/                # one self-contained analysis
    └── recommendations/
        ├── index.html
        └── recommendations.json
```

Artifacts reside in `patterns/` rather than the repository root so links resolve identically in local and published pages. No copying or rewriting is required.

## Running the site

Press **F5**. The `Pattern Library` configuration starts a static server on port 4173 and opens the landing page with the debugger attached. Breakpoints in `docs/assets/site.js` bind to the served file. Edge is the default; a Chrome configuration is available for installations with Chrome.

The task serves `docs/` with `python3 -m http.server`, without installing dependencies or using repository server code. An equivalent static server also works:

```
python3 -m http.server --directory docs 4173
npx serve docs
```

Alternatively, install the recommended [Live Preview](https://marketplace.visualstudio.com/items?itemName=ms-vscode.live-server) extension and click the preview button on a page under `docs/`, or run **Live Preview: Show Debug Preview** for breakpoints. `.vscode/settings.json` sets the server root to `docs/`.

**Run Task** provides these tasks:

| Task | Action |
|---|---|
| `site: serve` / `site: stop` | Start or stop the F5 server without the debugger |
| `analysis 2026-08: prepare sources` | Explicitly fetch or repair the pinned public AWS cache and check committed examples |
| `analysis 2026-08: verify` | Check locked inputs, then recompute every figure and extract offline; never fetch inputs |
| `analysis 2026-08: regenerate` | Check locked inputs, then run every generator in dependency order; never fetch inputs |

For the August analysis, run **prepare sources** once before **verify** or **regenerate**, and again if the public cache is missing, corrupt, or its pin changes. Preparation is not an automatic task dependency, so verification cannot silently access the network. No personal corpus folder or source-repository Actions variables are needed.

The [source lock](docs/analysis/2026-08-automating-technical-hardening-guidance/tools/source-lock.json) defines 6 committed IBM and 18 committed Easy Dynamics JSON inputs plus 231 public AWS JSON files pinned to revision `4a1779ffb556c4ab8fb3dad94a19d4d198116803`. Committed examples are authoritative, checked against the size and SHA-256 fingerprints in [data/examples.json](docs/analysis/2026-08-automating-technical-hardening-guidance/data/examples.json). Explicit preparation authenticates the AWS archive against the lock before caching it; subsequent source checks use that verified cache offline. Missing or corrupt inputs fail rather than becoming empty counts or skipped checks. Changing an input pin is an explicit tracked change requiring updates to affected provenance, link indexes and generated outputs. See the [analysis verification instructions](docs/analysis/2026-08-automating-technical-hardening-guidance/README.md#verifying-it) for the exact fetch/check commands and cache location. These are build-time inputs, not new browser downloads; Pages publication is unchanged.

The library index pages require a server to load lists from JSON registries: browsers block `fetch` on a `file://` origin. Affected pages display a message rather than an empty list.

The “Work in progress” bar appears only within active analyses without a recorded decision. Each analysis's `analysis.json` controls visibility: `status` must be `active`, with no `concluded`, `recommendation`, `decision`, `decided`, or `supersededBy` value. A missing decision does not imply that an analysis will issue a recommendation. Library landing pages and indexes carry no banner.

Closing the bar hides the notice across pages of that analysis for the browser tab's session, without affecting other analyses. With JavaScript disabled or status unavailable, the notice stays hidden. Folder-based copies read analysis status from the generated bundle.

Banner regression checks: `node docs/analysis/2026-08-automating-technical-hardening-guidance/tools/bannercheck.js`.

## Contributing

Contribute OSCAL examples grounded in implementation practice, organized by model, and following OSCAL best practices.

## License

See [LICENSE](LICENSE) for details.

## Resources

- [OSCAL Official Documentation](https://pages.nist.gov/OSCAL/)
- [OSCAL GitHub Repository](https://github.com/usnistgov/OSCAL)
- [OSCAL Foundation](https://oscalfoundation.org)