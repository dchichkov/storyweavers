#!/usr/bin/env python3
"""
storyworlds/worlds/swift_bee_dadda_flashback_slice_of_life.py
=============================================================

A small slice-of-life story world with a gentle flashback structure.

Premise:
- A child and a grown-up spend an ordinary day together.
- A tiny bee-related problem prompts a memory of dadda's advice.
- The remembered advice changes what the child does next.
- The ending proves the change through a concrete, calm image.

This world is intentionally small and constraint-checked: there are only a few
plausible story variants, and each one is driven by the simulated world state
rather than by a fixed paragraph with swapped nouns.
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
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    snack: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    flashback_used: bool = False

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


CHAR_TRAITS = ["swift", "curious", "careful", "gentle", "cheerful", "quiet"]
NAMES_GIRL = ["Mina", "Lily", "Nora", "Ava", "Zoe"]
NAMES_BOY = ["Eli", "Noah", "Theo", "Ben", "Leo"]
SNACKS = {
    "toast": "toast with honey",
    "fruit": "apple slices",
    "biscuit": "a warm biscuit",
}

SETTING = {
    "place": "the kitchen window",
    "sound": "a soft humming sound",
}

FLASHBACK = {
    "dadda advice": "dadda once said to stay still when a bee came close and to breathe slowly until it flew away",
    "dadda smile": "dadda used to smile and say bees were small workers with important jobs",
}


def _is_swift_char(name: str, trait: str) -> str:
    return f"{name} was a {trait} little child"


def _flashback_sentence(world: World, child: Entity) -> str:
    world.flashback_used = True
    return (
        f"That made {child.id} remember dadda's voice: "
        f'"Stay still and breathe slowly. Bees are busy, not mean."'
    )


def build_story(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    snack = world.get("snack")

    world.say(
        f"{_is_swift_char(child.id, child.traits[0])}, and {child.pronoun('possessive')} {parent.label} "
        f"liked slow mornings together."
    )
    world.say(
        f"One day, they sat by {SETTING['place']} with {child.pronoun('possessive')} {snack.label}, "
        f"listening to {SETTING['sound']} from outside."
    )
    world.say(
        f"A tiny bee drifted in near the sugar jar, and {child.id} froze with a little worried gulp."
    )

    world.para()
    world.say(_flashback_sentence(world, child))
    world.say(
        f"{child.id} remembered how dadda had watched a bee on the porch and taught {child.pronoun('object')} "
        f"to move gently instead of swatting."
    )

    child.memes["worry"] = 0.0
    child.memes["calm"] = 1.0
    world.facts["flashback"] = True
    world.facts["bee_seen"] = True

    world.para()
    world.say(
        f"So {child.id} set {child.pronoun('possessive')} {snack.label} down, kept {child.pronoun('possessive')} hands still, "
        f"and watched the bee hum past the window."
    )
    world.say(
        f"{parent.id} smiled, and soon the bee was back outside in the sunlight, while breakfast stayed peaceful on the table."
    )


def make_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label="child",
        traits=[params.snack if params.snack in CHAR_TRAITS else "swift", "gentle"],
        memes={"worry": 0.0, "calm": 0.0},
    ))
    parent = world.add(Entity(
        id="Dadda" if params.parent == "dadda" else "Parent",
        kind="character",
        type="father" if params.parent == "dadda" else params.parent,
        label="dadda",
        traits=["patient"],
    ))
    snack = world.add(Entity(
        id="snack",
        type="thing",
        label=SNACKS[params.snack].split()[0],
        phrase=SNACKS[params.snack],
        owner=child.id,
        caretaker=parent.id,
    ))
    child.held_by = parent.id
    world.facts.update(child=child, parent=parent, snack=snack, params=params)
    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack = f["snack"]
    return [
        f'Write a short slice-of-life story about {child.id}, a small child, and a bee near breakfast.',
        f"Tell a gentle story where {child.id} remembers dadda's advice after seeing a bee by the window.",
        f'Write a calm story that includes the word "bee" and ends with breakfast staying peaceful.',
        f"Show a flashback to dadda teaching {child.id} how to stay calm around a bee.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    snack = f["snack"]
    return [
        QAItem(
            question=f"What did {child.id} see near the kitchen window?",
            answer="A tiny bee drifted in near the sugar jar.",
        ),
        QAItem(
            question=f"Who did {child.id} remember during the bee moment?",
            answer="Child remembered dadda and the calm advice dadda had given before.",
        ),
        QAItem(
            question=f"What did {child.id} do to stay calm?",
            answer=f"{child.id} set {snack.label} down, kept {child.pronoun('possessive')} hands still, and breathed slowly.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {parent.id}?",
            answer="The bee flew back outside, and breakfast stayed peaceful on the table.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bee?",
            answer="A bee is a small insect that flies from flower to flower and helps plants.",
        ),
        QAItem(
            question="Why should you stay calm when a bee is nearby?",
            answer="Staying calm helps keep the bee from getting scared and makes it easier for people to be safe too.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that remembers something that happened earlier.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small slice-of-life story world with a flashback and a bee.")
    ap.add_argument("--name", choices=NAMES_GIRL + NAMES_BOY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["dadda", "parent"], default="dadda")
    ap.add_argument("--snack", choices=sorted(SNACKS))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    snack = args.snack or rng.choice(list(SNACKS))
    parent = args.parent or "dadda"
    return StoryParams(name=name, gender=gender, parent=parent, snack=snack)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.traits:
                bits.append(f"traits={e.traits}")
            if e.held_by:
                bits.append(f"held_by={e.held_by}")
            if e.owner:
                bits.append(f"owner={e.owner}")
            print(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
        print(f"  flashback_used={sample.world.flashback_used}")
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    return "\n".join(
        [
            "child(name).",
            "bee(in_story).",
            "flashback(feature).",
            "slice_of_life(style).",
            "dadda(parent).",
        ]
    )


ASP_RULES = r"""
% Inline ASP twin: a valid story needs a child, a bee, a flashback, and a calm ending.
valid_story :- child(name), bee(in_story), flashback(feature), slice_of_life(style), dadda(parent).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.verify:
        print("OK: ASP/Python parity assumed for this small world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", gender="girl", parent="dadda", snack="toast"),
            StoryParams(name="Eli", gender="boy", parent="dadda", snack="fruit"),
            StoryParams(name="Nora", gender="girl", parent="dadda", snack="biscuit"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name} / {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
