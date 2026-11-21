"""The short-story budget must not turn every detail into another reminder."""
from collections import Counter
from copy import deepcopy
import unittest

from .beat_generation import _echo_used
from .storytelling.runtime import generate,replay


class BeatPacingTests(unittest.TestCase):
    def test_one_reminder_per_origin_arc_across_several_available_details(self):
        echoes=0
        for source in ('repair','museum','pottery'):
            for seed in (7,19,41,103,211,307):
                row=generate(source,seed,beat_budget=6,continuations='expanded')
                replay(row)
                history=row['final_world']['narrative']['beats']['history']
                count=Counter((b['source_scenario'],b['prefix']) for b in history if b['detail'])
                self.assertTrue(all(v<=1 for v in count.values()))
                echoes+=sum(count.values())
        self.assertGreater(echoes,3)

    def test_reminder_scope_is_bound_to_source_and_import_prefix(self):
        memory={'history':[{'detail':'a:repair:rattle','source_scenario':'repair','prefix':'a:'}]}
        before=deepcopy(memory)
        self.assertTrue(_echo_used(memory,{'source_scenario':'repair','prefix':'a:'}))
        self.assertFalse(_echo_used(memory,{'source_scenario':'repair','prefix':'b:'}))
        self.assertFalse(_echo_used(memory,{'source_scenario':'museum','prefix':'a:'}))
        self.assertEqual(memory,before)


if __name__=='__main__':unittest.main()
