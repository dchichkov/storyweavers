from copy import deepcopy
import unittest
from branch_prompts import branch_prompt


class BranchPromptTests(unittest.TestCase):
    def source(self):
        initial = {'meadow.wind': 'breezy', 'moss.capacity': 1}
        return dict(story='SECRET PROSE', trace=dict(
            entities={'meadow': dict(name='meadow', kind='place'), 'moss': dict(name='Moss', kind='donkey')},
            initial=initial, premise=deepcopy(initial), final={'secret': 'SECRET ENDING'}))

    def test_branch_changes_prompt_and_preserves_source(self):
        a = self.source(); original = deepcopy(a)
        b = deepcopy(a)
        b['trace']['initial']['moss.capacity'] = b['trace']['premise']['moss.capacity'] = 2
        pa, evidence = branch_prompt(dict(premise='Bring a picnic to a friend.'), a)
        pb, _ = branch_prompt(dict(premise='Bring a picnic to a friend.'), b)
        self.assertNotEqual(pa, pb)
        self.assertIn('only 1 item', pa)
        self.assertIn('only 2 items', pb)
        self.assertNotIn('SECRET', pa)
        self.assertEqual(a, original)
        self.assertEqual(len(evidence['facts']), 2)

    def test_final_state_and_prose_cannot_change_prompt(self):
        a = self.source(); b = deepcopy(a)
        b['trace']['final'] = {}; b['story'] = 'Different ending.'
        self.assertEqual(branch_prompt(dict(premise='A picnic.'), a), branch_prompt(dict(premise='A picnic.'), b))

    def test_distinct_pride_branches_do_not_collapse(self):
        a = self.source(); b = self.source()
        for s, value in ((a, 2), (b, 3)):
            s['trace']['premise']['moss.memes.Pride'] = value
            s['trace']['initial']['moss.memes.Pride'] = value
        self.assertNotEqual(branch_prompt(dict(premise='A picnic.'), a)[0],
                            branch_prompt(dict(premise='A picnic.'), b)[0])

    def test_unknown_and_inconsistent_conditions_fail_explicitly(self):
        a = self.source(); a['trace']['premise']['moss.capacity'] = 2
        with self.assertRaises(ValueError): branch_prompt(dict(premise='A picnic.'), a)
        a = self.source()
        a['trace']['premise']['moss.unsupported'] = a['trace']['initial']['moss.unsupported'] = 'z'
        with self.assertRaises(ValueError): branch_prompt(dict(premise='A picnic.'), a)


if __name__ == '__main__': unittest.main()
