#!/usr/bin/env python3
"""
storyworlds/worlds/stretch_dialogue_rhyming_story.py
====================================================

A tiny storyworld about a child who wants to stretch something long and soft,
but a careful grownup worries it may snap. The tale keeps a rhyming, dialogue-
driven tone and ends with a gentle compromise.

Premise:
- A child wants to stretch a colorful ribbon.
- A grownup worries it may tear or tangle.
- They choose a safer way to play, so the ribbon stays pretty.

The world tracks:
- meters: ribbon tension, stretch, and damage
- memes: desire, worry, frustration, joy, and relief

The story is generated from a small simulated state, not from a frozen template.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
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
    place: str = "the sunny playroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    safe: bool = True


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


def meter_get(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme_get(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def meter_add(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter_get(e, key) + amt


def meme_add(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme_get(e, key) + amt


def rhyming_lines(activity: str, item: Item, tool: Optional[Tool]) -> tuple[str, str]:
    if activity == "stretch":
        return (
            f"\"Oh, let me stretch it!\" the child said with a grin,",
            f"\"If we stretch it too hard, it may tear at the hem.\"",
        )
    return (
        f"\"Let's play a careful game,\" the grownup softly said,",
        f"\"So fun can bloom like sunshine and stay nice and spread.\"",
    )


def safe_way_line(tool: Tool) -> str:
    return f"\"We can use {tool.label} first,\" the grownup sang, \"and keep the ribbon in one pretty tang!\""


def story_setup(world: World, child: Entity, grownup: Entity, ribbon: Entity) -> None:
    world.say(
        f"In the {world.setting.place}, {child.id} found a ribbon bright, "
        f"all shiny and silky, all blue, red, and light."
    )
    world.say(
        f"{child.id} loved to pull it and twirl it in fun, "
        f"for stretching the ribbon felt springy as sun."
    )
    world.say(
        f"But {grownup.id} smiled and said, \"Now wait, little dear, "
        f"if we tug it too much, it may fray right here.\""
    )
    ribbon.meters["pretty"] = 1.0
    child.memes["love"] = 1.0
    grownup.memes["care"] = 1.0
    world.facts.update(child=child, grownup=grownup, ribbon=ribbon)


def predict_damage(world: World, child: Entity, ribbon: Entity, tool: Optional[Tool]) -> bool:
    tension = 1.0
    if tool is None:
        tension += 1.0
    return tension > 1.0


def try_stretch(world: World, child: Entity, ribbon: Entity, tool: Optional[Tool]) -> None:
    child.memes["desire"] = 1.0
    meter_add(child, "stretch", 1.0)
    meter_add(ribbon, "tension", 1.0)
    world.say(f"\"I want to stretch it!\" {child.id} cried with glee.")
    if predict_damage(world, child, ribbon, tool):
        ribbon.meters["risk"] = 1.0
        world.say(f"\"Not that way,\" said the grownup, \"or snap it may be.\"")
        child.memes["frustration"] = 1.0
        grownup = world.facts["grownup"]
        grownup.memes["worry"] = 1.0
    else:
        world.say(f"\"That seems safe,\" said the grownup, \"we'll do it with care.\"")


def offer_compromise(world: World, child: Entity, grownup: Entity, ribbon: Entity, tool: Tool) -> None:
    world.say(safe_way_line(tool))
    child.memes["joy"] = 1.0
    grownup.memes["relief"] = 1.0
    child.memes["frustration"] = 0.0
    ribbon.meters["tension"] = 0.5
    ribbon.meters["damage"] = 0.0
    world.say(
        f"They used {tool.phrase}, and lightly they played; "
        f"the ribbon stretched softly, then settled, well-made."
    )
    world.say(
        f"{child.id} clapped and laughed, \"What a twinkly tune!\" "
        f"And the ribbon went swish-swish beneath a bright moon."
    )


def tell() -> World:
    setting = Setting(place="the sunny playroom", affords={"stretch"})
    world = World(setting)
    child = world.add(Entity(id="Mina", kind="character", type="girl"))
    grownup = world.add(Entity(id="Grandma", kind="character", type="mother", label="Grandma"))
    ribbon = world.add(Entity(
        id="ribbon",
        type="thing",
        label="ribbon",
        phrase="a colorful ribbon",
        owner=child.id,
        caretaker=grownup.id,
        region="hands",
    ))
    tool = Tool(
        id="scarftube",
        label="a soft scarf tube",
        phrase="a soft scarf tube",
        helps="stretch gently",
        safe=True,
    )

    story_setup(world, child, grownup, ribbon)
    world.para()
    world.say(f"One warm afternoon, {child.id} and {grownup.id} were side by side,")
    world.say(f"with sunlight like gold on the floor far and wide.")

    try_stretch(world, child, ribbon, tool=None)
    world.say(rhyming_lines("stretch", ribbon, None)[0])
    world.say(rhyming_lines("stretch", ribbon, None)[1])

    world.para()
    offer_compromise(world, child, grownup, ribbon, tool)

    world.facts["tool"] = tool
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    grownup: Entity = f["grownup"]
    ribbon: Entity = f["ribbon"]
    return [
        "Write a short rhyming story for a young child about stretching something carefully.",
        f"Tell a gentle dialogue story where {child.id} wants to stretch {ribbon.phrase} "
        f"but {grownup.id} worries it may tear.",
        "Write a sunny playroom story with a child, a grownup, and a safe compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    grownup: Entity = world.facts["grownup"]
    ribbon: Entity = world.facts["ribbon"]
    tool: Tool = world.facts["tool"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the ribbon?",
            answer=f"{child.id} wanted to stretch the colorful ribbon and make it dance.",
        ),
        QAItem(
            question=f"Why did {grownup.id} worry about the ribbon?",
            answer="The grownup worried that if they tugged too hard, the ribbon could fray or snap.",
        ),
        QAItem(
            question=f"What safe idea helped them play together?",
            answer=f"They used {tool.label} and stretched the ribbon gently instead of pulling it hard.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to stretch something?",
            answer="To stretch something means to pull it gently so it becomes longer or wider.",
        ),
        QAItem(
            question="Why should a fragile ribbon be handled carefully?",
            answer="A fragile ribbon can tear, tangle, or lose its pretty shape if it is pulled too hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming dialogue storyworld about careful stretching.")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(seed=args.seed if args.seed is not None else rng.randrange(2**31))


def generate(params: StoryParams) -> StorySample:
    world = tell()
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


ASP_RULES = r"""
#show valid/1.
valid(stretch).
"""


def asp_facts() -> str:
    return "activity(stretch).\n"


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [StoryParams(seed=1)]


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
