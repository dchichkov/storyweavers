"""Compose display, launch and lighting goals; preserve the earlier harbor trials.

This opt-in experiment has no deadline. Opening the tub uses a rope that may
already hold the chart; a dark launch needs the lantern that may already light
the window. Completed displays can be dismantled and restored by the same
goal methods. The simulator, not prose selection, checks each combination.
"""
from dataclasses import asdict, dataclass
import argparse
import json
import random

from .capabilities.api import registry
from .capabilities.core import Action, Entity, Query, WorldSpec, fingerprint, plain, replay
from .capabilities.epistemic import Fact, Proposition, Result
from .capabilities.physical import Container, Ownership, Parent, Route
from .capabilities.reading import Reader
from .goal_planning import Act, Goal, Method, Need, plan


@dataclass(frozen=True, kw_only=True)
class Conditions:
    priorities: tuple[str, ...] = ("chart", "lamp", "boat")
    supports: tuple[str, ...] = ("rope", "clip", "board")
    clip: bool = False
    board: bool = False
    dark_launch: bool = True
    light_window: bool = True

    def __post_init__(self):
        if len(self.priorities) != 3 or set(self.priorities) != {"chart", "lamp", "boat"}:
            raise ValueError("Priorities must order the three goals exactly once")
        if len(self.supports) != 3 or set(self.supports) != {"rope", "clip", "board"}:
            raise ValueError("Support preferences must order the three methods")
        if any(type(x) is not bool for x in (self.clip, self.board, self.dark_launch, self.light_window)):
            raise ValueError("Physical conditions must be Boolean")


def conditions(seed):
    rng = random.Random(seed)
    return Conditions(priorities=tuple(rng.sample(("chart", "lamp", "boat"), 3)),
        supports=tuple(rng.sample(("rope", "clip", "board"), 3)),
        clip=rng.random() < .5, board=rng.random() < .5,
        dark_launch=rng.random() < .6, light_window=rng.random() < .6)


def build(c):
    entities = tuple(Entity(id=id, name=name, kind=kind, mass=mass,
                            capacity=30 if id == "case" else 20) for id, name, kind, mass in (
        ("ari", "Ari", "actor", 1), ("bo", "Bo", "actor", 1), ("cy", "Cy", "actor", 1),
        ("workshop", "the workshop", "place", 1), ("quay", "the quay window", "place", 1),
        ("jetty", "the jetty", "place", 1), ("display", "the window shelf", "container", 1),
        ("board", "the jetty board", "container", 1), ("clip", "the window clip", "container", 1),
        ("case", "the tool case", "container", 1), ("tools", "the tools", "object", 12),
        ("rope", "Ari's rope", "container", 12), ("chart", "Ari's harbor chart", "object", 1),
        ("tub", "the launch tub", "container", 1), ("boat", "Cy's wooden boat", "object", 1),
        ("lantern", "Ari's shuttered lantern", "container", 1), ("bulb", "the glowing bulb", "object", 0)))
    parents = dict(ari="workshop", bo="jetty", cy="workshop", display="quay", board="jetty",
        clip="display", case="workshop", tools="case", rope="case", chart="workshop", tub="jetty",
        boat="cy", lantern="workshop", bulb="lantern")
    routes = tuple(Route(id=f"{a}_{b}", source=a, destination=b, max_load=20)
                   for a in ("workshop", "quay", "jetty") for b in ("workshop", "quay", "jetty") if a != b)
    premises = dict(
        chart=("ari", "show the harbor chart hanging upright"),
        boat=("cy", "put the little boat onto water"),
        lamp=("ari", "light the window chart" if c.light_window else "leave the lantern lighting the jetty"),
        load=("case", "the tools and rope together are too heavy for one person"),
        cover=("tub", "filled water tub; its heavy cover needs the rope and tools to lift"),
        darkness=("jetty", "a lantern is needed to see where to lower the boat" if c.dark_launch else "enough daylight for the launch"),
        glow=("bulb", "glowing behind the closed lantern shutter"),
        clip=("clip", "usable paper clip" if c.clip else "clip jaws stuck shut"),
        board=("board", "usable chart clamps" if c.board else "board clamps stuck shut"))
    premises.update(chart_made=("chart", "Ari drew the harbor chart"), boat_made=("boat", "Cy made the wooden boat"))
    records = dict(entities=entities, parents=tuple(Parent(id=i, parent=p) for i,p in parents.items()),
        containers=tuple(Container(id=i, open=opened) for i,opened in (
            ("display", True), ("board", c.board), ("clip", c.clip), ("case", True),
            ("rope", True), ("tub", False), ("lantern", False))), routes=routes,
        ownership=tuple(Ownership(id=i, owner=owner) for i,owner in (
            ("rope", "ari"), ("chart", "ari"), ("lantern", "ari"), ("boat", "cy"), ("case", "bo"))),
        propositions=tuple(Proposition(id=i, subject=carrier, predicate="premise", scope="authored_premise",
            result=Result(kind="exact", value=text), reference_start=0, reference_end=0)
            for i,(carrier,text) in premises.items()),
        facts=tuple(Fact(id=i, carrier=carrier, proposition=i) for i,(carrier,_) in premises.items()))
    actions, goals = [], []

    def q(table, key, field, value, op="eq"):
        return Query(table=table, key=key, field=field, value=value, op=op)

    def at(obj, dest):
        return q("parents", obj, "parent", dest)

    def action(id, operation, actor, **args):
        requires = args.pop("requires", ())
        actions.append(Action(id=id, operation=operation, actor=actor, args=args, requires=requires, max_uses=6))
        return Act(id=id)

    def need(id):
        return Need(id=id)

    def method(id, *steps):
        return Method(id=id, steps=tuple(steps))

    def goal(id, carrier, queries, *methods):
        goals.append(Goal(id=id, carrier=carrier, queries=tuple(queries), methods=tuple(methods)))

    for actor in ("ari", "bo", "cy"):
        for dest in ("workshop", "quay", "jetty"):
            goal(f"{actor}@{dest}", actor, (at(actor, dest),), *(method(f"from_{r.source}",
                 action(f"{actor}_{r.id}", "travel", actor, route=r.id)) for r in routes if r.destination == dest))

    # The same retrieval goal is used before mounting and after dismantling.
    for obj, sources in (("chart", ("workshop", "rope", "clip", "board")),
                         ("rope", ("case", "display", "jetty")),
                         ("lantern", ("workshop", "display", "jetty"))):
        methods = []
        for source in sources:
            place = "workshop" if source in ("workshop", "case") else "jetty" if source in ("board", "jetty") else "quay"
            prefix = (need("has_chart"),) if obj == "rope" and source == "display" else ()
            guards = (q("parents", "chart", "parent", "rope", "ne"),) if prefix else ()
            take = action(f"take_{obj}_{source}", "pickup", "ari", object=obj, source=source, requires=guards)
            if prefix:
                methods.append(method("from_empty_display", need(f"ari@{place}"), take))
            methods.append(method(f"from_{source}", *prefix, need(f"ari@{place}"),
                take))
        goal(f"has_{obj}", "ari", (at(obj, "ari"),), *methods)

    goal("rope_at_window", "rope", (at("rope", "display"),), method("carry_to_window",
        need("has_rope"), need("ari@quay"), action("hang_rope", "put", "ari", object="rope", destination="display")))
    goal("rope_at_jetty", "rope", (at("rope", "jetty"),), method("carry_to_jetty",
        need("has_rope"), need("ari@jetty"), action("deliver_rope", "put", "ari", object="rope", destination="jetty")))
    chart_methods = dict(
        rope=method("rope_window", need("has_chart"), need("rope_at_window"), need("ari@quay"),
            action("hang_chart", "put", "ari", object="chart", destination="rope",
                   requires=(at("rope", "display"),))),
        clip=method("clip_window", need("has_chart"), need("ari@quay"),
            action("clip_chart", "put", "ari", object="chart", destination="clip")),
        board=method("board_jetty", need("has_chart"), need("ari@jetty"),
            action("board_chart", "put", "ari", object="chart", destination="board")))
    chart_query = q("parents", "chart", "parent", ("rope", "clip") if c.light_window else ("rope", "clip", "board"), "in")
    goal("chart", "ari", (chart_query,), *(chart_methods[m] for m in c.supports))

    for dest, place in (("display", "quay"), ("jetty", "jetty")):
        goal(f"lamp_{place}", "lantern", (at("lantern", dest),), method(f"carry_{place}",
            need("has_lantern"), need(f"ari@{place}"),
            action(f"lamp_{place}", "put", "ari", object="lantern", destination=dest)))
    goal("lamp_open", "lantern", (q("containers", "lantern", "open", True),), method("open_in_hand",
        need("has_lantern"), action("open_lantern", "set_container", "ari", container="lantern", open=True)))
    lamp_dest = "display" if c.light_window else "jetty"
    lamp_queries = (at("lantern", lamp_dest), q("containers", "lantern", "open", True))
    goal("lamp", "ari", lamp_queries, method("light_home", need("lamp_open"), need("lamp_quay" if c.light_window else "lamp_jetty")))

    take_case = action("take_case", "pickup", "cy", object="case", source="workshop")
    put_case = action("deliver_case", "put", "cy", object="case", destination="jetty")
    goal("case", "bo", (at("case", "jetty"),),
         method("carry_case", need("cy@workshop"), take_case, need("cy@jetty"), put_case),
         method("split_load", need("has_rope"), need("cy@workshop"), take_case, need("cy@jetty"), put_case))
    goal("tub_open", "tub", (q("containers", "tub", "open", True),), method("lift_cover",
        need("case"), need("rope_at_jetty"), need("bo@jetty"),
        action("open_tub", "set_container", "bo", container="tub", open=True,
               requires=(at("rope", "jetty"), at("case", "jetty"), at("tools", "case")))))
    light = (need("lamp_open"), need("lamp_jetty")) if c.dark_launch else ()
    light_guards = (at("lantern", "jetty"), q("containers", "lantern", "open", True)) if c.dark_launch else ()
    goal("boat", "cy", (at("boat", "tub"),), method("launch", need("tub_open"), *light, need("cy@jetty"),
        action("launch", "put", "cy", object="boat", destination="tub", requires=light_guards)))
    all_queries = (chart_query, at("boat", "tub"), *lamp_queries)
    # Revisit goals after the shared-resource work. Already-satisfied goals do
    # nothing; only displaced resources create further causal work.
    goal("evening", "ari", all_queries, method("combine_goals",
        *(need(g) for g in (*c.priorities, "chart", "lamp", "boat"))))
    return WorldSpec(title="The harbor was not finished yet", records=records, actions=tuple(actions),
                     goal=all_queries, max_steps=150), tuple(goals)


def generate(seed=0, *, prose_seed=None, config=None):
    from .harbor_composition_prose import render
    c = conditions(seed) if config is None else config
    spec, goals = build(c)
    result = plan(registry(), spec, goals, ("evening",), max_actions=1200)
    state = result.state
    path = [e.action.id for e in state.events]
    if replay(registry(), spec, path) != state:
        raise ValueError("Composed harbor failed exact replay")
    doc = render(spec, state, c, seed if prose_seed is None else prose_seed)
    actions = [e.action.id for e in state.events]
    plot = dict(purpose="composed_goals", outcome="all_three_goals",
        first_milestone=next(a for a in actions if a in ("hang_chart", "clip_chart", "board_chart", "lamp_quay", "lamp_jetty", "launch")),
        chart_rehung=actions.count("hang_chart") > 1,
        chart_support=state.get("parents", "chart").parent,
        lamp_at_both_sites="lamp_quay" in actions and "lamp_jetty" in actions,
        dark_launch=c.dark_launch)
    row = dict(ok=True, world="harbor_composition", sample_id=f"harbor_composition:{seed}", seed=seed,
        conditions=asdict(c), story=doc.story, words=len(doc.story.split()), plot=plot, path=path,
        trace_sha256=fingerprint(state), qa=[plain(q) for q in Reader(doc).questions()],
        planning=dict(attempted_actions=result.attempted_actions, rejected_actions=result.rejected_actions,
                      episodes=plain(result.episodes)))
    return row, spec, state, doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed)[0], indent=2))


if __name__ == "__main__":
    main()
