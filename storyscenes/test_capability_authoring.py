import unittest

from capabilities.authoring import Kernel, Pattern, Role
from capabilities.core import CapabilityError, Query


class CapabilityAuthoringTests(unittest.TestCase):
    def test_same_operation_composes_in_three_settings_without_text_rewrites(self):
        take = Kernel(operation="pickup", actor=Role("person"), arguments={"object": Role("item")})
        for actor, item in (("librarian", "atlas"), ("engineer", "caliper"), ("observer", "detector")):
            pattern = take.bind("take", bindings={"person": actor, "item": item},
                requires=(Query(table="parents", key=Role("item"), field="parent", value="shelf"),))
            action = pattern.actions[0]
            self.assertEqual(action.actor, actor)
            self.assertEqual(action.args["object"], item)
            self.assertEqual(action.requires[0].key, item)
            self.assertEqual(action.requires[0].value, "shelf")

    def test_attention_and_composition_preserve_definitions(self):
        kernel = Kernel(operation="travel", actor=Role("person"), arguments={"destination": Role("place")})
        first = kernel.bind("out", bindings={"person": "ada", "place": "harbor"})
        second = kernel.bind("back", bindings={"person": "ada", "place": "library"})
        combined = first + second / 2
        self.assertEqual([a.weight for a in combined.actions], [1.0, .5])
        self.assertEqual(second.actions[0].weight, 1.0)
        with self.assertRaises(CapabilityError):
            first + first
        for bad in (0, -1, True, float("inf")):
            with self.assertRaises(CapabilityError):
                first / bad

    def test_unbound_concepts_do_not_become_actions(self):
        kernel = Kernel(operation="observe", actor=Role("observer"), arguments={})
        with self.assertRaises(CapabilityError):
            kernel.bind("abstract", bindings={})


if __name__ == "__main__":
    unittest.main()
