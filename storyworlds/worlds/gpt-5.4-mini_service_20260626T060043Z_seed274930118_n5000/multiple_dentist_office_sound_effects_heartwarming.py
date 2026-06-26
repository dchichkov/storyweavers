#!/usr/bin/env python3
"""
Story world: multiple dentist-office sound effects, heartwarming style.

A small child comes to a dentist office, hears several tool sounds, feels
nervous, and then calms down with a gentle explanation, a helper, and a warm
ending image that proves the fear changed into relief.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class SoundEffect:
    id: str
    label: str
    source: str
    gentle_meaning: str
    scare: str
    role: str = "tool"


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    effect: str
    helps_against: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    helper: str
    sound: str
    comfort: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HELPER_NAMES = {
    "dentist": ("Dr. June", "dentist"),
    "hygienist": ("Mina", "hygienist"),
    "assistant": ("Tara", "assistant"),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Ava", "Mia", "Zoe"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Noah", "Ben", "Sam"]
TRAITS = ["brave", "curious", "gentle", "shy", "thoughtful", "small"]

SOUND_EFFECTS = {
    "whirr": SoundEffect(
        id="whirr",
        label="whirr-whirr",
        source="little spinning brush",
        gentle_meaning="the brush was just cleaning tiny teeth",
        scare="the spinning brush sounded too fast",
    ),
    "tap": SoundEffect(
        id="tap",
        label="tap-tap",
        source="small mirror",
        gentle_meaning="the mirror was checking each tooth carefully",
        scare="the tapping sounded like a tiny drumbeat",
    ),
    "suction": SoundEffect(
        id="suction",
        label="slurp-slurp",
        source="gentle suction straw",
        gentle_meaning="the straw was sipping away water",
        scare="the slurping sounded surprising",
    ),
    "spray": SoundEffect(
        id="spray",
        label="psst-psst",
        source="water sprayer",
        gentle_meaning="the sprayer was rinsing the mouth with a cool mist",
        scare="the mist hissed like a secret snake",
    ),
    "click": SoundEffect(
        id="click",
        label="click-click",
        source="bright little counter",
        gentle_meaning="the counter was making neat counting sounds",
        scare="the clicking sounded sharp at first",
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket with tiny stars",
        effect="felt like a hug",
        helps_against={"whirr", "suction"},
    ),
    "headphones": Comfort(
        id="headphones",
        label="music headphones",
        phrase="headphones that played a quiet song",
        effect="turned the room into a calmer place",
        helps_against={"whirr", "tap", "click"},
    ),
    "stuffie": Comfort(
        id="stuffie",
        label="a stuffed bunny",
        phrase="a stuffed bunny with floppy ears",
        effect="gave the child something warm to hold",
        helps_against={"spray", "suction"},
    ),
}


class WorldModel:
    def __init__(self, params: StoryParams) -> None:
        self.world = World()
        self.params = params
        self.helper_role = HELPER_NAMES[params.helper][1]
        self.child = self.world.add(Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.name,
            memes=defaultdict(float),
            meters=defaultdict(float),
        ))
        helper_name, helper_role = HELPER_NAMES[params.helper]
        self.helper = self.world.add(Entity(
            id="helper",
            kind="character",
            type=self.helper_role,
            label=helper_name,
            memes=defaultdict(float),
            meters=defaultdict(float),
        ))
        self.parent = self.world.add(Entity(
            id="parent",
            kind="character",
            type=params.parent,
            label=params.parent,
            memes=defaultdict(float),
            meters=defaultdict(float),
        ))
        self.sound = SOUND_EFFECTS[params.sound]
        self.comfort = COMFORTS[params.comfort]
        self.comfort_item = self.world.add(Entity(
            id="comfort",
            type="thing",
            label=self.comfort.label,
            phrase=self.comfort.phrase,
            owner=self.child.id,
        ))
        self.comfort_item.meters["present"] += 1

    def speak_setup(self) -> None:
        name = self.child.id
        self.world.say(f"{name} was a little {next(t for t in TRAITS if t != 'brave')} {self.child.type} who went to the dentist office with {self.parent.label}.")
        self.world.say(f"{name} liked to bring {self.comfort.phrase} because it made waiting feel less scary.")
        self.world.say(f"Inside the office, the air smelled clean and the chair looked tall and shiny.")

    def sound_turn(self) -> None:
        name = self.child.id
        self.child.memes["nervous"] += 1
        self.child.meters["tightness"] += 1
        self.world.say(f"Then the room made {self.sound.label} from {self.sound.source}.")
        self.world.say(f"At first, {name} thought {self.sound.scare}.")
        self.world.say(f"{name} squeezed {self.comfort.label} and leaned close to {self.parent.label}.")

    def comfort_turn(self) -> None:
        name = self.child.id
        self.helper.memes["kindness"] += 1
        self.world.say(f"{self.helper.label} smiled and said, \"That sound means {self.sound.gentle_meaning}.\"")
        self.world.say(f"{self.helper.label} showed {name} how the chair moved slowly and how each tool had a small job.")
        self.world.say(f"{self.comfort.label.capitalize()} {self.comfort.effect}, and {name}'s shoulders dropped a little.")
        self.child.memes["calm"] += 1
        self.child.meters["tightness"] = max(0.0, self.child.meters["tightness"] - 1)

    def ending(self) -> None:
        name = self.child.id
        self.world.para()
        self.world.say(f"By the end, {name} listened to one sound after another: {self.sound.label}, a gentle click, and a quiet rinse.")
        self.world.say(f"Nothing felt frightening anymore, because every noise had a kind meaning and a careful hand behind it.")
        self.world.say(f"{name} smiled with {self.parent.label} and {self.helper.label} while {self.comfort.label} stayed tucked close like a tiny shield.")

    def build(self) -> World:
        self.speak_setup()
        self.world.para()
        self.sound_turn()
        self.comfort_turn()
        self.ending()
        self.world.facts = {
            "child": self.child,
            "helper": self.helper,
            "parent": self.parent,
            "sound": self.sound,
            "comfort": self.comfort,
        }
        return self.world


def valid_combo(sound: SoundEffect, comfort: Comfort) -> bool:
    return sound.id in comfort.helps_against


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, sound in SOUND_EFFECTS.items():
        for cid, comfort in COMFORTS.items():
            if valid_combo(sound, comfort):
                combos.append((sid, cid))
    return combos


def explain_rejection(sound: SoundEffect, comfort: Comfort) -> str:
    return (
        f"(No story: {comfort.label} would not really help with {sound.label}. "
        f"The ending needs a comfort that matches the sound and makes the fear softer.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming dentist-office story world with multiple sound effects.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--helper", choices=list(HELPER_NAMES))
    ap.add_argument("--sound", choices=list(SOUND_EFFECTS))
    ap.add_argument("--comfort", choices=list(COMFORTS))
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
    helper = args.helper or rng.choice(list(HELPER_NAMES))
    sound = args.sound or rng.choice(list(SOUND_EFFECTS))
    comfort = args.comfort or rng.choice([c for c in COMFORTS if valid_combo(SOUND_EFFECTS[sound], COMFORTS[c])])
    if args.sound and args.comfort and not valid_combo(SOUND_EFFECTS[args.sound], COMFORTS[args.comfort]):
        raise StoryError(explain_rejection(SOUND_EFFECTS[args.sound], COMFORTS[args.comfort]))
    if args.gender and args.name:
        pass
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if args.name:
        gender = "girl" if args.name in GIRL_NAMES else "boy"
    return StoryParams(name=name, gender=gender, parent=parent, helper=helper, sound=sound, comfort=comfort)


def generation_prompts(sample: World) -> list[str]:
    f = sample.facts
    child = f["child"].id
    sound = f["sound"].label
    helper = f["helper"].label
    comfort = f["comfort"].label
    return [
        f'Write a heartwarming story for a young child about a dentist office where {child} hears {sound}.',
        f"Tell a gentle story that includes multiple sound effects, a caring helper named {helper}, and {comfort}.",
        f"Write a simple story in a dentist office where a child feels nervous, learns the noises are kind, and feels safe again.",
    ]


def story_qa(sample: World) -> list[QAItem]:
    f = sample.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    sound = f["sound"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"Why did {child.id} feel nervous in the dentist office?",
            answer=f"{child.id} felt nervous because {sound.label} sounded surprising at first, even though it was only a tool doing its job.",
        ),
        QAItem(
            question=f"Who helped explain the sounds to {child.id}?",
            answer=f"{helper.label} helped by explaining that {sound.label} had a gentle meaning and by showing {child.id} each small job in the room.",
        ),
        QAItem(
            question=f"What comfort helped {child.id} stay calm?",
            answer=f"{comfort.label.capitalize()} helped because it was something soft and familiar for {child.id} to hold while the appointment went on.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"It ended with {child.id} smiling beside {parent.label} and {helper.label}, after learning that the noises were safe and kind.",
        ),
    ]


def world_knowledge_qa(sample: World) -> list[QAItem]:
    f = sample.facts
    sound = f["sound"]
    comfort = f["comfort"]
    return [
        QAItem(
            question="What is a dentist office for?",
            answer="A dentist office is a place where people go to check their teeth, clean them, and keep their mouths healthy.",
        ),
        QAItem(
            question=f"What does {sound.label} sound like?",
            answer=f"{sound.label.capitalize()} is a little sound effect that can make a tool seem busy, but it does not mean anything bad is happening.",
        ),
        QAItem(
            question=f"Why can {comfort.label} help a child?",
            answer=f"{comfort.label.capitalize()} can help because soft, familiar things make a scary moment feel more like home.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
sound_help(S, C) :- sound(S), comfort(C), helps(C, S).
valid(S, C) :- sound(S), comfort(C), sound_help(S, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_label", sid, s.label))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for s in sorted(c.helps_against):
            lines.append(asp.fact("helps", cid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    wm = WorldModel(params)
    world = wm.build()
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
    StoryParams(name="Lily", gender="girl", parent="mother", helper="dentist", sound="whirr", comfort="headphones"),
    StoryParams(name="Theo", gender="boy", parent="father", helper="hygienist", sound="tap", comfort="blanket"),
    StoryParams(name="Mia", gender="girl", parent="mother", helper="assistant", sound="spray", comfort="stuffie"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid sound/comfort combos:\n")
        for s, c in combos:
            print(f"  {s:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.sound} with {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
