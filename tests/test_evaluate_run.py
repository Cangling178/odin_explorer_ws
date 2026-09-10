import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("evaluate_run", Path(__file__).resolve().parents[1] / "tools/evaluate_run.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
evaluate = MODULE.evaluate


class EvaluationTests(unittest.TestCase):
    def metadata(self, **changes):
        result = dict(run_id="test", data_kind="synthetic", measurement_source="fixture",
                      start_time_s=0, end_time_s=4, completed=True,
                      wrong_branch_events=0, tolerance_m=1, max_sample_hold_s=4)
        result.update(changes)
        return result

    def test_weights_irregular_samples_by_time(self):
        rows = [dict(time_s="0", error_m="1", valid="1"),
                dict(time_s="1", error_m="-3", valid="1")]
        result = evaluate(rows, self.metadata())
        self.assertAlmostEqual(result["rms_error_m"], 7 ** 0.5)
        self.assertEqual(result["mean_abs_error_m"], 2.5)
        self.assertEqual(result["p95_abs_error_m"], 3)
        self.assertEqual(result["time_above_tolerance_s"], 3)

    def test_invalid_intervals_are_not_zero_error(self):
        rows = [dict(time_s="0", error_m="2", valid="1"),
                dict(time_s="1", error_m="", valid="0")]
        result = evaluate(rows, self.metadata())
        self.assertEqual(result["valid_time_coverage"], 0.25)
        self.assertEqual(result["rms_error_m"], 2)

    def test_hold_limit_reveals_gaps(self):
        result = evaluate([dict(time_s="1", error_m="0", valid="1")], self.metadata(max_sample_hold_s=0.5))
        self.assertEqual(result["valid_duration_s"], 0.5)
        self.assertEqual(result["invalid_or_uncovered_duration_s"], 3.5)

    def test_no_valid_duration_reports_null(self):
        for rows in ([], [dict(time_s="0", error_m="", valid="0")],
                     [dict(time_s="4", error_m="0", valid="1")]):
            with self.subTest(rows=rows):
                result = evaluate(rows, self.metadata())
                self.assertIsNone(result["rms_error_m"])
                self.assertEqual(result["valid_time_coverage"], 0)

    def test_wrong_branch_or_incomplete_cannot_claim_completion_time(self):
        for changes in (dict(completed=False), dict(wrong_branch_events=1)):
            result = evaluate([], self.metadata(**changes))
            self.assertIsNone(result["completion_time_s"])
            self.assertFalse(result["completion_claim_valid"])

    def test_bad_metadata_rejected(self):
        for changes in (dict(end_time_s=0), dict(tolerance_m=-1),
                        dict(max_sample_hold_s=0), dict(completed="false"),
                        dict(wrong_branch_events=True), dict(start_time_s="nan"),
                        dict(data_kind="unknown"), dict(measurement_source="")):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                evaluate([], self.metadata(**changes))

    def test_nonfinite_or_out_of_order_data_rejected(self):
        for rows in ([dict(time_s="0", error_m="nan", valid="1")],
                     [dict(time_s="nan", error_m="0", valid="1")],
                     [dict(time_s="5", error_m="0", valid="1")],
                     [dict(time_s="0", error_m="0", valid="maybe")],
                     [dict(time_s="1", error_m="0", valid="1"), dict(time_s="1", error_m="0", valid="1")],
                     [dict(time_s="2", error_m="0", valid="1"), dict(time_s="1", error_m="0", valid="1")]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                evaluate(rows, self.metadata())


if __name__ == "__main__":
    unittest.main()
