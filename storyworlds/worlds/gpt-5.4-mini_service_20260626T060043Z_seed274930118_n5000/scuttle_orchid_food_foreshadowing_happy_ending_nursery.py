#!/usr/bin/env python3
"""
A tiny Storyweavers world for a nursery-rhyme-style tale about scuttling,
orchids, and food, with foreshadowing and a happy ending.

The seed tale behind this world is simple:
A little beetle scuttles through a moonlit garden looking for food.
A bright orchid sways above a leaf, and a chirpy cricket warns that
evening is getting cold. The beetle finds a fallen crumb, but the crumb
is too far under a curled petal. A kind caterpillar helps nudge the leaf
aside, and the beetle shares the food. By the end, the garden feels safe,
the orchid glows softly, and everyone is fed.

This script models that premise as a small state machine:
- physical meters: hunger, distance, wind, crumbs, shelter, bloom
- emotional memes: hope, worry, kindness, friendship

The story is generated from world state, not from a frozen paragraph.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"beetle", "cricket", "caterpillar"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = False
    breeze: str = "gentle"
    affords: set[str] = field(default_factory=set)


@dataclass
class ActorSpec:
    name: str
    type: str
    label: str
    traits: list[str]


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def breathy(name: str) -> str:
    return {
        "scuttle": "scuttled",
        "orchid": "orchid",
        "food": "food",
    }.get(name, name)


PLACES = {
    "garden": Place(
        name="the garden",
        indoors=False,
        breeze="gentle",
        affords={"search", "share", "shelter"},
    ),
    "moon_patio": Place(
        name="the moonlit patio",
        indoors=False,
        breeze="cool",
        affords={"search", "share", "shelter"},
    ),
}

ACTORS = {
    "beetle": ActorSpec(
        name="Pip",
        type="beetle",
        label="little beetle",
        traits=["tiny", "busy", "curious"],
    ),
    "cricket": ActorSpec(
        name="Mim",
        type="cricket",
        label="small cricket",
        traits=["bright", "watchful", "kind"],
    ),
    "caterpillar": ActorSpec(
        name="Lulu",
        type="caterpillar",
        label="soft caterpillar",
        traits=["gentle", "helpful", "patient"],
    ),
}

OBJECTS = {
    "orchid": ObjectSpec(
        label="orchid",
        phrase="a pink orchid with a shining throat",
        type="flower",
    ),
    "crumb": ObjectSpec(
        label="crumb",
        phrase="a crumb of sweet seed cake",
        type="food",
    ),
    "leaf": ObjectSpec(
        label="leaf",
        phrase="a curled green leaf",
        type="shelter",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: scuttle, orchid, food, foreshadowing, happy ending.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero", choices=ACTORS.keys())
    ap.add_argument("--helper", choices=["cricket", "caterpillar"])
    ap.add_argument("--prize", choices=["orchid", "crumb", "leaf"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES.keys()))
    hero = args.hero or "beetle"
    helper = args.helper or rng.choice(["cricket", "caterpillar"])
    prize = args.prize or rng.choice(list(OBJECTS.keys()))
    if hero == helper:
        raise StoryError("The helper must be different from the hero.")
    return StoryParams(place=place, hero=hero, helper=helper, prize=prize)


def line_join(parts: list[str]) -> str:
    return " ".join(parts)


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for e in list(world.entities.values()):
            if e.id == "hero" and _meter(e, "hunger") >= THRESHOLD and ("foreshadow", "warn") not in world.fired:
                world.fired.add(("foreshadow", "warn"))
                world.facts["foreshadow"] = True
                out.append("The breeze grew cool, and that was a little warning.")
                changed = True
            if e.id == "hero" and _mem(e, "hope") >= THRESHOLD and _meter(e, "food") >= THRESHOLD and ("resolve", "share") not in world.fired:
                world.fired.add(("resolve", "share"))
                e.meters["hunger"] = max(0.0, _meter(e, "hunger") - 1.0)
                e.memes["joy"] = _mem(e, "joy") + 1.0
                out.append("The hungry belly grew full, and the worry went away.")
                changed = True
    for s in out:
        world.say(s)
    return out


def tell(place: Place, hero_spec: ActorSpec, helper_spec: ActorSpec, prize: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero", kind="character", type=hero_spec.type, label=hero_spec.name,
        traits=list(hero_spec.traits), meters={"hunger": 1.0, "travel": 0.0}, memes={"hope": 1.0, "worry": 0.0, "joy": 0.0}
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=helper_spec.type, label=helper_spec.name,
        traits=list(helper_spec.traits), meters={"wind_notice": 1.0}, memes={"kindness": 1.0}
    ))
    orchid = world.add(Entity(id="orchid", type="flower", label="orchid", phrase=OBJECTS["orchid"].phrase, meters={"bloom": 1.0}))
    food = world.add(Entity(id="food", type="food", label="crumb", phrase=OBJECTS["crumb"].phrase, meters={"food": 0.0}))
    leaf = world.add(Entity(id="leaf", type="shelter", label="leaf", phrase=OBJECTS["leaf"].phrase, meters={"cover": 1.0}))

    world.facts.update(hero=hero, helper=helper, orchid=orchid, food=food, leaf=leaf, prize=prize, place=place)

    world.say(f"Under {place.name}, little {hero.label} did scuttle, scuttle, scuttle along.")
    world.say(f"Above {hero.pronoun('possessive')} head sat the orchid, so bright and fair, like a lantern song.")
    world.say(f"{helper.label} called softly, 'The air is turning cool; a snack may hide somewhere near.'")

    world.para()
    world.say(f"{hero.label} felt a tiny hunger and searched by root and stone for food.")
    hero.meters["travel"] += 1.0
    hero.meters["hunger"] += 1.0
    propagate(world)

    if prize == "orchid":
        world.say("But the orchid only shivered in the breeze; it was not a meal at all.")
    elif prize == "leaf":
        world.say("The leaf was good for shelter, but not for supper, so the search went on.")
    else:
        world.say("At last, a crumb of food was seen, tucked beneath a curled leaf.")

    world.para()
    world.say("The crumb was near, yet not near enough; it trembled under the petal's small dome.")
    world.say("That was the foreshadowing, soft as a hush: hunger would not be solved alone.")
    hero.memes["worry"] += 1.0
    world.facts["foreshadow"] = True

    if helper_spec.type == "cricket":
        world.say(f"{helper.label} hopped along and tapped the leaf with a careful toe.")
        world.say("The leaf swung wide, and the hidden food came free at last.")
    else:
        world.say(f"{helper.label} curled around the leaf and nudged it up with a gentle back.")
        world.say("The leaf lifted like a little door, and the hidden food came free at last.")

    food.meters["food"] = 1.0
    hero.meters["hunger"] = max(0.0, hero.meters.get("hunger", 0.0) - 1.0)
    hero.memes["hope"] += 1.0
    hero.memes["joy"] += 1.0
    helper.memes["kindness"] += 1.0
    world.say(f"{hero.label} munched the crumb of food, and {helper.label} smiled as moonlight spread.")
    world.say(f"The orchid glowed like a tiny star, and the garden felt warm again instead of dread.")
    world.say(f"So under {place.name}, little {hero.label} did scuttle no more in a hungry song,")
    world.say(f"for food was found, the night grew sweet, and all was safe and bright and strong.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    return [
        f'Write a short nursery rhyme about a {hero.type} who scuttles through {place.name} looking for food.',
        f"Tell a gentle story with an orchid, a little bit of foreshadowing, and a happy ending.",
        f'Write a rhyming tale where {hero.label} needs food, {helper.label} helps, and the orchid shines at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who scuttled through {place.name} looking for food?",
            answer=f"Little {hero.label} did. {hero.label} was the hungry beetle who went searching under the orchid's glow.",
        ),
        QAItem(
            question="What was the little warning before the happy ending?",
            answer="The breeze grew cool, and that foreshadowed that hunger would not be solved unless someone helped.",
        ),
        QAItem(
            question=f"Who helped {hero.label} get the food?",
            answer=f"{helper.label} helped by moving the leaf aside, so the crumb could be reached safely.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The food was found, the beetle was full, the orchid glowed softly, and the garden felt safe and sweet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchid?",
            answer="An orchid is a kind of flower with delicate petals and a lovely shape.",
        ),
        QAItem(
            question="What is food for?",
            answer="Food is for giving living things energy so they can move, grow, and feel better when they are hungry.",
        ),
        QAItem(
            question="What does it mean to foreshadow something in a story?",
            answer="Foreshadowing is a small clue early in a story that hints at what may happen later.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTORS[params.hero], ACTORS[params.helper], params.prize)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
% Minimal declarative twin for parity/verification.
hero(H) :- actor(H).
helper(K) :- actor(K).
foreshadow :- hunger(hero), breeze(cool).
happy_ending :- food(found), helper(helped), foreshadow.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, spec in ACTORS.items():
        lines.append(asp.fact("actor", key))
        lines.append(asp.fact("type_of", key, spec.type))
    for key, place in PLACES.items():
        lines.append(asp.fact("place", key))
        if place.indoors:
            lines.append(asp.fact("indoors", key))
        lines.append(asp.fact("breeze", place.breeze))
    for key in OBJECTS:
        lines.append(asp.fact("thing", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        raise StoryError(f"ASP verification requires clingo/asp helper: {e}") from e
    # lightweight parity check: program parses and has at least one model
    model = asp.one_model(asp_program("#show happy_ending/0."))
    ok = any(sym.name == "happy_ending" for sym in model)
    if ok:
        print("OK: ASP twin produced a happy ending model.")
        return 0
    print("MISMATCH: ASP twin did not produce happy ending.")
    return 1


CURATED = [
    StoryParams(place="garden", hero="beetle", helper="cricket", prize="crumb"),
    StoryParams(place="moon_patio", hero="beetle", helper="caterpillar", prize="orchid"),
]


def format_qa(sample: StorySample) -> str:
    lines = []
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
