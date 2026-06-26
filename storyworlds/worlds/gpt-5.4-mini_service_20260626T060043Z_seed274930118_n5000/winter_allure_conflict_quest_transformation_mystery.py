#!/usr/bin/env python3
"""
A standalone story world: winter allure, a small mystery, a conflict, a quest,
and a transformation.

The seed premise:
- In winter, something beautiful and tempting appears in a small place.
- A child wants to follow the allure of the mystery.
- A careful helper worries about the risk.
- The pair go on a short quest, solve the little mystery, and something about
  the child changes by the end.

This world is deliberately small and constraint-checked. It generates a single,
fully narrated child-facing story plus grounded Q&A.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
    indoor: bool = False
    wintery: bool = True
    opens: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    label: str
    phrase: str
    region: str
    risk: str
    clue: str
    solved_by: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Clue:
    label: str
    phrase: str
    hint: str
    reveal: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "frozen_lake": Place("the frozen lake", indoor=False, wintery=True, opens={"glint", "tracks"}),
    "lantern_hall": Place("the lantern hall", indoor=True, wintery=True, opens={"glow", "riddle"}),
    "snowy_garden": Place("the snowy garden", indoor=False, wintery=True, opens={"footprints", "glow"}),
}

QUEST_ITEMS = {
    "lantern": QuestItem(
        label="lantern",
        phrase="a small brass lantern",
        region="hand",
        risk="cold",
        clue="glow",
        solved_by="light",
        genders={"girl", "boy"},
    ),
    "scarf": QuestItem(
        label="scarf",
        phrase="a soft red scarf",
        region="neck",
        risk="wind",
        clue="tracks",
        solved_by="warmth",
        genders={"girl", "boy"},
    ),
    "boots": QuestItem(
        label="boots",
        phrase="warm wool-lined boots",
        region="feet",
        risk="ice",
        clue="footprints",
        solved_by="safe steps",
        genders={"girl", "boy"},
    ),
}

CLUES = {
    "glow": Clue(
        label="glow",
        phrase="a tiny glow behind the snow",
        hint="something warm was hidden under the drift",
        reveal="a lantern reflected on a clear patch of ice",
    ),
    "tracks": Clue(
        label="tracks",
        phrase="a line of delicate tracks",
        hint="someone small had passed by here recently",
        reveal="a rabbit had hopped through the powder",
    ),
    "footprints": Clue(
        label="footprints",
        phrase="small footprints in the snow",
        hint="the snow showed where someone had already tested the ground",
        reveal="the path was safe because the footprints led to solid stone",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Elsa", "Rina", "Tess", "Maya"]
BOY_NAMES = ["Finn", "Owen", "Jasper", "Theo", "Eli", "Noah", "Pip", "Arlo"]
TRAITS = ["curious", "quiet", "brave", "careful", "gentle", "bright"]
HELPERS = ["grandmother", "father", "mother", "uncle", "aunt"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest_item: str
    clue: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rules and simulation
# ---------------------------------------------------------------------------

def item_at_risk(item: QuestItem, place: Place) -> bool:
    return place.wintery and item.risk in {"cold", "wind", "ice"}


def compatible_item(item: QuestItem, place: Place) -> bool:
    return item_at_risk(item, place)


def predict_quest(world: World, hero: Entity, item: QuestItem, clue: Clue) -> dict:
    sim = world.copy()
    simulate_quest(sim, hero, item, clue, narrate=False)
    solved = sim.facts.get("solved", False)
    return {"solved": solved, "changed": sim.facts.get("changed", False)}


def simulate_quest(world: World, hero: Entity, item: QuestItem, clue: Clue, narrate: bool = True) -> None:
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        hero.memes["curiosity"] = 1.0
    hero.memes["quest"] = hero.memes.get("quest", 0.0) + 1.0
    world.facts["on_quest"] = True
    world.facts["quest_item"] = item.label
    world.facts["clue"] = clue.label
    world.facts["changed"] = False
    if narrate:
        world.say(
            f"{hero.id} followed the {clue.phrase} because the winter air made it feel important."
        )


def transformation(world: World, hero: Entity, helper: Entity, item: QuestItem, clue: Clue) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    world.facts["changed"] = True
    world.facts["solved"] = True
    world.say(
        f"At the end, {hero.id} understood the little mystery and felt different inside: "
        f"still curious, but steadier now."
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('possessive')} {hero.memes.get('trait', '')} {hero.type} "
        f"who loved winter because the world looked quieter and more secret then."
    )
    world.say(
        f"One afternoon, {hero.id} saw {item.phrase} and felt its allure at once."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {helper.type} noticed the look on {hero.id}'s face and knew a small quest was beginning."
    )


def conflict(world: World, hero: Entity, helper: Entity, item: QuestItem, clue: Clue) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted to hurry toward the {clue.phrase}, but {helper.id} worried about the cold and the ice."
    )
    world.say(
        f'"Let\'s not rush," {helper.id} said. "Winter can hide trouble under its pretty shine."'
    )


def quest_turn(world: World, hero: Entity, helper: Entity, item: QuestItem, clue: Clue) -> None:
    world.say(
        f"So they made a careful plan. They went slowly, watching the snow for signs and following the hint in the air."
    )
    world.say(
        f"Near the end of the path, the {clue.label} turned out to mean {clue.reveal}."
    )
    world.say(
        f"{hero.id} found the answer because {helper.id} stayed close and helped with each careful step."
    )


def resolution(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    world.say(
        f"In the end, {hero.id} did not just chase the allure of the mystery; {hero.id} learned how to carry it wisely."
    )
    world.say(
        f"The winter place looked the same, but {hero.id} walked home with a calmer face and a braver heart."
    )


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    item = QUEST_ITEMS[params.quest_item]
    clue = CLUES[params.clue]
    world = World(place)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="girl" if params.gender == "girl" else "boy",
            meters={},
            memes={"trait": params.trait},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper.capitalize(),
            kind="character",
            type=params.helper,
        )
    )
    world.add(
        Entity(
            id="quest_item",
            type=item.label,
            label=item.label,
            phrase=item.phrase,
            owner=hero.id,
            region=item.region,
        )
    )

    intro(world, hero, helper, item)
    world.para()
    conflict(world, hero, helper, item, clue)
    world.para()
    quest_turn(world, hero, helper, item, clue)
    transformation(world, hero, helper, item, clue)
    world.para()
    resolution(world, hero, helper, item)

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        clue=clue,
        place=place,
        solved=True,
        changed=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    item: QuestItem = f["item"]
    clue: Clue = f["clue"]
    place: Place = f["place"]
    return [
        f'Write a short winter story for a child named {hero.id} about an alluring mystery at {place.name}.',
        f"Tell a gentle story where {hero.id} follows a clue, has a small conflict with a careful helper, and learns something new.",
        f'Write a mystery-tinged TinyStories tale that uses the word "{clue.label}" and ends with a transformation.',
        f"Make a child-facing story in which {hero.id} is tempted by {item.label} but solves a winter quest safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: QuestItem = f["item"]
    clue: Clue = f["clue"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"What was the story about at {place.name}?",
            answer=(
                f"It was about {hero.id}, who noticed {item.phrase} in the winter and wanted to learn its secret."
            ),
        ),
        QAItem(
            question=f"Why did {helper.id} worry when {hero.id} wanted to follow the mystery?",
            answer=(
                f"{helper.id} worried because winter can hide cold, wind, or ice, and the path needed careful steps."
            ),
        ),
        QAItem(
            question=f"What clue helped {hero.id} on the quest?",
            answer=f"The clue was {clue.phrase}, and it led them toward the answer.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=(
                f"{hero.id} changed from simply chasing the allure to being more careful and brave at the same time."
            ),
        ),
        QAItem(
            question=f"What was the answer to the little mystery?",
            answer=f"The answer was {clue.reveal}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does allure mean?",
            answer="Allure means something feels very tempting or attractive, so it pulls your attention toward it.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand yet, so you look for clues to figure it out.",
        ),
        QAItem(
            question="Why can winter make a story feel mysterious?",
            answer=(
                "Winter can make a story feel mysterious because snow can hide footprints, quiet places can feel secret, and shiny ice can look like a clue."
            ),
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small search or journey where someone looks for an answer, a thing, or a way to help.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation is when something changes in an important way, like a character learning, growing, or becoming braver.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_name(P,N) :- place(P), name_of_place(P,N).
item(I) :- quest_item(I).
clue(C) :- clue_item(C).

tempting(I) :- quest_item(I).
winter_place(P) :- place(P), wintery(P).

risk(I) :- quest_item(I), risk_of(I, cold).
risk(I) :- quest_item(I), risk_of(I, wind).
risk(I) :- quest_item(I), risk_of(I, ice).

compatible(P,I) :- winter_place(P), risk(I).
valid_story(P,I,C) :- place(P), quest_item(I), clue_item(C), compatible(P,I), clue_matches(C, I).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.wintery:
            lines.append(asp.fact("wintery", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for o in sorted(p.opens):
            lines.append(asp.fact("opens", pid, o))
        lines.append(asp.fact("name_of_place", pid, p.name))

    for qid, q in QUEST_ITEMS.items():
        lines.append(asp.fact("quest_item", qid))
        lines.append(asp.fact("risk_of", qid, q.risk))
        lines.append(asp.fact("clue_matches", q.clue, qid))

    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_item", cid))

    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for i, item in QUEST_ITEMS.items():
            for c in CLUES:
                if compatible_story(p, i, c):
                    combos.append((p, i, c))
    return combos


def compatible_story(place_id: str, item_id: str, clue_id: str) -> bool:
    return PLACES[place_id].wintery and item_at_risk(QUEST_ITEMS[item_id], PLACES[place_id]) and QUEST_ITEMS[item_id].clue == clue_id


def asp_verify() -> int:
    import asp

    clingo_set = set(asp_valid_stories())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest_item: str
    clue: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Winter allure mystery quest story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.quest_item and args.place:
        if not compatible_story(args.place, args.quest_item, args.clue or QUEST_ITEMS[args.quest_item].clue):
            raise StoryError("That item does not fit this winter mystery quest.")
    place = args.place or rng.choice(list(PLACES))
    quest_item = args.quest_item or rng.choice(list(QUEST_ITEMS))
    clue = args.clue or QUEST_ITEMS[quest_item].clue
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    if clue != QUEST_ITEMS[quest_item].clue:
        raise StoryError("That clue does not match the selected quest item.")
    return StoryParams(place=place, quest_item=quest_item, clue=clue, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} owner={e.owner} worn_by={e.worn_by} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="frozen_lake", quest_item="lantern", clue="glow", name="Mina", gender="girl", helper="mother", trait="curious"),
        StoryParams(place="snowy_garden", quest_item="boots", clue="footprints", name="Finn", gender="boy", helper="father", trait="careful"),
        StoryParams(place="lantern_hall", quest_item="scarf", clue="tracks", name="Ivy", gender="girl", helper="aunt", trait="bright"),
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

        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for row in combos:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
