#!/usr/bin/env python3
"""
A bedtime-story world about kindness, a herring, and a tiny scare that turns
into an excellent goodnight.

The world premise:
- A small child notices a frightened herring in a harbor pond.
- A shadowy gull and a rolling cart make the herring feel terrify/terrified.
- The child uses kindness: a calm voice, a lantern, and a sheltered bowl.
- The ending shows the herring safe, the child proud, and the night quiet.

This file is a standalone storyworld script.
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


# ---------------------------------------------------------------------------
# Entities / world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "animal"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
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
    place: str = "the harbor"
    quiet: bool = True
    dark: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Small simulation
# ---------------------------------------------------------------------------
def _night_breeze(world: World) -> list[str]:
    out = []
    herring = world.get("herring")
    if herring.memes.get("fear", 0) >= 1 and ("breeze",) not in world.fired:
        world.fired.add(("breeze",))
        herring.memes["fear"] += 0.5
        out.append("A chilly breeze whispered over the water, and the little herring shivered.")
    return out


def _kindness_warmth(world: World) -> list[str]:
    out = []
    child = world.get("child")
    herring = world.get("herring")
    lantern = world.get("lantern")
    if child.memes.get("kindness", 0) >= 1 and herring.memes.get("fear", 0) >= 1:
        sig = ("warmth",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        herring.memes["calm"] = herring.memes.get("calm", 0) + 1
        herring.memes["fear"] = max(0.0, herring.memes.get("fear", 0) - 1.0)
        lantern.meters["light"] = lantern.meters.get("light", 0) + 1
        out.append("The lantern made a small gold pool of light, and the herring felt a little braver.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_night_breeze, _kindness_warmth):
            sents = fn(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


# ---------------------------------------------------------------------------
# Story craft
# ---------------------------------------------------------------------------
SETTING = Setting(place="the harbor")
HERRING_WORD = "herring"
EXCELLENT_WORD = "excellent"
KINDNESS_WORD = "Kindness"

def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id="child", kind="character", type=params.gender, label=params.name
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=params.parent, label=params.parent
    ))
    herring = world.add(Entity(
        id="herring", kind="animal", type="herring", label="small herring", plural=False
    ))
    lantern = world.add(Entity(
        id="lantern", kind="thing", type="lantern", label="lantern"
    ))
    bowl = world.add(Entity(
        id="bowl", kind="thing", type="bowl", label="tiny bowl", caretaker="child"
    ))

    child.memes["kindness"] = 1
    child.memes["care"] = 1
    herring.memes["fear"] = 1
    herring.meters["water"] = 1

    world.facts.update(child=child, parent=parent, herring=herring, lantern=lantern, bowl=bowl)

    # Act 1: bedtime setup.
    world.say(
        f"At bedtime, {params.name} and {params.parent} sat beside {SETTING.place}, where the moon made the water look soft and silver."
    )
    world.say(
        f"{params.name} noticed a little {HERRING_WORD} near the dock, and {params.name}'s heart went gentle with {KINDNESS_WORD}."
    )
    world.say(
        f"{params.name} whispered that the night could still be {EXCELLENT_WORD}, even if something felt a little scary."
    )

    # Act 2: tension.
    world.para()
    world.say(
        "A shadow from a rocking boat slid over the water, and the herring flinched as if the dark had grown teeth."
    )
    world.say(
        f"The {HERRING_WORD} looked very small beside the waves, and its fear bubbled up like a tiny storm."
    )
    propagate(world)

    # Act 3: resolution.
    world.para()
    world.say(
        f"{params.name} lifted the lantern and set the bowl where the water was calmest, then spoke in a hush as soft as a pillow."
    )
    world.say(
        f"With {KINDNESS_WORD}, {params.name} gave the {HERRING_WORD} a safe place to rest, and the little fish slid into the bowl without a splash."
    )
    world.say(
        f"At last, the harbor was quiet again, the herring was safe, and the night felt {EXCELLENT_WORD} and cozy."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["child"]
    return [
        f"Write a bedtime story about {p.label}, a frightened herring, and a gentle act of kindness.",
        f"Tell a quiet harbor story where a child makes the night feel excellent for a herring.",
        f"Write a soothing story that includes the words 'herring', 'kindness', and 'excellent'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Who helped the herring feel safer at the harbor?",
            answer=f"{child.label} helped the herring feel safer by using kindness, a lantern, and a calm voice."
        ),
        QAItem(
            question=f"Why did the herring get scared?",
            answer="The herring got scared when a shadow from a rocking boat slid over the water and the dark felt threatening."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the herring safe in a tiny bowl, the harbor quiet, and {child.label} and {parent.label} ready for sleep."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a herring?",
            answer="A herring is a small fish that swims in the sea or in salty water near the shore."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring so someone else feels safe and comforted."
        ),
        QAItem(
            question="What does excellent mean?",
            answer="Excellent means very good, like something that works well or feels especially nice."
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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
kindness_helped :- child_kindness, herring_fear, lantern_light.
resolved :- kindness_helped.
#show resolved/0.
#show kindness_helped/0.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child_kindness"),
        asp.fact("herring_fear"),
        asp.fact("lantern_light"),
    ]
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    shown = {str(a) for a in model}
    ok = "resolved" in shown
    if ok:
        print("OK: ASP parity gate passes.")
        return 0
    print("MISMATCH: ASP parity gate failed.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about kindness and a herring.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
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
    name = args.name or rng.choice(["Mina", "Luna", "Ari", "Nina", "Owen", "Milo"])
    gender = args.gender
    parent = args.parent
    return StoryParams(name=name, gender=gender, parent=parent)


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
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0. #show kindness_helped/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name="Mina", gender="girl", parent="mother", seed=base_seed)
        samples = [generate(params)]
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
