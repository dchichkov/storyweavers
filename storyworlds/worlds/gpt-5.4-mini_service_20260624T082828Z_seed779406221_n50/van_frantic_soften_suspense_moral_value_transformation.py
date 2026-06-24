#!/usr/bin/env python3
"""
A small fable-like story world about a van, a frantic rush, and learning to soften.
The domain is intentionally tiny: one road, one van, one hurried goal, one moral turn.

Premise seed:
- A van carries a parcel to a hill village.
- The driver grows frantic when the road closes.
- A calm helper suggests a softer way: slow down, ask for help, and share the load.
- The ending proves the change by showing the van reaching the village safely and gently.

This world uses a simple physical/emotional model:
- meters track visible state such as load, fuel, damage, distance, stuckness.
- memes track emotional state such as franticness, worry, calm, kindness, trust.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "driver", "boy", "father"}
        female = {"woman", "girl", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Route:
    place: str = "the hill road"
    destination: str = "the village"
    weather: str = "windy"
    obstacle: str = "a fallen branch"
    affordance: str = "a side path through the meadow"


@dataclass
class StoryParams:
    place: str = "road"
    seed: Optional[int] = None


class World:
    def __init__(self, route: Route) -> None:
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.route)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


def _inc(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _mem(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, driver: Entity, parcel: Entity) -> None:
    world.say(
        f"Once, a small van rolled along the hill road with {parcel.phrase} inside. "
        f"The driver was named {driver.id}, and {driver.pronoun()} liked to arrive on time."
    )


def setup_suspense(world: World, driver: Entity, helper: Entity, parcel: Entity) -> None:
    _mem(driver, "eagerness", 1)
    _mem(driver, "worry", 1)
    world.say(
        f"{driver.id} glanced at the clouds and grew frantic, because the road ahead was narrowing. "
        f"{driver.pronoun().capitalize()} still wanted to reach the village before night."
    )
    world.say(
        f"Then {helper.id} came from the meadow and pointed to {world.route.obstacle}. "
        f'"There is a softer way," {helper.pronoun()} said, "if you are willing to slow down."'
    )


def predict_loss(world: World, driver: Entity, parcel: Entity) -> bool:
    sim = world.copy()
    _inc(sim.get(driver.id), "frantic", 1)
    _inc(sim.get("van"), "stuck", 1)
    _inc(sim.get(parcel.id), "jolt", 1)
    return True


def react_frantic(world: World, driver: Entity) -> None:
    _mem(driver, "frantic", 1)
    world.say(
        f"{driver.id} felt frantic and nearly pressed on too hard, but the wheels began to slip in the mud."
    )


def moral_turn(world: World, driver: Entity, helper: Entity) -> None:
    _mem(driver, "humble", 1)
    _mem(helper, "kindness", 1)
    _mem(driver, "trust", 1)
    _mem(driver, "calm", 1)
    world.say(
        f"{helper.id} did not laugh. Instead, {helper.pronoun()} offered a steadier idea: "
        f'"Let the van rest, share the load, and choose the softer path."'
    )
    world.say(
        f"{driver.id} listened. The frantic feeling softened, like a knot loosening in warm hands."
    )


def transform(world: World, driver: Entity, helper: Entity, parcel: Entity) -> None:
    van = world.get("van")
    _inc(van, "distance", 1)
    _inc(van, "fuel", -1)
    _inc(van, "damage", -1)
    _mem(van, "steady", 1)
    _mem(driver, "calm", 2)
    _mem(driver, "frantic", -1)
    world.say(
        f"They took the side path through the meadow and gave the parcel a gentler ride. "
        f"The van moved more slowly, but it moved safely."
    )
    world.say(
        f"At last the van reached the village, and {parcel.phrase} was delivered without a single hard bump."
    )


def ending(world: World, driver: Entity, helper: Entity, parcel: Entity) -> None:
    world.say(
        f"{driver.id} thanked {helper.id} for the warning and the wiser way. "
        f"From then on, {driver.pronoun()} remembered that speed is not the same as wisdom."
    )
    world.say(
        f"And so the little van went home at dusk, its load lighter, its road gentler, and its driver no longer frantic."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The van story is reasonable when the road is narrow, an obstacle appears,
% and the helper can offer a softer way.
reasonably_suspenseful(V) :- van(V), obstacle(o), helper(h), route(r).
frantic(V) :- van(V), narrow_road(r), obstacle(o).
soften(V) :- van(V), helper(h), willing_to_listen(d).
moral_value(d, kindness) :- helper(h).
transformation(d) :- frantic(d), soften(d).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("van", "van"),
        asp.fact("driver", "driver"),
        asp.fact("helper", "helper"),
        asp.fact("parcel", "parcel"),
        asp.fact("route", "route"),
        asp.fact("obstacle", "o"),
        asp.fact("narrow_road", "r"),
        asp.fact("willing_to_listen", "driver"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    from asp import atoms, one_model

    model = one_model(asp_program("#show reasonably_suspenseful/1.\n#show transformation/1.\n#show moral_value/2.\n#show soften/1.\n#show frantic/1."))
    shown = set()
    for name in ("reasonably_suspenseful", "transformation", "moral_value", "soften", "frantic"):
        shown.update((name,) + tuple(x) for x in atoms(model, name))
    expected = {
        ("reasonably_suspenseful", "van"),
        ("transformation", "driver"),
        ("moral_value", "driver", "kindness"),
        ("soften", "driver"),
        ("frantic", "van"),
    }
    if shown == expected:
        print("OK: ASP and Python world intent are aligned.")
        return 0
    print("MISMATCH between ASP and expected intent.")
    print("ASP:", sorted(shown))
    print("Expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROUTES = {
    "road": Route(place="the hill road", destination="the village", weather="windy",
                  obstacle="a fallen branch", affordance="a side path through the meadow"),
}

NAMES = ["Milo", "Nina", "Tara", "Oren", "Ivy", "Finn", "Mara", "Pip"]


# ---------------------------------------------------------------------------
# Core story simulation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    route = ROUTES["road"]
    world = World(route)

    driver = world.add(Entity(
        id=random.choice(NAMES),
        kind="character",
        type="driver",
        label="driver",
        meters={"distance": 0.0, "fuel": 3.0, "damage": 0.0},
        memes={"worry": 0.0, "frantic": 0.0, "calm": 0.0, "trust": 0.0},
        tags={"moral"},
    ))
    helper = world.add(Entity(
        id="Aunt Bee",
        kind="character",
        type="woman",
        label="helper",
        meters={"distance": 0.0},
        memes={"kindness": 0.0, "calm": 1.0},
        tags={"moral"},
    ))
    parcel = world.add(Entity(
        id="parcel",
        kind="thing",
        type="package",
        label="parcel",
        phrase="a basket of ripe pears",
        owner=driver.id,
        carried_by="van",
        meters={"jolt": 0.0},
        memes={"value": 1.0},
        tags={"parcel"},
    ))
    van = world.add(Entity(
        id="van",
        kind="thing",
        type="van",
        label="van",
        phrase="the little van",
        owner=driver.id,
        meters={"distance": 0.0, "fuel": 3.0, "damage": 0.0, "stuck": 0.0},
        memes={"steady": 0.0},
        tags={"vehicle", "suspense"},
    ))

    intro(world, driver, parcel)
    world.para()
    setup_suspense(world, driver, helper, parcel)
    react_frantic(world, driver)
    world.para()
    moral_turn(world, driver, helper)
    transform(world, driver, helper, parcel)
    ending(world, driver, helper, parcel)

    world.facts.update(
        driver=driver,
        helper=helper,
        parcel=parcel,
        van=van,
        route=route,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable about a van that becomes frantic on a hill road and learns to soften its haste.',
        'Tell a child-friendly story where a driver faces suspense, chooses a moral value, and changes by the end.',
        'Write a gentle transformation story about a van, a worried driver, and a kinder way to reach the village.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["driver"]
    h: Entity = f["helper"]
    p: Entity = f["parcel"]
    return [
        QAItem(
            question=f"What made {d.id} frantic on the hill road?",
            answer=f"{d.id} became frantic when the road narrowed and {world.route.obstacle} blocked the easiest way to the village.",
        ),
        QAItem(
            question=f"How did {h.id} help when the van could not hurry safely?",
            answer=f"{h.id} offered a softer way: slow down, share the load, and take the side path through the meadow.",
        ),
        QAItem(
            question=f"What changed by the end of the story for the van and the parcel?",
            answer=f"The van stopped rushing, reached the village safely, and delivered {p.phrase} without hard bumps.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a van?",
            answer="A van is a vehicle with room for people or cargo, and it is often used to carry things from one place to another.",
        ),
        QAItem(
            question="What does it mean to soften a hard feeling?",
            answer="To soften a hard feeling means to become calmer, gentler, or less sharp, so it is easier to think clearly.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something important might go wrong.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of living or acting, such as kindness, honesty, or patience.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is a change from one state to another, like moving from fear to calm or from trouble to success.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like van story world.")
    ap.add_argument("--place", choices=list(ROUTES))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(place=args.place or "road", seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonably_suspenseful/1.\n#show transformation/1.\n#show moral_value/2.\n#show soften/1.\n#show frantic/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples.append(generate(StoryParams(place="road", seed=base_seed)))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
