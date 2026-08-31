# Open-source evaluation rubric

Use this rubric for a structured comparison, especially when adoption will create a production dependency. Adjust weights only when the requirement makes another priority explicit.

## Hard gates

Reject or escalate a candidate before scoring when any of these conditions applies:

- No identifiable license, or a license incompatible with the intended use.
- Archived or clearly abandoned without a credible maintained fork.
- Known critical security exposure without a viable remediation path.
- Requires excessive privileges, undisclosed data transfer, or unsafe credential handling.
- Core functionality depends on an unavailable proprietary service.
- Cannot run in the target environment or violates a mandatory architecture constraint.

Unknown evidence is not a pass. Mark it as unknown and recommend the smallest check that can resolve it.

## Weighted assessment

| Dimension | Weight | Questions |
|---|---:|---|
| Functional fit | 25 | Does it solve the core problem without extensive unrelated machinery? |
| Architecture fit | 15 | Does its model align with the target system, data flow, and extension points? |
| Maintainability | 15 | Are releases, commits, issues, documentation, and maintainers healthy enough? |
| License and governance | 15 | Is the license compatible, and is project ownership sufficiently clear? |
| Security and supply chain | 15 | Are dependencies, privileges, advisories, update practices, and data movement acceptable? |
| Operations | 10 | Can it be deployed, observed, upgraded, backed up, and recovered affordably? |
| Integration cost | 5 | How much adapter code, migration, training, and long-term support is required? |

Score each dimension from 0 to 5, multiply by its weight, then divide the sum by 5 to obtain a 0–100 comparison score. Use the score to expose tradeoffs, not to replace judgment.

## Recommendation guidance

- **80–100**: strong adoption candidate if all hard gates pass.
- **65–79**: likely adaptation candidate; validate the largest gap.
- **50–64**: reference candidate unless constraints are unusually favorable.
- **Below 50**: build or continue searching.

The recommendation must identify the decisive evidence and the cost of being wrong. When top candidates are close, prefer a time-boxed proof of concept over artificial scoring precision.

## Minimum comparison fields

Record for each candidate:

- Repository and canonical documentation links.
- What it actually solves.
- Primary language and runtime.
- License.
- Latest meaningful maintenance evidence.
- Deployment and data model.
- Required privileges and external services.
- Integration effort and irreversible lock-in.
- Top benefit, top gap, and top risk.
