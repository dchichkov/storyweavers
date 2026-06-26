#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/suffer_lesson_learned_happy_ending_quest_detective.py
===============================================================================================================

A tiny detective-story world: someone loses something important, a child
detective follows clues, somebody suffers a little from the mistake, and the
ending turns into a lesson learned and a happy ending.

The world is built around one seed word, "suffer", with a quest-shaped mystery:
the missing thing must be found, the person who lost it feels bad, and the
resolution teaches a small child-facing lesson.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
    clue_spots: list[str]
    search_words: list[str]


@dataclass
class CaseFile:
    missing: str
    missing_phrase: str
    loss_reason: str
    clue_chain: list[str]
    location: str
    lesson: str
    fix_action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "school_hall": Setting(
        place="the school hallway",
        clue_spots=["locker", "bench", "coat rack", "door mat"],
        search_words=["hallway", "locker", "bench", "coat rack"],
    ),
    "library": Setting(
        place="the library",
        clue_spots=["reading table", "return cart", "quiet corner", "front desk"],
        search_words=["library", "books", "cart", "desk"],
    ),
    "garden": Setting(
        place="the garden",
        clue_spots=["flower bed", "watering can", "stone path", "bushes"],
        search_words=["garden", "flowers", "path", "bushes"],
    ),
}

MISSING = {
    "badge": CaseFile(
        missing="badge",
        missing_phrase="a bright silver badge",
        loss_reason="was left on a bench",
        clue_chain=[
            "a shiny mark on the bench",
            "a tiny trail of dust by the door",
            "a reflection from under the coat rack",
        ],
        location="under the coat rack",
        lesson="It is better to stop and check your things before hurrying away.",
        fix_action="put the badge back on the jacket",
    ),
    "key": CaseFile(
        missing="key",
        missing_phrase="a small brass key",
        loss_reason="slipped out of a pocket",
        clue_chain=[
            "a little brass glint near the floor",
            "a scuff mark by the door",
            "a soft clink near the return cart",
        ],
        location="behind the return cart",
        lesson="A careful pocket check can prevent a lot of worry.",
        fix_action="hang the key on a ribbon",
    ),
    "toy": CaseFile(
        missing="toy",
        missing_phrase="a tiny toy train",
        loss_reason="was forgotten on a table",
        clue_chain=[
            "a red wheel print on the table edge",
            "a small curve of paint near the chair",
            "a toy whistle from the quiet corner",
        ],
        location="behind the reading table",
        lesson="Sharing a place means putting precious things back where they belong.",
        fix_action="return the train to its box",
    ),
}

DETECTIVES = [
    ("Maya", "girl", "curious"),
    ("Leo", "boy", "careful"),
    ("Nina", "girl", "brave"),
    ("Owen", "boy", "patient"),
]

HELPERS = [
    ("Ms. Pine", "woman", "librarian"),
    ("Mr. Cole", "man", "custodian"),
    ("Aunt June", "woman", "helper"),
]

OWNERS = [
    ("Toby", "boy", "child"),
    ("Mila", "girl", "child"),
    ("Evan", "boy", "child"),
    ("Sara", "girl", "child"),
]


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for setting_name, setting in SETTINGS.items():
        for missing_name, case in MISSING.items():
            if setting_name == "garden" and missing_name == "key":
                combos.append((setting_name, missing_name))
            elif setting_name == "school_hall" and missing_name in {"badge", "key"}:
                combos.append((setting_name, missing_name))
            elif setting_name == "library" and missing_name in {"badge", "toy"}:
                combos.append((setting_name, missing_name))
    return combos


ASP_RULES = r"""
setting(school_hall). setting(library). setting(garden).
missing(badge). missing(key). missing(toy).

valid(school_hall,badge).
valid(school_hall,key).
valid(library,badge).
valid(library,toy).
valid(garden,key).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MISSING:
        lines.append(asp.fact("missing", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    missing: str
    detective_name: str
    detective_gender: str
    owner_name: str
    owner_gender: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    case = MISSING[params.missing]
    world = World(setting)

    detective_type = "girl" if params.detective_gender == "girl" else "boy"
    owner_type = "girl" if params.owner_gender == "girl" else "boy"

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=detective_type,
        label="detective",
        meters={"focus": 1.0},
        memes={"curiosity": 1.0},
    ))
    owner = world.add(Entity(
        id=params.owner_name,
        kind="character",
        type=owner_type,
        label="owner",
        meters={"worry": 0.0},
        memes={"sadness": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="woman",
        label="helper",
        meters={"calm": 1.0},
    ))
    missing = world.add(Entity(
        id=f"missing_{params.missing}",
        type=params.missing,
        label=params.missing,
        phrase=case.missing_phrase,
        owner=owner.id,
        carried_by=None,
        location=case.location,
    ))

    world.facts.update(
        setting=setting,
        case=case,
        detective=detective,
        owner=owner,
        helper=helper,
        missing=missing,
    )

    # Act 1: setup
    world.say(
        f"{detective.id} was a little {detective.pronoun('possessive')} detective who liked solving small mysteries."
    )
    world.say(
        f"One morning, {owner.id} looked upset, because {owner.pronoun('possessive')} {params.missing} had gone missing."
    )
    world.say(
        f"{owner.id} had been carrying {case.missing_phrase}, but it {case.loss_reason}."
    )

    # Act 2: quest and clues
    world.para()
    world.say(
        f"{detective.id} made a quiet quest through {setting.place}."
    )
    clue_bits = []
    for spot, clue in zip(setting.clue_spots, case.clue_chain):
        clue_bits.append(f"At the {spot}, {detective.id} noticed {clue}.")
    world.say(" ".join(clue_bits))
    world.say(
        f"Each clue pointed a little more clearly toward {case.location}."
    )

    # Emotional turn: suffering from the mistake
    owner.meters["worry"] = 1.0
    owner.memes["sadness"] = 1.0
    world.say(
        f"{owner.id} began to suffer from the worry, because losing {case.missing_phrase} felt terrible."
    )
    world.say(
        f"{helper.id} stayed calm and reminded everyone to look carefully instead of panicking."
    )

    # Act 3: discovery and happy ending
    world.para()
    missing.location = case.location
    missing.carried_by = detective.id
    world.say(
        f"At last, {detective.id} found {case.missing_phrase} {case.location}."
    )
    world.say(
        f"{detective.id} brought it back, and {helper.id} helped {owner.id} {case.fix_action}."
    )
    owner.meters["worry"] = 0.0
    owner.memes["sadness"] = 0.0
    owner.memes["relief"] = 1.0
    world.say(
        f"{owner.id} smiled with relief, and the little mystery ended in a happy ending."
    )
    world.say(
        f"{owner.id} learned a lesson: {case.lesson}"
    )

    world.facts["resolved"] = True
    world.facts["lesson"] = case.lesson
    world.facts["quest_done"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: CaseFile = f["case"]
    owner: Entity = f["owner"]
    detective: Entity = f["detective"]
    return [
        f'Write a short detective story for a young child about a missing {case.missing} and a gentle quest to find it.',
        f"Tell a story where {detective.id} helps {owner.id} search for {case.missing_phrase}, and the ending teaches a lesson learned.",
        f'Create a happy-ending mystery using the word "suffer" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: CaseFile = f["case"]
    owner: Entity = f["owner"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer=f"It is a small detective story with a quest, a lesson learned, and a happy ending.",
        ),
        QAItem(
            question=f"Who made the quest to solve the mystery?",
            answer=f"{detective.id} made the quest through {setting.place} to find {case.missing_phrase}.",
        ),
        QAItem(
            question=f"Why did {owner.id} suffer in the story?",
            answer=f"{owner.id} suffered because {owner.pronoun('possessive')} {case.missing} was lost, and that made {owner.pronoun('object')} worry and feel sad.",
        ),
        QAItem(
            question=f"Where was the missing {case.missing} found?",
            answer=f"It was found {case.location}, after the clues led {detective.id} there.",
        ),
        QAItem(
            question=f"What did {helper.id} help do at the end?",
            answer=f"{helper.id} helped {owner.id} {case.fix_action}, which made the ending happy again.",
        ),
        QAItem(
            question=f"What lesson was learned?",
            answer=case.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or adventure to find something or solve a problem.",
        ),
        QAItem(
            question="What does it mean to suffer?",
            answer="To suffer means to feel bad, hurt, sad, or worried for a while.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters feel better at the end.",
        ),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny detective-story world with a quest, suffer, lesson learned, and happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-name")
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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
    if args.setting and args.missing and (args.setting, args.missing) not in combos:
        raise StoryError("That setting does not make a reasonable mystery for the chosen missing thing.")

    candidates = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.missing is None or c[1] == args.missing)
    ]
    if not candidates:
        raise StoryError("No valid combination matches the given options.")

    setting, missing = rng.choice(sorted(candidates))
    detective_name, detective_gender, _ = rng.choice(DETECTIVES)
    owner_name, owner_gender, _ = rng.choice(OWNERS)
    helper_name, _, _ = rng.choice(HELPERS)

    if args.detective_name:
        detective_name = args.detective_name
    if args.detective_gender:
        detective_gender = args.detective_gender
    if args.owner_name:
        owner_name = args.owner_name
    if args.owner_gender:
        owner_gender = args.owner_gender
    if args.helper_name:
        helper_name = args.helper_name

    return StoryParams(
        setting=setting,
        missing=missing,
        detective_name=detective_name,
        detective_gender=detective_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, missing) combos:\n")
        for s, m in combos:
            print(f"  {s:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, missing in valid_combos():
            p = StoryParams(
                setting=setting,
                missing=missing,
                detective_name="Maya",
                detective_gender="girl",
                owner_name="Toby",
                owner_gender="boy",
                helper_name="Ms. Pine",
                seed=base_seed,
            )
            samples.append(generate(p))
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
            header = f"### {p.setting} / {p.missing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
