#!/usr/bin/env python3
"""
storyworlds/worlds/enroll_kindness_surprise_detective_story.py
==============================================================

A small detective-style story world about enrollment day, a hidden kindness,
and a surprise that turns out to be helpful.

Premise:
- A child detective wants to enroll in a club or class.
- Someone seems to be keeping a sign-up form, a badge, or a seat out of reach.
- Clues point to a surprise, and the detective learns the surprise was kindness.

The world simulates:
- a location with a desk, line, folder, and helper
- an emotional arc from curiosity -> worry -> relief
- a physical arc where an enrollment item moves from withheld to shared
- a gentle reveal that a surprise was planned to welcome the hero

This file is self-contained and follows the Storyworld contract.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # character | thing
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
        if not self.meters:
            self.meters = {"seen": 0.0, "moved": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    effect: str
    kind: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_gender: str
    helper_type: str
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
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _pyname(s: str) -> str:
    return s.replace("_", " ")


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue in CLUES:
            if clue in setting.affords:
                combos.append((place, clue))
    return combos


def reasonableness_gate(place: str, clue: str) -> None:
    if clue not in SETTINGS[place].affords:
        raise StoryError(
            f"(No story: the {clue} clue does not belong at {SETTINGS[place].place}.)"
        )


def clue_to_kind(clue_id: str) -> str:
    return CLUES[clue_id].kind


def predict_resolution(world: World, hero: Entity, clue: Clue) -> bool:
    sim = world.copy()
    _inspect_clue(sim, sim.get(hero.id), clue, narrate=False)
    return bool(sim.facts.get("solved"))


def _inspect_clue(world: World, hero: Entity, clue: Clue, narrate: bool = True) -> None:
    hero.memes["curiosity"] += 1
    hero.meters["seen"] += 1
    if clue.kind == "surprise":
        hero.memes["worry"] += 1
    world.facts["clue_seen"] = clue.id
    if narrate:
        world.say(clue.text)


def _ask_helper(world: World, hero: Entity, helper: Entity) -> None:
    helper.memes["kindness"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} asked {helper.pronoun('object')} about the odd clue. "
        f"{helper.pronoun().capitalize()} smiled in a calm, kind way."
    )


def _reveal(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    world.facts["solved"] = True
    world.say(
        f"Then {helper.pronoun('possessive')} secret came out: the surprise was a kindness gift, "
        f"made for the new student who wanted to enroll."
    )
    world.say(
        f"The missing sign-up card was not lost at all. {helper.pronoun().capitalize()} had kept it safe "
        f"so {hero.id} could fill it in at the right moment."
    )
    world.say(
        f"{hero.id} grinned, enrolled with a careful signature, and left with the clue solved and a warm feeling in {hero.pronoun('possessive')} chest."
    )


def tell(place: Setting, clue: Clue, hero_name: str, hero_gender: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=_pyname(helper_type)))
    folder = world.add(Entity(
        id="folder",
        kind="thing",
        type="folder",
        label="enrollment folder",
        phrase="the enrollment folder",
        owner=helper.id,
        caretaker=helper.id,
    ))
    card = world.add(Entity(
        id="card",
        kind="thing",
        type="card",
        label="sign-up card",
        phrase="a sign-up card for the club",
        owner=hero.id,
        caretaker=helper.id,
    ))

    world.say(
        f"{hero.id} was a young detective with sharp eyes and a steady step."
    )
    world.say(
        f"{hero.id} wanted to enroll at {place.place} and get {card.label} signed."
    )
    world.say(
        f"But on the desk, the {folder.label} was closed, and a strange clue waited nearby."
    )

    world.para()
    _inspect_clue(world, hero, clue)
    world.say(
        f"The clue made {hero.id} curious, but also a little worried."
    )
    _ask_helper(world, hero, helper)

    world.para()
    if clue.kind == "surprise":
        world.say(
            f"{helper.pronoun().capitalize()} had been planning a surprise for the new enrollment day."
        )
    else:
        world.say(
            f"The clue pointed to a careful plan, not a danger."
        )
    _reveal(world, hero, helper, clue)

    world.facts.update(
        hero=hero,
        helper=helper,
        folder=folder,
        card=card,
        clue=clue,
        place=place,
        solved=True,
    )
    return world


SETTINGS = {
    "school_desk": Setting(place="the school desk", indoors=True, affords={"note", "ticket", "sticker"}),
    "club_room": Setting(place="the club room", indoors=True, affords={"badge", "note", "sticker"}),
    "lobby": Setting(place="the bright lobby", indoors=True, affords={"ticket", "badge", "note"}),
}

CLUES = {
    "note": Clue(
        id="note",
        text="A folded note was tucked under the folder. It said, 'Wait for the welcome surprise.'",
        effect="kindness",
        kind="surprise",
    ),
    "ticket": Clue(
        id="ticket",
        text="A small ticket had the words 'New member' written in neat blue ink.",
        effect="enroll",
        kind="enroll",
    ),
    "sticker": Clue(
        id="sticker",
        text="A shiny sticker showed a smiling star and the word 'Kindness'.",
        effect="kindness",
        kind="kindness",
    ),
    "badge": Clue(
        id="badge",
        text="A badge gleamed on the desk, tied to a ribbon that said 'Surprise guest'.",
        effect="surprise",
        kind="surprise",
    ),
}

HERO_NAMES = ["Mina", "Leo", "Nia", "Owen", "Tara", "Finn", "Ava", "Noah"]
HELPERS = ["librarian", "teacher", "principal", "club_leader"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style story world about enroll, kindness, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.clue:
        reasonableness_gate(args.place, args.clue)

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, clue=clue, hero_name=hero_name, hero_gender=gender, helper_type=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    place: Setting = f["place"]
    return [
        f"Write a short detective story for a child where {hero.id} tries to enroll at {place.place} and notices a clue about {clue.effect}.",
        f"Tell a gentle mystery with a kind surprise, a sign-up card, and a detective who follows clues.",
        f"Write a simple story about enroll day at {place.place} that ends with kindness being the real answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clue: Clue = f["clue"]
    place: Setting = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.place}?",
            answer=f"{hero.id} wanted to enroll there and get the sign-up card signed.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice?",
            answer=f"{clue.text}",
        ),
        QAItem(
            question=f"Who helped solve the mystery?",
            answer=f"The {helper.type} helped by keeping the card safe and explaining the surprise.",
        ),
        QAItem(
            question=f"Why did the clue feel a little strange at first?",
            answer=f"It felt strange because it looked hidden, but it was actually part of a kind surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to enroll?",
            answer="To enroll means to sign up and become part of a class, club, or group.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something caring, gentle, and helpful for someone else.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that someone did not know about ahead of time.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place_valid(P) :- setting(P).
clue_valid(C) :- clue(C).

valid_story(P, C) :- place_valid(P), clue_valid(C), affords(P, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        params.hero_name,
        params.hero_gender,
        params.helper_type,
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
    StoryParams(place="school_desk", clue="note", hero_name="Mina", hero_gender="girl", helper_type="teacher"),
    StoryParams(place="club_room", clue="sticker", hero_name="Leo", hero_gender="boy", helper_type="club_leader"),
    StoryParams(place="lobby", clue="badge", hero_name="Nia", hero_gender="girl", helper_type="principal"),
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
        for c in combos:
            print(c)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
