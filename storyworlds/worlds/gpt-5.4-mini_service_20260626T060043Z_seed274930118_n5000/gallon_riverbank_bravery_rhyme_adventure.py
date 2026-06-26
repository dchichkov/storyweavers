#!/usr/bin/env python3
"""
A small story world for a riverbank adventure with a gallon jug, bravery, and rhyme.

Premise:
A child must carry a gallon of water across a riverbank path to help a thirsty garden,
but the path is windy and the jug is heavy. The child uses bravery to keep going and
sings a rhyme to stay steady. A helper suggests a smarter route and the story ends
with the gallon delivered safely.
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

# World constants
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    place: str = "riverbank"
    seed: Optional[int] = None


CHARACTER_NAMES = {
    "girl": ["Mina", "Lena", "Ivy", "Rosa", "Nia", "Tara"],
    "boy": ["Eli", "Nico", "Finn", "Owen", "Milo", "Jasper"],
    "helper": ["Aunt", "Uncle", "Grandpa", "Grandma"],
}

RIVERBANK_DETAILS = [
    "The riverbank path was bright with stones and bent grass.",
    "A breeze slid over the water and made the reeds whisper.",
    "The shore dipped and rose in little bumps, like a sleepy trail.",
]

RHYMES = [
    "Step by step, keep the jug still, brave feet can cross the hill.",
    "Left foot, right foot, slow and true, the water stays if you do.",
    "Hush, jug, hush; hold tight, heart. Brave rhymes help when paths are hard.",
]


class StoryState:
    def __init__(self, world: World) -> None:
        self.world = world

    def child(self) -> Entity:
        return self.world.get("child")

    def helper(self) -> Entity:
        return self.world.get("helper")

    def gallon(self) -> Entity:
        return self.world.get("gallon")


def setup_world(params: StoryParams) -> World:
    world = World(place=params.place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"tired": 0.0},
        memes={"bravery": 0.0, "worry": 0.0, "joy": 0.0, "rhythm": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="helper",
        label=params.helper,
        meters={"work": 0.0},
        memes={"care": 0.0},
    ))
    gallon = world.add(Entity(
        id="gallon",
        kind="thing",
        type="jug",
        label="gallon jug",
        phrase="a heavy gallon jug of water",
        owner=child.id,
        caretaker=helper.id,
        meters={"full": 1.0, "heavy": 1.0, "safe": 0.0},
    ))
    world.facts.update(child=child, helper=helper, gallon=gallon)
    return world


def intro(world: World) -> None:
    child = world.get("child")
    gallon = world.get("gallon")
    world.say(
        f"{child.label} was a small adventurous child who loved wide-open paths and windy places."
    )
    world.say(
        f"One morning, {child.label} had to carry {gallon.phrase} along the {world.place}."
    )
    world.say(random.choice(RIVERBANK_DETAILS))


def tension(world: World) -> None:
    child = world.get("child")
    gallon = world.get("gallon")
    child.memes["worry"] += 1.0
    child.meters["tired"] += 1.0
    world.say(
        f"The jug felt heavy in {child.pronoun('possessive')} hands, and the breeze kept nudging {gallon.it()}."
    )
    world.say(
        f"{child.label} could feel {child.pronoun('possessive')} knees wobble, but {child.pronoun()} did not want to stop."
    )


def bravery_turn(world: World) -> None:
    child = world.get("child")
    child.memes["bravery"] += 1.0
    world.say(
        f"{child.label} took one deep breath and remembered to be brave."
    )
    world.say(
        f"Bravery did not make the jug lighter, but it made the next step feel possible."
    )


def rhyme_help(world: World) -> None:
    child = world.get("child")
    child.memes["rhythm"] += 1.0
    rhyme = random.choice(RHYMES)
    world.say(
        f"Then {child.label} hummed a rhyme: “{rhyme}”"
    )
    world.say(
        f"The little song gave {child.pronoun('object')} a steady rhythm, and the water stopped sloshing so wildly."
    )


def helper_offer(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    gallon = world.get("gallon")
    helper.memes["care"] += 1.0
    world.say(
        f"{helper.label} saw the wobble and pointed to a flatter line of stones near the bank."
    )
    world.say(
        f'"Take the safe side," {helper.label.lower()} said. "We can protect the gallon by moving slowly together."'
    )
    gallon.meters["safe"] = 1.0


def resolve(world: World) -> None:
    child = world.get("child")
    gallon = world.get("gallon")
    child.meters["tired"] = max(0.0, child.meters["tired"] - 0.5)
    child.memes["joy"] += 1.0
    world.say(
        f"{child.label} followed the flatter stones, kept the rhyme going, and held the jug close."
    )
    world.say(
        f"At last, {child.label} reached the garden gate with the gallon still full enough to pour."
    )
    world.say(
        f"{child.label} smiled as the water splashed into the waiting bucket, and the riverbank felt like an adventure well won."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    tension(world)
    bravery_turn(world)
    rhyme_help(world)
    helper_offer(world)
    world.para()
    resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.get("child")
    return [
        f"Write a short adventure story for young children about {child.label} carrying a gallon jug along a riverbank.",
        "Tell a gentle story where bravery and a rhyme help someone finish a hard but safe journey.",
        "Write a simple riverbank adventure with a heavy gallon, a worried child, and a helpful turn at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    helper = world.get("helper")
    return [
        QAItem(
            question=f"Who carried the gallon jug in the story?",
            answer=f"{child.label} carried the gallon jug along the riverbank.",
        ),
        QAItem(
            question=f"What helped {child.label} keep going when the jug felt heavy?",
            answer=f"Bravery helped {child.label} keep going, and the rhyme gave {child.pronoun('object')} a steady rhythm.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} pointed out a flatter path and told {child.label} to move slowly on the safe side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gallon?",
            answer="A gallon is a unit for measuring liquids, like water or milk.",
        ),
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land beside a river.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means being afraid or uncertain but choosing to keep going anyway.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line of words that sound nice together, often with matching ending sounds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A gallon journey is reasonable if there is a child, a gallon, and a helper.
story(child,gallon,helper) :- child(child), gallon(gallon), helper(helper).

% The gallon is safe when the helper offers the flatter path and the child uses it.
safe(gallon) :- offered_flat_path(helper), followed_path(child), story(child,gallon,helper).

% Bravery and rhyme are the emotional tools that let the child continue.
steady(child) :- bravery(child), rhyme(child).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child", "child"),
        asp.fact("gallon", "gallon"),
        asp.fact("helper", "helper"),
        asp.fact("bravery", "child"),
        asp.fact("rhyme", "child"),
        asp.fact("offered_flat_path", "helper"),
        asp.fact("followed_path", "child"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe/1.\n#show steady/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    expected = {("safe", ("gallon",)), ("steady", ("child",))}
    if atoms == expected:
        print("OK: ASP and Python reasonableness match.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Riverbank adventure story world with a gallon jug, bravery, and rhyme.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=CHARACTER_NAMES["helper"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHARACTER_NAMES[gender])
    helper = args.helper or rng.choice(CHARACTER_NAMES["helper"])
    return StoryParams(name=name, gender=gender, helper=helper, seed=args.seed)


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


CURATED = [
    StoryParams(name="Mina", gender="girl", helper="Aunt"),
    StoryParams(name="Eli", gender="boy", helper="Grandpa"),
    StoryParams(name="Ivy", gender="girl", helper="Grandma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe/1.\n#show steady/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe/1.\n#show steady/1."))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
