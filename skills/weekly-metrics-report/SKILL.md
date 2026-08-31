---
name: weekly-metrics-report
description: Generate evidence-based weekly metric comparisons and email-ready reports from two periods of structured data. Use when calculating period-over-period deltas, formatting KPI summaries, or drafting weekly updates from JSON or CSV. Do not use to invent missing values or retrieve data from authenticated or internal services.
---

# Weekly Metrics Report

Turn two comparable reporting periods into a concise, traceable weekly metrics update.

## Workflow

1. Inspect the supplied data and confirm that the two periods use the same metric definitions and units.
2. Read [references/input-schema.md](references/input-schema.md) when preparing JSON/CSV input or interpreting optional fields.
3. Use `scripts/generate_report.py` for deterministic arithmetic and formatting when the input matches the documented schema.
4. Verify unusual results against the raw values, especially negative deltas, zero baselines, missing comparison values, and rates outside the expected range.
5. Return the report together with the periods used, any assumptions, and explicit missing-data notes.

## Period Rules

- Prefer periods explicitly supplied by the user or input file.
- Otherwise use the latest seven complete calendar days ending yesterday as the current period, and the seven immediately preceding days as the comparison period.
- Treat both ranges as inclusive and use the user's local date unless another timezone or cutoff is specified.
- Do not silently compare periods of different length or different metric definitions.

## Calculation Rules

- Absolute delta is `current_value - previous_value` and must use the same scale and unit as the displayed current value.
- Relative change is `(current_value - previous_value) / previous_value * 100`; report it only when requested and when the previous value is non-zero.
- A percentage-point change is not the same as a percentage change. Label it explicitly if it is included.
- Preserve zeros. Never treat zero as missing.
- If a comparison value or success rate is absent, display it as unavailable instead of estimating it.
- Do not aggregate metrics with incompatible units or meanings.

## Safety Boundary

- This skill formats data already available to the user. It does not log into dashboards, reuse browser sessions, or call private APIs.
- Before publishing or sharing a report, remove internal domains, credentials, customer data, private identifiers, proprietary metric names, and confidential business figures.
- Use synthetic data in public examples and tests.

## Script Usage

```text
python scripts/generate_report.py input.json --output report.md
python scripts/generate_report.py input.csv --language en --scale 1000 --unit k
```

The script exits with an error for invalid current values, invalid dates, negative values, or rates outside `0..100`.
