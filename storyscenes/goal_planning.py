"""Bounded author-side goal decomposition over the existing capability executor.

Methods are authored action/subgoal recipes, not alternative finished stories.
Only successful physical execution enters the returned trace. Search failures
are diagnostics and must not be narrated as a character's attempted actions.
"""
from dataclasses import dataclass

from .capabilities.core import CapabilityError, Query, State, execute, matches


@dataclass(frozen=True, kw_only=True)
class Act:
    id: str


@dataclass(frozen=True, kw_only=True)
class Need:
    id: str


@dataclass(frozen=True, kw_only=True)
class Method:
    id: str
    steps: tuple[Act | Need, ...]


@dataclass(frozen=True, kw_only=True)
class Goal:
    id: str
    carrier: str
    queries: tuple[Query, ...]
    methods: tuple[Method, ...]


@dataclass(frozen=True, kw_only=True)
class Episode:
    goal: str
    method: str
    event_ids: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class Plan:
    state: State
    episodes: tuple[Episode, ...]
    attempted_actions: int
    rejected_actions: int


def plan(registry, spec, goals, agenda, *, max_actions=1000):
    """Find the first executable decomposition satisfying every root goal.

Method order is an explicit author preference, not a score-based story filter.
An achieved root is checked again at the end: later work may undo it. The
bound counts every attempted action, including successful speculative branches.
No claim of impossibility is made when that bound is exhausted.
"""
    if type(max_actions) is not int or max_actions < 1:
        raise CapabilityError("A positive action-search bound is required")
    goals = tuple(goals)
    agenda = tuple(agenda)
    by_goal = {g.id: g for g in goals}
    actions = {a.id: a for a in spec.actions}
    state = registry.initial(spec)
    if len(goals) > 64 or sum(len(g.methods) for g in goals) > 256:
        raise CapabilityError("Goal decomposition definition budget exceeded")
    if len(by_goal) != len(goals) or not agenda or len(set(agenda)) != len(agenda):
        raise CapabilityError("Goals and root agenda need unique identities")
    if set(agenda) - set(by_goal):
        raise CapabilityError("Unknown root goal")
    for goal in goals:
        if not goal.id or state.get("entities", goal.carrier) is None or not goal.queries:
            raise CapabilityError("Goals need a physical carrier and explicit state predicates")
        if len({m.id for m in goal.methods}) != len(goal.methods):
            raise CapabilityError("Methods within a goal need unique identities")
        for query in goal.queries:
            registry.validate_query(query)
        for method in goal.methods:
            if not method.id or not method.steps:
                raise CapabilityError("Methods need an identity and nonempty steps")
            if len(method.steps) > 200:
                raise CapabilityError("Method step budget exceeded")
            for step in method.steps:
                if isinstance(step, Act) and step.id in actions:
                    continue
                if isinstance(step, Need) and step.id in by_goal:
                    continue
                raise CapabilityError("Unknown method step")
    attempts = rejected = 0

    def satisfied(s, goal):
        return all(matches(s, q) for q in goal.queries)

    def sequence(s, steps, episodes, active, depth=0):
        nonlocal attempts, rejected
        if depth > 256:
            raise CapabilityError("Goal decomposition depth budget exhausted")
        if not steps:
            yield s, episodes
            return
        step, *rest = steps
        if isinstance(step, Act):
            if attempts >= max_actions:
                raise CapabilityError("Goal decomposition action budget exhausted")
            attempts += 1
            after = execute(registry, spec, s, actions[step.id])
            if after is None:
                rejected += 1
                return
            yield from sequence(after, rest, episodes, active, depth + 1)
            return
        goal = by_goal[step.id]
        if satisfied(s, goal):
            yield from sequence(s, rest, episodes, active, depth + 1)
            return
        # Cyclic decomposition is not an enacted action. A later sibling can
        # seek this goal again after another method has changed the world.
        if goal.id in active:
            return
        for method in goal.methods:
            for after, nested in sequence(s, method.steps, episodes, active + (goal.id,), depth + 1):
                if not satisfied(after, goal):
                    continue
                episode = Episode(goal=goal.id, method=method.id,
                                  event_ids=tuple(e.id for e in after.events[len(s.events):]))
                yield from sequence(after, rest, nested + (episode,), active, depth + 1)

    for result, episodes in sequence(state, tuple(Need(id=g) for g in agenda), (), ()):
        if all(satisfied(result, by_goal[g]) for g in agenda):
            return Plan(state=result, episodes=episodes, attempted_actions=attempts, rejected_actions=rejected)
    raise CapabilityError("No plan in the authored method space")
