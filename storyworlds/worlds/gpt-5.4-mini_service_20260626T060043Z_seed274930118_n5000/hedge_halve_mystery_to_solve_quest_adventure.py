#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hedge_halve_mystery_to_solve_quest_adventure.py
==========================================================================================================================

A small adventure storyworld about a quest through a hedge maze, where a mystery
must be solved by halving a clue and choosing the right path.

The seed words are woven into the domain:
- hedge: the maze, the obstacle, and the green boundary of the quest
- halve: the key method for splitting a clue to reveal the next step

The world is intentionally small and classical:
- one hero
- one quest
- one mystery
- one helpful companion or elder
- one useful object
- one turning-point action
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "princess"}
        male = {"boy", "man", "father", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    clue: str
    halves_into: tuple[str, str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    setting_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(name="the garden", outdoors=True, affords={"hedge_quest"}),
    "estate": Place(name="the old estate garden", outdoors=True, affords={"hedge_quest"}),
    "maze": Place(name="the hedge maze", outdoors=True, affords={"hedge_quest"}),
}

ADVENTURES = {
    "hedge_quest": Adventure(
        id="hedge_quest",
        verb="follow the hedge path",
        gerund="following the hedge path",
        rush="dash between the hedges",
        risk="the path could twist them away from the clue",
        setting_line="The hedges stood tall and green, like walls in a secret castle.",
        tags={"hedge", "quest", "adventure"},
    )
}

QUEST_ITEMS = {
    "map": QuestItem(
        id="map",
        label="map",
        phrase="a folded treasure map",
        clue="It showed only one thick line, and the line was too long to read at once.",
        halves_into=("left half of the map", "right half of the map"),
        tags={"map", "mystery", "halve"},
    ),
    "note": QuestItem(
        id="note",
        label="note",
        phrase="a small mystery note",
        clue="It had one sentence on it, but the middle was covered by a berry stain.",
        halves_into=("top half of the note", "bottom half of the note"),
        tags={"note", "mystery", "halve"},
    ),
}

HERO_NAMES = ["Milo", "Nina", "Tara", "Owen", "Pia", "Ezra", "Lena", "Arlo"]
HERO_TYPES = {"girl": ["Nina", "Tara", "Pia", "Lena"], "boy": ["Milo", "Owen", "Ezra", "Arlo"]}
HERO_TRAITS = ["brave", "curious", "careful", "spirited", "lively"]
HELPERS = {
    "grandma": ("grandma", "she"),
    "gardener": ("the gardener", "they"),
    "uncle": ("uncle", "he"),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    adventure: str
    item: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for adv in p.affords:
            for item in QUEST_ITEMS:
                combos.append((place, adv, item))
    return combos


def explain_rejection(place: str, adventure: str, item: str) -> str:
    return f"(No story: {place} cannot support {adventure}, or the clue item {item} does not fit the hedge mystery.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is valid when the place affords the adventure and the item has the
% mystery/halve theme needed to reveal a hidden clue.
valid(Place, Adventure, Item) :- place(Place), adventure(Adventure), item(Item),
                                 affords(Place, Adventure),
                                 clue_theme(Item, mystery),
                                 clue_theme(Item, halve).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for iid, item in QUEST_ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("clue_theme", iid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
# Story simulation
# ---------------------------------------------------------------------------
def choose_item(item_id: str) -> QuestItem:
    if item_id not in QUEST_ITEMS:
        raise StoryError(f"Unknown item: {item_id}")
    return QUEST_ITEMS[item_id]


def choose_adventure(adv_id: str) -> Adventure:
    if adv_id not in ADVENTURES:
        raise StoryError(f"Unknown adventure: {adv_id}")
    return ADVENTURES[adv_id]


def choose_place(place_id: str) -> Place:
    if place_id not in PLACES:
        raise StoryError(f"Unknown place: {place_id}")
    return PLACES[place_id]


def tell(place: Place, adventure: Adventure, item: QuestItem, hero_name: str, gender: str, helper: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={"hope": 1}, memes={"curiosity": 1}))
    guide_label, guide_pronoun = HELPERS[helper]
    guide = world.add(Entity(id="guide", kind="character", type=helper, label=guide_label, meters={"care": 1}))

    world.say(f"{hero.id} was a {trait} child who loved a good quest.")
    world.say(f"{hero.pronoun().capitalize()} heard about {item.phrase} and wanted to solve the mystery hidden in it.")
    world.say(f"{adventure.setting_line}")

    world.para()
    world.say(f"At {place.name}, {hero.id} found {item.clue}")
    world.say(f"To make sense of it, {hero.pronoun()} had to halve the clue and look at each part carefully.")

    left, right = item.halves_into
    world.facts["left_half"] = left
    world.facts["right_half"] = right
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["item"] = item
    world.facts["adventure"] = adventure
    world.facts["place"] = place

    world.para()
    world.say(f"{guide.label} stepped closer and pointed at the two halves.")
    world.say(f'"If you put the halves side by side," {guide.pronoun().capitalize()} said, "the clue will stop hiding."')
    world.say(f"{hero.id} listened, then turned one half just so, because the mystery only solved itself when the clue was split in the right way.")

    world.para()
    world.say(f"Then {hero.id} read the halves together and found the hidden instruction.")
    world.say(f"The instruction led {hero.pronoun('object')} along the hedge path to a tiny gate, where the real answer waited.")
    world.say(f"In the end, {hero.id} finished {adventure.gerund}, and the hedge maze no longer felt like a puzzle.")

    world.facts["solved"] = True
    return world


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    adv = f["adventure"]
    place = f["place"]
    return [
        f'Write a short adventure story for a child where {hero.id} must solve a mystery at {place.name} by halving a clue.',
        f"Tell a gentle quest story about {hero.id} following a hedge path and using {item.label} to solve the mystery.",
        f'Write a simple adventure that includes the words "hedge" and "halve" and ends with a solved quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    item = f["item"]
    adv = f["adventure"]
    place = f["place"]
    left, right = f["left_half"], f["right_half"]

    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {place.name}?",
            answer=f"{hero.id} was trying to solve a mystery on a quest through the hedge path.",
        ),
        QAItem(
            question=f"What did {hero.id} have to do with the clue in order to understand it?",
            answer=f"{hero.id} had to halve the clue so the hidden instruction could be read more clearly.",
        ),
        QAItem(
            question=f"Who helped {hero.id} notice the clue more carefully?",
            answer=f"{guide.label.capitalize()} helped {hero.id} by pointing at the two halves and explaining how they fit together.",
        ),
        QAItem(
            question=f"What happened after {hero.id} read the two halves together?",
            answer=f"{hero.id} found the hidden instruction, followed the hedge path, and solved the mystery.",
        ),
        QAItem(
            question=f"What were the two parts of the clue called?",
            answer=f"They were the {left} and the {right}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hedge?",
            answer="A hedge is a line of bushes or shrubs that grows thick and green, and it can make a path feel secret or tricky.",
        ),
        QAItem(
            question="What does it mean to halve something?",
            answer="To halve something means to split it into two equal parts.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood right away, so you have to look for clues.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find something, learn something, or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind:8}) type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# StorySample interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small hedge-maze adventure storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    if args.place and args.adventure and args.item:
        if (args.place, args.adventure, args.item) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.adventure, args.item))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.adventure is None or c[1] == args.adventure)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, adventure, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_TYPES[gender])
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(HERO_TRAITS)
    return StoryParams(place=place, adventure=adventure, item=item, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        choose_place(params.place),
        choose_adventure(params.adventure),
        choose_item(params.item),
        params.name,
        params.gender,
        params.helper,
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


# ---------------------------------------------------------------------------
# CLI / main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="maze", adventure="hedge_quest", item="map", name="Milo", gender="boy", helper="grandma", trait="curious"),
    StoryParams(place="garden", adventure="hedge_quest", item="note", name="Lena", gender="girl", helper="gardener", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.name}: {p.adventure} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
