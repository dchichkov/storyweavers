"""Independent checks of the authoring adapter against the original sampler."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

from . import engine, world
from .grammar import Grammar, tokenize
from .pack_runtime import build_forest, check_guard_interventions


class PackRuntimeTests(unittest.TestCase):
    def original_pack(self):
        return SimpleNamespace(candidates=world.frames,
                               realize=lambda w, f, tense: Grammar(w, tense).for_frame(f))

    def test_adapter_preserves_original_event_and_word_distributions(self):
        for scenario in world.SCENARIOS:
            state = engine.advance(scenario, 7, 1)
            before = deepcopy(state.to_dict())
            existing = engine.build_forest(state)
            adapted = build_forest(self.original_pack(), state)
            for prefix in ((), tokenize('she'), tokenize('he'), tokenize('Nora'), tokenize('Sam')):
                self.assertEqual(existing.predict(prefix), adapted.predict(prefix))
            self.assertEqual(state.to_dict(), before)

    def test_prediction_state_mutation_is_detected(self):
        def impure(state):
            result = world.frames(state)
            state.flags.add('illegal_prediction_effect')
            return result
        pack = self.original_pack()
        pack.candidates = impure
        with self.assertRaisesRegex(AssertionError, 'candidates mutated'):
            build_forest(pack, world.make_world())

    def test_join_intervention_catches_flag_only_consent(self):
        state = world.make_world()
        state.entities['partner'] = world.Entity('partner', 'Mateo', 'person', state.setting,
                                                state={'consented'})
        state.entities['spare'] = world.Entity('spare', 'drum', 'instrument', 'partner')
        frame = world.Frame('join', 'partner')
        broken = SimpleNamespace(candidates=lambda w: [(world.kernel('join'), frame)])
        with self.assertRaisesRegex(AssertionError, 'survives broken'):
            check_guard_interventions(broken, state, frame)


if __name__ == '__main__':
    unittest.main()
