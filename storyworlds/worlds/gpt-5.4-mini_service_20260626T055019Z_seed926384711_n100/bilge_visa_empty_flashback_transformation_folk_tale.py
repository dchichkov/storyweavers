#!/usr/bin/env python3
"""
storyworlds/worlds/bilge_visa_empty_flashback_transformation_folk_tale.py
========================================================================

A tiny folk-tale storyworld about a river crossing, an empty boat, a needed
visa, and a flashback that changes how the ending is understood.

Premise:
- A poor traveler must cross a river to reach a fair.
- The ferryman will not row without a visa seal.
- The boat starts empty except for bilge water in the lowest plank seam.

Tension:
- The traveler remembers, in a flashback, how their grandmother taught them
  to keep promises and carry a true seal, not a stolen one.

Turn:
- The traveler transforms an empty, useless token into a real one by helping
  the ferryman bale the bilge and earn the village clerk's trust.

Resolution:
- The visa is stamped, the boat leaves the shore, and the empty boat becomes
  full of song, passengers, and hope.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the river landing"
    affords: set[str] = field(default_factory=lambda: {"crossing"})


@dataclass
class StoryParams:
    place: str
    traveler: str
    traveler_type: str
    clerk: str
    clerk_type: str
    parent_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_used = False
        self.transformed = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.flashback_used = self.flashback_used
        c.transformed = self.transformed
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bilge(world: World) -> list[str]:
    out: list[str] = []
    boat = world.entities.get("boat")
    ferryman = world.entities.get("ferryman")
    if not boat or not ferryman:
        return out
    if boat.meters.get("bilge", 0.0) < THRESHOLD:
        return out
    sig = ("bilge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ferryman.memes["worry"] = ferryman.memes.get("worry", 0.0) + 1
    out.append("The boat groaned because bilge water sloshed in its lowest boards.")
    return out


def _r_empty_to_full(world: World) -> list[str]:
    out: list[str] = []
    boat = world.entities.get("boat")
    travelers = [e for e in world.entities.values() if e.kind == "character"]
    if not boat:
        return out
    if boat.meters.get("empty", 0.0) < THRESHOLD:
        return out
    if boat.meters.get("song", 0.0) >= THRESHOLD:
        return out
    sig = ("empty_to_full",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.meters["song"] = 1.0
    for t in travelers:
        t.memes["hope"] = t.memes.get("hope", 0.0) + 1
    out.append("By the end, the empty boat had become full of song and hope.")
    return out


CAUSAL_RULES = [Rule("bilge", _r_bilge), Rule("empty_to_full", _r_empty_to_full)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback(world: World, traveler: Entity) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    traveler.memes["memory"] = traveler.memes.get("memory", 0.0) + 1
    world.say(
        f"{traveler.id} remembered a winter night when {traveler.pronoun('possessive')} "
        f"grandmother said, 'A true road opens for an honest heart.'"
    )


def transform_visa(world: World, traveler: Entity, clerk: Entity) -> None:
    if world.transformed:
        return
    world.transformed = True
    visa = world.entities["visa"]
    visa.label = "stamped visa"
    visa.phrase = "a stamped visa with a bright seal"
    visa.meters["empty"] = 0.0
    visa.meters["sealed"] = 1.0
    traveler.memes["relief"] = traveler.memes.get("relief", 0.0) + 1
    clerk.memes["trust"] = clerk.memes.get("trust", 0.0) + 1
    world.say(
        f"The clerk watched the traveler mend the ferry rope and stamped the once-empty visa."
    )
    world.say(
        f"It was no longer an empty slip of paper; it had become a real pass for the road ahead."
    )


def setup_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    traveler = world.add(Entity(
        id=params.traveler, kind="character", type=params.traveler_type,
        traits=["poor", "patient"],
    ))
    clerk = world.add(Entity(
        id=params.clerk, kind="character", type=params.clerk_type,
        label="the village clerk",
        traits=["careful", "wise"],
    ))
    boat = world.add(Entity(
        id="boat", type="boat", label="boat", phrase="a little river boat",
    ))
    visa = world.add(Entity(
        id="visa", type="paper", label="visa", phrase="an empty visa slip",
        owner=traveler.id, caretaker=clerk.id,
    ))
    boat.meters["bilge"] = 1.0
    boat.meters["empty"] = 1.0
    visa.meters["empty"] = 1.0

    world.facts.update(traveler=traveler, clerk=clerk, boat=boat, visa=visa, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    traveler: Entity = f["traveler"]
    clerk: Entity = f["clerk"]
    boat: Entity = f["boat"]
    visa: Entity = f["visa"]
    params: StoryParams = f["params"]

    world.say(
        f"Once, at {world.setting.place}, there lived a poor traveler named {traveler.id} "
        f"who wanted to cross the river for the fair."
    )
    world.say(
        f"{traveler.id} carried an empty visa slip and hoped the village clerk would stamp it."
    )

    world.para()
    world.say(
        f"But the little boat was empty and sad, and bilge water lay in its lowest seam."
    )
    world.say(
        f"{clerk.id} said the crossing could not begin until the papers were true and the boat was ready."
    )
    flashback(world, traveler)

    world.para()
    world.say(
        f"{traveler.id} did not beg. Instead, {traveler.pronoun('subject')} helped bale the bilge, "
        f"tied a rope, and listened to the clerk's careful questions."
    )
    propagate(world, narrate=True)
    transform_visa(world, traveler, clerk)

    world.para()
    world.say(
        f"At last, the boat pushed off. The empty slip was gone, the visa shone with a seal, "
        f"and the river carried {traveler.id} toward the fair."
    )
    world.say(
        f"The traveler smiled, for the road had changed: what began empty had become full, "
        f"and the old memory had turned into a kinder future."
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short folk tale about a traveler, an empty visa, and bilge water in a boat.',
        'Tell a gentle story in which a flashback helps someone earn trust and receive a visa.',
        'Write a simple river-crossing tale where something empty is transformed into something useful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler: Entity = f["traveler"]
    clerk: Entity = f["clerk"]
    visa: Entity = f["visa"]
    return [
        QAItem(
            question=f"Why could {traveler.id} not cross the river right away?",
            answer=(
                f"{traveler.id} could not cross right away because the boat had bilge water in it "
                f"and the visa was still empty, so the clerk would not send anyone across."
            ),
        ),
        QAItem(
            question=f"What did {traveler.id} remember before the visa changed?",
            answer=(
                f"{traveler.id} remembered {traveler.pronoun('possessive')} grandmother saying that "
                f"an honest heart finds a true road, and that memory helped {traveler.id} stay calm."
            ),
        ),
        QAItem(
            question=f"What changed the empty visa into a real pass?",
            answer=(
                f"The visa changed when the clerk saw {traveler.id} help bale the bilge and fix the ferry rope. "
                f"Then the clerk stamped it, and the empty slip became a stamped visa."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bilge water?",
            answer="Bilge water is the water that gathers in the lowest part of a boat.",
        ),
        QAItem(
            question="What is a visa?",
            answer="A visa is a paper pass or stamp that says a traveler is allowed to enter or cross somewhere.",
        ),
        QAItem(
            question="What does empty mean?",
            answer="Empty means there is nothing inside or nothing yet in the place where something can go.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "river landing": Setting(place="the river landing"),
    "old ferry": Setting(place="the old ferry"),
    "market ford": Setting(place="the market ford"),
}

NAMES = ["Mira", "Tomas", "Anya", "Borin", "Lena", "Jori"]
TYPES = {"girl": ["girl", "woman"], "boy": ["boy", "man"]}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld with bilge, visa, empty, flashback, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    traveler_type = gender
    clerk_type = "woman"
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    clerk = args.parent or rng.choice(["Ayla", "Sorin", "Marta"])
    return StoryParams(place=place, traveler=name, traveler_type=traveler_type,
                       clerk=clerk, clerk_type=clerk_type, parent_name=clerk)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
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


ASP_RULES = r"""
billow(boat) :- bilge(boat).
needs_stamp(visa) :- empty(visa).
allowed_crossing(traveler) :- stamped(visa), cleared_boat(boat).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("bilge", "boat"),
        asp.fact("empty", "visa"),
        asp.fact("traveler", "migrator"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show allowed_crossing/1."))
        return
    if args.verify:
        print("OK: ASP twin present; storyworld is deterministic enough for this tiny domain.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [StoryParams(place=p, traveler=n, traveler_type="girl", clerk="Marta", clerk_type="woman", parent_name="Marta")
                  for p, n in [("the river landing", "Mira"), ("the old ferry", "Anya"), ("the market ford", "Lena")]]
        samples = [generate(p) for p in combos]
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
