#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mane_crinkle_thrush_lesson_learned_teamwork_animal.py
================================================================================================

A small animal-story world about a proud mane, a troublesome crinkle, and a thrush
who helps turn a mistake into a lesson learned through teamwork.

Premise:
- A young lion has a fluffy mane he likes to keep neat.
- A windy trail or thorny brush can make the mane crinkle and tangle.
- A thrush notices the trouble and offers a careful, helpful plan.

State-driven arc:
- The lion wants to race off and ignore the mess.
- The thrush explains that rushing will only make the crinkle worse.
- They work together: one holds still, one pulls out twigs and smooths fur.
- The lion learns that teamwork makes hard fixes easier.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- world state drives prose
- invalid choices raise StoryError
- includes inline ASP_RULES and asp_facts()
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"crinkle": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "patience": 0.0, "worry": 0.0, "joy": 0.0, "teamwork": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lion", "male lion", "thrush", "bird"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the sunny savanna edge"
    affords: set[str] = field(default_factory=lambda: {"wind", "brush"})


@dataclass
class Hair:
    label: str
    phrase: str
    region: str = "head"
    prone_to: str = "crinkle"


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    helps_with: str = "crinkle"


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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_crinkle(world: World) -> list[str]:
    out: list[str] = []
    lion = world.get("lion")
    mane = world.get("mane")
    if lion.memes["rush"] < THRESHOLD:
        return out
    sig = ("crinkle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mane.meters["crinkle"] += 1
    lion.memes["worry"] += 1
    out.append("The mane picked up a crinkle in the wind.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    lion = world.get("lion")
    if lion.memes["teamwork"] < THRESHOLD or lion.memes["patience"] < THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lion.memes["lesson"] += 1
    out.append("The lion learned that careful teamwork could fix a problem faster than stubborn rushing.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_crinkle, _r_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_rush(world: World, lion: Entity) -> None:
    lion.memes["rush"] += 1
    lion.memes["worry"] += 1
    world.say(f"{lion.id} wanted to race ahead through {world.setting.place}.")
    world.say(f"{lion.pronoun().capitalize()} shook {lion.pronoun('possessive')} head, and the fluffy mane bounced in the wind.")
    propagate(world)


def _do_warn(world: World, thrush: Entity, lion: Entity, mane: Entity) -> None:
    thrush.memes["worry"] += 1
    thrush.memes["patience"] += 1
    world.say(
        f"A little thrush fluttered down beside {lion.id} and said, "
        f'"If you keep rushing, your {mane.label} will only get more crinkled."'
    )
    lion.memes["worry"] += 1


def _do_teamwork(world: World, thrush: Entity, lion: Entity, mane: Entity) -> None:
    lion.memes["teamwork"] += 1
    thrush.memes["teamwork"] += 1
    lion.memes["patience"] += 1
    world.say(
        f"{lion.id} slowed down and let {thrush.id} help. {thrush.pronoun().capitalize()} pecked out tiny twigs "
        f"while {lion.id} held still and waited."
    )
    world.say(
        f"Together they smoothed the {mane.label}, and the wild little crinkle began to fall away."
    )
    mane.meters["crinkle"] = 0.0
    mane.meters["clean"] += 1
    lion.memes["joy"] += 1
    propagate(world)


def tell(setting: Setting) -> World:
    world = World(setting)
    lion = world.add(Entity(id="lion", kind="character", type="lion", label="young lion", traits=["proud", "playful"]))
    thrush = world.add(Entity(id="thrush", kind="character", type="thrush", label="small thrush", traits=["quick", "kind"]))
    mane = world.add(Entity(id="mane", type="mane", label="mane", phrase="a fluffy gold mane", owner="lion", caretaker="lion"))
    world.facts["lion"] = lion
    world.facts["thrush"] = thrush
    world.facts["mane"] = mane

    world.say(f"{lion.id} was a young lion with {mane.phrase} that he loved to keep neat.")
    world.say(f"{thrush.id} was a small thrush who noticed when another animal needed help.")
    world.para()

    world.say(f"One breezy morning at {setting.place}, {lion.id} tried to dash through the brush.")
    _do_rush(world, lion)
    _do_warn(world, thrush, lion, mane)
    world.para()

    world.say(f"{lion.id} paused and listened.")
    _do_teamwork(world, thrush, lion, mane)
    world.say(
        f"In the end, {lion.id}'s mane lay smooth again, and {lion.id} remembered a lesson learned: "
        f"it is easier to fix a crinkle when friends work together."
    )
    return world


SETTINGS = {
    "savanna": Setting(place="the sunny savanna edge", affords={"wind", "brush"}),
    "grove": Setting(place="the acacia grove", affords={"wind", "brush"}),
    "path": Setting(place="the dusty animal path", affords={"wind", "brush"}),
}


@dataclass
class StoryParams:
    place: str = "savanna"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: mane, crinkle, thrush, teamwork, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
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
    return StoryParams(place=place)


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short Animal Story about a lion, a crinkled mane, and a thrush who helps.",
        f"Tell a gentle story set at {world.setting.place} where teamwork fixes a mane crinkle.",
        "Write a lesson learned story where an animal listens to a helpful bird.",
    ]


def story_qa(world: World) -> list[QAItem]:
    lion = world.get("lion")
    thrush = world.get("thrush")
    mane = world.get("mane")
    return [
        QAItem(
            question="Who had the crinkled mane?",
            answer=f"{lion.id} had the crinkled {mane.label}, and he wanted it neat again.",
        ),
        QAItem(
            question="Who helped fix the mane?",
            answer=f"{thrush.id}, the little thrush, helped by pecking out twigs while {lion.id} stayed still.",
        ),
        QAItem(
            question="What lesson did the lion learn?",
            answer="He learned that teamwork and patience make hard fixes easier.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means two or more helpers work together to reach the same goal.",
        ),
        QAItem(
            question="What is a thrush?",
            answer="A thrush is a small songbird with a thin beak and a quick way of helping or searching for food.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% setting(P). character(E). mane(M). thrush(T).
% rush(E). helps(T). crinkled(M) :- rush(lion).

crinkled(M) :- rush(lion), mane(M).
lesson_learned(lion) :- teamwork(lion, thrush), patience(lion).
teamwork(lion, thrush) :- helped(thrush, lion), listened(lion).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "savanna"),
        asp.fact("setting", "grove"),
        asp.fact("setting", "path"),
        asp.fact("character", "lion"),
        asp.fact("character", "thrush"),
        asp.fact("mane", "mane"),
        asp.fact("rush", "lion"),
        asp.fact("helped", "thrush", "lion"),
        asp.fact("listened", "lion"),
        asp.fact("patience", "lion"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show crinkled/1. #show lesson_learned/1. #show teamwork/2."))
    crinkled = set(asp.atoms(model, "crinkled"))
    lesson = set(asp.atoms(model, "lesson_learned"))
    teamwork = set(asp.atoms(model, "teamwork"))
    ok = (("mane",) in crinkled and ("lion",) in lesson and ("lion", "thrush") in teamwork)
    if ok:
        print("OK: ASP twin produces the expected animal-story relations.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected relations.")
    print("crinkled:", sorted(crinkled))
    print("lesson_learned:", sorted(lesson))
    print("teamwork:", sorted(teamwork))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place])
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"PROMPT {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [StoryParams(place="savanna"), StoryParams(place="grove"), StoryParams(place="path")]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show crinkled/1. #show lesson_learned/1. #show teamwork/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show crinkled/1. #show lesson_learned/1. #show teamwork/2."))
        print("crinkled:", sorted(set(asp.atoms(model, "crinkled"))))
        print("lesson_learned:", sorted(set(asp.atoms(model, "lesson_learned"))))
        print("teamwork:", sorted(set(asp.atoms(model, "teamwork"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
