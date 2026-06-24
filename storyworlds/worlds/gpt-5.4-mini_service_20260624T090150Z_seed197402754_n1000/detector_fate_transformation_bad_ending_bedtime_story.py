#!/usr/bin/env python3
"""
A bedtime-story world about a little detector, a troubling fate, and a small
transformation that does not end as hoped.

The world is intentionally tiny:
- one child and one parent
- one bedtime object with a detector
- one gentle transformation
- one ending that stays child-facing but is a little sad or uneasy

The prose is driven by state changes:
- the detector can sense a fate
- the child can try to change the object's fate
- the transformation may or may not help
- the ending reflects the final state, including a bad ending when the change
  cannot be fully repaired
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    transformed: bool = False
    broken: bool = False
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    bedtime: bool = True
    words: tuple[str, ...] = ("quiet", "lamp", "blanket")


@dataclass
class DetectorSpec:
    label: str
    phrase: str
    sense: str
    fate: str
    turn: str
    result: str
    bad_result: str
    show: str


@dataclass
class TransformationSpec:
    label: str
    before: str
    after: str
    trigger: str
    cost: str
    risky: bool = True


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", bedtime=True),
    "nursery": Setting(place="the nursery", bedtime=True),
    "attic_room": Setting(place="the attic room", bedtime=True),
}

DETECTORS = {
    "dream_lamp": DetectorSpec(
        label="dream detector",
        phrase="a small dream detector with a silver button",
        sense="fate",
        fate="it sensed that the night would change",
        turn="the little light flickered and pointed at the toy",
        result="the child could see what would happen next",
        bad_result="the lamp grew dim and the room felt colder",
        show="dream",
    ),
    "clock_glass": DetectorSpec(
        label="fate detector",
        phrase="a round fate detector with a glass face",
        sense="fate",
        fate="it felt the ending coming before anyone else did",
        turn="the glass face shivered and turned dark",
        result="the child learned the toy's fate too soon",
        bad_result="the detector showed only a shadowy ending",
        show="fate",
    ),
    "night_bee": DetectorSpec(
        label="night detector",
        phrase="a little night detector shaped like a bee",
        sense="fate",
        fate="it buzzed softly when a change was near",
        turn="its tiny wings opened like a warning sign",
        result="the change could begin, but not be stopped",
        bad_result="the bee detector buzzed sadly in the dark",
        show="night",
    ),
}

TRANSFORMS = {
    "doll_to_owl": TransformationSpec(
        label="toy transformation",
        before="a soft doll with button eyes",
        after="a wise little owl toy",
        trigger="the moonlight touched it",
        cost="the doll could not stay exactly the same",
        risky=True,
    ),
    "bear_to_star": TransformationSpec(
        label="bedtime transformation",
        before="a sleepy bear plush",
        after="a star-shaped pillow",
        trigger="the child hugged it too tightly",
        cost="the bear's shape began to melt away",
        risky=True,
    ),
    "train_to_cloud": TransformationSpec(
        label="dream transformation",
        before="a toy train",
        after="a small cloud toy",
        trigger="the detector began to hum",
        cost="the wheels were gone for good",
        risky=True,
    ),
}

NAMES = ["Mia", "Luna", "Noah", "Eli", "Ava", "Nora", "Milo", "Ivy"]
GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    setting: str
    detector: str
    transformation: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DETECTORS:
            for t in TRANSFORMS:
                combos.append((s, d, t))
    return combos


def explain_invalid() -> str:
    return "No valid bedtime story can be built from those choices."


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    detector = DETECTORS[params.detector]
    trans = TRANSFORMS[params.transformation]

    toy = world.add(Entity(
        id="Toy",
        kind="thing",
        type="toy",
        label=trans.after,
        phrase=trans.before,
        owner=hero.id,
    ))
    gadget = world.add(Entity(
        id="Detector",
        kind="thing",
        type="detector",
        label=detector.label,
        phrase=detector.phrase,
        owner=hero.id,
    ))

    hero.memes["curiosity"] = 1
    hero.memes["worry"] = 0
    parent.memes["gentleness"] = 1

    world.facts.update(
        hero=hero, parent=parent, detector=detector, trans=trans, toy=toy, gadget=gadget
    )
    return world


def intro(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    toy: Entity = f["toy"]
    gadget: Entity = f["gadget"]
    world.say(
        f"At {world.setting.place}, little {hero.id} had {toy.phrase} and a {gadget.phrase}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked the soft bedtime quiet, and {hero.pronoun('possessive')} "
        f"{parent.type} sat nearby with a warm lamp and a patient smile."
    )


def detector_turn(world: World) -> None:
    f = world.facts
    det: DetectorSpec = f["detector"]
    toy: Entity = f["toy"]
    hero: Entity = f["hero"]
    toy.meters["tension"] = 1
    hero.memes["worry"] += 1
    world.say(
        f"Then the {det.label} stirred. {det.fate.capitalize()}, and {det.turn}."
    )
    world.say(
        f"{hero.id} looked at {toy.phrase} and whispered, "
        f"\"What is its fate tonight?\""
    )


def try_transformation(world: World) -> None:
    f = world.facts
    trans: TransformationSpec = f["trans"]
    toy: Entity = f["toy"]
    hero: Entity = f["hero"]
    toy.transformed = True
    toy.label = trans.after
    toy.hidden = False
    hero.memes["hope"] = 1
    world.say(
        f"{hero.id} tried a small transformation. {trans.trigger.capitalize()}, and the toy changed."
    )
    world.say(
        f"It became {trans.after}, but {trans.cost}."
    )


def bad_ending(world: World) -> None:
    f = world.facts
    det: DetectorSpec = f["detector"]
    toy: Entity = f["toy"]
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]

    if toy.transformed:
        toy.broken = True
        hero.memes["worry"] += 1
        world.say(
            f"That was not quite the ending {hero.id} wanted. The change could not be undone."
        )
        world.say(
            f"The {det.label} showed a shadowy fate, and {det.bad_result}."
        )
        world.say(
            f"{hero.id} curled up under the blanket while {parent.type} held the lamp a little closer."
        )
    else:
        world.say(
            f"The room stayed quiet, but the detector kept its secret about fate."
        )


def ending_image(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    toy: Entity = f["toy"]
    world.say(
        f"In the end, {hero.id} lay still and listened to the soft night, while {toy.label} rested by the pillow."
    )
    if toy.broken:
        world.say(
            "It was a small, sad bedtime ending, with the room calm but the toy changed forever."
        )
    else:
        world.say(
            "The room was calm, though the detector's warning still felt like a little shadow."
        )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    det: DetectorSpec = f["detector"]
    trans: TransformationSpec = f["trans"]
    return [
        f'Write a gentle bedtime story about {hero.id}, a {det.label}, and a small fate change.',
        f'Tell a child-friendly story where a detector notices fate and a toy goes through a transformation.',
        f'Write a bedtime story with a little mystery, a transformation, and a bad ending that stays calm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    det: DetectorSpec = f["detector"]
    trans: TransformationSpec = f["trans"]
    toy: Entity = f["toy"]
    return [
        QAItem(
            question=f"What did {hero.id} have beside the bed?",
            answer=f"{hero.id} had {toy.phrase} and a {det.phrase} beside the bed.",
        ),
        QAItem(
            question=f"What did the detector sense?",
            answer=f"The detector sensed fate, which meant the night would change.",
        ),
        QAItem(
            question=f"What transformation happened to the toy?",
            answer=f"The toy changed from {trans.before} into {trans.after}.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                "The ending was bad because the change could not be undone, so the toy stayed changed."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detector?",
            answer="A detector is a thing that notices or senses something and gives a sign about it.",
        ),
        QAItem(
            question="What does fate mean in a bedtime story?",
            answer="Fate is what is going to happen, even before the characters know it.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
detector(D) :- detector_fact(D).
transformation(T) :- transformation_fact(T).

story(S,D,T) :- setting(S), detector(D), transformation(T).
has_fate(D) :- detector_facts(D, fate).
does_transform(T) :- transformation_facts(T, before, after).

valid_story(S,D,T) :- story(S,D,T), has_fate(D), does_transform(T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for d in DETECTORS:
        lines.append(asp.fact("detector_fact", d))
        lines.append(asp.fact("detector_facts", d, "fate"))
    for t, spec in TRANSFORMS.items():
        lines.append(asp.fact("transformation_fact", t))
        lines.append(asp.fact("transformation_facts", t, spec.before, spec.after))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("Only in python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with detector, fate, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detector", choices=DETECTORS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if args.gender and args.name:
        pass
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.detector:
        combos = [c for c in combos if c[1] == args.detector]
    if args.transformation:
        combos = [c for c in combos if c[2] == args.transformation]
    if not combos:
        raise StoryError(explain_invalid())
    setting, detector, transformation = rng.choice(combos)
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(setting=setting, detector=detector, transformation=transformation, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    intro(world)
    world.para()
    detector_turn(world)
    world.para()
    try_transformation(world)
    world.para()
    bad_ending(world)
    ending_image(world)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.transformed:
            bits.append("transformed=True")
        if e.broken:
            bits.append("broken=True")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bedroom", "dream_lamp", "doll_to_owl", "Mia", "girl", "mother"),
            StoryParams("nursery", "clock_glass", "bear_to_star", "Noah", "boy", "father"),
            StoryParams("attic_room", "night_bee", "train_to_cloud", "Ava", "girl", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
