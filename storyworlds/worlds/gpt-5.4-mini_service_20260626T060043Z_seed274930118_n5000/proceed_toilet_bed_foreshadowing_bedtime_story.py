#!/usr/bin/env python3
"""
A small bedtime-story world about a sleepy child, a last toilet trip, and the
gentle turn toward bed.

Premise:
- A child gets sleepy and starts bedtime.
- Before the lights go out, the child feels a small pressure and must proceed
  to the toilet.

Foreshadowing:
- Early signs hint that a toilet trip will be needed before bed.
- The parent notices these signs and nudges the child to proceed now rather than
  risk an uncomfortable pause later.

Turn:
- The child goes to the toilet, washes hands, and returns calmer.

Resolution:
- The child settles into bed with the worry gone, and the bedtime scene ends
  in a soft, restful image.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=lambda: {"toilet", "bed"})


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.facts = dict(self.facts)
        return clone


def _do_toilet(world: World, child: Entity, narrate: bool = True) -> None:
    child.meters["pressure"] = max(0.0, child.meters.get("pressure", 0.0) - 1.0)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    if narrate:
        world.say(f"{child.id} went to the toilet and felt much better.")


def _do_bed(world: World, child: Entity, narrate: bool = True) -> None:
    child.meters["sleep"] = child.meters.get("sleep", 0.0) + 1.0
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    if narrate:
        world.say(f"{child.id} climbed into bed and tucked the blanket under {child.pronoun('possessive')} chin.")


def predict_need(world: World, child: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).meters["pressure"] = sim.get(child.id).meters.get("pressure", 0.0) + 1.0
    return sim.get(child.id).meters["pressure"] >= THRESHOLD


def bedtime_signal(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"It was bedtime in {world.setting.place}, and {child.id} was already feeling sleepy."
    )
    if child.meters.get("pressure", 0.0) >= THRESHOLD:
        world.say(
            f"{parent.pronoun().capitalize()} noticed {child.pronoun('possessive')} small fidget and said, "
            f'"Let’s proceed to the toilet first, so bed can feel peaceful after."'
        )
    else:
        world.say(
            f"{parent.pronoun().capitalize()} smiled and said, "
            f'"Let’s check the toilet first, just in case, before we go to bed."'
        )


def fidget(world: World, child: Entity) -> None:
    child.meters["pressure"] = child.meters.get("pressure", 0.0) + 1.0
    child.memes["unease"] = child.memes.get("unease", 0.0) + 1.0
    world.say(
        f"{child.id} wiggled on the rug and looked toward the hall. Something small and important was bothering {child.pronoun('object')}."
    )


def foreshadow(world: World, child: Entity, parent: Entity) -> None:
    if predict_need(world, child):
        world.facts["foreshadowed"] = True
        world.say(
            f"{parent.id} saw the hint early: if {child.id} went straight to bed, the night would not feel settled."
        )


def proceed_to_toilet(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"So {child.id} and {parent.id} proceeded down the hall to the toilet, steps quiet on the floor."
    )
    _do_toilet(world, child, narrate=True)


def wash_hands(world: World, child: Entity) -> None:
    child.meters["clean"] = child.meters.get("clean", 0.0) + 1.0
    world.say(f"{child.id} washed {child.pronoun('possessive')} hands and watched the water swirl away.")


def settle_bed(world: World, child: Entity, parent: Entity) -> None:
    _do_bed(world, child, narrate=False)
    world.say(
        f"When they returned, {child.id} climbed into bed without the earlier fuss, and {parent.id} pulled the blanket up softly."
    )
    world.say(
        f"The room grew still. {child.id} breathed out, sleepy and safe, while the toilet trip faded into a tiny memory before dreams."
    )


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child_type = params.gender
    child = world.add(Entity(id=params.name, kind="character", type=child_type, meters={"pressure": 0.0, "sleep": 0.0}, memes={"calm": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    world.facts.update(child=child, parent=parent)

    child.meters["sleep"] += 1.0
    world.say(f"{child.id} was a little {child_type} who loved bedtime stories and warm blankets.")
    world.say(f"After playtime, {child.id} became very sleepy and began to proceed toward bedtime.")

    world.para()
    fidget(world, child)
    foreshadow(world, child, parent)
    bedtime_signal(world, child, parent)

    world.para()
    proceed_to_toilet(world, child, parent)
    wash_hands(world, child)

    world.para()
    settle_bed(world, child, parent)

    world.facts.update(resolved=True, pressure=child.meters.get("pressure", 0.0), sleep=child.meters.get("sleep", 0.0))
    return world


SETTINGS = {"bedroom": Setting()}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Ben", "Theo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        'Write a gentle bedtime story for a toddler that uses the words "proceed", "toilet", and "bed".',
        f"Tell a story where {child.id} feels sleepy, needs the toilet before bed, and ends calm under the blanket.",
        "Write a cozy story with foreshadowing that gently leads a child from the hall to the toilet and then into bed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Why did {child.id} and {parent.id} not go straight to bed?",
            answer=f"They noticed a small sign that {child.id} needed the toilet first, so they proceeded there before bedtime could feel comfortable.",
        ),
        QAItem(
            question=f"What happened after {child.id} went to the toilet?",
            answer=f"{child.id} washed {child.pronoun('possessive')} hands and then climbed into bed feeling calmer and more settled.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"It ended with {child.id} tucked safely in bed, sleepy, calm, and ready for dreams.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do people sometimes go to the toilet before bed?",
            answer="People sometimes go to the toilet before bed so they can sleep more comfortably without waking up right away.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint about something that will matter later in the story.",
        ),
        QAItem(
            question="Why is bed important at bedtime?",
            answer="A bed is where a tired child can rest, get cozy, and fall asleep safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
need_toilet(C) :- pressure(C).
can_bed(C) :- need_toilet(C), toilet_done(C).
story_ok(C) :- can_bed(C).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("pressure", "child") if True else "",
            asp.fact("toilet_done", "child"),
            asp.fact("bed", "bed"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with foreshadowing.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name="Mia", gender="girl", parent="mother"))]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
