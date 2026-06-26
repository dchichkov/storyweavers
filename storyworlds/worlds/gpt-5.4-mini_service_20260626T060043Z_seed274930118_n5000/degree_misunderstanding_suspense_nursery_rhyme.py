#!/usr/bin/env python3
"""
storyworlds/worlds/degree_misunderstanding_suspense_nursery_rhyme.py
=====================================================================

A tiny storyworld about a child, a misunderstood degree, and a suspenseful
little fix, told in a nursery-rhyme style.

The seed tale behind this world is simple:
- a child hears about degrees,
- misunderstands what "degree" means,
- a warm or cold thing becomes risky,
- a caregiver explains in time,
- the ending image shows the safe change.

The world keeps the story grounded in simulated state:
meters track warmth, chill, worry, and readiness;
memes track confusion, suspense, relief, and trust.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class DegreeChoice:
    id: str
    label: str
    phrase: str
    expected: int
    unit: str
    kind: str
    at_risk: str
    suspense_word: str
    confusion_line: str
    danger_line: str
    fix_line: str
    resolution_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    supports: set[str]
    prep: str
    tail: str
    plural: bool = False


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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["hero"]
    choice = world.facts["choice"]
    if child.memes.get("confusion", 0) < THRESHOLD:
        return out
    sig = ("confusion", choice.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(choice.confusion_line)
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["hero"]
    choice = world.facts["choice"]
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("suspense", choice.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(choice.danger_line)
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["hero"]
    choice = world.facts["choice"]
    if child.memes.get("relief", 0) < THRESHOLD:
        return out
    sig = ("resolution", choice.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(choice.resolution_line)
    return out


CAUSAL_RULES = [
    Rule("confusion", _r_confusion),
    Rule("suspense", _r_suspense),
    Rule("resolution", _r_resolution),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"bake", "soup"}),
    "garden": Setting(place="the garden", indoor=False, affords={"soup"}),
    "porch": Setting(place="the porch", indoor=False, affords={"soup", "tea"}),
}

DEGREES = {
    "cake": DegreeChoice(
        id="cake",
        label="the cake pan",
        phrase="a little cake pan",
        expected=350,
        unit="degrees",
        kind="bake",
        at_risk="burning",
        suspense_word="hot",
        confusion_line="Little Bea thought the word degree meant a tiny stepping stone, one by one.",
        danger_line="But the oven was hot as a dragon's sigh, and the cake would brown too fast if no one watched it.",
        fix_line="Her mother pointed to the numbers and said they were heat, not steps at all.",
        resolution_line="So Bea wore oven mitts, and the cake baked sweet and slow, with a golden top like honeyed sun.",
        tags={"bake", "hot", "cake", "oven"},
    ),
    "soup": DegreeChoice(
        id="soup",
        label="the soup pot",
        phrase="a little soup pot",
        expected=180,
        unit="degrees",
        kind="soup",
        at_risk="boiling",
        suspense_word="warm",
        confusion_line="Little Pip thought degrees were coins in a counting game, shiny and round.",
        danger_line="But the soup was near its boil, and one careless stir could send up a splashy song.",
        fix_line="His father showed him the steam and said, 'Degrees are how hot the pot feels.'",
        resolution_line="So Pip stirred with a wooden spoon, and the soup stayed safe and softly steaming.",
        tags={"soup", "steam", "warm"},
    ),
    "tea": DegreeChoice(
        id="tea",
        label="the tea cup",
        phrase="a small tea cup",
        expected=160,
        unit="degrees",
        kind="tea",
        at_risk="too_hot",
        suspense_word="steamy",
        confusion_line="Little Nell thought a degree was a tiny dance turn, twirl and whirl.",
        danger_line="But the tea was steamy hot, and a hurried sip could sting a lip.",
        fix_line="Her grandmother smiled and said the tea must cool a little first.",
        resolution_line="So Nell waited with a spoon, and the tea grew safe and sweet, like rain on a rose.",
        tags={"tea", "steam", "warm"},
    ),
}


GEAR = [
    Gear(
        id="mitts",
        label="oven mitts",
        phrase="the oven mitts",
        protects_from={"burning", "too_hot"},
        supports={"bake"},
        prep="put on the oven mitts",
        tail="wore the oven mitts and held the pan with care",
        plural=True,
    ),
    Gear(
        id="spoon",
        label="a wooden spoon",
        phrase="a wooden spoon",
        protects_from={"boiling"},
        supports={"soup"},
        prep="use the wooden spoon",
        tail="used the wooden spoon and stirred with care",
    ),
    Gear(
        id="cooling_wait",
        label="a cooling spoon and a little wait",
        phrase="a cooling spoon and a little wait",
        protects_from={"too_hot"},
        supports={"tea"},
        prep="wait for the tea to cool with a spoon nearby",
        tail="waited for the tea to cool and kept both hands safe",
    ),
]


GIRL_NAMES = ["Bea", "Nell", "Mia", "Lily", "Rose"]
BOY_NAMES = ["Pip", "Finn", "Tom", "Ben", "Max"]
TRAITS = ["tiny", "curious", "cheerful", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    choice: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def choice_at_risk(choice: DegreeChoice, gear: Gear) -> bool:
    return choice.kind in gear.supports


def select_gear(choice: DegreeChoice) -> Optional[Gear]:
    for gear in GEAR:
        if choice.kind in gear.supports and choice.at_risk in gear.protects_from:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for choice_id, choice in DEGREES.items():
            if choice.kind in setting.affords and select_gear(choice):
                combos.append((place, choice_id))
    return combos


def tell(setting: Setting, choice: DegreeChoice, hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        meters={"warmth": 0.0, "readiness": 0.0},
        memes={"confusion": 0.0, "worry": 0.0, "relief": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        meters={"care": 1.0},
        memes={"watchful": 1.0},
    ))
    target = world.add(Entity(
        id=choice.id,
        kind="thing",
        type=choice.id,
        label=choice.label,
        phrase=choice.phrase,
        owner=hero.id,
        caretaker=parent.id,
        meters={"heat": float(choice.expected)},
        memes={"hush": 1.0},
    ))
    world.facts.update(hero=hero, parent=parent, choice=choice, target=target, trait=trait)

    world.say(
        f"Little {hero_name} was a {trait} {gender} who loved to listen for rhyme and ring."
    )
    world.say(
        f"In {setting.place}, {hero_name} heard the word degree, and wondered what that might bring."
    )
    world.say(
        f"{parent_type.capitalize()} showed {hero_name} {choice.phrase}, all snug and waiting in line."
    )

    world.para()
    hero.memes["confusion"] += 1
    hero.memes["worry"] += 1
    world.say(choice.confusion_line)

    world.say(
        f"Yet {hero_name} moved too fast, and the {choice.label} began to feel {choice.suspense_word} and high."
    )
    world.say(choice.danger_line)

    gear = select_gear(choice)
    if gear is None:
        raise StoryError("No safe gear exists for this degree choice.")

    world.para()
    world.say(choice.fix_line)
    world.say(
        f"Then {parent_type} said, 'How about we {gear.prep}?' and the room grew quiet as a sigh."
    )
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.meters["readiness"] += 1
    world.say(
        f"{hero_name} nodded, and the answer came clear as a bell in the sky."
    )
    world.say(
        f"So {hero_name} {gear.tail}, while the {choice.label} reached the right degree at last."
    )
    world.say(choice.resolution_line)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    choice: DegreeChoice = f["choice"]
    hero: Entity = f["hero"]
    return [
        f'Write a nursery-rhyme style story about a child named {hero.id} who misunderstands the word "degree".',
        f"Tell a gentle suspense story where {hero.id} thinks a degree means something small and simple, but the {choice.label} needs careful watching.",
        f'Write a short child-friendly rhyme where "{choice.kind}" and "degree" appear together, and the grown-up explains the mix-up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    choice: DegreeChoice = f["choice"]
    parent: Entity = f["parent"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What did {hero.id} misunderstand about the word degree?",
            answer=(
                f"{hero.id} thought degree meant a tiny stepping or counting thing, "
                f"but the grown-up explained that here it meant heat on the {choice.label}."
            ),
        ),
        QAItem(
            question=f"Why was the {choice.label} part of the story suspenseful?",
            answer=(
                f"It was suspenseful because the {choice.label} was getting too {choice.at_risk.replace('_', ' ')}, "
                f"and that could spoil the safe little plan if no one helped in time."
            ),
        ),
        QAItem(
            question=f"How did {parent.type} help {hero.id} in the end?",
            answer=(
                f"{parent.type.capitalize()} showed {hero.id} the right meaning of degree, "
                f"then used the safe gear so {hero.id} could help without a mistake."
            ),
        ),
        QAItem(
            question=f"What kind of child was {hero.id} in the story?",
            answer=f"{hero.id} was a {trait} child, which made the rhyme feel gentle and bright.",
        ),
    ]


KNOWLEDGE = {
    "degrees": [
        (
            "What are degrees in temperature?",
            "Degrees are numbers that tell how hot or cold something is.",
        )
    ],
    "bake": [
        (
            "Why do people use oven mitts?",
            "Oven mitts help your hands stay safe when you touch something hot from the oven.",
        )
    ],
    "soup": [
        (
            "Why do people stir soup?",
            "People stir soup so it cooks evenly and does not stick to the bottom of the pot.",
        )
    ],
    "tea": [
        (
            "Why should tea cool before you sip it?",
            "Tea should cool a little so it is warm enough to drink without hurting your mouth.",
        )
    ],
    "steam": [
        (
            "What is steam?",
            "Steam is warm water vapor that can rise from hot soup, tea, or bath water.",
        )
    ],
    "warm": [
        (
            "What does warm mean?",
            "Warm means not cold and not scorching hot, just nicely cozy.",
        )
    ],
    "cake": [
        (
            "What makes cake special?",
            "Cake is a sweet baked treat that often feels like a celebration.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["choice"].tags)
    tags.add("degrees")
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: str, choice: DegreeChoice) -> str:
    return f"(No story: {place} cannot safely host {choice.kind} in this tiny rhyme world.)"


ASP_RULES = r"""
valid_story(P, C) :- place(P), choice(C), affords(P, C), has_gear(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, setting in SETTINGS.items():
        lines.append(asp.fact("place", p))
        if setting.indoor:
            lines.append(asp.fact("indoor", p))
        for c in sorted(setting.affords):
            lines.append(asp.fact("affords", p, c))
    for c_id, c in DEGREES.items():
        lines.append(asp.fact("choice", c_id))
        lines.append(asp.fact("kind", c.kind))
        lines.append(asp.fact("has_gear", c_id))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about degree, misunderstanding, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--choice", choices=DEGREES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.choice:
        combos = [c for c in combos if c[1] == args.choice]
    if not combos:
        raise StoryError("(No valid degree story matches the given options.)")
    place, choice = rng.choice(sorted(combos))
    degree = DEGREES[choice]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, choice=choice, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        DEGREES[params.choice],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
    StoryParams(place="kitchen", choice="cake", name="Bea", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="kitchen", choice="soup", name="Pip", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="porch", choice="tea", name="Nell", gender="girl", parent="grandmother" if False else "mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible degree stories:\n")
        for p, c in combos:
            print(f"  {p:8} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
