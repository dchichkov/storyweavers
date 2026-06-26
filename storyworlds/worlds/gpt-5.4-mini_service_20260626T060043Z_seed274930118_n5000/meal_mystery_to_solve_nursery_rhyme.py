#!/usr/bin/env python3
"""
A nursery-rhyme style storyworld about a meal-time mystery to solve.

Seed premise:
- A child sits down for a meal.
- Something small and puzzling is missing or misplaced.
- Gentle clues around the table help solve the mystery.
- The ending proves what changed in the world.

The simulation keeps physical meters and emotional memes, and the prose is
driven by state changes rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core entities and world model
# ---------------------------------------------------------------------------
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Meal:
    id: str
    label: str
    phrase: str
    smell: str
    warmth: str
    time_word: str
    setting_words: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    solved_by: str
    reveal: str
    question_word: str = "where"


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    action: str
    found: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    meal: str
    mystery: str
    child_name: str
    child_type: str
    caregiver_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"meal"}),
    "porch": Setting(place="the sunny porch", affords={"meal"}),
    "nursery": Setting(place="the nursery nook", affords={"meal"}),
}

MEALS = {
    "porridge": Meal(
        id="porridge",
        label="porridge",
        phrase="a warm bowl of porridge",
        smell="sweet and toasty",
        warmth="warm",
        time_word="morning",
        setting_words=["bowl", "spoon", "table"],
    ),
    "soup": Meal(
        id="soup",
        label="soup",
        phrase="a steaming bowl of soup",
        smell="savory and soft",
        warmth="steaming",
        time_word="noon",
        setting_words=["bowl", "spoon", "napkin"],
    ),
    "apples": Meal(
        id="apples",
        label="apple slices",
        phrase="a plate of apple slices",
        smell="fresh and sweet",
        warmth="cool",
        time_word="afternoon",
        setting_words=["plate", "fork", "cloth"],
    ),
    "peas": Meal(
        id="peas",
        label="peas",
        phrase="a bright little bowl of peas",
        smell="green and grassy",
        warmth="warm",
        time_word="supper",
        setting_words=["bowl", "spoon", "tray"],
    ),
}

MYSTERIES = {
    "spoon": Mystery(
        id="spoon",
        missing="spoon",
        clue="a shiny spoon-shaped trail on the chair",
        solved_by="inside the napkin fold",
        reveal="the spoon had slipped into the napkin and been hiding all along",
    ),
    "napkin": Mystery(
        id="napkin",
        missing="napkin",
        clue="a soft square corner peeking from under the bowl",
        solved_by="under the bowl",
        reveal="the napkin was tucked under the bowl to keep it from blowing away",
    ),
    "cup": Mystery(
        id="cup",
        missing="cup",
        clue="a round ring of water on the table",
        solved_by="beside the plate",
        reveal="the cup was sitting beside the plate, tipped just a little",
    ),
}

CHILD_NAMES = ["Nina", "Milo", "Pip", "Luna", "Toby", "Maya", "Finn", "Poppy"]
CAREGIVERS = {"mother", "father"}
CHILD_TYPES = {"girl", "boy"}


# ---------------------------------------------------------------------------
# Tiny rhyme helpers
# ---------------------------------------------------------------------------
def _a(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def nursery_line(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p).strip()


def title_case_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).title()


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, meal: Meal, mystery: Mystery) -> None:
    world.say(
        nursery_line(
            f"Little {child.id} sat by {world.setting.place},",
            f"for {meal.time_word} meal was a happy way.",
        )
    )
    world.say(
        nursery_line(
            f"The porridge-sweet air, or soup-sure air, if you please,",
            f"was {meal.smell}, and it tickled the nose like a breeze.".replace(
                "porridge-sweet air, or soup-sure air, if you please,", meal.smell.capitalize() + " air"
            )
        )
    )
    world.say(
        nursery_line(
            f"{child.pronoun('subject').capitalize()} liked {meal.phrase},",
            f"and {child.pronoun('possessive')} eyes were bright and neat.",
        )
    )
    world.facts["meal"] = meal
    world.facts["mystery"] = mystery


def clue_appears(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    world.say(
        nursery_line(
            f"But oho, what a wee surprise!",
            f"A mystery sat before {child.pronoun('object')}: {mystery.clue}.",
        )
    )
    world.say(
        nursery_line(
            f"{child.pronoun('subject').capitalize()} tilted {child.pronoun('possessive')} head and said,",
            f"\"Oh dear me, oh my, oh where can it be?\"",
        )
    )


def ask_caregiver(world: World, child: Entity, caregiver: Entity, mystery: Mystery) -> None:
    caregiver.memes["helpful"] = caregiver.memes.get("helpful", 0.0) + 1
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        nursery_line(
            f"{child.id} looked to {child.pronoun('possessive')} {caregiver.type},",
            f"and asked, \"Will the missing thing be found by tea?\"",
        )
    )
    world.say(
        nursery_line(
            f"{caregiver.pronoun('subject').capitalize()} smiled a smile as calm as a hymn,",
            f"\"We shall look and we shall see; the answer may be dim.\"",
        )
    )


def search(world: World, child: Entity, caregiver: Entity, mystery: Mystery) -> None:
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1
    world.say(
        nursery_line(
            f"They peeped by the plate, and they peeped by the chair,",
            f"and they peeped by the cup with a careful, kind care.",
        )
    )
    world.say(
        nursery_line(
            f"Then {caregiver.id} whispered, \"Look here, little one,",
            f"the clue is a pointer; the hunt has begun.\"",
        )
    )


def solve(world: World, child: Entity, caregiver: Entity, mystery: Mystery) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 2
    child.memes["wonder"] = max(0.0, child.memes.get("wonder", 0.0) - 1)
    world.facts["solved"] = True
    world.say(
        nursery_line(
            f"Under the napkin, or under the bowl,",
            f"they found what was missing and made the story whole.".replace(
                "Under the napkin, or under the bowl,", f"At {mystery.solved_by},"
            )
        )
    )
    world.say(
        nursery_line(
            f"\"There it is!\" sang {child.id}, with a giggly grin,",
            f"\"The mystery's solved, and the meal can begin!\"",
        )
    )
    world.say(
        nursery_line(
            f"And so the small table grew merry and bright,",
            f"for the little lost thing was back in plain sight.",
        )
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
meal_day(M) :- meal(M).
mystery_item(X) :- mystery(X).

solved(X) :- clue(C), hidden_at(X, C).
has_clue(X) :- mystery(X), clue_for(X, _).
valid_story(S, M, X) :- setting(S), meal(M), mystery(X), allows(S, M), has_clue(X).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("allows", sid, m))
    for mid, m in MEALS.items():
        lines.append(asp.fact("meal", mid))
        lines.append(asp.fact("meal_label", mid, m.label))
    for xid, x in MYSTERIES.items():
        lines.append(asp.fact("mystery", xid))
        lines.append(asp.fact("clue_for", xid, x.clue))
        lines.append(asp.fact("hidden_at", xid, x.solved_by))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for mid in MEALS:
            for xid in MYSTERIES:
                out.append((sid, mid, xid))
    return out


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    meal = MEALS[params.meal]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    caregiver = world.add(Entity(id=params.caregiver_type, kind="character", type=params.caregiver_type))
    table = world.add(Entity(id="table", type="thing", label="table"))
    table.meters["set"] = 1
    world.facts.update(child=child, caregiver=caregiver, meal=meal, mystery=mystery, table=table)
    introduce(world, child, meal, mystery)
    world.para()
    clue_appears(world, child, mystery)
    ask_caregiver(world, child, caregiver, mystery)
    world.para()
    search(world, child, caregiver, mystery)
    solve(world, child, caregiver, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    meal = f["meal"]
    mystery = f["mystery"]
    return [
        f"Write a short nursery-rhyme story about {child.id} and {meal.phrase} with a small mystery to solve.",
        f"Tell a gentle, musical tale where a child finds a clue about a missing {mystery.missing} at meal time.",
        f"Write a child-friendly rhyme in which a caregiver helps solve the mystery of the missing {mystery.missing}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    meal = f["meal"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What meal was {child.id} having when the mystery began?",
            answer=f"{child.id} was having {meal.phrase} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What clue helped {child.id} notice the mystery?",
            answer=f"The clue was {mystery.clue}. That gave {child.id} a reason to ask for help.",
        ),
        QAItem(
            question=f"Who helped solve the mystery for {child.id}?",
            answer=f"{caregiver.id} helped look carefully, and together they found the missing {mystery.missing}.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=mystery.reveal.capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    meal: Meal = world.facts["meal"]
    mystery: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question="What is a meal?",
            answer="A meal is a time when people sit down to eat food together.",
        ),
        QAItem(
            question="Why do people use a spoon at meals?",
            answer="People use a spoon to scoop food like soup or porridge from a bowl.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or missing that people try to figure out.",
        ),
        QAItem(
            question=f"Why might a family look under a napkin or bowl during a meal like {meal.label}?",
            answer="They might look there because small things can slip out of sight and hide nearby.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme meal mystery storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--meal", choices=sorted(MEALS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(CHILD_TYPES))
    ap.add_argument("--parent", choices=sorted(CAREGIVERS))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    meal = args.meal or rng.choice(sorted(MEALS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(sorted(CAREGIVERS))
    if args.gender is not None and args.gender not in CHILD_TYPES:
        raise StoryError("invalid gender choice")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("unknown setting")
    return StoryParams(setting=setting, meal=meal, mystery=mystery, child_name=name, child_type=gender, caregiver_type=parent)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("kitchen", "porridge", "spoon", "Nina", "girl", "mother"),
            StoryParams("porch", "soup", "napkin", "Milo", "boy", "father"),
            StoryParams("nursery", "apples", "cup", "Pip", "girl", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
