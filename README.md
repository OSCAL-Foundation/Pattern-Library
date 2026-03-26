# OSCAL Foundation — Pattern Library

A curated collection of high-quality, realistic [OSCAL](https://pages.nist.gov/OSCAL/) example artifacts published by the **OSCAL Foundation** to serve as patterns and practices for the community.

## About OSCAL Foundation

The Open Security Controls Assessment Language (OSCAL) is a machine-readable language that simplifies and standardizes information system security assessments through the exchange of information via automation.

Originally developed by the National Institute of Standards and Technology (NIST) in collaboration with FedRAMP and industry, OSCAL aims to improve the efficiency, timeliness, accuracy, and consistency of system security assessments.

The **OSCAL Foundation** is dedicated to furthering the development and adoption of the OSCAL standards. The Foundation is a nonprofit organization seeking 501(c)(3) tax-exempt status recognition.

## Purpose

There are few high-quality, representative examples of what an actual compliance package in OSCAL looks like. This Pattern Library fills that gap by providing complete, realistic model office examples that demonstrate proper use of all seven OSCAL models working together.

## Examples

| System | Organization | Description |
|--------|-------------|-------------|
| [**Summit**](summit/) | Oscalate Systems | A complete model office example covering all 7 OSCAL models |

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
└── summit/                          # Model Office: Summit by Oscalate Systems
    ├── README.md
    ├── diagrams/                    # Architecture and system diagrams
    ├── catalog/                     # OSCAL Catalog artifacts
    ├── profile/                     # OSCAL Profile (Baseline) artifacts
    ├── component-definition/        # OSCAL Component Definition artifacts
    ├── system-security-plan/        # OSCAL SSP artifacts
    ├── assessment-plan/             # OSCAL SAP artifacts
    ├── assessment-results/          # OSCAL SAR artifacts
    └── poam/                        # OSCAL POA&M artifacts
```

## Contributing

Contributions of high-quality OSCAL examples are welcome. Please ensure examples are realistic, well-structured, and follow OSCAL best practices.

## License

See [LICENSE](LICENSE) for details.

## Resources

- [OSCAL Official Documentation](https://pages.nist.gov/OSCAL/)
- [OSCAL GitHub Repository](https://github.com/usnistgov/OSCAL)
- [OSCAL Foundation](https://oscalfoundation.org)