"""Geometry, independent error metrics, and conservative chassis envelope."""
import json
import math
from pathlib import Path
import sys
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/odin_racer/racer_description'))
sys.path.insert(0,str(ROOT/'tools'))
from racer_description.course_world import LINE_SCENES,line_fixture
from isolated_line_metrics import Evaluator,footprint,error_stats,summarize

class IsolatedLineTests(unittest.TestCase):
    def test_mirrored_fixtures_and_sharp_corner(self):
        for a,b in [('line_left','line_right'),('line_corner_left','line_corner_right')]:
            left,right=[line_fixture(k) for k in (a,b)]
            np.testing.assert_allclose(np.array(left['reference'])*[1,-1],right['reference'])
            self.assertEqual(left['parameters'],right['parameters'])
        corner=np.array(line_fixture('line_corner_left')['reference'])
        self.assertTrue(np.all((abs(corner[:,0]-.8)<1e-10)|(abs(corner[:,1])<1e-10)))
    def test_parameters_are_validated_and_spawn_is_explicit(self):
        for args in ({'radius':0},{'line_width':.1},{'spawn_y':float('nan')},{'unknown':1}):
            with self.assertRaises(ValueError):line_fixture('line_left',args)
        f=line_fixture('line_s',dict(spawn_x=.2,spawn_y=.01,spawn_yaw=.08))
        self.assertEqual(f['spawn'],[.2,.01,.08])
        self.assertIn('not_official',f['conditions'])
    def test_reference_projection_and_endpoint_are_independent(self):
        e=Evaluator(line_fixture('line_corner_left'),np.array([[0.,0.]]))
        self.assertAlmostEqual(e.project([.4,.02])[0],.02)
        self.assertAlmostEqual(e.project([.82,.4])[0],-.02)
        self.assertFalse(e.sample(.8,.7,0)['at_end'])
        self.assertTrue(e.sample(.8,.7,math.pi/2)['at_end'])
    def test_physical_envelope_includes_wheels_and_front_plate(self):
        points,envelope=footprint(ROOT/'src/odin_racer/racer_description')
        self.assertGreaterEqual(envelope['max'][0],.227)
        self.assertGreaterEqual(envelope['max'][1],.141)
        self.assertLessEqual(envelope['min'][1],-.141)
        self.assertGreater(len(points),500)
    def test_full_error_cannot_be_hidden_by_good_tail(self):
        criteria=json.loads((ROOT/'experiments/isolated_line/acceptance.json').read_text())
        samples=[dict(time=i*.05,error=.2 if i<10 else 0,progress=i*.002,state='RUNNING',
                      swept_distance=.15,at_end=i==29,cmd_v=.04,cmd_w=0) for i in range(30)]
        metrics,checks=summarize(samples,criteria,'line_straight')
        self.assertTrue(checks['regression_tail']);self.assertFalse(checks['full_max']);self.assertFalse(checks['full_rms'])
        samples[15]['progress']=1.
        self.assertFalse(summarize(samples,criteria,'line_s')[1]['ordered_progress'])
    def test_right_angle_projection_switch_is_not_physical_jump(self):
        criteria=json.loads((ROOT/'experiments/isolated_line/acceptance.json').read_text())
        fixture=line_fixture('line_corner_right')
        evaluator=Evaluator(fixture,np.array([[0.,0.]]))
        positions=[(i*.005,0.) for i in range(145)]
        positions += [(.72,-i*.005) for i in range(1,20)]
        positions += [(.72+.08*i/100,-.095-.605*i/100) for i in range(101)]
        samples=[]
        for i,(x,y) in enumerate(positions):
            sample=dict(time=i*.05,x=x,y=y,state='RUNNING',cmd_v=.05,cmd_w=0)
            sample.update(evaluator.sample(x,y,-math.pi/2));samples.append(sample)
        metrics,checks=summarize(samples,criteria,'line_corner_right',fixture)
        self.assertGreater(metrics['max_nearest_projection_jump_m'],.1)
        self.assertTrue(checks['ordered_progress'])
        # A physical shortcut skipping the incoming gate sequence must still fail.
        self.assertFalse(summarize(samples[:10]+samples[-10:],criteria,'line_corner_right',fixture)[1]['ordered_progress'])

    def test_single_sample_has_no_fabricated_rms(self):
        self.assertIsNone(error_stats([dict(time=0,error=.01)]))

if __name__=='__main__':unittest.main()
