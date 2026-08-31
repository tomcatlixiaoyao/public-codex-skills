from __future__ import annotations

import argparse
import importlib.util
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_report.py"
SPEC = importlib.util.spec_from_file_location("generate_report", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def args(**overrides):
    defaults = {
        "language": None,
        "as_of": date(2026, 8, 31),
        "scale": None,
        "unit": None,
        "precision": None,
        "rate_precision": None,
        "include_relative_change": False,
        "include_rate_change": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class GenerateReportTests(unittest.TestCase):
    def test_scaled_delta_and_default_periods(self):
        payload = {
            "language": "zh",
            "value_label": "请求量",
            "scale": 10000,
            "unit": "万",
            "metrics": [
                {
                    "name": "图片处理",
                    "current_value": 15122000,
                    "previous_value": 15016000,
                    "success_rate": 99.9,
                }
            ],
        }
        report = MODULE.generate_report(payload, args())
        self.assertIn("本期：2026-08-24 – 2026-08-30", report)
        self.assertIn("对比期：2026-08-17 – 2026-08-23", report)
        self.assertIn("请求量：1512.2(+10.6)万", report)
        self.assertIn("成功率：99.9%", report)

    def test_missing_values_are_explicit(self):
        payload = {
            "metrics": [{"name": "延迟", "current_value": 25, "value_label": "P95"}]
        }
        report = MODULE.generate_report(payload, args())
        self.assertIn("P95：25", report)
        self.assertIn("成功率：未提供", report)
        self.assertIn("对比值未提供", report)

    def test_zero_baseline_does_not_invent_relative_change(self):
        payload = {
            "include_relative_change": True,
            "metrics": [
                {"name": "任务量", "current_value": 10, "previous_value": 0, "success_rate": 100}
            ],
        }
        report = MODULE.generate_report(payload, args())
        self.assertIn("相对变化不可计算（基准为零）", report)

    def test_invalid_rate_is_rejected(self):
        payload = {
            "metrics": [{"name": "任务量", "current_value": 10, "success_rate": 101}]
        }
        with self.assertRaises(MODULE.InputError):
            MODULE.generate_report(payload, args())

    def test_rate_change_is_labeled_as_percentage_points(self):
        payload = {
            "include_rate_change": True,
            "metrics": [
                {
                    "name": "任务量",
                    "current_value": 10,
                    "previous_value": 9,
                    "success_rate": 99.9,
                    "previous_success_rate": 99.7,
                }
            ],
        }
        report = MODULE.generate_report(payload, args())
        self.assertIn("成功率：99.9%（+0.2 个百分点）", report)


if __name__ == "__main__":
    unittest.main()
