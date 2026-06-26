#!/usr/bin/env python3
"""
zed_lavender_dialogue_conflict_comedy.py
========================================

A small comedy storyworld built from the seed words "zed" and "lavender".

Premise:
- Zed and Lavender are friends preparing a tiny joke show.
- A single prop, a laugh bell, becomes the source of a silly conflict.
- Dialogue drives the turn: each character wants a different punchline.
- The resolution is a compromise that lets both jokes land.

The world model tracks physical meters and emotional memes, and the narration
is generated from simulated state rather than a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little stage in the library"
    affordance: str = "joke show"


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str = "thing"


@dataclass
class StoryParams:
    place: str
    prop: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PROPS = {
    "bell": Prop(id="bell", label="laugh bell", phrase="a shiny laugh bell"),
    "hat": Prop(id="hat", label="joke hat", phrase="a floppy joke hat"),
    "card": Prop(id="card", label="pun card", phrase="a tiny pun card"),
}

SETTINGS = {
    "stage": Setting(place="the little stage in the library"),
    "kitchen": Setting(place="the kitchen table"),
    "yard": Setting(place="the backyard bench"),
}

GENTLE_JOKES = [
    "a penguin in a scarf",
    "a broccoli prince",
    "a cloud with sneakers",
    "a grape that told riddles",
]

TRAITS = ["silly", "curious", "bright", "chatty", "playful"]


def reasonableness_gate(place: str, prop: str) -> bool:
    return place in SETTINGS and prop in PROPS


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    lines.append(asp.fact("feature", "dialogue"))
    lines.append(asp.fact("feature", "conflict"))
    lines.append(asp.fact("style", "comedy"))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, Prop) :- setting(P), prop(Prop).
has_conflict(P) :- compatible(P, Prop).
% The storyworld is tiny and deterministic: every compatible setup has a conflict
% because two comedians want the same prop in different ways.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, pr) for p in SETTINGS for pr in PROPS]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy dialogue conflict storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    if args.place and args.prop and not reasonableness_gate(args.place, args.prop):
        raise StoryError("(No valid combination matches the given options.)")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.prop:
        combos = [c for c in combos if c[1] == args.prop]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prop = rng.choice(sorted(combos))
    a = args.name_a or rng.choice(["Zed", "Zig", "Zuri", "Zane"])
    b = args.name_b or rng.choice(["Lavender", "Luna", "Lila", "Lark"])
    if a == b:
        b = "Lavender"
    return StoryParams(place=place, prop=prop, name_a=a, name_b=b)


def _introduce(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    world.say(
        f"{a.id} and {b.id} were getting ready for a tiny joke show at {world.setting.place}."
    )
    world.say(
        f"They loved funny faces, quick chatter, and {prop.phrase}, which looked important even when it was not."
    )


def _setup(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    a.memes["excited"] = 1
    b.memes["excited"] = 1
    prop.held_by = a.id
    world.say(
        f"{a.id} said, \"I should start with the bell.\""
    )
    world.say(
        f"{b.id} said, \"No, the hat is the funny part.\""
    )


def _conflict(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    a.memes["stubborn"] = 1
    b.memes["stubborn"] = 1
    a.memes["conflict"] = 1
    b.memes["conflict"] = 1
    world.say(
        f"{a.id} hugged the {prop.label} a little tighter and said, \"My joke needs this exact one.\""
    )
    world.say(
        f"{b.id} crossed {b.pronoun('possessive')} arms. \"Mine needs it more,\" {b.pronoun()} said."
    )
    world.say(
        f"That made the stage feel very tiny and very dramatic, which was funny for everyone except them."
    )


def _compromise(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    if prop.id == "bell":
        world.say(
            f"{b.id} peeked at the bell and grinned. \"What if we ring it only after the punchline?\""
        )
        world.say(
            f"{a.id} blinked, then laughed. \"And what if you wear the hat while I ring it?\""
        )
        prop.held_by = b.id
    elif prop.id == "hat":
        world.say(
            f"{a.id} slid the hat onto the table and said, \"We can share it if we take turns looking ridiculous.\""
        )
        world.say(
            f"{b.id} laughed so hard that {b.pronoun('possessive')} shoulders bounced."
        )
    else:
        world.say(
            f"{a.id} held up the pun card and said, \"We can read one joke each, and then do the silly face together.\""
        )
        world.say(
            f"{b.id} nodded at once. \"That is the least serious plan I have ever loved.\""
        )
    a.memes["conflict"] = 0
    b.memes["conflict"] = 0
    a.memes["joy"] = 2
    b.memes["joy"] = 2
    prop.meters["used"] = 1


def _ending(world: World, a: Entity, b: Entity, prop: Entity) -> None:
    joke = random.choice(GENTLE_JOKES)
    world.say(
        f"At last, they performed {joke}, and the whole room laughed when {a.id} and {b.id} timed the prop perfectly."
    )
    world.say(
        f"The {prop.label} ended the show in {b.id}'s hands, and the big applause sounded like a happy drumroll."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    a = world.add(Entity(id=params.name_a, kind="character", type="child"))
    b = world.add(Entity(id=params.name_b, kind="character", type="child"))
    prop = world.add(Entity(id=params.prop, kind="thing", type="prop", label=PROPS[params.prop].label, phrase=PROPS[params.prop].phrase))

    _introduce(world, a, b, prop)
    world.para()
    _setup(world, a, b, prop)
    _conflict(world, a, b, prop)
    world.para()
    _compromise(world, a, b, prop)
    _ending(world, a, b, prop)

    world.facts.update(a=a, b=b, prop=prop, setting=world.setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    prop = world.facts["prop"]
    return [
        f'Write a short comedy story for children about {p.name_a} and {p.name_b} at {world.setting.place}.',
        f'Include a dialogue conflict over {prop.phrase} and end with a funny compromise.',
        f'Tell a playful story featuring the words "zed" and "lavender" and a joke show.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    a = world.facts["a"]
    b = world.facts["b"]
    prop = world.facts["prop"]
    return [
        QAItem(
            question=f"Who were the two children getting ready for the joke show?",
            answer=f"The children were {a.id} and {b.id}. They were preparing at {world.setting.place} with {prop.phrase}.",
        ),
        QAItem(
            question=f"What did {a.id} and {b.id} argue about?",
            answer=f"They argued about {prop.label}. Each one thought {prop.label} should be used for {p.name_a if prop.held_by == p.name_a else p.name_b}'s joke first.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They talked it out, shared the prop, and used a silly compromise so both jokes could work. That made the conflict disappear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compromise?",
            answer="A compromise is a plan where people each give a little so everyone can keep going together.",
        ),
        QAItem(
            question="Why can a joke show be funny?",
            answer="A joke show is funny because people tell silly lines, make faces, and surprise each other in a playful way.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="stage", prop="bell", name_a="Zed", name_b="Lavender"),
    StoryParams(place="kitchen", prop="hat", name_a="Zed", name_b="Lavender"),
    StoryParams(place="yard", prop="card", name_a="Zed", name_b="Lavender"),
]


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prop) combos:\n")
        for place, prop in combos:
            print(f"  {place:8} {prop}")
        return

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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} at {p.place} (prop: {p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
