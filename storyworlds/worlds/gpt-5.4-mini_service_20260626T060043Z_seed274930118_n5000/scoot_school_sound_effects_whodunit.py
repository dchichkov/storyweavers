#!/usr/bin/env python3
"""
storyworlds/worlds/scoot_school_sound_effects_whodunit.py
==========================================================

A small school whodunit about scooting, sound effects, and a mystery that gets
solved by noticing what the noises mean.

The seed tale:
---
At school, Jun noticed a strange squeak-scrape-scoot sound in the hallway.
A class poster had slipped off the wall, and everybody wondered who made the mess.
Jun listened carefully, followed the sounds, and found that the teacher's rolling
chair had scooted into the poster board when the class rushed out for recess.
Together they straightened the poster, and the hallway went quiet again.
---

This script turns that premise into a tiny state-driven storyworld:
- physical meters: noise, clutter, distance, balance
- emotional memes: curiosity, worry, suspicion, relief
- a whodunit-style investigation that begins with a sound, turns on a clue,
  and ends with a clear reveal and a calmer school hallway
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

SOUNDS = ["squeak", "scrape", "scoot", "thump", "tap", "rustle"]
PLACES = ["hallway", "classroom", "library", "art room", "cafeteria"]
ROLES = ["student", "teacher", "custodian"]
OBJECTS = ["poster", "chair", "book cart", "supply bin", "marker tray"]
ACTIONS = ["scoot down the hall", "check the clue", "look under the poster", "follow the sound"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    movable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["noise", "clutter", "distance", "balance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "suspicion", "relief", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "teacher"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class SchoolSetting:
    place: str = "school"
    primary_spot: str = "the hallway"
    secondary_spot: str = "the classroom"


@dataclass
class StoryParams:
    place: str
    sound: str
    object: str
    name: str
    role: str
    seed: Optional[int] = None


@dataclass
class Rule:
    name: str
    apply: callable


class World:
    def __init__(self, setting: SchoolSetting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_noise(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"A {world.facts['sound']} sound echoed through the {world.setting.primary_spot}.")
        world.facts["heard_noise"] = True
    return out


def _r_clutter(world: World) -> list[str]:
    out = []
    poster = world.entities.get("poster")
    chair = world.entities.get("chair")
    if poster and chair and poster.meters["clutter"] >= THRESHOLD and chair.meters["distance"] >= THRESHOLD:
        sig = ("clutter",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        out.append("The poster had slipped, and the wall looked messy.")
        world.facts["messy_poster"] = True
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    chair = world.entities.get("chair")
    detective = world.entities.get("detective")
    poster = world.entities.get("poster")
    if not chair or not detective or not poster:
        return out
    if detective.memes["curiosity"] < THRESHOLD:
        return out
    if chair.meters["distance"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspicion"] = 0.0
    detective.memes["relief"] += 1
    out.append("Jun followed the clue and found the rolling chair near the poster board.")
    world.facts["reveal"] = "chair"
    return out


def _r_fix(world: World) -> list[str]:
    out = []
    poster = world.entities.get("poster")
    chair = world.entities.get("chair")
    if not poster or not chair:
        return out
    if poster.meters["clutter"] < THRESHOLD or chair.meters["distance"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    poster.meters["clutter"] = 0.0
    chair.meters["distance"] = 0.0
    for e in world.entities.values():
        e.memes["worry"] = max(0.0, e.memes["worry"] - 1)
        e.memes["relief"] += 1
    out.append("Together, they straightened the poster and rolled the chair back where it belonged.")
    return out


CAUSAL_RULES = [
    Rule("noise", _r_noise),
    Rule("clutter", _r_clutter),
    Rule("reveal", _r_reveal),
    Rule("fix", _r_fix),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "school":
        raise StoryError("This storyworld is set at school.")
    if params.sound not in SOUNDS:
        raise StoryError("Unknown sound choice.")
    if params.object not in OBJECTS:
        raise StoryError("Unknown object choice.")
    if params.role not in ROLES:
        raise StoryError("Unknown role choice.")


def build_story(world: World, params: StoryParams) -> World:
    detective = world.add(Entity(id=params.name, kind="character", type="student", label=params.name))
    teacher = world.add(Entity(id="teacher", kind="character", type="teacher", label="Ms. Pine"))
    object_e = world.add(Entity(id="chair", kind="thing", type="chair", label="rolling chair", movable=True))
    poster = world.add(Entity(id="poster", kind="thing", type="poster", label="class poster"))
    poster.caretaker = teacher.id

    world.facts.update(
        sound=params.sound,
        object=params.object,
        detective=detective,
        teacher=teacher,
        chair=object_e,
        poster=poster,
    )

    detective.memes["curiosity"] += 1
    detective.memes["worry"] += 1
    detective.meters["distance"] += 1
    object_e.meters["distance"] += 1
    object_e.meters["noise"] += 1
    poster.meters["clutter"] += 1

    world.say(f"At school, {params.name} heard a strange {params.sound}-squeak-scoot sound in the {world.setting.primary_spot}.")
    world.say(f"{params.name} was a little detective at heart, so {detective.pronoun().capitalize()} stopped to listen.")
    world.say(f"Everybody wondered what had happened to the {poster.label}.")

    world.para()
    world.say(f"{params.name} decided to {random.choice(ACTIONS)}.")
    propagate(world, narrate=True)
    detective.memes["curiosity"] += 1
    detective.memes["worry"] += 1
    object_e.meters["distance"] += 1

    world.para()
    world.say(f"{params.name} peeked closer, looked under the poster, and spotted the answer.")
    propagate(world, narrate=True)
    world.say(f"It was the {teacher.label_word if hasattr(teacher, 'label_word') else 'teacher'}'s rolling chair that had scooted into the poster board.")
    world.say(f"The mystery was solved, and the hallway felt calm again.")

    world.facts["solved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    chair = f["chair"]
    poster = f["poster"]
    sound = f["sound"]
    return [
        QAItem(
            question=f"What strange sound did {detective.id} hear at school?",
            answer=f"{detective.id} heard a {sound}-squeak-scoot sound in the hallway.",
        ),
        QAItem(
            question="What was wrong in the hallway?",
            answer="The class poster had slipped, and the hallway looked messy.",
        ),
        QAItem(
            question="What did Jun find that solved the mystery?",
            answer="Jun found that the rolling chair had scooted into the poster board.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The poster was straightened, the chair was rolled back, and the hallway went quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to scoot?",
            answer="To scoot means to move along in a quick sliding way, often with little steps or by rolling a chair.",
        ),
        QAItem(
            question="Why do sound effects help in a mystery?",
            answer="Sound effects can be clues because a detective can listen closely and figure out what caused the noise.",
        ),
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where someone tries to find out what happened and who caused it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    return [
        f"Write a school whodunit for a young child where {detective.id} hears a {f['sound']} sound and solves the mystery.",
        f"Tell a gentle detective story set at school that includes the word '{f['sound']}' and the action scoot.",
        f"Write a mystery story in which a child listens to a sound effect, follows the clue, and finds out what moved the poster.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {"school": SchoolSetting()}


@dataclass
class StoryParams:
    place: str = "school"
    sound: str = "scoot"
    object: str = "chair"
    name: str = "Jun"
    role: str = "student"
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="school", sound="scoot", object="chair", name="Jun", role="student"),
    StoryParams(place="school", sound="scrape", object="poster", name="Mina", role="student"),
    StoryParams(place="school", sound="squeak", object="book cart", name="Leo", role="student"),
]


ASP_RULES = r"""
heard_noise :- sound(scoot).
mystery_started :- heard_noise.
clue_found :- mystery_started.
solved :- clue_found.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "school")]
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for r in ROLES:
        lines.append(asp.fact("role", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A school whodunit with scoots and sound effects.")
    ap.add_argument("--place", choices=["school"])
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    params = StoryParams(
        place=args.place or "school",
        sound=args.sound or rng.choice(SOUNDS),
        object=args.object or rng.choice(OBJECTS),
        name=args.name or rng.choice(["Jun", "Mina", "Leo", "Sana", "Iris"]),
        role=args.role or "student",
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_story(World(SETTINGS[params.place]), params)
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
    import asp
    model = asp.one_model(asp_program("#show heard_noise/0.\n#show mystery_started/0.\n#show clue_found/0.\n#show solved/0."))
    atoms = {a.name for a in model}
    expected = {"heard_noise", "mystery_started", "clue_found", "solved"}
    if atoms == expected:
        print("OK: ASP twin produces the expected whodunit progression.")
        return 0
    print("MISMATCH in ASP twin:", sorted(atoms), "!=" , sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show heard_noise/0.\n#show mystery_started/0.\n#show clue_found/0.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show heard_noise/0.\n#show mystery_started/0.\n#show clue_found/0.\n#show solved/0."))
        print("ASP model:", " ".join(sorted(a.name for a in model)))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
