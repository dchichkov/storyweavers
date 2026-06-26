#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/salamander_excitement_eyed_quest_repetition_heartwarming.py
================================================================================================

A heartwarming story world about a child on a small Quest to help a tiny salamander.
The domain is built around repetition, noticing, gentle care, and a soft payoff:
the child learns to look, wait, and return the salamander safely to its home.

Seed words: salamander, excitement, eyed
Features: Quest, Repetition
Style: Heartwarming
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


@dataclass
class Creature:
    id: str
    kind: str = "animal"
    type: str = "salamander"
    label: str = "salamander"
    phrase: str = "a tiny salamander"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Person:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = "child"
    phrase: str = "a curious child"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    helps: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: Place
    child: Person
    salamander: Creature
    quest_item: QuestItem
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    place: str
    quest_item: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(id="garden", label="the garden", phrase="a quiet garden with soft leaves"),
    "pond": Place(id="pond", label="the pond", phrase="a little pond under reeds and stones"),
    "woods": Place(id="woods", label="the woods", phrase="a leafy path beside mossy logs"),
}

QUEST_ITEMS = {
    "lantern": QuestItem(id="lantern", label="lantern", phrase="a tiny lantern", helps="see carefully"),
    "bucket": QuestItem(id="bucket", label="bucket", phrase="a small bucket", helps="carry water gently"),
    "journal": QuestItem(id="journal", label="journal", phrase="a little journal", helps="write down clues"),
}

NAMES = ["Maya", "Nora", "Eli", "Leo", "Ava", "Iris", "Theo", "Lumi"]


class WorldStateError(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming salamander Quest with repetition and careful noticing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--name", choices=NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    quest_item = args.quest_item or rng.choice(list(QUEST_ITEMS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, quest_item=quest_item, name=name)


def heartwarming_intro(world: World) -> None:
    c = world.child
    p = world.place
    s = world.salamander
    world.say(
        f"{c.id} loved quiet walks in {p.label}, where little surprises sometimes waited under leaves."
    )
    world.say(
        f"One morning, {c.id} eyed a tiny salamander near a cool stone and felt a burst of excitement."
    )
    world.say(
        f"{c.id} did not shout. {c.id} only smiled, because the salamander looked small and shy."
    )
    world.facts["intro_seen"] = True
    world.facts["eye_word"] = "eyed"
    world.facts["emotion"] = "excitement"
    world.facts["creature"] = s


def quest_turn(world: World) -> None:
    c = world.child
    s = world.salamander
    q = world.quest_item
    world.para()
    world.say(
        f"{c.id} began a little Quest: find a safe way to help the salamander back home."
    )
    world.say(
        f"With the {q.label}, {c.id} could {q.helps}, then look again, then look once more."
    )
    world.say(
        f"That Repetition helped {c.id} stay calm, even when the salamander slipped behind a fern."
    )
    world.facts["quest_started"] = True
    world.facts["repetition"] = 3
    world.facts["quest_item"] = q
    world.facts["salamander"] = s


def gentle_search(world: World) -> None:
    c = world.child
    s = world.salamander
    world.say(
        f"{c.id} peeked under one leaf, then another leaf, and then the same stone again."
    )
    world.say(
        f"At last, the salamander blinked its shiny eyes and stayed very still, as if waiting to be understood."
    )
    s.memes["trust"] = s.memes.get("trust", 0.0) + 1.0
    c.memes["care"] = c.memes.get("care", 0.0) + 1.0
    world.facts["found"] = True


def resolution(world: World) -> None:
    c = world.child
    p = world.place
    s = world.salamander
    q = world.quest_item
    world.para()
    world.say(
        f"{c.id} made a tiny path with a stick and a leaf, then guided the salamander toward the damp corner of {p.label}."
    )
    world.say(
        f"The salamander went safely home, and {c.id} felt warm inside because the Quest had ended kindly."
    )
    world.say(
        f"{q.label.capitalize()} rested in {c.id}'s hand, no longer needed for searching, only for remembering."
    )
    world.facts["resolved"] = True
    world.facts["ending_image"] = "salamander home, child smiling"


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest_item = QUEST_ITEMS[params.quest_item]
    child = Person(id=params.name, label="child", phrase=f"{params.name}, a gentle child")
    salamander = Creature(id="salamander")
    world = World(place=place, child=child, salamander=salamander, quest_item=quest_item)
    heartwarming_intro(world)
    quest_turn(world)
    gentle_search(world)
    resolution(world)
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUEST_ITEMS:
        lines.append(asp.fact("quest_item", qid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Q) :- place(P), quest_item(Q).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, q) for p in PLACES for q in QUEST_ITEMS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a heartwarming story about a child named {world.child.id} who eyed a salamander and felt excitement.',
        f"Tell a small Quest story where {world.child.id} uses a {world.quest_item.label} to help a salamander safely.",
        f'Write a gentle story with Repetition, where "{world.salamander.label}" appears and the ending feels warm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.child
    p = world.place
    q = world.quest_item
    return [
        QAItem(
            question=f"What did {c.id} do when they first saw the salamander at {p.label}?",
            answer=f"{c.id} eyed the salamander and felt excitement, but stayed quiet and careful."
        ),
        QAItem(
            question=f"What was the Quest in the story?",
            answer=f"The Quest was to help the salamander get safely back to the damp place it liked."
        ),
        QAItem(
            question=f"How did the {q.label} help during the Repetition of searching?",
            answer=f"The {q.label} helped {c.id} look carefully again and again without rushing."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the salamander safely home and {c.id} feeling warm and happy."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salamander?",
            answer="A salamander is a small amphibian, often found in damp places like leaf litter, moss, or near water."
        ),
        QAItem(
            question="What does excitement mean?",
            answer="Excitement is a strong happy feeling that makes someone eager to see what will happen next."
        ),
        QAItem(
            question="Why can repetition help someone learn or stay calm?",
            answer="Repetition can help because doing something again and again makes it easier to remember and can feel steady and safe."
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
    lines.append(f"place={world.place.label}")
    lines.append(f"child={world.child.id}")
    lines.append(f"salamander_trust={world.salamander.memes.get('trust', 0.0)}")
    lines.append(f"child_care={world.child.memes.get('care', 0.0)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", quest_item="journal", name="Maya"),
    StoryParams(place="pond", quest_item="lantern", name="Eli"),
    StoryParams(place="woods", quest_item="bucket", name="Nora"),
]


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos:")
        for p, q in combos:
            print(f"  {p} / {q}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
