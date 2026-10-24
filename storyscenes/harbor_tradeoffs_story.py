"""Persistent resource conflicts over the composed harbor's reusable methods.

Initial physical laws can make desired final states mutually exclusive. Ari's
declared priorities choose a compatible goal set before execution, never by
literary scores. Deferred goals get concrete resting states, not fake success.
"""
from dataclasses import asdict, dataclass, replace
from itertools import combinations
import argparse
import json
import random

from . import harbor_composition_story as base
from .capabilities.core import Action, CapabilityError, Entity, Query, Record, fingerprint, matches, plain, replay
from .capabilities.epistemic import Fact, Proposition, Result
from .capabilities.physical import Container, Parent
from .capabilities.reading import Reader
from .goal_planning import Act, Goal, Method, Need, plan

GOALS = ("chart", "lamp", "boat")


@dataclass(frozen=True, kw_only=True)
class ResourceRules(Record):
    hold_cover: bool
    keep_launch_light: bool


@dataclass(frozen=True, kw_only=True)
class Preferences(Record):
    priorities: tuple[str, ...]
    window_display: bool


@dataclass(frozen=True, kw_only=True)
class Choice(Record):
    actor: str
    kept: tuple[str, ...]
    deferred: tuple[str, ...]
    blockers: tuple[str, ...]


def conflicts(get):
    """Necessary final-state exclusions derived from physical resources.

Only this bounded domain's declared methods are considered: jammed clips and
clamps have no repair method. This is not a general impossibility prover.
"""
    rules = get("harbor_resource_rules", "harbor")
    preference = get("harbor_preferences", "ari")
    alternatives = get("containers", "clip").open or (
        not preference.window_display and get("containers", "board").open)
    pairs = []
    if rules.hold_cover and not alternatives:
        pairs.append(("rope", frozenset(("chart", "boat"))))
    if rules.keep_launch_light and preference.window_display:
        pairs.append(("lantern", frozenset(("lamp", "boat"))))
    return tuple(pairs)


def select_goals(priorities, exclusions):
    """Lexicographic preference: lower priorities cannot outvote the first."""
    choices = [frozenset(s) for n in range(1, 4) for s in combinations(GOALS, n)
               if not any(pair <= set(s) for _, pair in exclusions)]
    selected = max(choices, key=lambda s: tuple(g in s for g in priorities))
    return tuple(g for g in priorities if g in selected)


def choose(tx, *, kept):
    tx.require(tx.action.actor == "ari", "Only Ari decides how to use Ari's resources")
    tx.require(all(tx.get("ownership", obj).owner == "ari" for obj in ("rope", "lantern")),
               "Ari must own the resources whose use is being chosen")
    tx.require(tx.maybe("harbor_choices", "evening") is None, "A plan has already been chosen")
    preference = tx.get("harbor_preferences", "ari")
    exclusions = conflicts(tx.get)
    expected = select_goals(preference.priorities, exclusions)
    tx.require(tuple(kept) == expected, "Choice must respect declared priorities and resource exclusions")
    deferred = tuple(g for g in preference.priorities if g not in kept)
    blockers = tuple(name for name, pair in exclusions if pair.intersection(deferred) and pair.intersection(kept))
    tx.put("harbor_choices", Choice(id="evening", actor="ari", kept=tuple(kept), deferred=deferred, blockers=blockers))
    tx.emit(kept=tuple(kept), deferred=deferred, blockers=blockers)


def validate(state):
    rules = state.get("harbor_resource_rules", "harbor")
    prefs = state.get("harbor_preferences", "ari")
    if rules is None or prefs is None or set(state.tables["harbor_resource_rules"]) != {"harbor"} or set(state.tables["harbor_preferences"]) != {"ari"}:
        raise CapabilityError("Explicit harbor rules and embodied preferences required")
    if any(type(b) is not bool for b in (rules.hold_cover, rules.keep_launch_light, prefs.window_display)):
        raise CapabilityError("Resource laws must be Boolean")
    if len(prefs.priorities) != 3 or set(prefs.priorities) != set(GOALS):
        raise CapabilityError("Preferences must order all three goals")
    if state.get("entities", prefs.id) is None or state.get("entities", prefs.id).kind != "actor":
        raise CapabilityError("Preferences need a physical actor")
    if rules.hold_cover and state.get("containers", "tub").open and state.get("parents", "rope").parent != "jetty":
        raise CapabilityError("The open cover still requires the secured rope at the jetty")
    if rules.keep_launch_light and state.get("parents", "boat").parent == "tub":
        if state.get("parents", "lantern").parent != "jetty" or not state.get("containers", "lantern").open:
            raise CapabilityError("A floating boat still requires the launch light")
    for choice in state.tables["harbor_choices"].values():
        if (choice.id != "evening" or choice.actor != "ari" or set(choice.kept) & set(choice.deferred)
                or set(choice.kept) | set(choice.deferred) != set(GOALS)
                or len(choice.kept) != len(set(choice.kept)) or len(choice.deferred) != len(set(choice.deferred))
                or len(choice.blockers) != len(set(choice.blockers)) or set(choice.blockers) - {"rope", "lantern"}):
            raise CapabilityError("Invalid embodied goal choice")


def initial(state):
    if state.tables["harbor_choices"]:
        raise CapabilityError("Goal choices must be enacted, not preloaded")


def registry():
    reg = base.registry()
    reg.table("harbor_resource_rules", ResourceRules)
    reg.table("harbor_preferences", Preferences)
    reg.table("harbor_choices", Choice)
    reg.operation("choose_harbor_goals", choose,
        reads={"harbor_choices", "harbor_preferences", "harbor_resource_rules", "containers", "ownership"},
        writes={"harbor_choices"})
    reg.validators.append(validate)
    reg.initial_validators.append(initial)
    return reg


@dataclass(frozen=True, kw_only=True)
class Conditions(base.Conditions):
    hold_cover: bool = True
    keep_launch_light: bool = True

    def __post_init__(self):
        super().__post_init__()
        if any(type(x) is not bool for x in (self.hold_cover, self.keep_launch_light)):
            raise ValueError("Persistent resource conditions must be Boolean")


def conditions(seed):
    c = base.conditions(seed)
    rng = random.Random(seed + 9187)
    return Conditions(**asdict(c), hold_cover=rng.random() < .7, keep_launch_light=rng.random() < .7)


def build(c):
    spec, original_goals = base.build(c)
    records = dict(spec.records)
    records["harbor_resource_rules"] = (ResourceRules(id="harbor", hold_cover=c.hold_cover,
        keep_launch_light=c.keep_launch_light and c.dark_launch),)
    records["harbor_preferences"] = (Preferences(id="ari", priorities=c.priorities, window_display=c.light_window),)
    records["entities"] += (Entity(id="dry_dock", name="the dry boat cradle", kind="container", capacity=10),)
    records["parents"] += (Parent(id="dry_dock", parent="jetty"),)
    records["containers"] += (Container(id="dry_dock"),)
    descriptions = {}
    if c.hold_cover:
        descriptions["cover"] = "filled water tub; rope and tools lift the cover, and the rope must stay secured at the jetty to hold it up"
    if c.keep_launch_light and c.dark_launch:
        descriptions["darkness"] = "the lantern must stay at the jetty while the little boat is on the dark water"
    records["propositions"] = tuple(replace(p, result=Result(kind="exact", value=descriptions[p.id]))
        if p.id in descriptions else p for p in records["propositions"])
    records["propositions"] += (Proposition(id="priorities", subject="ari", predicate="preference", scope="authored_premise",
        result=Result(kind="exact", value=" > ".join(c.priorities)), reference_start=0, reference_end=0),)
    records["facts"] += (Fact(id="priorities", carrier="ari", proposition="priorities"),)
    spec = replace(spec, records=records)
    exclusions = conflicts(registry().initial(spec).get)
    kept = select_goals(c.priorities, exclusions)
    deferred = tuple(g for g in c.priorities if g not in kept)
    goals = [g for g in original_goals if g.id != "evening"]
    by_goal = {g.id: g for g in goals}
    actions = list(spec.actions)
    actions.append(Action(id="choose_goals", operation="choose_harbor_goals", actor="ari", args=dict(kept=kept)))
    fallback = []
    if "chart" in deferred:
        actions.append(Action(id="lay_chart_flat", operation="put", actor="ari", args=dict(object="chart", destination="display")))
        goals.append(Goal(id="park_chart", carrier="ari",
            queries=(Query(table="parents", key="chart", field="parent", value="display"),),
            methods=(Method(id="flat_display", steps=(Need(id="has_chart"), Need(id="ari@quay"), Act(id="lay_chart_flat"))),)))
        fallback.append("park_chart")
    if "boat" in deferred:
        actions.append(Action(id="dock_boat", operation="put", actor="cy", args=dict(object="boat", destination="dry_dock")))
        goals.append(Goal(id="park_boat", carrier="cy",
            queries=(Query(table="parents", key="boat", field="parent", value="dry_dock"),),
            methods=(Method(id="dry_dock", steps=(Need(id="cy@jetty"), Act(id="dock_boat"))),)))
        fallback.append("park_boat")
    desired = tuple(q for g in kept for q in by_goal[g].queries)
    rests = tuple(q for g in goals if g.id in fallback for q in g.queries)
    chosen = Query(table="harbor_choices", key="evening", field="kept", value=kept)
    queries = (chosen, *desired, *rests)
    goals.append(Goal(id="evening", carrier="ari", queries=queries, methods=(Method(id="chosen_goals", steps=(
        Act(id="choose_goals"), *(Need(id=g) for g in kept),
        *(Need(id=g) for g in ("chart", "lamp", "boat") if g in kept),
        *(Need(id=g) for g in fallback))),)))
    return replace(spec, title="Not everything could have a turn", actions=tuple(actions), goal=queries), tuple(goals)


def generate(seed=0, *, prose_seed=None, config=None):
    from .harbor_tradeoffs_prose import render
    c = conditions(seed) if config is None else config
    spec, goals = build(c)
    result = plan(registry(), spec, goals, ("evening",), max_actions=1600)
    state = result.state
    path = [e.action.id for e in state.events]
    if replay(registry(), spec, path) != state or not all(matches(state, q) for q in spec.goal):
        raise ValueError("Tradeoff plan failed exact replay or declared resolution")
    decision = state.get("harbor_choices", "evening")
    original = {g.id: g for g in goals if g.id in GOALS}
    attained = tuple(g for g in c.priorities if all(matches(state, q) for q in original[g].queries))
    if attained != decision.kept:
        raise ValueError("Outcome does not match the declared kept/deferred goals")
    doc = render(spec, state, c, seed if prose_seed is None else prose_seed)
    plot = dict(purpose="resource_tradeoffs", outcome="+".join(g for g in GOALS if g in decision.kept),
        deferred=list(decision.deferred), blockers=list(decision.blockers), chart=state.get("parents", "chart").parent,
        boat=state.get("parents", "boat").parent, lamp=state.get("parents", "lantern").parent,
        chart_rehung=sum(e.action.id in {"hang_chart", "clip_chart", "board_chart"} for e in state.events) > 1)
    row = dict(ok=True, world="harbor_tradeoffs", sample_id=f"harbor_tradeoffs:{seed}", seed=seed,
        conditions=asdict(c), story=doc.story, words=len(doc.story.split()), plot=plot, path=path,
        trace_sha256=fingerprint(state), qa=[plain(q) for q in Reader(doc).questions()],
        planning=dict(attempted_actions=result.attempted_actions, rejected_actions=result.rejected_actions,
                      episodes=plain(result.episodes)))
    return row, spec, state, doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--qa", action="store_true", help="Print the story and its visible questions")
    args = parser.parse_args()
    row = generate(args.seed)[0]
    if args.qa:
        print(row["story"])
        print(json.dumps(row["qa"], indent=2))
    else:
        print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
