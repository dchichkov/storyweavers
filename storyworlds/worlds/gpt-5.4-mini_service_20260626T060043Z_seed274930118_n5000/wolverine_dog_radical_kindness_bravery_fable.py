#!/usr/bin/env python3
"""
storyworlds/worlds/wolverine_dog_radical_kindness_bravery_fable.py
===================================================================

A tiny fable world about a wolverine, a dog, and a radical choice:
Kindness and Bravery can change how a forest quarrel ends.

The seed image is a short fable-like tale:
A stubborn wolverine guards a berry patch and growls at a friendly dog.
The dog is brave enough to return with an empty paw and a kind voice.
The wolverine expects a fight, but the dog offers help instead.
That radical kindness softens the wolverine, and the two share the patch.

World model:
- physical meters: hunger, fatigue, hurt, berry_count, pawprints, distance
- emotional memes: fear, anger, trust, kindness, bravery, pride, relief

The story is generated from actual state changes:
- guarding raises anger and fear
- a brave approach reduces distance and can lower fear
- kindness raises trust and relief
- sharing berries resolves hunger and ends the quarrel

This world keeps a classical fable shape:
setup -> test of manners -> turn -> moral ending
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
# Core world entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["hunger", "fatigue", "hurt", "berry_count", "pawprints", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "anger", "trust", "kindness", "bravery", "pride", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dog"}:
            return {"subject": "the dog", "object": "the dog", "possessive": "the dog's"}[case]
        if self.type in {"wolverine"}:
            return {"subject": "the wolverine", "object": "the wolverine", "possessive": "the wolverine's"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the berry grove"
    weather: str = "cool"
    affords: set[str] = field(default_factory=lambda: {"guard", "approach", "share"})


@dataclass
class StoryParams:
    name_wolverine: str
    name_dog: str
    setting: str = "grove"
    seed: Optional[int] = None


@dataclass
class Event:
    name: str
    detail: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
SETTING = Setting()

MORAL_LINES = [
    "Kindness can be braver than a growl.",
    "A gentle paw can open a stubborn heart.",
    "Radical kindness often changes what force cannot.",
]

# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def _log(world: World, name: str, detail: str) -> None:
    world.events.append(Event(name=name, detail=detail))


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    wolverine = world.add(Entity(
        id=params.name_wolverine,
        kind="character",
        type="wolverine",
        label=params.name_wolverine,
        traits=["stubborn", "small but fierce"],
    ))
    dog = world.add(Entity(
        id=params.name_dog,
        kind="character",
        type="dog",
        label=params.name_dog,
        traits=["friendly", "loyal"],
    ))
    berries = world.add(Entity(
        id="berries",
        type="thing",
        label="berry patch",
        phrase="a basket of ripe berries",
    ))
    world.facts.update(wolverine=wolverine, dog=dog, berries=berries)
    return world


def opening(world: World) -> None:
    w = world.facts["wolverine"]
    d = world.facts["dog"]
    b = world.facts["berries"]

    w.meters["hunger"] += 2
    w.memes["pride"] += 1
    d.memes["kindness"] += 1
    d.memes["bravery"] += 1
    b.meters["berry_count"] = 12

    world.say(
        f"In {world.setting.place}, {w.label} the wolverine guarded a patch of berries as if "
        f"the whole grove belonged to {w.label} alone."
    )
    world.say(
        f"{d.label} the dog came wandering near, tail high and eyes bright, hoping only to share the path."
    )
    _log(world, "setup", "wolverine guards berries; dog arrives kindly")


def guard_and_worry(world: World) -> None:
    w = world.facts["wolverine"]
    d = world.facts["dog"]
    w.memes["anger"] += 2
    w.memes["fear"] += 1
    w.meters["distance"] = 5

    world.say(
        f"{w.label} bristled and warned {d.label} to stay back. "
        f"That sharp warning made the little patch feel colder than the morning air."
    )
    world.say(
        f"{d.label} stopped at a respectful distance and waited, because a brave heart can also be patient."
    )
    _log(world, "guard", "anger rises; dog stays respectful")


def radical_turn(world: World) -> None:
    w = world.facts["wolverine"]
    d = world.facts["dog"]

    # The dog chooses radical kindness: no challenge, just a helpful offer.
    d.memes["kindness"] += 2
    d.memes["bravery"] += 1
    d.meters["pawprints"] += 1
    w.meters["distance"] = 1
    w.memes["trust"] += 1

    world.say(
        f"Then {d.label} did something radical: {d.label} lowered {d.label}'s head, "
        f"smiled softly, and pushed a few berries forward with an empty paw."
    )
    world.say(
        f'"I do not want your berries for myself," said {d.label}. "I only wanted to walk kindly."'
    )
    _log(world, "radical_kindness", "offer of help changes the mood")


def soften_and_share(world: World) -> None:
    w = world.facts["wolverine"]
    d = world.facts["dog"]
    b = world.facts["berries"]

    if d.memes["kindness"] >= 2 and d.memes["bravery"] >= 1:
        w.memes["anger"] = max(0.0, w.memes["anger"] - 2)
        w.memes["fear"] = max(0.0, w.memes["fear"] - 1)
        w.memes["trust"] += 2
        w.memes["relief"] += 2
        w.meters["berry_count"] -= 4
        d.meters["berry_count"] += 4
        w.meters["hunger"] = max(0.0, w.meters["hunger"] - 1)
        d.meters["hunger"] = max(0.0, d.meters["hunger"] - 1)

        world.say(
            f"{w.label} blinked at the kind offer, and the hard look in {w.label}'s face melted away."
        )
        world.say(
            f"At last, {w.label} nodded, and the two friends shared the berries until the patch looked lighter and friendlier."
        )
        _log(world, "share", "trust wins; berries are shared")
        b.meters["berry_count"] = max(0.0, b.meters["berry_count"] - 4)


def ending(world: World) -> None:
    w = world.facts["wolverine"]
    d = world.facts["dog"]
    if w.memes["trust"] > 0:
        world.say(
            f"By sunset, the wolverine sat beside the dog instead of against it, and the grove felt safe again."
        )
    else:
        world.say(
            f"By sunset, the dog still stood calmly by the berries, and the wolverine had not found a reason to growl."
        )
    world.say(f"Moral: {random.choice(MORAL_LINES)}")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    opening(world)
    world.para()
    guard_and_worry(world)
    radical_turn(world)
    soften_and_share(world)
    world.para()
    ending(world)
    world.facts["params"] = params
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short fable about {p.name_wolverine} the wolverine, {p.name_dog} the dog, and radical kindness.",
        f"Tell a child-friendly story in which a wolverine learns bravery from a dog and kindness changes the ending.",
        "Write a simple forest fable that includes the words wolverine, dog, radical, Kindness, and Bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    w = world.facts["wolverine"]
    d = world.facts["dog"]
    return [
        QAItem(
            question=f"Who guarded the berries at the start of the story?",
            answer=f"{w.label} the wolverine guarded the berries at the start, acting stubborn and protective.",
        ),
        QAItem(
            question=f"What did {d.label} do that was radical?",
            answer=f"{d.label} chose radical kindness: the dog lowered a paw, spoke gently, and offered help instead of a fight.",
        ),
        QAItem(
            question=f"How did the story end for {w.label} and {d.label}?",
            answer=f"They shared the berries, and the wolverine sat beside the dog in a calmer, friendlier grove.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, caring, and helpful toward someone else.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary even when you feel nervous.",
        ),
        QAItem(
            question="What does a dog often show by wagging its tail?",
            answer="A wagging tail often shows that a dog is happy, friendly, or excited.",
        ),
        QAItem(
            question="What does a wolverine usually seem like in a forest fable?",
            answer="A wolverine is often shown as a tough, fierce animal with a strong temper and a lot of energy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id} ({e.type}) meters={meters} memes={memes}")
    lines.append("events:")
    for ev in world.events:
        lines.append(f"  - {ev.name}: {ev.detail}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/2.

valid_story(W, D) :- wolverine(W), dog(D), radical_story(W, D).

radical_story(W, D) :- brave(D), kind(D), guards(W), shares(D), softens(W).

softens(W) :- trust(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("wolverine", "wolverine"))
    lines.append(asp.fact("dog", "dog"))
    lines.append(asp.fact("guards", "wolverine"))
    lines.append(asp.fact("brave", "dog"))
    lines.append(asp.fact("kind", "dog"))
    lines.append(asp.fact("shares", "dog"))
    lines.append(asp.fact("trust", "wolverine"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_reasonable() -> list[tuple[str, str]]:
    return [("wolverine", "dog")]


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(python_reasonable())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Parsing and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about a wolverine, a dog, and radical kindness.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name-wolverine", dest="name_wolverine")
    ap.add_argument("--name-dog", dest="name_dog")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name_wolverine = args.name_wolverine or rng.choice(["Wren", "Bruno", "Moss", "Talon", "Bram"])
    name_dog = args.name_dog or rng.choice(["Pip", "Sunny", "Clover", "Scout", "Puddle"])
    if name_wolverine == name_dog:
        raise StoryError("The wolverine and the dog need different names.")
    return StoryParams(name_wolverine=name_wolverine, name_dog=name_dog, setting="grove")


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid fable story pattern(s):")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name_wolverine="Wren", name_dog="Pip", setting="grove"),
            StoryParams(name_wolverine="Bruno", name_dog="Scout", setting="grove"),
            StoryParams(name_wolverine="Moss", name_dog="Clover", setting="grove"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_wolverine} and {p.name_dog}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
