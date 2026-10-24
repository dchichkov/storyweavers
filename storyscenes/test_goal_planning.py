from dataclasses import replace
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.core import Action, CapabilityError, Entity, Query, WorldSpec, replay
from storyscenes.capabilities.physical import Container, Parent
from storyscenes.goal_planning import Act, Goal, Method, Need, plan


class GoalPlanningTests(unittest.TestCase):
    def fixture(self):
        spec = WorldSpec(title="Two loads", records=dict(
            entities=(Entity(id="a", name="Ada", kind="actor", capacity=2),
                      Entity(id="room", name="Room", kind="place"),
                      Entity(id="box", name="Box", kind="container", mass=1),
                      Entity(id="weight", name="Weight", kind="object", mass=2)),
            containers=(Container(id="box"),),
            parents=(Parent(id="a", parent="room"), Parent(id="box", parent="room"), Parent(id="weight", parent="box"))),
            actions=(Action(id="take_box", operation="pickup", actor="a", args=dict(object="box", source="room")),
                     Action(id="take_weight", operation="pickup", actor="a", args=dict(object="weight", source="box")),
                     Action(id="put_weight", operation="put", actor="a", args=dict(object="weight", destination="room")),
                     Action(id="put_box", operation="put", actor="a", args=dict(object="box", destination="room"))),
            goal=(Query(table="parents", key="box", field="parent", value="a"),))
        empty = Goal(id="empty", carrier="box", queries=(Query(table="parents", key="weight", field="parent", value="room"),),
            methods=(Method(id="unload", steps=(Act(id="take_weight"), Act(id="put_weight"))),))
        carry = Goal(id="carry", carrier="a", queries=spec.goal, methods=(
            Method(id="whole", steps=(Act(id="take_box"),)),
            Method(id="split", steps=(Need(id="empty"), Act(id="take_box")))))
        return spec, (empty, carry)

    def test_failed_candidate_does_not_leak_into_world_or_episodes(self):
        spec, goals = self.fixture()
        result = plan(registry(), spec, goals, ("carry",))
        self.assertEqual(result.rejected_actions, 1)
        self.assertEqual([e.action.id for e in result.state.events], ["take_weight", "put_weight", "take_box"])
        self.assertEqual([e.method for e in result.episodes], ["unload", "split"])
        self.assertEqual(replay(registry(), spec, [e.action.id for e in result.state.events]), result.state)

    def test_rechecks_earlier_goals_after_later_actions(self):
        spec, goals = self.fixture()
        undo = Goal(id="undo", carrier="box", queries=(Query(table="parents", key="box", field="parent", value="room"),),
            methods=(Method(id="put_down", steps=(Act(id="put_box"),)),))
        with self.assertRaisesRegex(CapabilityError, "No plan"):
            plan(registry(), spec, (*goals, undo), ("carry", "undo"))

    def test_backtracks_across_root_goals_not_only_local_failure(self):
        spec, goals = self.fixture()
        # A locally completed emptying method can leave the weight in Ada's
        # hand, preventing the next carrying goal. The planner must reconsider.
        empty = replace(goals[0], queries=(Query(table="parents", key="weight", field="parent", op="ne", value="box"),),
            methods=(Method(id="hold", steps=(Act(id="take_weight"),)), *goals[0].methods))
        result = plan(registry(), spec, (empty, goals[1]), ("empty", "carry"))
        self.assertEqual(result.state.get("parents", "weight").parent, "room")
        self.assertNotIn("hold", [e.method for e in result.episodes])

    def test_cycle_fails_closed(self):
        spec, goals = self.fixture()
        cyclic = replace(goals[1], methods=(Method(id="cycle", steps=(Need(id="carry"),)),))
        with self.assertRaisesRegex(CapabilityError, "No plan"):
            plan(registry(), spec, (cyclic,), ("carry",))

    def test_action_bound_is_not_reported_as_impossibility(self):
        spec, goals = self.fixture()
        with self.assertRaisesRegex(CapabilityError, "budget exhausted"):
            plan(registry(), spec, goals, ("carry",), max_actions=1)

    def test_unknown_carrier_and_unknown_action_are_rejected(self):
        spec, goals = self.fixture()
        with self.assertRaisesRegex(CapabilityError, "physical carrier"):
            plan(registry(), spec, (goals[0], replace(goals[1], carrier="idea")), ("carry",))
        with self.assertRaisesRegex(CapabilityError, "Unknown method step"):
            plan(registry(), spec, (replace(goals[1], methods=(Method(id="x", steps=(Act(id="invented"),)),)),), ("carry",))

    def test_already_satisfied_goals_add_no_action_or_episode(self):
        spec, _ = self.fixture()
        goal = Goal(id="here", carrier="box", queries=(Query(table="parents", key="box", field="parent", value="room"),), methods=())
        result = plan(registry(), spec, (goal,), ("here",))
        self.assertEqual(result.attempted_actions, 0)
        self.assertEqual(result.episodes, ())

    def test_satisfied_subgoals_cannot_bypass_the_recursion_bound(self):
        spec, goals = self.fixture()
        here = Goal(id="here", carrier="box", queries=(Query(table="parents", key="box", field="parent", value="room"),), methods=())
        # A deep chain of already-satisfied steps performs no actions, so an
        # action counter alone would not bound the Python call stack.
        chain = []
        for i in range(4):
            steps = (Need(id="here"),) * 150 + ((Need(id=f"g{i+1}"),) if i < 3 else (Act(id="take_box"),))
            chain.append(Goal(id=f"g{i}", carrier="box", queries=spec.goal,
                              methods=(Method(id="nested", steps=steps),)))
        with self.assertRaisesRegex(CapabilityError, "depth budget"):
            plan(registry(), spec, (here, *chain), ("g0",))


if __name__ == "__main__":
    unittest.main()
