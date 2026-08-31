#!/usr/bin/env python3
"""Generate a deterministic weekly metrics report from JSON or CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


class InputError(ValueError):
    """Raised when report input cannot be interpreted safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 .json or .csv input file")
    parser.add_argument("--output", type=Path, help="Write Markdown to this file instead of stdout")
    parser.add_argument("--language", choices=("zh", "en"), help="Override input language")
    parser.add_argument("--as-of", type=parse_iso_date, help="Today date used for default periods")
    parser.add_argument("--scale", type=parse_positive_decimal, help="Positive display divisor")
    parser.add_argument("--unit", help="Display suffix such as k, M, 万, or ms")
    parser.add_argument("--precision", type=parse_precision, help="Decimal places for values")
    parser.add_argument("--rate-precision", type=parse_precision, help="Decimal places for rates")
    parser.add_argument(
        "--include-relative-change",
        action="store_true",
        help="Include percentage change when the previous value is non-zero",
    )
    parser.add_argument(
        "--include-rate-change",
        action="store_true",
        help="Include percentage-point change when both success rates are available",
    )
    return parser.parse_args()


def parse_iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date: {value}") from exc


def parse_positive_decimal(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("scale must be numeric") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise argparse.ArgumentTypeError("scale must be greater than zero")
    return parsed


def parse_precision(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("precision must be an integer") from exc
    if not 0 <= parsed <= 8:
        raise argparse.ArgumentTypeError("precision must be between 0 and 8")
    return parsed


def to_decimal(value: Any, field: str, *, required: bool = True) -> Decimal | None:
    if value is None or value == "":
        if required:
            raise InputError(f"{field} is required")
        return None
    if isinstance(value, bool):
        raise InputError(f"{field} must be numeric")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InputError(f"{field} must be numeric") from exc
    if not parsed.is_finite():
        raise InputError(f"{field} must be finite")
    return parsed


def load_input(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InputError(f"input file not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InputError(f"invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise InputError("JSON root must be an object")
        return payload
    if suffix == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return {"metrics": list(csv.DictReader(handle))}
        except UnicodeDecodeError as exc:
            raise InputError("CSV must be UTF-8") from exc
    raise InputError("input must use .json or .csv")


def clean_text(value: Any, field: str, *, default: str | None = None) -> str:
    if value is None or value == "":
        if default is not None:
            return default
        raise InputError(f"{field} is required")
    cleaned = " ".join(str(value).split())
    if not cleaned:
        raise InputError(f"{field} is required")
    return cleaned


def normalize_metrics(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_metrics = payload.get("metrics")
    if not isinstance(raw_metrics, list) or not raw_metrics:
        raise InputError("metrics must be a non-empty array")

    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_metrics, start=1):
        if not isinstance(raw, dict):
            raise InputError(f"metrics[{index}] must be an object")
        metric = {
            "name": clean_text(raw.get("name"), f"metrics[{index}].name"),
            "current_value": to_decimal(raw.get("current_value"), f"metrics[{index}].current_value"),
            "previous_value": to_decimal(
                raw.get("previous_value"), f"metrics[{index}].previous_value", required=False
            ),
            "success_rate": to_decimal(
                raw.get("success_rate"), f"metrics[{index}].success_rate", required=False
            ),
            "previous_success_rate": to_decimal(
                raw.get("previous_success_rate"),
                f"metrics[{index}].previous_success_rate",
                required=False,
            ),
            "value_label": clean_text(raw.get("value_label"), "value_label", default=""),
        }
        for field in ("current_value", "previous_value"):
            value = metric[field]
            if value is not None and value < 0:
                raise InputError(f"metrics[{index}].{field} must be non-negative")
        for field in ("success_rate", "previous_success_rate"):
            value = metric[field]
            if value is not None and not Decimal("0") <= value <= Decimal("100"):
                raise InputError(f"metrics[{index}].{field} must be between 0 and 100")
        normalized.append(metric)
    return normalized


def parse_period(raw: Any, field: str) -> tuple[date, date]:
    if not isinstance(raw, dict):
        raise InputError(f"{field} must be an object with start and end")
    try:
        start = datetime.strptime(str(raw["start"]), "%Y-%m-%d").date()
        end = datetime.strptime(str(raw["end"]), "%Y-%m-%d").date()
    except (KeyError, ValueError) as exc:
        raise InputError(f"{field} must contain valid ISO start and end dates") from exc
    if start > end:
        raise InputError(f"{field}.start must not be after end")
    return start, end


def resolve_periods(
    payload: dict[str, Any], as_of: date | None
) -> tuple[tuple[date, date], tuple[date, date]]:
    current_raw = payload.get("current_period")
    previous_raw = payload.get("previous_period")
    if (current_raw is None) != (previous_raw is None):
        raise InputError("current_period and previous_period must be supplied together")
    if current_raw is not None:
        current = parse_period(current_raw, "current_period")
        previous = parse_period(previous_raw, "previous_period")
        if (current[1] - current[0]) != (previous[1] - previous[0]):
            raise InputError("current and previous periods must have the same inclusive length")
        return current, previous

    today = as_of or date.today()
    current_end = today - timedelta(days=1)
    current_start = current_end - timedelta(days=6)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=6)
    return (current_start, current_end), (previous_start, previous_end)


def resolve_decimal_option(
    payload: dict[str, Any], key: str, override: Decimal | None, default: str
) -> Decimal:
    value = override if override is not None else to_decimal(payload.get(key, default), key)
    assert value is not None
    if value <= 0:
        raise InputError(f"{key} must be greater than zero")
    return value


def resolve_precision(payload: dict[str, Any], key: str, override: int | None, default: int) -> int:
    if override is not None:
        return override
    raw = payload.get(key, default)
    if isinstance(raw, bool):
        raise InputError(f"{key} must be an integer between 0 and 8")
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{key} must be an integer between 0 and 8") from exc
    if not 0 <= value <= 8:
        raise InputError(f"{key} must be between 0 and 8")
    return value


def format_decimal(value: Decimal, precision: int) -> str:
    quantum = Decimal(1).scaleb(-precision)
    formatted = format(value.quantize(quantum, rounding=ROUND_HALF_UP), "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def format_scaled(value: Decimal, scale: Decimal, precision: int) -> str:
    return format_decimal(value / scale, precision)


def format_period(period: tuple[date, date]) -> str:
    return f"{period[0].isoformat()} – {period[1].isoformat()}"


def roman(index: int) -> str:
    values = (
        (1000, "m"),
        (900, "cm"),
        (500, "d"),
        (400, "cd"),
        (100, "c"),
        (90, "xc"),
        (50, "l"),
        (40, "xl"),
        (10, "x"),
        (9, "ix"),
        (5, "v"),
        (4, "iv"),
        (1, "i"),
    )
    result: list[str] = []
    remaining = index
    for number, symbol in values:
        while remaining >= number:
            result.append(symbol)
            remaining -= number
    return "".join(result)


def generate_report(payload: dict[str, Any], args: argparse.Namespace) -> str:
    language = args.language or str(payload.get("language", "zh")).lower()
    if language not in {"zh", "en"}:
        raise InputError("language must be zh or en")
    metrics = normalize_metrics(payload)
    current_period, previous_period = resolve_periods(payload, args.as_of)
    scale = resolve_decimal_option(payload, "scale", args.scale, "1")
    precision = resolve_precision(payload, "precision", args.precision, 1)
    rate_precision = resolve_precision(payload, "rate_precision", args.rate_precision, 2)
    unit = args.unit if args.unit is not None else str(payload.get("unit", ""))
    unit = clean_text(unit, "unit", default="")
    include_relative = args.include_relative_change or bool(payload.get("include_relative_change", False))
    include_rate_change = args.include_rate_change or bool(payload.get("include_rate_change", False))

    default_title = "周度指标报告" if language == "zh" else "Weekly Metrics Report"
    title = clean_text(payload.get("title"), "title", default=default_title)
    default_label = "指标值" if language == "zh" else "Value"
    shared_label = clean_text(payload.get("value_label"), "value_label", default=default_label)

    if language == "zh":
        lines = [
            f"# {title}",
            "",
            f"- 本期：{format_period(current_period)}",
            f"- 对比期：{format_period(previous_period)}",
            "",
            "## 指标明细",
            "",
        ]
    else:
        lines = [
            f"# {title}",
            "",
            f"- Current period: {format_period(current_period)}",
            f"- Comparison period: {format_period(previous_period)}",
            "",
            "## Metrics",
            "",
        ]

    notes: list[str] = []
    for index, metric in enumerate(metrics, start=1):
        label = metric["value_label"] or shared_label
        current = metric["current_value"]
        previous = metric["previous_value"]
        current_text = format_scaled(current, scale, precision)
        if previous is None:
            value_text = f"{current_text}{unit}"
            comparison_text = "对比值未提供" if language == "zh" else "comparison unavailable"
            notes.append(f"{metric['name']}: {comparison_text}")
        else:
            delta = current - previous
            delta_text = format_scaled(abs(delta), scale, precision)
            sign = "+" if delta > 0 else "-" if delta < 0 else ""
            value_text = f"{current_text}({sign}{delta_text}){unit}"
            if include_relative:
                if previous == 0:
                    relative_text = (
                        "相对变化不可计算（基准为零）"
                        if language == "zh"
                        else "relative change unavailable (zero baseline)"
                    )
                    notes.append(f"{metric['name']}: {relative_text}")
                else:
                    relative = (current - previous) / previous * Decimal("100")
                    relative_sign = "+" if relative > 0 else ""
                    relative_text = f"{relative_sign}{format_decimal(relative, rate_precision)}%"
                    value_text += (
                        f"，相对变化：{relative_text}"
                        if language == "zh"
                        else f", relative change: {relative_text}"
                    )

        success = metric["success_rate"]
        if success is None:
            success_text = "未提供" if language == "zh" else "unavailable"
            notes.append(
                f"{metric['name']}: "
                f"{'成功率未提供' if language == 'zh' else 'success rate unavailable'}"
            )
        else:
            success_text = f"{format_decimal(success, rate_precision)}%"
            previous_success = metric["previous_success_rate"]
            if include_rate_change:
                if previous_success is None:
                    notes.append(
                        f"{metric['name']}: "
                        f"{'上期成功率未提供' if language == 'zh' else 'previous success rate unavailable'}"
                    )
                else:
                    point_delta = success - previous_success
                    point_sign = "+" if point_delta > 0 else ""
                    point_text = f"{point_sign}{format_decimal(point_delta, rate_precision)}"
                    success_text += (
                        f"（{point_text} 个百分点）"
                        if language == "zh"
                        else f" ({point_text} pp)"
                    )

        marker = roman(index)
        if language == "zh":
            lines.append(f"{marker}. {metric['name']}，{label}：{value_text}，成功率：{success_text}")
        else:
            lines.append(f"{marker}. {metric['name']}: {label} {value_text}; success rate {success_text}")

    if notes:
        lines.extend(["", "## 数据说明" if language == "zh" else "## Data Notes", ""])
        lines.extend(f"- {note}" for note in notes)

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    try:
        payload = load_input(args.input)
        report = generate_report(payload, args)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report, encoding="utf-8")
        else:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            sys.stdout.write(report)
    except (InputError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
