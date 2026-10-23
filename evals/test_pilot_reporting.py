"""Offline pilot-report regressions; fabricated test doubles are not results."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilot_reporting as report


class PilotReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pilot-report-test-", dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.manifest = {"phase": "pilot", "status": "blocked_before_live_pilot", "date": "2026-10-23",
                         "source_commit": "synthetic_test_only", "models": {r: {"model": None, "temperature": 0.2, "max_tokens": 2400} for r in ("eval", "judge", "simulator")}}

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n")

    def populate(self):
        """Synthetic ledger exists only in an automatically removed test folder."""
        calls = []
        def call(role, run_id, condition, purpose):
            return {"is_empirical": True, "role": role, "run_id": run_id, "condition": condition, "purpose": purpose,
                    "status": "complete", "model_returned": "SYNTHETIC_TEST_" + role,
                    "temperature": 0.2, "max_tokens": 2400, "seed": 41, "seed_requested": 41,
                    "seed_sent": 41 if role == "judge" else None,
                    "usage": {"input_tokens": 100, "output_tokens": 10}, "latency_seconds": 1,
                    "estimated_uncached_cost_usd": .01}
        for fixture in ("f01", "f06"):
            for condition in report.CONDITIONS:
                for task in report.TASKS:
                    run_id = f"{fixture}_41001_{task}_{condition}"
                    self.write_json(self.output / "pilot/live/transcripts" / (run_id + ".jsonl"),
                                    {"kind": "trial", "is_empirical": True, "run_id": run_id, "fixture_id": fixture,
                                     "seed": 41001, "condition": condition, "task": task, "status": "complete", "messages": [{"role": "assistant"}]})
                    calls.append(call("eval", run_id, condition, "evaluated_agent"))
                    calls.extend(call("judge", run_id, condition, "blind_judgment") for _ in range(2))
            calls.append(call("simulator", None, "shared", "paired_builder_script"))
            calls.append(call("judge", None, "shared", "script_validation"))
        path = self.output / "pilot/live/calls.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(c) + "\n" for c in calls))
        self.write_json(self.output / "pilot/live/result.json", {"status": "passed"})
        return calls

    def test_missing_ledger_is_unmeasured_not_zero(self):
        data = report.pilot_data(self.output, self.manifest)
        self.assertEqual(data["totals"]["attempted_calls"], 0)
        self.assertIsNone(data["totals"]["input_tokens"])
        self.assertIsNone(data["totals"]["cost_usd"])
        self.assertEqual(report.projection(data)["status"], "unavailable_until_complete_pilot")

    def test_nested_pilot_ledger_and_returned_ids_are_used(self):
        self.populate()
        data = report.pilot_data(self.output, self.manifest)
        self.assertEqual(len(data["conversations"]), 18)
        self.assertEqual(data["totals"]["attempted_calls"], 58)
        self.assertEqual(data["totals"]["input_tokens"], 5800)
        self.assertEqual(data["conversations"][0]["eval_input_tokens"], 100)
        self.assertEqual(data["conversations"][0]["judge_input_tokens"], 200)
        self.assertEqual(data["accepted_settings"][0]["returned_models"], ["SYNTHETIC_TEST_eval"])
        self.assertEqual(data["accepted_settings"][0]["effective_setting_echo"], "not returned by these provider responses")

    def test_main_projection_includes_simulator_and_script_audits(self):
        self.populate()
        budget = report.projection(report.pilot_data(self.output, self.manifest))
        self.assertEqual(budget["total_main_conversations"], 432)
        self.assertEqual(budget["main_script_audits"], 48)
        self.assertEqual(budget["estimates"]["combined_main"]["input_tokens"], 5800 * 24)
        self.assertAlmostEqual(budget["estimates"]["combined_main"]["cost_usd"], .58 * 24)
        self.assertAlmostEqual(budget["estimates"]["combined_main_plus_one_additional_pilot"]["cost_usd"], .58 * 25)

    def test_partial_pilot_does_not_project(self):
        self.populate()
        self.write_json(self.output / "pilot/live/result.json", {"status": "failed"})
        budget = report.projection(report.pilot_data(self.output, self.manifest))
        self.assertNotIn("estimates", budget)

    def test_unknown_error_usage_is_not_zero_filled(self):
        calls = [{"status": "complete", "usage": {"input_tokens": 100, "output_tokens": 10}, "latency_seconds": 1, "cost_usd": .01},
                 {"status": "error", "latency_seconds": 2}]
        data = report.aggregate(calls)
        self.assertIsNone(data["input_tokens"])
        self.assertIsNone(data["cost_usd"])
        self.assertEqual(data["latency_seconds"], 3)

    def test_sourced_price_matches_exact_returned_model(self):
        call = {"model_returned": "SYNTHETIC_TEST_eval", "usage": {"input_tokens": 100, "output_tokens": 10}}
        wrong = {"models": {"another-model": {"input_usd_per_million": 1, "output_usd_per_million": 2, "source_url": "https://example.invalid/test"}}}
        self.assertIsNone(report.priced_call(call, self.manifest, wrong)["cost_usd"])
        right = {"models": {"SYNTHETIC_TEST_eval": {"input_usd_per_million": 1, "output_usd_per_million": 2, "source_url": "https://example.invalid/test"}}}
        self.assertAlmostEqual(report.priced_call(call, self.manifest, right)["cost_usd"], .00012)

    def test_pilot_dispatch_does_not_read_main_key_or_compute_effects(self):
        import reporting
        result = reporting.write_reports(self.output, self.output, self.manifest)
        self.assertEqual(result["status"], "not_measured")
        self.assertTrue((self.output / "Worth_Using_Evaluation.pdf").read_bytes().startswith(b"%PDF-"))
        text = (self.output / "REPORT.md").read_text()
        self.assertIn("pilot is blocked before any live call", text)
        self.assertIn("not a null result", text)
        self.assertNotIn("No live API call ledger entries are present", text)


if __name__ == "__main__":
    unittest.main()
