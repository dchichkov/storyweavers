#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/efficiency_pity_lesson_learned_bravery_whodunit.py
=============================================================================================================

A small whodunit-style story world about a careful young sleuth, a missing
thing, a suspect with a reason, and a brave, efficient search that ends with a
lesson learned.

The world keeps one concrete mystery model:
- a prized item goes missing from a small setting
- clues accumulate through search
- the hero may feel pity for the true culprit
- bravery is needed to investigate the dark or awkward place
- efficiency is rewarded because the hero narrows the search quickly

The story format stays child-facing and clue-driven rather than like a raw log.
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
# Core model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
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
    place: str
    dark_spot: str
    has_lamp: bool = False


@dataclass
class Mystery:
    id: str
    prize: str
    phrase: str
    place: str
    dark_spot: str
    culprit: str
    reason: str
    clue_item: str
    clue_phrase: str
    clue_spot: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting, self.mystery)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", dark_spot="the pantry", has_lamp=True),
    "classroom": Setting(place="the classroom", dark_spot="the supply closet", has_lamp=True),
    "shed": Setting(place="the garden shed", dark_spot="the back shelf", has_lamp=False),
    "attic": Setting(place="the attic room", dark_spot="the corner trunk", has_lamp=False),
}

MYSTERIES = {
    "cookie": Mystery(
        id="cookie",
        prize="cookie tin",
        phrase="a tin of warm sugar cookies",
        place="the kitchen",
        dark_spot="the pantry",
        culprit="mouse",
        reason="it was hungry and wanted crumbs for its babies",
        clue_item="crumbs",
        clue_phrase="tiny crumbs on the floor",
        clue_spot="the pantry step",
    ),
    "crayon": Mystery(
        id="crayon",
        prize="crayon box",
        phrase="a bright box of crayons",
        place="the classroom",
        dark_spot="the supply closet",
        culprit="little brother",
        reason="he wanted to draw a surprise picture for his sister",
        clue_item="paper",
        clue_phrase="a scrap of drawing paper",
        clue_spot="the closet door",
    ),
    "lantern": Mystery(
        id="lantern",
        prize="lantern",
        phrase="a small brass lantern",
        place="the garden shed",
        dark_spot="the back shelf",
        culprit="neighbor",
        reason="it needed a lamp to finish a repair after sunset",
        clue_item="ribbon",
        clue_phrase="a red ribbon caught on a nail",
        clue_spot="the back shelf",
    ),
    "shell": Mystery(
        id="shell",
        prize="shell necklace",
        phrase="a shell necklace in a blue pouch",
        place="the attic room",
        dark_spot="the corner trunk",
        culprit="cat",
        reason="it liked the shiny string and dragged it to make a nest",
        clue_item="fur",
        clue_phrase="a patch of soft gray fur",
        clue_spot="the trunk lid",
    ),
}

HERO_NAMES = ["Mina", "Noah", "Tia", "Owen", "Ruby", "Ezra", "Lena", "Milo"]
TRAITS = ["careful", "curious", "quiet", "quick-thinking", "patient", "brave"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(S, M) :- setting(S), mystery(M), placed_in(M, S).
brave_solution(M) :- mystery(M), clue_at(M, _), culprit_reasonable(M).
efficient_solution(M) :- mystery(M), clue_at(M, _), setting_has_lamp(S), placed_in(M, S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_lamp:
            lines.append(asp.fact("setting_has_lamp", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("placed_in", mid, m.id if mid in SETTINGS else m.id))
        # The facts below are world-structured and used only to mirror Python checks.
        lines.append(asp.fact("clue_at", mid, m.clue_spot.replace("the ", "").replace(" ", "_")))
        lines.append(asp.fact("culprit_reasonable", mid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _search(world: World, hero: Entity, clue_hit: bool = False) -> None:
    hero.memes["efficiency"] = hero.memes.get("efficiency", 0) + (1.0 if clue_hit else 0.0)
    hero.meters["searched"] = hero.meters.get("searched", 0) + 1


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting, mystery)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"searched": 0.0},
        memes={"efficiency": 0.0, "bravery": 0.0, "pity": 0.0, "wonder": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="parent",
        memes={"concern": 0.0},
    ))
    culprit = world.add(Entity(
        id="Culprit",
        kind="character",
        type=mystery.culprit,
        label=mystery.culprit,
        memes={"worry": 0.0, "relief": 0.0},
    ))
    missing = world.add(Entity(
        id="Missing",
        type="thing",
        label=mystery.prize,
        phrase=mystery.phrase,
        owner=parent.id,
        carried_by=culprit.id,
        hidden_in=mystery.dark_spot,
    ))
    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label=mystery.clue_item,
        phrase=mystery.clue_phrase,
        hidden_in=mystery.clue_spot,
    ))

    # Act 1: the mystery appears.
    world.say(f"{hero.id} was a {params.hero_type} who liked to solve little puzzles.")
    world.say(f"One morning, {missing.phrase} was gone from {setting.place}.")
    world.say(f"{params.hero_name}'s {parent.pronoun('possessive')} face looked worried, and everyone wanted to know whodunit.")
    world.para()

    # Act 2: the search.
    world.say(f"{hero.id} looked first at {setting.dark_spot}.")
    hero.memes["bravery"] += 1
    if not setting.has_lamp:
        world.say(f"The corner was dark, but {hero.id} held still and took one brave step at a time.")
    else:
        world.say(f"A lamp lit the way, and {hero.id} searched carefully instead of rushing.")
    _search(world, hero, clue_hit=True)
    world.say(f"There, {mystery.clue_phrase} gave a tiny clue.")
    hero.memes["efficiency"] += 1
    world.say(f"{hero.id} did not scatter guesses everywhere. {hero.pronoun().capitalize()} followed the clue to the right place quickly.")
    world.para()

    # Act 3: the answer.
    culprit.memes["worry"] += 1
    hero.memes["pity"] += 1
    world.say(f"The trail led to the {culprit.type}, who was hiding the {missing.label}.")
    world.say(f"It had taken it because {mystery.reason}.")
    world.say(f"{hero.id} felt sorry for the {culprit.type}, so {hero.pronoun()} did not shout.")
    world.say(f"Instead, {hero.id} said it was better to ask than to sneak.")
    culprit.memes["relief"] += 1
    missing.carried_by = parent.id
    world.say(f"The {missing.label} went back where it belonged, and the little mystery was solved.")
    world.say(f"{hero.id} learned that bravery helps when a place feels dark, and efficiency helps when a clue is small.")
    world.say(f"By the end, the {culprit.type} had its needs heard, and everyone remembered the lesson learned.")

    world.facts.update(
        hero=hero,
        parent=parent,
        culprit=culprit,
        missing=missing,
        clue=clue,
        setting=setting,
        mystery=mystery,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child that includes the word "efficiency" and ends with a lesson learned.',
        f"Tell a gentle mystery about {f['hero'].id} finding out who took the {f['missing'].label} in {f['setting'].place}.",
        f"Write a brave little detective story where pity matters and the answer comes from a clue, not from guessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    culprit = f["culprit"]
    missing = f["missing"]
    clue = f["clue"]
    mystery = f["mystery"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"What was missing from {setting.place} at the start of the story?",
            answer=f"The {missing.label} was missing, and everyone wanted to find out who took it.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"{clue.phrase.capitalize()} gave the first real clue, so {hero.id} knew where to search next.",
        ),
        QAItem(
            question=f"Who really took the {missing.label}?",
            answer=f"The {culprit.type} took it, because {mystery.reason}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel pity at the end?",
            answer=f"{hero.id} felt pity because the {culprit.type} had a reason that made the choice sad instead of mean.",
        ),
        QAItem(
            question=f"What lesson learned did {hero.id} understand?",
            answer=f"{hero.id} learned that bravery helps in a hard place, and efficiency helps when a small clue points the way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does efficiency mean in a detective story?",
            answer="Efficiency means using a smart, careful way to do something so you do not waste time or effort.",
        ),
        QAItem(
            question="What does pity mean?",
            answer="Pity means feeling sorry for someone because they are having a hard time or made a sad choice.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard while staying steady and trying anyway.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps you figure out the answer to a mystery.",
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
@dataclass
class Resolved:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about efficiency, pity, bravery, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if args.setting and args.mystery:
        if MYSTERIES[mystery].place != SETTINGS[setting].place:
            raise StoryError("That mystery does not belong in that setting.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Verification / ASP
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_lamp:
            lines.append(asp.fact("lamp", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("placed_in", mid, m.place.replace("the ", "").replace(" ", "_")))
        lines.append(asp.fact("clue_at", mid, m.clue_spot.replace("the ", "").replace(" ", "_")))
        lines.append(asp.fact("culprit_reasonable", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable or failed: {exc}")
        return 1
    py = [(s, m) for s in SETTINGS for m in MYSTERIES if MYSTERIES[m].place == SETTINGS[s].place]
    if set(pairs) == set(py):
        print(f"OK: ASP parity matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH")
    print("ASP only:", sorted(set(pairs) - set(py)))
    print("Python only:", sorted(set(py) - set(pairs)))
    return 1


CURATED = [
    StoryParams(setting="kitchen", mystery="cookie", hero_name="Mina", hero_type="girl", parent_type="mother"),
    StoryParams(setting="classroom", mystery="crayon", hero_name="Noah", hero_type="boy", parent_type="father"),
    StoryParams(setting="shed", mystery="lantern", hero_name="Ruby", hero_type="girl", parent_type="father"),
    StoryParams(setting="attic", mystery="shell", hero_name="Ezra", hero_type="boy", parent_type="mother"),
]


def show_asp() -> None:
    print(asp_program("#show valid_story/2."))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        show_asp()
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
