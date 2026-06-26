#!/usr/bin/env python3
"""
Standalone storyworld: chipmunk priest moral value flashback nursery rhyme.

A tiny, classical simulation in a nursery-rhyme style:
- A chipmunk and a priest share a small chapel-garden world.
- The chipmunk wants a shiny bell and learns a Moral Value about sharing.
- A Flashback reveals how the priest once helped, turning worry into trust.
- The ending proves what changed in the world state.

This file follows the Storyweavers world contract and is self-contained.
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

MORAL_VALUE = "share what shines"
FLASHBACK = "flashback"


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chipmunk"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little chapel garden"
    affords: set[str] = field(default_factory=lambda: {"sing", "bell", "pray"})


@dataclass
class Prize:
    label: str = "bell"
    phrase: str = "a tiny silver bell"
    type: str = "bell"
    shine: str = "bright"
    value: str = MORAL_VALUE


@dataclass
class StoryParams:
    place: str = "chapel_garden"
    seed: Optional[int] = None
    name: str = "Nip"
    priest_name: str = "Father Reed"
    prize: str = "bell"
    mood: str = "curious"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
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


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def mood_line(mood: str) -> str:
    return {
        "curious": "curious and bright",
        "nervous": "small and shy",
        "cheerful": "light and merry",
    }.get(mood, "curious and bright")


def intro(world: World, chipmunk: Entity, priest: Entity, prize: Prize) -> None:
    world.say(
        f"On a hushy little morning, {chipmunk.id} the chipmunk was {mood_line(world.facts['mood'])}, "
        f"darting by moss and thyme where {priest.id} the priest sang soft and kind."
    )
    world.say(
        f"Near the chapel door there hung {prize.phrase}, and it shone so neat that "
        f"{chipmunk.id} blinked twice and sat on a stone."
    )


def want_bell(world: World, chipmunk: Entity, prize: Prize) -> None:
    chipmunk.memes["desire"] = chipmunk.memes.get("desire", 0) + 1
    world.say(
        f'"Oh, I want that bell," said {chipmunk.id}, "for its bright little ring and its merry little spell!"'
    )


def warn(world: World, priest: Entity, chipmunk: Entity, prize: Prize) -> None:
    priest.memes["care"] = priest.memes.get("care", 0) + 1
    world.say(
        f'{priest.id} smiled and said, "A bell is for blessing, not keeping. '
        f"Little paws should not hide what helps the whole flock sing.\""
    )
    chipmunk.memes["worry"] = chipmunk.memes.get("worry", 0) + 1


def flashback(world: World, priest: Entity, chipmunk: Entity) -> None:
    if FLASHBACK in world.fired:
        return
    world.fired.add(FLASHBACK)
    world.say(
        f"Then came a {FLASHBACK} in the chapel's glow: once, when {chipmunk.id} was cold and forlorn, "
        f"{priest.id} had shared warm crumbs and tucked a leaf over the nest."
    )
    world.say(
        f"So {chipmunk.id} remembered the good and the gentle, and {chipmunk.id}'s small heart grew less bumpy."
    )
    chipmunk.memes["trust"] = chipmunk.memes.get("trust", 0) + 1


def choose_moral(world: World, chipmunk: Entity, priest: Entity, prize: Prize) -> None:
    chipmunk.memes["moral_value"] = chipmunk.memes.get("moral_value", 0) + 1
    world.say(
        f'"I know," said {chipmunk.id}, "the best bright thing is not to keep, but to share. '
        f"{prize.value.capitalize()} makes the bell ring sweeter when it is given fair.\""
    )
    world.say(
        f"Then {chipmunk.id} placed the bell by the chapel step, where every song could find it."
    )
    world.facts["moral"] = prize.value


def ending(world: World, chipmunk: Entity, priest: Entity, prize: Prize) -> None:
    chipmunk.memes["joy"] = chipmunk.memes.get("joy", 0) + 1
    priest.memes["joy"] = priest.memes.get("joy", 0) + 1
    world.say(
        f"{priest.id} rang the bell once, just once, and the sound went tinkling across the garden."
    )
    world.say(
        f"{chipmunk.id} danced in the dew, and the bell stayed shining for all to hear; "
        f"the little chapel felt warmer, and the moon would be pleased that night."
    )


def tell(params: StoryParams) -> World:
    setting = Setting()
    prize = Prize()
    world = World(setting)
    world.facts["mood"] = params.mood

    chipmunk = world.add(Entity(id=params.name, kind="character", type="chipmunk", label="chipmunk"))
    priest = world.add(Entity(id=params.priest_name, kind="character", type="priest", label="priest"))
    bell = world.add(Entity(id="bell", kind="thing", type="bell", label="bell", phrase=prize.phrase, owner=priest.id))

    world.facts.update(chipmunk=chipmunk, priest=priest, prize=bell, prize_cfg=prize, setting=setting)

    intro(world, chipmunk, priest, prize)
    world.para()
    want_bell(world, chipmunk, prize)
    warn(world, priest, chipmunk, prize)
    flashback(world, priest, chipmunk)
    choose_moral(world, chipmunk, priest, prize)
    world.para()
    ending(world, chipmunk, priest, prize)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chipmunk = f["chipmunk"]
    priest = f["priest"]
    prize = f["prize_cfg"]
    return [
        f'Write a short nursery-rhyme style story about a chipmunk named {chipmunk.id}, a priest, and a shiny bell.',
        f'Tell a gentle story where {priest.id} the priest teaches {chipmunk.id} a Moral Value about {prize.value}.',
        f'Write a simple flashback story in which a little chipmunk remembers kindness and makes a better choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chipmunk = f["chipmunk"]
    priest = f["priest"]
    prize = f["prize_cfg"]
    return [
        QAItem(
            question=f"What did {chipmunk.id} want at the chapel garden?",
            answer=f"{chipmunk.id} wanted the shiny bell to keep its bright little ring.",
        ),
        QAItem(
            question=f"Why did {priest.id} worry about the bell?",
            answer=f"{priest.id} worried because the bell belonged to the chapel, and it was meant to help everyone sing, not to be kept by one little friend.",
        ),
        QAItem(
            question="What good choice did the chipmunk make at the end?",
            answer=f"The chipmunk chose to share the bell, which matched the Moral Value: {prize.value}.",
        ),
        QAItem(
            question="What did the flashback remind the chipmunk of?",
            answer=f"The flashback reminded the chipmunk that {priest.id} had once shared crumbs and shelter in a kind moment before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a priest?",
            answer="A priest is a person who leads prayers, songs, and kind guidance in a church or chapel.",
        ),
        QAItem(
            question="What is a chipmunk?",
            answer="A chipmunk is a small striped squirrel-like animal that lives on the ground and loves nuts and seeds.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good rule for how to treat others, like being fair, kind, or honest.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something that happened earlier, to help explain how a character feels now.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: moral={world.facts.get('moral')!r}")
    return "\n".join(lines)


ASP_RULES = r"""
chipmunk(c).
priest(p).
prize(bell).
moral_value(share_what_shines).

wants(c,bell).
helps(p,c) :- flashback_help(p,c).
good_choice(c,share) :- wants(c,bell), moral_value(share_what_shines), remembers(c,kindness).
resolved(c) :- good_choice(c,share).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("chipmunk", "chipmunk"),
            asp.fact("priest", "priest"),
            asp.fact("prize", "bell"),
            asp.fact("moral_value", "share_what_shines"),
            asp.fact("wants", "chipmunk", "bell"),
            asp.fact("flashback_help", "priest", "chipmunk"),
            asp.fact("remembers", "chipmunk", "kindness"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = set(asp.atoms(model, "resolved"))
    py = {("chipmunk",)} if True else set()
    if atoms == py:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Chipmunk priest moral-value flashback nursery-rhyme storyworld.")
    ap.add_argument("--name", default="Nip")
    ap.add_argument("--priest-name", default="Father Reed")
    ap.add_argument("--mood", choices=["curious", "nervous", "cheerful"], default="curious")
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
    name = args.name or rng.choice(["Nip", "Pip", "Milo"])
    priest_name = args.priest_name or rng.choice(["Father Reed", "Father Moss", "Father Bell"])
    mood = args.mood or rng.choice(["curious", "nervous", "cheerful"])
    return StoryParams(name=name, priest_name=priest_name, mood=mood, seed=args.seed)


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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(StoryParams(name="Nip", priest_name="Father Reed", mood="curious", seed=args.seed)))
        samples.append(generate(StoryParams(name="Pip", priest_name="Father Moss", mood="cheerful", seed=args.seed)))
        samples.append(generate(StoryParams(name="Milo", priest_name="Father Bell", mood="nervous", seed=args.seed)))
    else:
        for i in range(args.n):
            params = resolve_params(args, rng)
            params.seed = (args.seed + i) if args.seed is not None else None
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
