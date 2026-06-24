#!/usr/bin/env python3
"""
A tiny story world: persona-driven nap-room ghost story with foreshadowing.

Premise:
- A child in the nap room feels uneasy because little clues keep hinting that
  something unseen is nearby.
- The tension grows through soft sounds, shifting light, and a favorite object
  that goes missing.
- The turn reveals that the "ghost" is only a helpful surprise arranged by the
  child's caregiver, and the last image proves the room is safe again.

This script keeps the story grounded in world state:
- physical meters: light, quiet, hidden, tidy
- emotional memes: worry, curiosity, relief, courage
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
class Setting:
    place: str = "the nap room"
    dim: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    persona: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _py_or_0(d: dict[str, float], key: str) -> float:
    return float(d.get(key, 0.0))


def _add(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.meters[key] = _py_or_0(entity.meters, key) + amt


def _mem(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.memes[key] = _py_or_0(entity.memes, key) + amt


def _set(entity: Entity, key: str, val: float) -> None:
    entity.meters[key] = val


def _say_name(ent: Entity) -> str:
    return ent.id


def _child_like_persona(persona: str) -> str:
    return {
        "curious": "curious",
        "shy": "shy",
        "brave": "brave",
        "sleepy": "sleepy",
        "gentle": "gentle",
        "wary": "wary",
    }.get(persona, persona)


def intro(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a {_child_like_persona(world.facts['persona'])} little "
        f"{child.type} who liked the nap room because it was soft and quiet."
    )


def foreshadow_one(world: World, child: Entity) -> None:
    _add(child, "curiosity")
    _mem(child, "curiosity")
    world.say(
        f"At first, {child.id} noticed a small sign: the blanket on the cot had "
        f"slipped down, as if someone had been there a moment ago."
    )


def foreshadow_two(world: World, child: Entity, parent: Entity) -> None:
    _add(child, "worry")
    _mem(child, "worry")
    _add(parent, "quietness")
    world.say(
        f"Then there was a soft thump from the corner. "
        f"{parent.pronoun('subject').capitalize()} smiled and said nothing, "
        f"but {child.id} heard it anyway."
    )


def foreshadow_three(world: World, child: Entity, object_name: str) -> None:
    child.meters["hidden"] = 1.0
    world.say(
        f"When {child.id} looked for {object_name}, it was gone from the pillow "
        f"basket. That made the room feel even stranger."
    )


def reveal(world: World, child: Entity, parent: Entity, object_name: str) -> None:
    _add(child, "courage")
    _add(child, "relief")
    _mem(child, "worry", -_py_or_0(child.memes, "worry"))
    _mem(child, "relief")
    _set(child, "hidden", 0.0)
    world.say(
        f"At last, {parent.id} lifted the folded blanket and found {object_name} "
        f"tucked inside. It was not a ghost at all; it was a tiny flashlight "
        f"left there for a midnight nap-time surprise."
    )


def ending(world: World, child: Entity, parent: Entity, object_name: str) -> None:
    world.say(
        f"{child.id} laughed, held {object_name}, and curled back under the blanket. "
        f"The nap room was still dim, but now it felt friendly, and every soft shadow "
        f"looked like part of a safe, sleepy game."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    world.facts.update(
        child=child,
        parent=parent,
        persona=params.persona,
        object_name="a little flashlight",
        setting=setting,
    )
    _add(child, "worry", 0.0)
    _add(child, "curiosity", 0.0)
    _add(child, "relief", 0.0)
    _add(child, "courage", 0.0)

    intro(world, child)
    world.para()
    foreshadow_one(world, child)
    foreshadow_two(world, child, parent)
    foreshadow_three(world, child, world.facts["object_name"])
    world.para()
    reveal(world, child, parent, world.facts["object_name"])
    ending(world, child, parent, world.facts["object_name"])
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "nap room": Setting(place="the nap room", dim=True, affords={"ghost"}),
}

PERSONAS = ["curious", "shy", "brave", "sleepy", "gentle", "wary"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo"]
PARENTS = ["mother", "father"]


@dataclass
class ASPChoice:
    place: str
    persona: str


def valid_combos() -> list[tuple[str, str]]:
    return [("nap room", p) for p in PERSONAS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nap-room ghost story world with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--persona", choices=PERSONAS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    place = args.place or "nap room"
    if place not in SETTINGS:
        raise StoryError("The story must be set in the nap room.")
    persona = args.persona or rng.choice(PERSONAS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, persona=persona)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost-story for a child in {f["setting"].place} with the word "persona".',
        f"Tell a gentle spooky story where {f['child'].id} notices clues in the nap room and learns the ghost is friendly.",
        f"Write a foreshadowing story about a {f['persona']} child, a soft mystery, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    persona = world.facts["persona"]
    return [
        QAItem(
            question=f"Who was the story about in the nap room?",
            answer=f"It was about {c.id}, a {persona} little {c.type}, and {p.id} was there too.",
        ),
        QAItem(
            question="What clues made the room feel spooky before the ending?",
            answer="The blanket slipped down, there was a soft thump from the corner, and a little flashlight seemed to disappear.",
        ),
        QAItem(
            question="What was the ghost really?",
            answer="The ghost was not a real ghost. It was a little flashlight tucked inside a folded blanket for a surprise.",
        ),
        QAItem(
            question="How did the child feel at the end?",
            answer=f"{c.id} felt relieved and brave, then laughed and curled back under the blanket.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small clues early on that hint at something important later.",
        ),
        QAItem(
            question="Why do quiet rooms sometimes feel spooky?",
            answer="Quiet rooms can make tiny sounds and shadows stand out more, so they may feel spooky even when nothing dangerous is there.",
        ),
        QAItem(
            question="What is a persona?",
            answer="A persona is the kind of character feeling or role someone shows in a story, like shy, brave, or curious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(nap_room).
persona(curious;shy;brave;sleepy;gentle;wary).

valid_story(P, Pe) :- place(P), persona(Pe).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", "nap_room")] + [asp.fact("persona", p) for p in PERSONAS])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, persona in combos:
            print(f"  {place:9} {persona}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for persona in PERSONAS:
            p = StoryParams(place="nap room", name="Mia", gender="girl", parent="mother", persona=persona)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
