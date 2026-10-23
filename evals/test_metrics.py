"""Deterministic validation tests, never empirical model-evaluation data."""

import json
import copy
import random
import unittest
from pathlib import Path

from metrics import (BLIND_LEGEND, assess_evidence, automatic_metrics, blind_text, judge_agreement,
                     paired_summary, parse_ratings, parse_zone, resolve_team_ratings, restore_text)


ROOT = Path(__file__).resolve().parent


class MetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keys = json.loads((ROOT / "fixtures" / "key.json").read_text())["fixtures"]

    def test_parse_table_and_missing_grade(self):
        text = "| Job | Solid | Seen | O01 |\n**First value**: Missing, Seen (O02).\nReturn: Partial."
        rows = parse_ratings(text)
        self.assertEqual([r["criterion"] for r in rows], ["Job", "First value", "Return"])
        self.assertIsNone(rows[-1]["evidence"])
        self.assertEqual(rows[0]["observation_ids"], ["O01"])

    def test_no_rating_does_not_become_perfect(self):
        result = automatic_metrics({"messages": [{"role": "assistant", "content": "Looks nice."}]}, self.keys["f06"])
        self.assertEqual(result["evidence_upgrades_raw"], 0)
        self.assertEqual(result["rating_coverage"], 0)
        self.assertIsNone(result["evidence_upgrades_per_10_rated"])
        self.assertIsNone(result["all_rated_assertions_supported"])
        self.assertIsNone(result["zone_correct"])

    def test_evidence_grade_inflation(self):
        event = parse_ratings("Job: Solid, Repeated (O01).")[0]
        self.assertTrue(assess_evidence(event, self.keys["f06"])["definite_upgrade"])

    def test_reference_grade_is_not_support_ceiling(self):
        key = copy.deepcopy(self.keys["f06"])
        key["observations"]["O01"]["evidence_ceiling"] = "Repeated"
        self.assertEqual(key["criteria"]["Job"]["evidence"], "Seen")
        event = parse_ratings("Job: Solid, Repeated (O01).")[0]
        result = assess_evidence(event, key)
        self.assertFalse(result["definite_upgrade"])
        self.assertFalse(result["needs_judge"])

    def test_no_id_required_when_observation_exists(self):
        event = parse_ratings("Job: Solid, Seen. Nina has a weekly task.")[0]
        result = assess_evidence(event, self.keys["f06"])
        self.assertFalse(result["definite_upgrade"])
        self.assertFalse(result["needs_judge"])

    def test_grade_on_wrong_success_goes_to_judge(self):
        event = parse_ratings("First value: Solid, Seen (O02).")[0]
        result = assess_evidence(event, self.keys["f01"])
        self.assertTrue(result["needs_judge"])
        self.assertFalse(result["definite_upgrade"])

    def test_wrong_citation_goes_to_judge(self):
        event = parse_ratings("Trust: Solid, Seen (O99).")[0]
        self.assertTrue(assess_evidence(event, self.keys["f06"])["needs_judge"])

    def test_team_quoted_rows_not_endorsements(self):
        rows = parse_ratings("Job | Ana: Solid, Claimed | Ben: Missing, Seen | Cy: Partial, Seen")
        self.assertTrue(rows[0]["ambiguous"])
        result = automatic_metrics({"task": "team", "messages": [{"role": "assistant", "content": rows[0]["raw"]}]}, self.keys["f06"])
        self.assertEqual(result["rated_assertions"], 0)

    def test_no_averaging_instruction_is_not_arithmetic(self):
        transcript = {"task": "team", "messages": [{"role": "assistant", "content": "Do not average the three ratings. Report their spread."}]}
        self.assertEqual(automatic_metrics(transcript, self.keys["f06"])["team_averaging_candidate"], 0)
        transcript["messages"][0]["content"] = "The team average is 1.5."
        self.assertEqual(automatic_metrics(transcript, self.keys["f06"])["team_averaging_candidate"], 1)

    def test_blinding_exactly_reversible_with_preexisting_tokens(self):
        original = "Z1 E1 C1 CONDITION: Worth Using skill.\nStranger-ready: Solid / Seen. Claimed, Repeated; job."
        blinded = blind_text(original)
        self.assertEqual(restore_text(blinded), original)
        for phrase in ["Worth Using", "skill", "Stranger-ready", "Solid", "Seen", "Claimed", "Repeated"]:
            self.assertNotIn(phrase, blinded["text"])

    def test_blinding_detects_bad_map(self):
        blinded = blind_text("Solid")
        blinded["text"] = "bad"
        with self.assertRaises(ValueError):
            restore_text(blinded)

    def test_dimension_mask_preserves_generic_evidence(self):
        original = "Evidence: Strong. The evidence supports this result. Perspective, Specificity, Evidence, Calibration, Subtraction."
        blinded = blind_text(original)
        self.assertIn("B3: L2", blinded["text"])
        self.assertIn("The evidence supports", blinded["text"])
        self.assertIn("B1, B2, B3, B4, B5", blinded["text"])
        self.assertEqual(restore_text(blinded), original)
        self.assertEqual(blinded["map_version"], 2)
        self.assertIn("B3", BLIND_LEGEND)

    def test_teaching_and_card_phrases_masked(self):
        original = "Growth card. Grade the evidence. Predict, then watch. Name the dip. Round budget."
        blinded = blind_text(original)
        self.assertEqual(blinded["text"], "CARD_B. T6. T2. T7. H08.")
        self.assertEqual(restore_text(blinded), original)

    def test_zone_negation(self):
        cases = {
            "Stranger-ready: not met. Worth using: not met.": "not_ready",
            "Stranger-ready: met. Worth using: not yet shown.": "stranger_ready",
            "It is worth using.": "worth_using",
            "It is not stranger-ready or worth using.": "not_ready",
            "Not ready to ship.": "not_ready",
            "When it is stranger-ready, we can review again.": None,
            "This may be worth using next year.": None,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse_zone(text)["claimed_zone"], expected)

    def test_cap_not_successful_stop(self):
        transcript = {"task": "coach", "completed": True, "censored": True,
                      "messages": [{"role": "assistant", "content": "Round 3 still needs work."}]}
        result = automatic_metrics(transcript, self.keys["f01"])
        self.assertEqual(result["coach_completed"], 0)
        self.assertIsNone(result["stopped_within_three_rounds"])

    def test_simulator_not_scored(self):
        transcript = {"messages": [
            {"role": "assistant", "source": "simulator", "content": "Job: Solid, Repeated"},
            {"role": "assistant", "source": "evaluated_agent", "content": "One question?"}]}
        result = automatic_metrics(transcript, self.keys["f06"])
        self.assertEqual(result["rated_assertions"], 0)
        self.assertEqual(result["assistant_turns"], 1)

    def test_team_strongest_then_lower(self):
        raters = [
            {"name": "A", "criteria": {"Job": {"rating": "Solid", "evidence": "Repeated", "observation_ids": []}}},
            {"name": "B", "criteria": {"Job": {"rating": "Partial", "evidence": "Seen", "observation_ids": ["O01"]}}},
            {"name": "C", "criteria": {"Job": {"rating": "Solid", "evidence": "Seen", "observation_ids": ["O01"]}}},
        ]
        key = copy.deepcopy(self.keys["f06"])
        key["observations"]["O01"]["rating_support"]["Job"] = ["Partial", "Solid"]
        resolved = resolve_team_ratings(raters, key)["Job"]
        self.assertEqual(resolved["rating"], "Partial")
        self.assertEqual(resolved["evidence"], "Seen")
        self.assertEqual(resolved["spread_levels"], 1)
        self.assertEqual(resolved["raters"][0]["effective_evidence"], "Claimed")

    def test_team_citation_must_support_rating(self):
        raters = [
            {"name": "A", "ratings": {"First value": {"rating": "Solid", "evidence": "Seen", "observation_ids": ["O02"]}}},
            {"name": "B", "ratings": {"First value": {"rating": "Missing", "evidence": "Seen", "observation_ids": ["O02"]}}},
        ]
        resolved = resolve_team_ratings(raters, self.keys["f01"])["First value"]
        self.assertEqual(resolved["rating"], "Missing")
        self.assertEqual(resolved["raters"][0]["effective_evidence"], "Claimed")

    def test_empty_stats_are_missing_not_zero(self):
        result = paired_summary([], "metric", "baseline")
        self.assertIsNone(result["difference"])
        self.assertIsNone(result["reference_mean"])
        self.assertEqual(result["conclusion"], "not estimable")

    def test_bootstrap_pairing_and_reproducibility(self):
        rows = []
        for f in range(4):
            for s in range(3):
                for condition, value in [("skill", f + s), ("baseline", f + s + 2)]:
                    rows.append({"fixture_id": f, "seed": s, "task": "score", "condition": condition, "metric": value})
        result = paired_summary(rows, "metric", "baseline", bootstrap=200, seed=19)
        self.assertEqual(result, paired_summary(rows, "metric", "baseline", bootstrap=200, seed=19))
        self.assertEqual(result["paired_units"], 12)
        self.assertEqual(result["fixture_clusters"], 4)
        self.assertAlmostEqual(result["difference"], -2)
        self.assertAlmostEqual(result["difference_ci_low"], -2)
        self.assertAlmostEqual(result["difference_ci_high"], -2)
        self.assertIsNone(result["standardized_paired_fixture_dz"])

    def test_duplicate_judge_repeats_rejected(self):
        row = {"fixture_id": 1, "seed": 0, "task": "score", "condition": "skill", "metric": 2}
        with self.assertRaises(ValueError):
            paired_summary([row, row], "metric", "baseline")

    def test_missing_pairs_excluded_and_reported(self):
        rows = [
            {"fixture_id": "a", "seed": 0, "task": "score", "condition": "skill", "metric": 2},
            {"fixture_id": "a", "seed": 0, "task": "score", "condition": "baseline", "metric": None},
        ]
        result = paired_summary(rows, "metric", "baseline")
        self.assertEqual(result["unpaired_or_missing_units"], 1)
        self.assertIsNone(result["difference"])

    def test_stratified_bootstrap_preserves_category_weights(self):
        rows = []
        for category, shift in [("a", 0), ("b", 10)]:
            for fixture in range(2):
                for trial_seed in range(3):
                    for condition, value in [("skill", shift), ("baseline", 0)]:
                        rows.append({"fixture_id": category + str(fixture), "main_trap": category,
                                     "seed": trial_seed, "task": "score", "condition": condition, "metric": value})
        summary = paired_summary(rows, "metric", "baseline", bootstrap=200)
        self.assertEqual(summary["difference"], 5)
        self.assertEqual(summary["difference_ci_low"], 5)
        self.assertEqual(summary["difference_ci_high"], 5)
        self.assertEqual(summary["strata"]["a"]["weight"], .5)
        shuffled = rows[:]
        random.Random(908).shuffle(shuffled)
        self.assertEqual(summary, paired_summary(shuffled, "metric", "baseline", bootstrap=200))

    def test_missing_category_blocks_pooled_inference(self):
        rows = []
        for category in ["a", "b"]:
            for condition in ["skill", "baseline"]:
                rows.append({"fixture_id": category, "main_trap": category, "seed": 1, "task": "score",
                             "condition": condition, "metric": None if category == "b" else 2})
        summary = paired_summary(rows, "metric", "baseline", bootstrap=200)
        self.assertIsNone(summary["difference"])
        self.assertIsNone(summary["reference_mean"])
        self.assertIn("no complete pairs", summary["conclusion"])
        self.assertEqual(summary["strata"]["b"]["weight"], .5)

    def test_incomplete_fixture_does_not_change_category_weight(self):
        rows = []
        for category, shift in [("a", 0), ("b", 10)]:
            for fixture in range(2):
                for condition in ["skill", "baseline"]:
                    missing = category == "b" and fixture == 1 and condition == "baseline"
                    value = (shift if condition == "skill" else 0) if not missing else None
                    rows.append({"fixture_id": category + str(fixture), "main_trap": category,
                                 "seed": 1, "task": "score", "condition": condition, "metric": value})
        summary = paired_summary(rows, "metric", "baseline", bootstrap=200)
        self.assertEqual(summary["difference"], 5)
        self.assertEqual(summary["strata"]["b"]["weight"], .5)
        self.assertEqual(summary["strata"]["b"]["paired_fixture_clusters"], 1)

    def test_strata_consistency_validation(self):
        rows = [
            {"fixture_id": "a", "main_trap": "clean", "seed": 1, "task": "score", "condition": "skill", "metric": 1},
            {"fixture_id": "a", "main_trap": "setup_wall", "seed": 1, "task": "score", "condition": "baseline", "metric": 1},
        ]
        with self.assertRaises(ValueError):
            paired_summary(rows, "metric", "baseline", bootstrap=200)

    def test_judge_repeat_agreement(self):
        rows = [
            {"transcript_id": "a", "repeat": 1, "usefulness": 4},
            {"transcript_id": "a", "repeat": 2, "usefulness": 3},
            {"transcript_id": "b", "repeat": 1, "usefulness": 2},
            {"transcript_id": "b", "repeat": 2, "usefulness": 2},
        ]
        result = judge_agreement(rows)["usefulness"]
        self.assertEqual(result["exact_agreement"], .5)
        self.assertEqual(result["within_one"], 1)
        self.assertEqual(result["mean_absolute_difference"], .5)


if __name__ == "__main__":
    unittest.main()
