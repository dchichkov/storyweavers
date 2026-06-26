#!/usr/bin/env python3
"""
A small space-adventure story world: a crew on a quest solves a comma mystery
that is tied to a missing skirt. The world is state-driven, with suspense and
a final reveal that changes the physical and emotional state.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "boy", "man", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "engineer", "navigator", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str = "the Silver Comet"
    place: str = "deep space"
    has_station: bool = True
    has_map_lab: bool = True


@dataclass
class QuestItem:
    name: str
    clue: str
    location: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    quest_item: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.ship)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _m(e: Entity, key: str, delta: float) -> float:
    e.meters[key] = e.meters.get(key, 0.0) + delta
    return e.meters[key]


def _mem(e: Entity, key: str, delta: float) -> float:
    e.memes[key] = e.memes.get(key, 0.0) + delta
    return e.memes[key]


# ---------------------------------------------------------------------------
# World content
# ---------------------------------------------------------------------------

SUSPECTS = {
    "cargo_bot": QuestItem(
        name="cargo bot",
        clue="a tiny comma-shaped scratch",
        location="the cargo bay",
    ),
    "star_chart": QuestItem(
        name="star chart",
        clue="a comma that looked out of place",
        location="the map lab",
    ),
    "skirt": QuestItem(
        name="skirt",
        clue="a bright skirt tucked behind a toolbox",
        location="the airlock locker",
    ),
}

NAMES = ["Nova", "Mira", "Pax", "Luna", "Orin", "Tess", "Iris", "Juno"]
TYPES = ["captain", "pilot", "engineer", "navigator"]
HELPER_TYPES = ["robot", "crewmate"]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    hero.memes["curiosity"] = 1.0
    helper.memes["alert"] = 1.0
    world.say(
        f"Captain {hero.id} drifted through {world.ship.name} with {helper.label} at {heror('pos', hero)} side."
    )
    world.say(
        f"They were on a quiet quest through deep space, and {hero.pronoun('subject')} had found a clue: {item.clue}."
    )


def heror(mode: str, hero: Entity) -> str:
    return hero.pronoun("possessive")


def clue_scene(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    _mem(hero, "suspense", 1.0)
    world.say(
        f"In {item.location}, they found {item.name}, but it was not alone."
    )
    world.say(
        f"Near it, a strange comma mark glimmered on the floor like a tiny hook in a sentence."
    )
    world.say(
        f"{hero.id} leaned closer. '{item.clue},' {helper.id} beeped, as if the mark wanted to say more."
    )


def search(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    _m(hero, "search", 1.0)
    _mem(helper, "focus", 1.0)
    world.say(
        f"They searched every crate and cable, following the clue from one dark corner to the next."
    )
    world.say(
        f"The ship felt extra silent, as if it was holding its breath with them."
    )


def reveal(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    _mem(hero, "joy", 1.0)
    _mem(helper, "joy", 1.0)
    world.say(
        f"Then the mystery snapped into place: the comma was a label mark, and the missing skirt belonged to {hero.id}."
    )
    world.say(
        f"It had slipped behind the toolbox when the shuttle bumped the wall."
    )
    world.say(
        f"{hero.id} laughed, tucked the skirt under {hero.pronoun('possessive')} arm, and said the clue finally made sense."
    )


def ending(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    _m(hero, "relief", 1.0)
    world.say(
        f"By the time the stars brightened outside the window, the quest was done."
    )
    world.say(
        f"{hero.id} and {helper.id} floated back to the bridge with the skirt safe, the comma explained, and the ship calm again."
    )
    world.say(
        f"The little mystery had become a solved story, and the Silver Comet felt warm with victory."
    )


def build_world(params: StoryParams) -> World:
    ship = Ship()
    world = World(ship)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"search": 0.0},
        memes={"curiosity": 0.0, "suspense": 0.0, "joy": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        meters={"scan": 0.0},
        memes={"alert": 0.0, "focus": 0.0, "joy": 0.0},
    ))
    item = SUSPECTS[params.quest_item]

    world.facts.update(hero=hero, helper=helper, item=item, ship=ship)
    introduce(world, hero, helper, item)
    world.para()
    clue_scene(world, hero, helper, item)
    search(world, hero, helper, item)
    world.para()
    reveal(world, hero, helper, item)
    ending(world, hero, helper, item)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    return [
        f'Write a short space-adventure story for a child where {hero.id} and {helper.id} solve a mystery about a comma and a skirt.',
        f"Tell a suspenseful quest story on {world.ship.name} where a tiny comma clue helps {hero.id} find the missing {item.name}.",
        f"Write a gentle mystery-to-solve tale in space that ends with the comma making sense and the skirt safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who went on the quest in the story?",
            answer=f"Captain {hero.id} went on the quest with {helper.id} on {world.ship.name}.",
        ),
        QAItem(
            question=f"What was the mystery clue?",
            answer="The clue was a tiny comma-shaped mark that seemed to point the crew toward the answer.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"A {item.name} was missing until they found it behind the toolbox.",
        ),
        QAItem(
            question=f"How did the suspense end?",
            answer=f"The suspense ended when the crew learned the comma was a label mark and the {item.name} was safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a comma for?",
            answer="A comma is a small punctuation mark that helps separate parts of a sentence and make it easier to read.",
        ),
        QAItem(
            question="What is a skirt?",
            answer="A skirt is a piece of clothing that hangs from the waist and can be worn as part of an outfit.",
        ),
        QAItem(
            question="What does a quest mean?",
            answer="A quest is a search for something important, like a clue, a treasure, or an answer.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that makes you wonder what will happen next.",
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
item(I) :- quest_item(I).

mystery_comma(I) :- item(I), clue_kind(I, comma).
quest_story(H,K,I) :- hero(H), helper(K), item(I), mystery_comma(I), suspenseful(I).
resolved(I) :- quest_story(_,_,I), found_item(I), explained_comma(I).

#show mystery_comma/1.
#show quest_story/3.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero_name", "Nova"))
    lines.append(asp.fact("helper_name", "Byte"))
    lines.append(asp.fact("quest_item", "skirt"))
    lines.append(asp.fact("clue_kind", "skirt", "comma"))
    lines.append(asp.fact("suspenseful", "skirt"))
    lines.append(asp.fact("found_item", "skirt"))
    lines.append(asp.fact("explained_comma", "skirt"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = asp.atoms(model, "resolved")
    if atoms == [("skirt",)]:
        print("OK: ASP gate matches the Python mystery resolution.")
        return 0
    print("MISMATCH: ASP did not resolve the skirt mystery as expected.")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery storyworld.")
    ap.add_argument("--hero-name", choices=NAMES)
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--helper-name", choices=NAMES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--quest-item", choices=sorted(SUSPECTS))
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
    hero_name = args.hero_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != hero_name])
    hero_type = args.hero_type or rng.choice(TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    quest_item = args.quest_item or rng.choice(list(SUSPECTS))
    if hero_name == helper_name:
        raise StoryError("Hero and helper must be different characters.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        quest_item=quest_item,
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
        print("\n--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(f"{eid}: meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_story/3.\n#show resolved/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Nova", "captain", "Byte", "robot", "skirt"),
            StoryParams("Mira", "engineer", "Pax", "crewmate", "skirt"),
            StoryParams("Luna", "navigator", "Iris", "robot", "star_chart"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
