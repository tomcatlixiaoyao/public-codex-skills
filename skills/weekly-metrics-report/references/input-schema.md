# Input Schema

Use UTF-8 JSON or CSV. All examples are synthetic.

## JSON

```json
{
  "title": "Service metrics weekly report",
  "language": "en",
  "value_label": "Request volume",
  "scale": 1000,
  "unit": "k",
  "precision": 1,
  "rate_precision": 2,
  "current_period": {"start": "2026-08-24", "end": "2026-08-30"},
  "previous_period": {"start": "2026-08-17", "end": "2026-08-23"},
  "metrics": [
    {
      "name": "Image processing",
      "current_value": 1512200,
      "previous_value": 1501600,
      "success_rate": 99.9,
      "previous_success_rate": 99.8
    },
    {
      "name": "Audio processing",
      "current_value": 685900,
      "previous_value": 440900,
      "success_rate": 99.99
    }
  ]
}
```

Top-level fields:

- `metrics`: required non-empty array.
- `title`: optional report heading.
- `language`: `zh` or `en`; defaults to `zh`.
- `value_label`: optional label shared by all metrics; defaults to `指标值` or `Value`.
- `scale`: positive display divisor; defaults to `1`.
- `unit`: optional suffix such as `k`, `M`, `万`, or `ms`.
- `precision`: decimal places for scaled values and absolute deltas; defaults to `1`.
- `rate_precision`: decimal places for rates; defaults to `2`.
- `current_period` and `previous_period`: optional inclusive `{start, end}` ISO dates. Supply both or neither.
- `include_relative_change`: optional boolean. Relative change is unavailable when the previous value is zero.
- `include_rate_change`: optional boolean. When both rates exist, show their percentage-point difference.

Metric fields:

- `name`: required non-empty label.
- `current_value`: required non-negative number.
- `previous_value`: optional non-negative number. When omitted, no delta is invented.
- `success_rate`: optional percentage in `0..100`.
- `previous_success_rate`: optional percentage in `0..100`.
- `value_label`: optional per-metric override.

## CSV

```csv
name,current_value,previous_value,success_rate,previous_success_rate,value_label
Image processing,1512200,1501600,99.9,99.8,Request volume
Audio processing,685900,440900,99.99,,Request volume
Documents,1500,,98.47,,Request volume
```

CSV uses the same metric fields. Supply report-wide display options on the command line:

```text
python scripts/generate_report.py metrics.csv --language en --scale 1000 --unit k
```

## Missing Data

- Blank `previous_value`: show that the comparison value is unavailable.
- Blank `success_rate`: show that the rate is unavailable.
- Blank `previous_success_rate`: omit percentage-point comparison and disclose it when rate comparison was requested.
- Missing or invalid `current_value`: stop with an error because the current result cannot be reported reliably.
