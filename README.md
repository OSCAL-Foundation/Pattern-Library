# OSCAL Foundation — Pattern Library

A curated collection of high-quality, realistic [OSCAL](https://pages.nist.gov/OSCAL/) example artifacts published by the **OSCAL Foundation** to serve as patterns and practices for the community.

## About OSCAL Foundation

The Open Security Controls Assessment Language (OSCAL) is a machine-readable language that simplifies and standardizes information system security assessments through the exchange of information via automation.

Originally developed by the National Institute of Standards and Technology (NIST) in collaboration with FedRAMP and industry, OSCAL aims to improve the efficiency, timeliness, accuracy, and consistency of system security assessments.

The **OSCAL Foundation** is dedicated to furthering the development and adoption of the OSCAL standards. The Foundation is a nonprofit organization seeking 501(c)(3) tax-exempt status recognition.

## Purpose

There are few high-quality, representative examples of what an actual compliance package in OSCAL looks like, and few places where the arguments about how to build one are written down and kept. This repository holds both.

It is published as a website: **<https://oscal-foundation.github.io/Pattern-Library/>**

Three areas, each with its own lifecycle.

| Area | What it holds |
|---|---|
| [**Patterns**](summit/) | Model office examples covering the seven OSCAL models, published as files a tool can read |
| [**Analyses**](docs/analysis/) | Efforts that debate a question about OSCAL, one area per effort, retained after the effort ends |
| [**Recommendations**](docs/recommendations/) | What the Foundation recommends, each one citing the analysis it came from |

## Examples

| System | Organization | Description |
|--------|-------------|-------------|
| [**Summit**](summit/) | Oscalate Systems | A complete model office example covering all 7 OSCAL models |

## Analyses

Each effort gets its own dated area and keeps it. An area is never renamed, never moved and never deleted, and a concluded one is not edited into agreement with a later view: when an effort is superseded the new one gets its own area and the old one is marked, so the record shows the change rather than replacing it.

| Opened | Analysis | Status |
|---|---|---|
| 2026-08 | [Automating Technical Hardening Guidance with OSCAL](docs/analysis/2026-08-automating-technical-hardening-guidance/) | active |

An analysis carries an `analysis.json` beside its `index.html`, and an entry in [docs/analysis/analyses.json](docs/analysis/analyses.json) that the index page renders from. Adding an effort means adding an area and appending to that file; no page is edited.

## OSCAL Models Covered

Each example in this library aims to include artifacts for all seven OSCAL models:

1. **Catalog** — Security control definitions
2. **Profile** — Baseline selection and tailoring
3. **Component Definition** — Component-level security capabilities
4. **System Security Plan (SSP)** — System security documentation
5. **Assessment Plan (SAP)** — Security assessment planning
6. **Assessment Results (SAR)** — Assessment findings
7. **Plan of Action & Milestones (POA&M)** — Remediation tracking

## Repository Structure

```
Pattern-Library/
├── README.md
├── .github/workflows/
│   ├── pages.yml                    # assembles and deploys the site
│   └── verify-2026-08-*.yml         # one analysis's own verification harness
├── summit/                          # Model Office: Summit by Oscalate Systems
│   ├── README.md
│   ├── diagrams/                    # Architecture and system diagrams
│   ├── catalog/                     # OSCAL Catalog artifacts
│   ├── profile/                     # OSCAL Profile (Baseline) artifacts
│   ├── component-definition/        # OSCAL Component Definition artifacts
│   ├── system-security-plan/        # OSCAL SSP artifacts
│   ├── assessment-plan/             # OSCAL SAP artifacts
│   ├── assessment-results/          # OSCAL SAR artifacts
│   └── poam/                        # OSCAL POA&M artifacts
└── docs/                            # the published site
    ├── index.html
    ├── assets/
    ├── patterns/
    ├── analysis/
    │   ├── analyses.json            # the registry the index renders from
    │   └── 2026-08-…/               # one self-contained analysis
    └── recommendations/
        └── recommendations.json
```

The pattern artifacts live at `summit/` because they are the repository's product rather than part of its website. The deploy workflow copies them to `patterns/summit/` on the published site so the pages that link them are same-origin.

## Running the site

```
python3 tools/serve.py
```

Nothing to install. It serves `docs/` as the site root and answers anything under `/patterns/summit/` from `summit/` where it actually sits, which is the shape the deploy produces without the copy — so an edit shows up on refresh.

It listens on **8100**, not 8000. Each analysis ships its own server defaulting to 8000, and on WSL a Windows-side listener answers `127.0.0.1` without appearing in `ss`, so a collision there is silent and serves the wrong site. The VS Code task passes `--exact-port` so that fails loudly instead.

In VS Code, **Run and Debug** carries the same thing with a debugger attached:

| Configuration | What it does |
|---|---|
| Launch site (Chrome / Edge) | Starts the server and opens the landing page. Breakpoints in `docs/assets/site.js` bind to the served file. |
| Launch the 2026-08 analysis | Same, opening that analysis directly |
| Debug the server | Steps through `tools/serve.py` itself |
| Debug the analysis harness | Steps through that analysis's `tools/verify.py` |

Tasks (**Run Task**) cover the rest: `site: serve`, `site: stop`, `site: assemble _site`, and the 2026-08 analysis's `verify` and `regenerate`.

To check the artifact the workflow actually uploads rather than the overlay, run the `site: assemble _site` task, or:

```
rm -rf _site && mkdir -p _site/patterns
cp -r docs/. _site/ && cp -r summit _site/patterns/summit
python3 -m http.server -d _site 8000
```

## Contributing

Contributions of high-quality OSCAL examples are welcome. Please ensure examples are realistic, well-structured, and follow OSCAL best practices.

## License

See [LICENSE](LICENSE) for details.

## Resources

- [OSCAL Official Documentation](https://pages.nist.gov/OSCAL/)
- [OSCAL GitHub Repository](https://github.com/usnistgov/OSCAL)
- [OSCAL Foundation](https://oscalfoundation.org)