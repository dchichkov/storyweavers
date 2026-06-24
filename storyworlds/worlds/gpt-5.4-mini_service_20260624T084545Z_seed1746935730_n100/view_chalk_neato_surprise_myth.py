#!/usr/bin/env python3
"""
A tiny mythic storyworld about a hillside view, a chalk mark, and a surprising reveal.

The seed tale:
- A child hikes to a windy lookout and carries a piece of chalk.
- They love drawing a tiny sign that says "neato" on a stone wall.
- A cloud or curtain of mist hides the view.
- The child tries to make the place feel special anyway.
- A surprise reveals something beautiful: the chalk mark becomes a guide, and the view opens.

This world simulates:
- a place with physical features (meters)
- a character with feelings (memes)
- a hidden or revealed view
- chalk that can mark stone, point a path, or be shared
- a surprise turn that changes what the child sees and feels

The prose is intended to read like a small myth: concrete, a little formal, and gently wondrous.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill"
    has_view: bool = True
    misty: bool = True


@dataclass
class StoryEvent:
    name: str
    text: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(copy.deepcopy(self.setting))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "hill": Setting(place="the hill", has_view=True, misty=True),
    "cliff": Setting(place="the cliff", has_view=True, misty=True),
    "tower": Setting(place="the old tower", has_view=True, misty=True),
    "valley": Setting(place="the valley path", has_view=True, misty=False),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Mara", "Tess", "Aria"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Finn", "Max", "Jules", "Pax"]
PARENTS = ["mother", "father"]

ASP_RULES = r"""
% If the place has a view and mist hides it, the view is not clear.
clear_view(P) :- place(P), has_view(P), not misty(P).
hidden_view(P) :- place(P), has_view(P), misty(P).

% Chalk can make a sign.
has_sign(C) :- chalk(C), marked(C).

% A surprise happens when the child marks the stone and the view opens.
surprised(C, P) :- child(C), place(P), marked_chalk(C), hidden_view(P), reveal(P).

% The story is valid when the child starts with wonder, meets the hidden view,
% makes a chalk mark, and ends with the surprise reveal.
valid_story(P, C) :- child(C), place(P), has_view(P), marked_chalk(C), reveal(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.has_view:
            lines.append(asp.fact("has_view", pid))
        if setting.misty:
            lines.append(asp.fact("misty", pid))
    lines.append(asp.fact("chalk", "chalk"))
    lines.append(asp.fact("child", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "chalk") for place in SETTINGS if SETTINGS[place].has_view]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of view, chalk, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    return [
        f'Write a short mythic story for a child named {hero.id} about a hidden view, chalk, and a surprise at {setting.place}.',
        f"Tell a gentle legend where {hero.id} brings chalk to {setting.place}, sees a hidden view, and finds something neato.",
        f'Write a simple story that includes the word "neato" and ends with a surprising view opening at {setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    chalk: Entity = world.facts["chalk"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {parent.pronoun('object')} who came along for the walk.",
        ),
        QAItem(
            question=f"What did {hero.id} do with the chalk?",
            answer=f"{hero.id} used the chalk to make a small mark on the stone and point toward the view.",
        ),
        QAItem(
            question=f"What surprise changed the day at {setting.place}?",
            answer=f"A surprise opening in the mist revealed the view, and that made the little chalk sign feel neato.",
        ),
    ]
    if world.facts.get("surprise"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel after the surprise?",
                answer=f"{hero.id} felt proud and amazed, because the chalk mark helped the hidden place become beautiful instead of plain.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chalk?",
            answer="Chalk is a soft white or colored stick that makes marks on stone, boards, and sidewalks.",
        ),
        QAItem(
            question="What does a view mean?",
            answer="A view is what you can see when you look out across a place, like hills, water, or sky.",
        ),
        QAItem(
            question="What does neato mean?",
            answer='"Neato" is a playful word people can say when something seems neat, fun, or cool.',
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect, so it makes a moment feel sudden and special.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


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


def valid_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    chalk = world.add(Entity(id="chalk", type="chalk", label="chalk", phrase="a small piece of chalk"))
    world.facts.update(hero=hero, parent=parent, chalk=chalk, setting=setting)
    return world


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    chalk: Entity = world.facts["chalk"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]

    hero.memes["wonder"] = 1
    world.say(
        f"Long ago, {hero.id} climbed {setting.place} with {hero.pronoun('possessive')} {parent.type}, "
        f"and the air felt old as a song."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} chalk like a tiny torch and looked out for the view."
    )
    world.para()
    hero.memes["desire"] = 1
    world.say(
        f"But the mist hid the far hills, so the view stayed folded away."
    )
    world.say(
        f'{hero.id} said, "That is not very neato," and tapped the chalk against the stone.'
    )
    chalk.meters["marked"] = 1
    hero.meters["mark"] = 1
    world.say(
        f"{hero.id} drew one bright line, then another, and the marks formed a little path of hope."
    )
    world.para()
    hero.memes["patience"] = 1
    world.say(
        f"Then the wind shifted, and the mist opened like a curtain."
    )
    world.say(
        f"All at once, the hidden view appeared, wide and shining, as if the hill had been waiting to show it."
    )
    hero.memes["surprise"] = 1
    hero.memes["joy"] = 1
    world.facts["surprise"] = True
    world.say(
        f"{hero.id} stared, smiling, because the chalk sign looked neato beside the bright new view."
    )


def generate(params: StoryParams) -> StorySample:
    world = valid_story_world(params)
    tell(world)
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
    StoryParams(place="hill", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="cliff", name="Theo", gender="boy", parent="father"),
    StoryParams(place="tower", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, child in stories:
            print(f"  {place:8} {child}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
