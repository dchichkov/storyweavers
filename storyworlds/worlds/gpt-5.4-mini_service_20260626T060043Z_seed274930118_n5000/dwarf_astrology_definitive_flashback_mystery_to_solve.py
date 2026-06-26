#!/usr/bin/env python3
"""
storyworlds/worlds/dwarf_astrology_definitive_flashback_mystery_to_solve.py
============================================================================

A small fairy-tale storyworld about a dwarf, astrology, a flashback, and a
mystery to solve.

Premise:
- A young dwarf in a mountain home studies the stars and notices something is
  missing.
- A remembered lesson from an elder becomes the flashback that points to the
  answer.
- The dwarf uses astrology, compares clues, and finds a definitive solution.

The story is intentionally small and constraint-checked. It is not a frozen
paragraph with swapped names: the protagonist's meters and memes change through
setup, flashback, investigation, and resolution.
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


# ---------------------------------------------------------------------------
# Entities and world state
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother", "dwarf"}
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
    indoors: bool
    sky: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    clue_kind: str
    clue_phrase: str
    cause_phrase: str
    solution_phrase: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AstrologyPractice:
    id: str
    verb: str
    gerund: str
    tool: str
    insight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    practice: str
    name: str
    title: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cave": Setting(
        place="the moonlit cave",
        indoors=True,
        sky="hidden",
        supports={"astrology", "mystery"},
    ),
    "ridge": Setting(
        place="the high ridge",
        indoors=False,
        sky="open",
        supports={"astrology", "mystery"},
    ),
    "forge": Setting(
        place="the warm forge room",
        indoors=True,
        sky="smoky",
        supports={"astrology", "mystery"},
    ),
}

ASTROLOGY = {
    "stargaze": AstrologyPractice(
        id="stargaze",
        verb="study the stars",
        gerund="studying the stars",
        tool="a little brass telescope",
        insight="the stars looked like a trail of breadcrumbs",
        tags={"stars", "night"},
    ),
    "chart": AstrologyPractice(
        id="chart",
        verb="read the star chart",
        gerund="reading star charts",
        tool="a folded star chart",
        insight="the chart pointed the way like a lantern",
        tags={"stars", "map"},
    ),
    "moonwise": AstrologyPractice(
        id="moonwise",
        verb="watch the moon",
        gerund="watching the moon",
        tool="a silver moon dial",
        insight="the moon made a pale line over the rocks",
        tags={"moon", "night"},
    ),
}

MYSTERIES = {
    "lostpin": Mystery(
        id="lostpin",
        missing="the captain's bronze pin",
        clue_kind="ash",
        clue_phrase="a line of ash on the floor",
        cause_phrase="the pin had rolled behind the warm forge stone",
        solution_phrase="the pin was tucked under the coal shelf",
        location="the forge hearth",
        tags={"forged", "ash"},
    ),
    "missingstone": Mystery(
        id="missingstone",
        missing="the village moonstone",
        clue_kind="dust",
        clue_phrase="a crescent of pale dust on the window ledge",
        cause_phrase="the moonstone had been lifted to the ridge by a curious bat",
        solution_phrase="the moonstone was resting in a nest of dry grass",
        location="the ridge ledge",
        tags={"moon", "dust"},
    ),
    "silentbell": Mystery(
        id="silentbell",
        missing="the tiny silver bell",
        clue_kind="soot",
        clue_phrase="a smudge of soot by the bell rope",
        cause_phrase="the bell rope had snagged above the chimney beam",
        solution_phrase="the bell was caught in a rafters hook",
        location="the smoke beam",
        tags={"soot", "chimney"},
    ),
}

DWARF_NAMES = ["Bram", "Tilda", "Nori", "Hilda", "Rurik", "Mara", "Oren", "Sela"]
TITLES = ["young dwarf", "little dwarf", "bright dwarf", "grave dwarf"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for practice_id in setting.supports:
            for mystery_id in MYSTERIES:
                combos.append((place, practice_id, mystery_id))
    return combos


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def lower_name(name: str) -> str:
    return name[0].lower() + name[1:] if name else name


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.label} who lived where the stone was kind and the lamps were warm."
    )


def love_astrology(world: World, hero: Entity, practice: AstrologyPractice) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {practice.gerund} with {practice.tool}, because "
        f"{practice.insight}."
    )


def setup_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    missing = world.add(Entity(
        id="Missing",
        type="thing",
        label=mystery.missing,
        phrase=mystery.missing,
        owner=hero.id,
        caretaker=hero.id,
        location="gone",
    ))
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0.0) + 1
    world.say(
        f"One evening, {hero.id} noticed that {missing.label} was gone from {mystery.location}."
    )


def flashback(world: World, hero: Entity, mystery: Mystery, practice: AstrologyPractice) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0.0) + 1
    world.say(
        f"Then {hero.id} had a flashback to the old lesson: "
        f'"When you solve a mystery, look for the smallest sign, then trust the sky."'
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered that {mystery.clue_phrase} could mean something moved the missing thing."
    )
    hero.meters["clarity"] = hero.meters.get("clarity", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1


def investigate(world: World, hero: Entity, mystery: Mystery, practice: AstrologyPractice) -> None:
    hero.meters["attention"] = hero.meters.get("attention", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} took a breath and used {practice.verb} to compare the clue with the room."
    )
    world.say(
        f"The {mystery.clue_kind} looked {practice.insight}, and that made the answer feel near."
    )


def solve_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["clarity"] = hero.meters.get("clarity", 0.0) + 1
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"At last, {hero.id} found the definitive clue: {mystery.clue_phrase}."
    )
    world.say(
        f"It pointed to the place where {mystery.cause_phrase}, and soon the mystery was solved."
    )
    world.say(
        f"{mystery.missing.capitalize()} was found, safe and sound, and the little dwarf smiled like a candle in the dark."
    )


def tell(setting: Setting, practice: AstrologyPractice, mystery: Mystery,
         name: str, title: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type="dwarf",
        label=title,
        owner=None,
        meters={"curiosity": 0.0, "attention": 0.0, "clarity": 0.0},
        memes={"wonder": 0.0, "worry": 0.0, "hope": 0.0, "joy": 0.0, "memory": 0.0},
    ))
    world.facts.update(hero=hero, practice=practice, mystery=mystery, setting=setting)

    introduce(world, hero)
    love_astrology(world, hero, practice)
    setup_mystery(world, hero, mystery)

    world.para()
    flashback(world, hero, mystery, practice)
    investigate(world, hero, mystery, practice)

    world.para()
    solve_mystery(world, hero, mystery)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    practice = f["practice"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        f"Write a fairy tale about a {hero.type} who loves {practice.gerund} and must solve a mystery in {setting.place}.",
        f"Tell a gentle story where {hero.id} remembers a flashback and uses astrology to find {mystery.missing}.",
        f"Write a short story for children about a dwarf, a clue, and a definitive answer under the stars.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    practice = f["practice"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What kind of character is {hero.id} in this story?",
            answer=f"{hero.id} is a little dwarf who lives in {setting.place} and loves {practice.gerund}.",
        ),
        QAItem(
            question=f"What made {hero.id} remember an old lesson?",
            answer=(
                f"{hero.id} had a flashback when the mystery felt hard. "
                f"The remembered lesson told {hero.id} to look for the smallest sign."
            ),
        ),
        QAItem(
            question=f"What was the mystery that needed solving?",
            answer=f"The mystery was missing {mystery.missing}.",
        ),
        QAItem(
            question=f"What was the definitive clue?",
            answer=f"The definitive clue was {mystery.clue_phrase}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} solved the mystery, found {mystery.missing}, and smiled in relief.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "stars": (
        "What are stars?",
        "Stars are huge balls of hot light in the night sky that shine far away from us.",
    ),
    "moon": (
        "What is the moon?",
        "The moon is the round bright rock that circles Earth and glows in the night sky.",
    ),
    "map": (
        "What is a star chart?",
        "A star chart is a kind of map that helps people find shapes and patterns among the stars.",
    ),
    "ash": (
        "What is ash?",
        "Ash is the soft gray powder left after something burns.",
    ),
    "dust": (
        "What is dust?",
        "Dust is made of tiny bits of dry stuff, like dirt or crumbs, that can gather on ledges and floors.",
    ),
    "soot": (
        "What is soot?",
        "Soot is a black powder made by smoke, and it can stick to walls or beams near a fire.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["practice"].tags)
    out = []
    for tag in ["stars", "moon", "map", "ash", "dust", "soot"]:
        if tag in tags or tag in {"stars", "moon"}:
            q, a = WORLD_KNOWLEDGE[tag]
            out.append(QAItem(question=q, answer=a))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
practice(A) :- astrology(A).
mystery(M) :- mystery_item(M).

compatible(P, A, M) :- supports(P, A), supports(P, M).
valid_story(P, A, M) :- place(P), practice(A), mystery(M), compatible(P, A, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, tag))
    for aid, practice in ASTROLOGY.items():
        lines.append(asp.fact("astrology", aid))
        for tag in sorted(practice.tags):
            lines.append(asp.fact("supports", aid, tag))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery_item", mid))
        for tag in sorted(mystery.tags):
            lines.append(asp.fact("supports", mid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def explain_rejection(place: str, practice: str, mystery: str) -> str:
    return (
        f"(No story: {practice} and {mystery} do not form a coherent fairy-tale "
        f"mystery at {place}.)"
    )


def valid_story(place: str, practice: str, mystery: str) -> bool:
    return place in SETTINGS and practice in ASTROLOGY and mystery in MYSTERIES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        (p, a, m)
        for p, a, m in valid_combos()
        if (args.place is None or args.place == p)
        and (args.practice is None or args.practice == a)
        and (args.mystery is None or args.mystery == m)
    ]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, practice, mystery = rng.choice(sorted(choices))
    if args.place and args.practice and args.mystery and not valid_story(place, practice, mystery):
        raise StoryError(explain_rejection(place, practice, mystery))
    name = args.name or rng.choice(DWARF_NAMES)
    title = args.title or rng.choice(TITLES)
    return StoryParams(place=place, mystery=mystery, practice=practice, name=name, title=title)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ASTROLOGY[params.practice],
        MYSTERIES[params.mystery],
        params.name,
        params.title,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale dwarf astrology mystery storyworld."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--practice", choices=sorted(ASTROLOGY))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name", choices=DWARF_NAMES)
    ap.add_argument("--title", choices=TITLES)
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


CURATED = [
    StoryParams(place="cave", practice="chart", mystery="missingstone", name="Bram", title="young dwarf"),
    StoryParams(place="ridge", practice="stargaze", mystery="silentbell", name="Tilda", title="bright dwarf"),
    StoryParams(place="forge", practice="moonwise", mystery="lostpin", name="Nori", title="little dwarf"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for p, a, m in combos:
            print(f"  {p:7} {a:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.practice} at {p.place} (mystery: {p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
