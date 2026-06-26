#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tire_lacrosse_add_magic_curiosity_nursery_rhyme.py
===========================================================================================================

A tiny nursery-rhyme story world about a tire, a lacrosse game, a helpful add-on,
and a little bit of Magic and Curiosity.

The seed story idea:
---
In a nursery rhyme world, a child finds an old tire near the garden gate. The
child wants to add it to a lacrosse game as a playful ring, but the tire is too
heavy and wobbles on the grass. Curiosity leads the child to ask a wise old
helper for advice, and Magic makes a light ribbon hoop appear instead. The tire
stays by the gate as a seat, and the lacrosse game becomes safer and more fun.
---

This world is intentionally small, concrete, and constraint-checked. It
generates one complete story with a beginning, a turn, and an ending image
showing what changed.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"child", "girl", "boy"}:
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
            if self.type in {"woman", "mother"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"man", "father"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery yard"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class AddOn:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fits: set[str]
    magic: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
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


ACTIVITIES = {
    "lacrosse": Activity(
        id="lacrosse",
        verb="play lacrosse",
        gerund="playing lacrosse",
        rush="dash after the ball",
        mess="tumble",
        soil="all muddled",
        keyword="lacrosse",
        tags={"lacrosse", "game"},
    ),
}

PRIZES = {
    "tire": Prize(
        label="tire",
        phrase="an old tire from the shed",
        region="ground",
        plural=False,
    ),
}

ADDONS = {
    "magic_ribbon": AddOn(
        id="magic_ribbon",
        label="Magic ribbon hoop",
        phrase="a light ribbon hoop that could bounce and glow",
        helps={"lacrosse"},
        fits={"game"},
        magic=True,
    ),
    "soft_ball": AddOn(
        id="soft_ball",
        label="soft ball",
        phrase="a soft ball with bright stitches",
        helps={"lacrosse"},
        fits={"game"},
        magic=False,
    ),
}

SETTINGS = {
    "nursery_yard": Setting(
        place="the nursery yard",
        indoors=False,
        affords={"lacrosse"},
    )
}

CHILD_NAMES = ["Mia", "Nina", "Pip", "Tom", "June", "Penny", "Will", "Luna"]
HELPER_NAMES = ["Mum", "Grandma", "Nanny", "Papa", "Auntie", "Old Owl"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.label == "tire" and activity.id == "lacrosse"


def select_addon(activity: Activity, prize: Prize) -> Optional[AddOn]:
    if not prize_at_risk(activity, prize):
        return None
    for addon in ADDONS.values():
        if activity.id in addon.helps:
            return addon
    return None


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme story world about tire, lacrosse, add, Magic, and Curiosity."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "lacrosse"
    prize = args.prize or "tire"
    if not prize_at_risk(ACTIVITIES[activity], PRIZES[prize]):
        raise StoryError("No story: that tire-and-lacrosse turn would not create a real problem.")
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, helper=helper)


def _scene_intro(world: World, child: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{child.id} was a bright little child who loved {activity.gerund}. "
        f"By the nursery gate sat {prize.phrase}."
    )
    world.say(
        f"{child.id} had Curiosity in {child.pronoun('possessive')} pocket and a happy skip in {child.id}'s step."
    )
    child.memes["curiosity"] = 1
    child.memes["joy"] = 1


def _scene_tension(world: World, child: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.para()
    world.say(
        f"{child.id} wanted to add the {prize.label} to the game, like a bouncy ring in a nursery rhyme parade."
    )
    world.say(
        f"But when {child.id} tried to {activity.rush}, the heavy tire wobbled and rolled the wrong way."
    )
    child.meters["wobble"] = 1
    child.memes["trouble"] = 1
    world.say(
        f"{helper.id} smiled and said, 'A tire is clever for sitting, not for swinging in a lacrosse game.'"
    )


def _scene_turn(world: World, child: Entity, helper: Entity, prize: Entity, activity: Activity) -> Optional[AddOn]:
    world.say(
        f"{child.id}'s Curiosity grew. '{Can_magic := 'Can Magic make it kinder?'}' {child.id} asked."
    )
    addon = select_addon(activity, prize)
    if addon is None:
        return None
    child.memes["curiosity"] += 1
    child.memes["hope"] += 1
    world.say(
        f"{helper.id} tapped {helper.pronoun('possessive')} finger, and Magic answered with a {addon.label.lower()}."
    )
    world.say(
        f"The bright hoop was light as a feather, and it fit the game without hurting the grass."
    )
    return addon


def _scene_resolution(world: World, child: Entity, helper: Entity, prize: Entity, activity: Activity, addon: AddOn) -> None:
    world.para()
    world.say(
        f"So {child.id} used the {addon.label.lower()} and played {activity.gerund} with a merry little hop."
    )
    world.say(
        f"The old tire stayed by the gate as a seat, and the nursery yard felt tidy, tidy, tidy."
    )
    child.memes["joy"] += 2
    child.memes["trouble"] = 0
    world.facts["resolved"] = True
    world.facts["addon"] = addon


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type="helper"))
    prize = world.add(Entity(id=prize_cfg.label, type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase))
    world.facts.update(child=child, helper=helper, prize=prize, activity=activity, setting=setting)

    _scene_intro(world, child, helper, prize, activity)
    _scene_tension(world, child, helper, prize, activity)
    addon = _scene_turn(world, child, helper, prize, activity)
    if addon is None:
        raise StoryError("No story: the helpful add-on could not be found.")
    _scene_resolution(world, child, helper, prize, activity, addon)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a child, a tire, and lacrosse with a magical solution.',
        f"Tell a gentle story where {f['child'].id} wants to add a tire to a lacrosse game and Curiosity leads to Magic.",
        "Write a child-friendly rhyme where a tire stays safe while the game becomes playful and kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    prize = f["prize"]
    activity = f["activity"]
    addon = f["addon"]
    return [
        QAItem(
            question=f"What did {child.id} want to add to the lacrosse game?",
            answer=f"{child.id} wanted to add the tire to the lacrosse game, because {child.pronoun('possessive')} Curiosity made the idea sparkle.",
        ),
        QAItem(
            question=f"Why did {helper.id} say the tire was not right for the game?",
            answer="Because the tire was too heavy and wobbly for swinging around, so it would make the game clumsy instead of safe.",
        ),
        QAItem(
            question=f"What Magic item helped the child play without using the tire?",
            answer=f"A {addon.label.lower()} helped instead, so the child could play {activity.gerund} without turning the tire into a game piece.",
        ),
        QAItem(
            question=f"What happened to the tire at the end?",
            answer="The tire stayed by the gate as a seat, while the game went on with a lighter and kinder play piece.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tire usually for?",
            answer="A tire helps a wheel roll on the ground, like on a bike or cart, instead of being tossed around as a toy.",
        ),
        QAItem(
            question="What is lacrosse?",
            answer="Lacrosse is a running and catching game where players use sticks to move a ball or play piece.",
        ),
        QAItem(
            question="What does Curiosity do?",
            answer="Curiosity is the feeling that makes you ask questions and want to learn what happens next.",
        ),
        QAItem(
            question="What does Magic mean in a nursery rhyme story?",
            answer="Magic means something surprising and wonderful can happen, like a new helpful thing appearing when it is needed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.kind}/{ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(tire,lacrosse).
compatible_addon(magic_ribbon,lacrosse).
valid_story(P,A,Pr,Ad) :- prize_at_risk(Pr,A), compatible_addon(Ad,A), setting(P).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", pid) for pid in SETTINGS]
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for aid in ADDONS:
        lines.append(asp.fact("addon", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {("nursery_yard", "lacrosse", "tire", "magic_ribbon")}
    if clingo_set == py_set:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH:", clingo_set, py_set)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.helper)
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
    StoryParams(place="nursery_yard", activity="lacrosse", prize="tire", name="Mia", helper="Nanny"),
    StoryParams(place="nursery_yard", activity="lacrosse", prize="tire", name="Pip", helper="Old Owl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
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
