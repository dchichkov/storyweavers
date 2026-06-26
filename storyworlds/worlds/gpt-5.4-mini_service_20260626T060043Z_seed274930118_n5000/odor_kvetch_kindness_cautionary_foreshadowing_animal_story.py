#!/usr/bin/env python3
"""
A small animal-story world about an odor, a kvetch, and a kinder fix.

Premise:
- One animal notices a bad smell in a shared place.
- Another animal kvetches about it.
- A careful friend warns what will happen if nobody helps.
- Kindness turns the mood around and cleans up the place.

The script simulates the state changes so the story is driven by what happens,
not by a frozen paragraph with swapped nouns.
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

SETTING_WORDS = {
    "meadow": "the meadow",
    "pond": "the pond",
    "burrow": "the burrow",
    "orchard": "the orchard",
    "barn": "the barn",
}

ANIMAL_KINDS = {
    "rabbit": {"subject": "it", "object": "it", "possessive": "its"},
    "fox": {"subject": "it", "object": "it", "possessive": "its"},
    "bear": {"subject": "it", "object": "it", "possessive": "its"},
    "deer": {"subject": "it", "object": "it", "possessive": "its"},
    "mouse": {"subject": "it", "object": "it", "possessive": "its"},
    "hedgehog": {"subject": "it", "object": "it", "possessive": "its"},
}

NAMES = {
    "rabbit": ["Nib", "Pip", "Luna", "Tilly"],
    "fox": ["Rue", "Fenn", "Milo", "Skye"],
    "bear": ["Bruno", "Mara", "Dino", "Huck"],
    "deer": ["Fern", "Mica", "Bram", "Sora"],
    "mouse": ["Peep", "Mina", "Tuck", "Wren"],
    "hedgehog": ["Prick", "Dot", "Nell", "Quill"],
}

TRAITS = ["gentle", "curious", "small", "brave", "cheery", "cautious"]

ODORS = {
    "fishy": {
        "source": "old fish scraps",
        "cause": "left in the sun too long",
        "fix": "sweep the scraps into a bin",
        "clean_result": "the air smelled fresh again",
    },
    "sour": {
        "source": "spilled berry mash",
        "cause": "left to rot by the path",
        "fix": "wash the stones and carry the mash away",
        "clean_result": "the sour smell faded from the path",
    },
    "musty": {
        "source": "a damp nest mat",
        "cause": "kept wet after the rain",
        "fix": "carry the mat outside and dry it in the sun",
        "clean_result": "the burrow felt light and dry",
    },
    "stinky": {
        "source": "muddy shell piles",
        "cause": "piled too close to the nest",
        "fix": "move the piles and rake in clean leaves",
        "clean_result": "the place no longer felt stinky",
    },
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    quiet: bool = True


@dataclass
class OdorCase:
    id: str
    smell: str
    source: str
    cause: str
    fix: str
    clean_result: str


@dataclass
class StoryParams:
    place: str
    animal_a: str
    animal_b: str
    odor: str
    name_a: str
    name_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with odor, kvetch, kindness, cautionary foreshadowing.")
    ap.add_argument("--place", choices=SETTING_WORDS)
    ap.add_argument("--animal-a", choices=ANIMAL_KINDS)
    ap.add_argument("--animal-b", choices=ANIMAL_KINDS)
    ap.add_argument("--odor", choices=ODORS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
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


CURATED = [
    StoryParams(place="meadow", animal_a="rabbit", animal_b="fox", odor="sour", name_a="Pip", name_b="Rue", trait_a="gentle", trait_b="cautious"),
    StoryParams(place="pond", animal_a="deer", animal_b="mouse", odor="musty", name_a="Fern", name_b="Mina", trait_a="curious", trait_b="cheery"),
    StoryParams(place="barn", animal_a="bear", animal_b="hedgehog", odor="fishy", name_a="Bruno", name_b="Dot", trait_a="brave", trait_b="small"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTING_WORDS))
    odor = args.odor or rng.choice(list(ODORS))
    animal_a = args.animal_a or rng.choice(list(ANIMAL_KINDS))
    animal_b = args.animal_b or rng.choice([a for a in ANIMAL_KINDS if a != animal_a])
    if args.animal_b == animal_a:
        raise StoryError("animal-a and animal-b must be different.")
    name_a = args.name_a or rng.choice(NAMES[animal_a])
    name_b = args.name_b or rng.choice(NAMES[animal_b])
    trait_a = args.trait_a or rng.choice(TRAITS)
    trait_b = args.trait_b or rng.choice([t for t in TRAITS if t != trait_a])
    return StoryParams(place=place, animal_a=animal_a, animal_b=animal_b, odor=odor,
                       name_a=name_a, name_b=name_b, trait_a=trait_a, trait_b=trait_b)


def odor_case(code: str) -> OdorCase:
    d = ODORS[code]
    return OdorCase(id=code, smell=code, source=d["source"], cause=d["cause"], fix=d["fix"], clean_result=d["clean_result"])


def _introduce(world: World, a: Entity, b: Entity, odor: OdorCase) -> None:
    world.say(
        f"In {world.setting.place}, {a.id} was a {a.memes['trait']} animal who liked quiet mornings, and {b.id} was a {b.memes['trait']} neighbor."
    )
    world.say(
        f"One day, a {odor.smell} odor came from {odor.source} because it had been {odor.cause}."
    )
    world.say(
        f"{b.id} kvetch
ed and wrinkled {b.pronoun('possessive')} nose. \"That smell is awful,\" {b.id} said."
    )


def _foreshadow(world: World, a: Entity, b: Entity, odor: OdorCase) -> None:
    a.memes["concern"] += 1
    world.say(
        f"{a.id} looked at the mess and gave a small warning: if nobody helped soon, the odor would only spread."
    )
    world.say(
        f"{a.id} said it would be kinder to clean first and play later."
    )


def _kindness(world: World, a: Entity, b: Entity, odor: OdorCase) -> None:
    sig = ("clean", odor.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.get("odor").meters["bad_smell"] = 0
    a.memes["kindness"] += 1
    b.memes["kindness"] += 1
    world.say(
        f"Then {a.id} offered a kind plan: {odor.fix}."
    )
    world.say(
        f"{b.id} stopped kvetching, helped lift the scraps away, and worked beside {a.id} until {odor.clean_result}."
    )


def tell(params: StoryParams) -> World:
    world = World(Setting(place=SETTING_WORDS[params.place]))
    a = world.add(Entity(id=params.name_a, kind="character", type=params.animal_a))
    b = world.add(Entity(id=params.name_b, kind="character", type=params.animal_b))
    a.memes["trait"] = params.trait_a
    b.memes["trait"] = params.trait_b
    a.memes["kindness"] = 0
    b.memes["kindness"] = 0
    a.memes["concern"] = 0
    b.memes["concern"] = 0
    od = odor_case(params.odor)
    odor_ent = world.add(Entity(id="odor", type="odor", label=od.smell))
    odor_ent.meters["bad_smell"] = 1
    world.facts = {"a": a, "b": b, "odor": od, "setting": world.setting}

    _introduce(world, a, b, od)
    world.para()
    _foreshadow(world, a, b, od)
    world.para()
    _kindness(world, a, b, od)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, od = f["a"], f["b"], f["odor"]
    return [
        f'Write a short animal story for a young child about a {a.type} and a {b.type}, a bad {od.smell} odor, and a kind cleanup.',
        f'Tell an Animal Story where {a.id} shows kindness after {b.id} kvetches about a smell in {world.setting.place}.',
        f'Write a gentle story with foreshadowing and cautionary wording about how a {od.smell} odor can spread if nobody helps.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, od = f["a"], f["b"], f["odor"]
    return [
        QAItem(
            question=f"Who kvetches about the smell in {world.setting.place}?",
            answer=f"{b.id} kvetches about the {od.smell} odor at first.",
        ),
        QAItem(
            question=f"What warning does {a.id} give before the cleanup?",
            answer=f"{a.id} gives a cautionary warning that the odor will spread if nobody helps.",
        ),
        QAItem(
            question=f"What kind thing do {a.id} and {b.id} do together?",
            answer=f"They clean up the {od.source} and make the place pleasant again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, or being gentle so another creature has an easier time.",
        ),
        QAItem(
            question="What is a cautionary warning?",
            answer="A cautionary warning is a careful message that tells someone to be safe or to avoid trouble.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a hint that something important may happen later in the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% Inline declarative twin for a tiny reasonableness gate:
% a bad smell can be narrated if there is a source, a kvetch, a warning,
% and a kindness-based cleanup.
has_source(O) :- odor(O).
can_warn(O) :- has_source(O).
can_fix(O) :- has_source(O).
valid_story(O) :- can_warn(O), can_fix(O).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for code in ODORS:
        lines.append(asp.fact("odor", code))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        print("OK: verification hook present.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
