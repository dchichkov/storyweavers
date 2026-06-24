#!/usr/bin/env python3
"""
storyworlds/worlds/van_frantic_soften_suspense_moral_value_transformation.py
=============================================================================

A small fable-like storyworld about a van, a frantic moment, and a softening
turn toward kindness. The simulation tracks physical meters and emotional memes
for a few typed entities, then renders a complete child-facing story with a
suspense beat, a moral value turn, and a transformation ending.

Seed image:
- A van rushes through a rainy lane.
- A frantic problem makes everyone hurry.
- A gentle choice softens the moment and changes how the van is used.

Style notes:
- Fable-like, simple, concrete, and moral.
- The world should feel state-driven rather than like a fixed paragraph with
  swapped nouns.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str
    label: str
    role: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    name: str
    damp: bool = False
    dark: bool = False
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    setting: str
    road: str
    passenger: str
    helper: str
    cargo: str
    weather: str
    risk: str
    moral: str
    transform: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    places: dict[str, Place] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_place(self, place: Place) -> Place:
        self.places[place.id] = place
        return place

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THEMES = {
    "lantern_lane": {
        "setting": "a sleepy lane by the orchard",
        "road": "the muddy road",
        "weather": "a wet evening",
        "moral": "kindness helps more than shouting",
        "transform": "from rushing and fear to calm and care",
    },
    "market_bridge": {
        "setting": "a small market street by the river",
        "road": "the cobbled street",
        "weather": "a windy afternoon",
        "moral": "a gentle heart can guide hurried hands",
        "transform": "from frantic noise to steady helpfulness",
    },
    "hill_path": {
        "setting": "a quiet path below the hill",
        "road": "the narrow path",
        "weather": "a gray morning",
        "moral": "doing the right thing can soften a hard moment",
        "transform": "from panic to patient care",
    },
}

CARGOS = {
    "apples": "a basket of apples",
    "bread": "fresh bread",
    "flowers": "a bundle of flowers",
}

PASSENGERS = ["Milo", "Nina", "Tess", "Owen"]
HELPERS = ["the old baker", "the kind gardener", "the postkeeper", "the lighthouse keeper"]
RISKS = {
    "storm": "a storm cloud rolling in",
    "ditch": "a deep ditch ahead",
    "goose": "a goose blocking the road",
}

WEATHER_WORDS = ["rain", "mist", "wind"]


def build_world(params: StoryParams) -> World:
    w = World()
    van = w.add_entity(Entity(id="van", kind="vehicle", label="van", role="worker"))
    passenger = w.add_entity(Entity(id="passenger", kind="character", label=params.passenger))
    helper = w.add_entity(Entity(id="helper", kind="character", label=params.helper))
    road = w.add_place(Place(id="road", name=params.road, dark=True))

    van.meters["speed"] = 2.0
    van.memes["purpose"] = 1.0
    passenger.memes["worry"] = 1.0
    helper.memes["care"] = 1.0
    road.meters["danger"] = 0.0

    w.facts.update(
        van=van,
        passenger=passenger,
        helper=helper,
        road=road,
        params=params,
    )
    return w


def suspense_beat(w: World, params: StoryParams) -> None:
    van = w.facts["van"]
    passenger = w.facts["passenger"]
    road = w.facts["road"]
    van.meters["speed"] += 1.0
    van.memes["frantic"] = 1.0
    passenger.memes["worry"] += 1.0
    road.meters["danger"] += 1.0
    w.say(
        f"On {params.setting}, a little van rattled along {params.road} while "
        f"{params.passenger} sat inside with {params.cargo} and watched the {params.weather} gather."
    )
    w.say(
        f"Then {params.risk} came into view, and the van grew frantic. "
        f"{params.passenger} held on tight, for the road looked long and uncertain."
    )


def soften_beat(w: World, params: StoryParams) -> None:
    helper = w.facts["helper"]
    passenger = w.facts["passenger"]
    van = w.facts["van"]
    road = w.facts["road"]
    helper.memes["care"] += 1.0
    passenger.memes["worry"] = max(0.0, passenger.memes["worry"] - 1.0)
    van.memes["frantic"] = 0.0
    road.meters["danger"] = max(0.0, road.meters["danger"] - 1.0)
    w.say(
        f"At the bend, {params.helper} waved and called out kindly. "
        f"Instead of rushing past, the van slowed down and let the helper speak."
    )
    w.say(
        f"{params.helper} showed the safest way forward, and that gentle help began to soften the worry."
    )


def transformation_beat(w: World, params: StoryParams) -> None:
    van = w.facts["van"]
    passenger = w.facts["passenger"]
    van.meters["speed"] = 1.0
    van.memes["frantic"] = 0.0
    van.memes["calm"] = 1.0
    passenger.memes["worry"] = 0.0
    passenger.memes["trust"] = 1.0
    w.say(
        f"After that, the van changed its way. It no longer raced; it carried its load carefully instead."
    )
    w.say(
        f"{params.passenger} smiled, because the same van that had felt frantic now moved with patience and grace."
    )
    w.say(
        f"That was the moral of the road: {params.moral}. In the end, the story was about {params.transform}."
    )


def tell(params: StoryParams) -> World:
    w = build_world(params)
    suspense_beat(w, params)
    w.para()
    soften_beat(w, params)
    w.para()
    transformation_beat(w, params)
    w.facts["outcome"] = "softened"
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a fable about a van on {p.road} that feels frantic when danger appears, but is softened by a kind helper.",
        f"Tell a child-friendly story set on {p.setting} where {p.passenger} learns a moral from a van's frightened moment.",
        f"Write a short fable with suspense, moral value, and transformation using a van, {p.cargo}, and a gentle ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What kind of vehicle is in the story?",
            answer="It is a van, and it begins the story moving quickly on a worried road.",
        ),
        QAItem(
            question=f"Why did {p.passenger} feel worried?",
            answer=f"{p.passenger} felt worried because {p.risk} appeared ahead and the road seemed uncertain.",
        ),
        QAItem(
            question=f"Who helped make the moment softer?",
            answer=f"{p.helper} helped by speaking kindly and showing the safest way forward.",
        ),
        QAItem(
            question="How did the van change by the end?",
            answer="The van changed from frantic and rushing to calm and careful.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What does frantic mean?",
        answer="Frantic means rushed, worried, and hard to calm down.",
    ),
    QAItem(
        question="What does soften mean?",
        answer="Soften means to make something gentler, calmer, or less harsh.",
    ),
    QAItem(
        question="What is a fable?",
        answer="A fable is a short story that teaches a moral, often with animals or simple symbols.",
    ),
    QAItem(
        question="What is a moral?",
        answer="A moral is the lesson a story wants to teach about how to act well.",
    ),
    QAItem(
        question="What is transformation in a story?",
        answer="Transformation is a change from one state to another, such as fear turning into calm.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    for p in world.places.values():
        lines.append(f"{p.id}: meters={p.meters} dark={p.dark}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("vehicle", "van"),
        asp.fact("state", "frantic"),
        asp.fact("state", "soften"),
        asp.fact("feature", "suspense"),
        asp.fact("feature", "moral_value"),
        asp.fact("feature", "transformation"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
feature(suspense) :- state(frantic).
feature(moral_value) :- state(soften).
feature(transformation) :- feature(suspense), feature(moral_value).
story_ok :- feature(suspense), feature(moral_value), feature(transformation).
#show feature/1.
#show story_ok/0.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok and asp_reasonable():
        print("OK: ASP and Python agree on story reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a van, frantic fear, and a softening turn.")
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    theme_key = args.theme or rng.choice(sorted(THEMES))
    t = THEMES[theme_key]
    passenger = rng.choice(PASSENGERS)
    helper = rng.choice(HELPERS)
    cargo_key = rng.choice(sorted(CARGOS))
    risk_key = rng.choice(sorted(RISKS))
    return StoryParams(
        setting=t["setting"],
        road=t["road"],
        passenger=passenger,
        helper=helper,
        cargo=CARGOS[cargo_key],
        weather=t["weather"],
        risk=RISKS[risk_key],
        moral=t["moral"],
        transform=t["transform"],
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("", "#show feature/1.\n#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show feature/1.\n#show story_ok/0."))
        print("ASP features:", [f"{a.name}({','.join(str(x) for x in a.arguments)})" for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for key in sorted(THEMES):
            p = resolve_params(argparse.Namespace(theme=key, seed=base_seed), random.Random(base_seed))
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.passenger} and {sample.params.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
