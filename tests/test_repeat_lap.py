"""Acceptance aggregation must retain missing/failed trials and reject mixed versions."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from repeat_competition_lap import summarize


def trial(name, binary='version-a', passed=True):
    return dict(run=name, exit_code=0 if passed else 1,
                report=dict(passed=passed, binary_sha256=binary,
                            source_sha256={'controller': 'source-a'}, criteria={'error': .1},
                            events=[{'time': 0., 'state': 'RUNNING'}, {'time': 3., 'state': 'FINISHED'}],
                            commands=[{'time': 2., 'v': .05}]))


class RepeatLapTests(unittest.TestCase):
    def test_same_frozen_version_passes_only_when_all_trials_finish(self):
        reports=[trial('one'), trial('two')]
        self.assertFalse(summarize(reports, 3)['passed'])
        reports.append(trial('three'))
        self.assertTrue(summarize(reports, 3)['passed'])

    def test_missing_report_counts_as_failed_attempt(self):
        result=summarize([trial('one'), dict(run='two', exit_code=1, report=None)], 2)
        self.assertTrue(result['complete'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['passed_runs'], 1)
        self.assertEqual(result['attempted'], 2)

    def test_mixed_versions_are_not_a_repeatability_pass(self):
        result=summarize([trial('one'), trial('two', binary='version-b')], 2)
        self.assertFalse(result['identical_version_and_criteria'])
        self.assertFalse(result['passed'])

    def test_zero_command_between_pose_samples_fails_the_full_stream_audit(self):
        report=trial('one')
        report['report']['commands'].append({'time': 2.01, 'v': 0.})
        result=summarize([report], 1)
        self.assertFalse(result['passed'])
        self.assertEqual(result['runs'][0]['command_audit']['nonpositive_or_invalid'], 1)

    def test_failed_trial_cannot_be_hidden_by_other_successes(self):
        result=summarize([trial('one'), trial('two', passed=False), trial('three')], 3)
        self.assertFalse(result['passed'])
        self.assertEqual(result['passed_runs'], 2)


if __name__ == '__main__':
    unittest.main()
