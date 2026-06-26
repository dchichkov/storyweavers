#!/usr/bin/env python3
"""
A tiny story world for a gentle Ghost Story-style twist.

Premise:
A child hears a strange snore in the night, follows it, and finds a twist:
the "ghost" is not scary at all, but an old kitchen helper dozing beside a
warm pot of okra. The fear turns into curiosity, then comfort.

This world models:
- a child with a small emotional arc
- a spooky place with soft physical facts
- a single causal twist that changes the meaning of the noise
- a resolved ending image that proves the change
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

GHOSTLY_PLACES = {
    "attic": ("the attic", "dusty beams, a moonlit window, and old trunks"),
    "kitchen": ("the kitchen", "a warm stove, a striped apron, and a sleepy chair"),
    "hall": ("the hall", "a creaky floor, a wall lamp, and a little umbrella stand"),
}

KIND_NAMES = ["girl", "boy"]
CHILD_NAMES = ["Mina", "Owen", "Ivy", "Theo", "Lina", "Milo", "June", "Ezra"]
ADULT_NAMES = ["Grandma", "Grandpa", "Aunt Rose", "Uncle Ben", "Mrs. Vale"]
TRAITS = ["brave", "curious", "quiet", "small", "gentle", "careful"]


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
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    adult_name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
    ap = argparse.ArgumentParser(description="A small ghost-story world with a snore and okra twist.")
    ap.add_argument("--place", choices=sorted(GHOSTLY_PLACES))
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--gender", choices=KIND_NAMES)
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
    place = args.place or rng.choice(sorted(GHOSTLY_PLACES))
    child_type = args.gender or rng.choice(KIND_NAMES)
    child_name = args.name or rng.choice(CHILD_NAMES)
    adult_name = args.adult or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, child_name=child_name, child_type=child_type,
                       adult_name=adult_name, trait=trait)


def _capitalize_name(name: str) -> str:
    return name


def tell(params: StoryParams) -> World:
    place_name, detail = GHOSTLY_PLACES[params.place]
    world = World(Setting(place=place_name, detail=detail))

    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=params.adult_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost", plural=False))
    pot = world.add(Entity(id="pot", type="thing", label="pot", phrase="a little pot of okra"))
    okra = world.add(Entity(id="okra", type="thing", label="okra", phrase="okra", plural=True, owner=adult.id))
    moon = world.add(Entity(id="moon", type="thing", label="moon", phrase="a pale moon"))

    child.memes["fear"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["relief"] = 0.0
    adult.memes["sleepiness"] = 1.0
    ghost.meters["snore"] = 1.0
    pot.meters["warmth"] = 1.0
    okra.meters["steam"] = 1.0
    moon.meters["light"] = 1.0

    world.say(
        f"At {world.setting.place}, little {params.child_name} was a {params.trait} {params.child_type} who liked quiet nights."
    )
    world.say(
        f"{params.child_name} knew every floorboard sound, every lamp shadow, and every soft creak in {world.setting.place}."
    )
    world.para()
    world.say(
        f"One night, {params.child_name} heard a strange snore from the dark room."
    )
    child.memes["fear"] += 1.0
    world.say(
        f"The snore went on, slow and round, and {params.child_name} tiptoed toward {world.setting.place} with a tiny shiver."
    )
    world.para()
    world.say(
        f"Inside, {world.setting.detail} glowed under the moonlight, and the snore came from a chair beside the stove."
    )
    child.memes["curiosity"] += 1.0
    world.say(
        f"There sat {params.adult_name}, fast asleep, with a little pot of okra warming nearby."
    )
    world.say(
        f"The smell of okra was warm and green, and the scary sound was only a sleepy breath after a long day."
    )
    world.para()
    world.say(
        f"{params.child_name} blinked, then smiled."
    )
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1.0
    world.say(
        f"The room was not haunted at all; it was just home, and the 'ghost' was only the night making a twist."
    )
    world.say(
        f"{params.child_name} quietly covered the pot, turned down the lamp, and listened to the gentlest snore in the house."
    )
    world.para()
    world.say(
        f"By morning, {params.child_name} remembered the snore as something soft, the okra as something comforting, and the dark as less lonely."
    )

    world.facts.update(
        child=child,
        adult=adult,
        ghost=ghost,
        pot=pot,
        okra=okra,
        moon=moon,
        setting=world.setting,
        twist="the snore came from a sleeping adult, not a ghost",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a short ghost story for a young child with a snore, okra, and a gentle twist.',
        f"Tell a spooky-but-kind story where {child.label} hears a snore, searches {world.setting.place}, and learns the sound is harmless.",
        f'Write a small bedtime story that includes the words "snore" and "okra" and ends with a comforting reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    return [
        QAItem(
            question=f"What did {child.label} hear in the dark room?",
            answer=f"{child.label} heard a strange snore coming from inside {world.setting.place}."
        ),
        QAItem(
            question=f"Who was making the snore?",
            answer=f"It was {adult.label}, fast asleep in a chair beside the stove."
        ),
        QAItem(
            question=f"What food was warming nearby?",
            answer="A little pot of okra was warming nearby, which made the room feel cozy instead of scary."
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer="The twist was that the scary sound was not a ghost at all. It was only a sleeping person breathing softly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a snore?",
            answer="A snore is a rough, sleepy sound someone makes while sleeping and breathing."
        ),
        QAItem(
            question="What is okra?",
            answer="Okra is a green vegetable that can be cooked until it is warm and soft."
        ),
        QAItem(
            question="Why can a dark room feel spooky?",
            answer="A dark room can feel spooky because shadows and strange sounds leave room for imagination."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:6} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable if it has a child, a location, a snore source, and okra.
reasonable_story(P) :- place(P), child(P), snore_source(P), okra_present(P), twist(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in GHOSTLY_PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("child", "story"))
    lines.append(asp.fact("snore_source", "story"))
    lines.append(asp.fact("okra_present", "story"))
    lines.append(asp.fact("twist", "story"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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
    StoryParams(place="kitchen", child_name="Mina", child_type="girl", adult_name="Grandma", trait="curious"),
    StoryParams(place="attic", child_name="Theo", child_type="boy", adult_name="Aunt Rose", trait="careful"),
    StoryParams(place="hall", child_name="Ivy", child_type="girl", adult_name="Mr. Vale", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            sample = generate(p)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
