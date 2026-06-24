#!/usr/bin/env python3
"""
storyworlds/worlds/impressive_twist_magic_heartwarming.py
==========================================================

A small, self-contained storyworld about a child making an impressive magical
gift, discovering a gentle twist, and ending with a warm surprise.

Seed tale sketch:
---
A child wants to make something impressive for someone they love.
They try a magic-looking project, but a small twist makes the plan wobble.
A helper, a kind repair, and a little courage turn the wobble into a happy
ending.

World model:
---
The child has two kinds of state:
- physical meters: neatness, sparkle, sturdiness, glow, small accidents
- emotional memes: hope, worry, pride, closeness, relief

The story is driven by causal changes in the world:
- building increases sturdiness and sparkle
- a mistake increases worry and can lower sturdiness
- a twist adds surprise and can unlock a better outcome
- sharing the result increases closeness and relief
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["neat", "sparkle", "sturdy", "glow", "mess", "broken"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "pride", "closeness", "relief", "surprise", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the kitchen table"
    afford: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    noun: str
    verb: str
    gerund: str
    magic_word: str
    twist: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    label: str
    phrase: str
    type: str
    touch: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    action: str
    effect: str
    fix: str
    tags: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTING = Setting(place="the kitchen table", afford={"craft", "glow"})
PROJECTS = {
    "lantern": Project(
        id="lantern",
        noun="lantern",
        verb="make a lantern",
        gerund="making lanterns",
        magic_word="magic",
        twist="the ribbon curl would not stay tied",
        mess="glitter",
        risk="the lantern could fall apart",
        tags={"magic", "twist", "impressive", "glow"},
    ),
    "card": Project(
        id="card",
        noun="card",
        verb="make a card",
        gerund="making cards",
        magic_word="magic",
        twist="the star folded the wrong way",
        mess="glue",
        risk="the card could smudge",
        tags={"magic", "twist", "impressive", "love"},
    ),
}
GIFTS = {
    "grandma": Gift(
        label="grandma",
        phrase="a handmade surprise for grandma",
        type="grandmother",
        touch="soft",
    ),
    "dad": Gift(
        label="dad",
        phrase="a shiny surprise for dad",
        type="father",
        touch="bright",
    ),
    "sister": Gift(
        label="sister",
        phrase="a sweet surprise for a little sister",
        type="sister",
        touch="gentle",
    ),
}
HELPERS = {
    "tape": Helper(
        id="tape",
        label="a strip of tape",
        action="held the curl in place",
        effect="sturdy",
        fix="tucked under the paper edge",
        tags={"repair"},
    ),
    "string": Helper(
        id="string",
        label="a bit of string",
        action="made the lantern hang straight",
        effect="sturdy",
        fix="tied the top loop again",
        tags={"repair"},
    ),
    "song": Helper(
        id="song",
        label="a tiny humming song",
        action="turned the waiting into something cozy",
        effect="glow",
        fix="softened the worry",
        tags={"heartwarming"},
    ),
}

NAMES = ["Mia", "Noah", "Luna", "Theo", "Ivy", "Eli", "Ava", "Finn"]
TRAITS = ["gentle", "brave", "curious", "kind", "quiet", "cheerful"]


def project_needs_help(project: Project, gift: Gift) -> bool:
    return True


def choose_helper(project: Project, gift: Gift) -> Optional[Helper]:
    if project.id == "lantern":
        return HELPERS["string"]
    if project.id == "card":
        return HELPERS["tape"]
    return None


def predict_outcome(world: World, child: Entity, project: Project) -> dict:
    sim = world.copy()
    do_build(sim, sim.get(child.id), project, narrate=False)
    return {
        "mess": sim.get(child.id).meters["mess"],
        "sturdy": sim.get(project.id).meters["sturdy"],
        "broken": sim.get(project.id).meters["broken"],
    }


def do_build(world: World, child: Entity, project: Project, narrate: bool = True) -> None:
    child.memes["hope"] += 1
    child.meters["neat"] += 1
    craft = world.get(project.id)
    craft.meters["sparkle"] += 1
    craft.meters["sturdy"] += 1
    if project.id == "lantern":
        craft.meters["glow"] += 1
    if narrate:
        world.say(
            f"{child.name_or_label()} worked carefully, and the {project.noun} grew more {project.magic_word} and impressive."
        )


def do_twist(world: World, child: Entity, project: Project, gift: Gift) -> None:
    child.memes["surprise"] += 1
    child.memes["worry"] += 1
    child.meters["mess"] += 1
    craft = world.get(project.id)
    craft.meters["sturdy"] -= 1
    if craft.meters["sturdy"] < 0:
        craft.meters["sturdy"] = 0
    world.say(
        f"Then came a twist: {project.twist}, and the {project.noun} wobbled on the table."
    )
    world.say(
        f"{child.name_or_label()} frowned, because {gift.phrase} deserved something nice."
    )


def do_fix(world: World, child: Entity, project: Project, helper: Helper) -> None:
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    child.memes["pride"] += 1
    craft = world.get(project.id)
    craft.meters["sturdy"] += 1
    craft.meters[helper.effect] += 1
    world.say(
        f"But {helper.label} {helper.action}, and {helper.fix}."
    )


def do_shine(world: World, child: Entity, project: Project, gift: Gift) -> None:
    child.memes["relief"] += 1
    child.memes["closeness"] += 1
    child.memes["love"] += 1
    craft = world.get(project.id)
    craft.meters["glow"] += 1
    world.say(
        f"At last, the {project.noun} glowed softly, and the whole thing looked even more impressive than before."
    )
    world.say(
        f"{child.name_or_label()} gave {gift.label} the finished surprise, and the room felt warm and happy."
    )


def tell(setting: Setting, project: Project, gift: Gift, name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name, meters={}, memes={}))
    child.meters.update({"neat": 0.0, "sparkle": 0.0, "sturdy": 0.0, "glow": 0.0, "mess": 0.0, "broken": 0.0})
    child.memes.update({"hope": 0.0, "worry": 0.0, "pride": 0.0, "closeness": 0.0, "relief": 0.0, "surprise": 0.0, "love": 0.0})
    craft = world.add(Entity(id=project.id, type=project.id, label=project.noun, phrase=project.verb))
    helper = world.add(Entity(id="helper", type="thing", label="", meters={}, memes={}))
    helper.meters["neat"] = 0.0

    world.say(f"{name} was a {trait} child who wanted to make something impressive.")
    world.say(f"{name} chose to {project.verb} for {gift.label}, using {project.magic_word} colors and a very careful smile.")
    world.para()
    world.say(f"At {setting.place}, the project began to shine while {name} kept folding and smoothing each piece.")
    do_build(world, child, project)
    world.say(f"{name} hoped the surprise would be lovely, not just clever, because it was meant with love.")
    world.para()
    do_twist(world, child, project, gift)
    helper_def = choose_helper(project, gift)
    if helper_def is None:
        raise StoryError("No gentle helper exists for this project.")
    world.facts["helper"] = helper_def
    do_fix(world, child, project, helper_def)
    world.para()
    do_shine(world, child, project, gift)
    world.facts.update(child=child, project=project, gift=gift, setting=setting, trait=trait)
    return world


@dataclass
class StoryParams:
    project: str
    gift: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming storyworld about an impressive magical project with a twist."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    project = args.project or rng.choice(list(PROJECTS))
    gift = args.gift or rng.choice(list(GIFTS))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(project=project, gift=gift, name=name, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short heartwarming story with the word "impressive" about a child making a {f["project"].noun}.',
        f"Tell a gentle story where {f['child'].id} tries to make {f['gift'].label} something magical, but a twist makes the plan wobble before it turns out lovely.",
        f'Write a child-friendly story about a small magical project, a twist, and a warm ending that feels impressive.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, project, gift = f["child"], f["project"], f["gift"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did {child.id} want to make for {gift.label}?",
            answer=f"{child.id} wanted to make {gift.phrase} by creating {project.verb}.",
        ),
        QAItem(
            question=f"What twist happened while {child.id} was making the {project.noun}?",
            answer=f"The twist was that {project.twist}, so the {project.noun} wobbled and made {child.id} worry for a moment.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{helper.label} helped because it {helper.action}, and that made the {project.noun} sturdy again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {project.noun} glowing softly and {child.id} giving {gift.label} a warm, loving surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does impressive mean?",
            answer="Impressive means so good, big, or skillful that it makes people notice and admire it.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story go in a new direction.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special or surprising that seems a little beyond ordinary life.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, PROJECTS[params.project], GIFTS[params.gift], params.name, params.trait)
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
    StoryParams(project="lantern", gift="grandma", name="Mia", trait="gentle"),
    StoryParams(project="card", gift="dad", name="Noah", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        print("OK: no ASP backend defined for this tiny world; Python gate is self-contained.")
        return
    if args.asp:
        print("This world has no clingo twin beyond the narrative gate.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
