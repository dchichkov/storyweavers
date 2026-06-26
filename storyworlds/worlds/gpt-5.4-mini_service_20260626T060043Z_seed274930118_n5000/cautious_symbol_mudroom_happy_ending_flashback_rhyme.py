#!/usr/bin/env python3
"""
A small storyworld about a cautious child, a mysterious symbol, a mudroom, and
an adventurous day that ends happily.

The premise:
- In a mudroom, a child discovers a symbol on a worn box.
- A flashback reveals why the symbol matters.
- A cautious choice prevents a mess from spreading.
- The story resolves with a happy ending and a light rhyme.

The world is intentionally tiny and state-driven: meters track physical mess and
distance-like progress, memes track emotion.
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
# Registry content
# ---------------------------------------------------------------------------

PLACES = {
    "mudroom": {
        "place": "the mudroom",
        "covering": "hooks and shelves",
        "floor": "the tiled floor",
        "light": "a narrow window",
    }
}

ACTIVITIES = {
    "search": {
        "verb": "search the mudroom",
        "gerund": "searching the mudroom",
        "rush": "dash to the box",
        "result": "found the hidden symbol",
        "keyword": "symbol",
        "tags": {"symbol", "adventure"},
    },
    "sort": {
        "verb": "sort the boots and coats",
        "gerund": "sorting boots and coats",
        "rush": "hurry to the shelf",
        "result": "made the room neat",
        "keyword": "boots",
        "tags": {"mudroom", "order"},
    },
}

SYMBOLS = {
    "sun": {
        "name": "sun symbol",
        "shape": "a round sun with small rays",
        "meaning": "a promise to stay brave in a storm",
        "flashback": "the child once saw the same mark on a paper map from a long-ago walk",
    },
    "key": {
        "name": "key symbol",
        "shape": "a tiny key with a curved handle",
        "meaning": "a clue that something important was tucked away safely",
        "flashback": "the grandparent had traced that mark before hiding a keepsake",
    },
    "leaf": {
        "name": "leaf symbol",
        "shape": "a leaf with a pointed tip",
        "meaning": "a reminder to move carefully through muddy places",
        "flashback": "the child remembered the leaf drawn on a note from a rainy hike",
    },
}

GEAR = {
    "boots": {
        "label": "rain boots",
        "helps": "keep feet dry",
        "covers": {"feet"},
        "guards": {"mud"},
    },
    "mat": {
        "label": "a thick floor mat",
        "helps": "catch muddy drops",
        "covers": {"floor"},
        "guards": {"mud"},
    },
    "towel": {
        "label": "a dry towel",
        "helps": "wipe off wet hands",
        "covers": {"hands"},
        "guards": {"wet"},
    },
}

NAMES = ["Mia", "Leo", "Noa", "Ivy", "Ari", "Zoe", "Theo", "Luna"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father", "grandparent"]
TRAITS = ["cautious", "brave", "curious", "gentle", "spirited", "careful"]


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------

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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mud": 0.0, "wet": 0.0, "distance": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "caution": 0.0, "wonder": 0.0, "worry": 0.0, "love": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    activity: str
    symbol: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place_key: str, activity_key: str, symbol_key: str) -> None:
        self.place_key = place_key
        self.activity_key = activity_key
        self.symbol_key = symbol_key
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        w = World(self.place_key, self.activity_key, self.symbol_key)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def risky(activity_key: str) -> bool:
    return activity_key == "search"


def select_fix(activity_key: str) -> Optional[str]:
    if activity_key == "search":
        return "mat"
    return "towel"


def valid_combo(place_key: str, activity_key: str, symbol_key: str) -> bool:
    return place_key == "mudroom" and symbol_key in SYMBOLS and activity_key in ACTIVITIES


# ---------------------------------------------------------------------------
# Narrative mechanics
# ---------------------------------------------------------------------------

def _flashback(world: World, hero: Entity, symbol: dict) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"As {hero.pronoun().capitalize()} looked at the {symbol['name']}, a flashback returned: "
        f"{symbol['flashback']}."
    )


def _caution(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["caution"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} felt cautious. {hero.pronoun().capitalize()} did not rush in; "
        f"{hero.pronoun().capitalize()} checked the floor and waited for {parent.pronoun('possessive')} nod."
    )


def _adventure_setup(world: World, hero: Entity, parent: Entity, symbol: dict, activity: dict) -> None:
    world.say(
        f"On a busy morning in {PLACES[world.place_key]['place']}, {hero.id} and {parent.id} stood by the hooks."
    )
    world.say(
        f"{hero.id} wanted to {activity['verb']}, because {hero.pronoun('possessive')} eyes had found {symbol['shape']}."
    )
    _flashback(world, hero, symbol)


def _risk(world: World, hero: Entity, activity_key: str) -> None:
    if activity_key == "search":
        hero.memes["worry"] += 1
        world.say(
            f"But the boxes were dusty, and a careless dash could send mud across the floor."
        )


def _offer_fix(world: World, parent: Entity, hero: Entity, activity_key: str) -> Optional[Entity]:
    fix_key = select_fix(activity_key)
    if not fix_key:
        return None
    gear = GEAR[fix_key]
    item = world.add(Entity(
        id=fix_key,
        type="gear",
        label=gear["label"],
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear["covers"]),
        plural=False,
    ))
    item.worn_by = hero.id
    world.say(
        f"{parent.id} pointed to {gear['label']} and said, "
        f"\"Let's use this so the adventure stays safe; it will {gear['helps']}.\""
    )
    return item


def _resolve(world: World, hero: Entity, parent: Entity, symbol: dict, activity: dict, gear: Optional[Entity]) -> None:
    hero.memes["joy"] += 2
    hero.memes["love"] += 1
    if gear:
        world.say(
            f"{hero.id} agreed, and soon {hero.pronoun()} was {activity['gerund']} without troubling the mudroom floor."
        )
    else:
        world.say(
            f"{hero.id} chose the careful path, and the room stayed tidy anyway."
        )
    world.say(
        f"At last, {hero.id} held up the {symbol['name']}, and the symbol's meaning felt true: "
        f"{symbol['meaning']}."
    )
    world.say(
        f"So the day ended bright and light; {hero.id} smiled, {parent.id} smiled, and the mudroom kept its calm."
    )
    world.say("Cautious steps make brave maps, and careful hearts keep happy parts.")


def tell(params: StoryParams) -> World:
    world = World(params.place, params.activity, params.symbol)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"mud": 0.0, "wet": 0.0, "distance": 0.0},
        memes={"joy": 0.0, "caution": 0.0, "wonder": 0.0, "worry": 0.0, "love": 0.0},
    ))
    parent = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=params.parent,
        label=params.parent,
    ))
    symbol = SYMBOLS[params.symbol]
    activity = ACTIVITIES[params.activity]

    world.facts.update(hero=hero, parent=parent, symbol=symbol, activity=activity, params=params)

    # Act 1
    _adventure_setup(world, hero, parent, symbol, activity)

    # Act 2
    world.para()
    _caution(world, hero, parent)
    _risk(world, hero, params.activity)
    if risky(params.activity):
        world.say(
            f"{hero.id} wanted to hurry, but {hero.pronoun('possessive')} caution said to slow down."
        )
    gear = _offer_fix(world, parent, hero, params.activity)

    # Act 3
    world.para()
    _resolve(world, hero, parent, symbol, activity, gear)

    world.facts["gear"] = gear
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short adventure story for a small child set in {PLACES[p.place]["place"]} that includes a symbol.',
        f"Tell a cautious but exciting story where {p.name} notices a symbol, remembers a flashback, and makes a safe choice.",
        f"Write a gentle adventure with a happy ending and a rhyme about being careful in the mudroom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    symbol = f["symbol"]
    activity = f["activity"]
    gear = f.get("gear")
    p: StoryParams = f["params"]

    qa = [
        QAItem(
            question=f"Where did {hero.id} look for the {symbol['name']}?",
            answer=f"{hero.id} looked in {PLACES[p.place]['place']}, where the hooks and shelves could hide a clue.",
        ),
        QAItem(
            question=f"Why was {hero.id} cautious?",
            answer=(
                f"{hero.id} was cautious because {hero.pronoun('possessive')} adventure could make mud spread on the floor, "
                f"and {hero.id} wanted to keep the mudroom safe."
            ),
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} about the {symbol['name']}?",
            answer=f"The flashback reminded {hero.id} that {symbol['flashback']}.",
        ),
        QAItem(
            question=f"How did {parent.id} help {hero.id}?",
            answer=(
                f"{parent.id} suggested {gear.label if gear else 'a careful plan'} so {hero.id} could keep exploring "
                f"without making a mess."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily: {hero.id} understood the symbol, stayed careful, and the mudroom stayed neat."
            ),
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "symbol": [
        QAItem(
            question="What is a symbol?",
            answer="A symbol is a simple mark or picture that can stand for an idea, a clue, or a special meaning.",
        )
    ],
    "mudroom": [
        QAItem(
            question="What is a mudroom?",
            answer="A mudroom is a room near a door where people leave muddy shoes, coats, and wet gear before going inside.",
        )
    ],
    "mud": [
        QAItem(
            question="What is mud?",
            answer="Mud is soft, wet dirt that can stick to shoes, hands, and floors.",
        )
    ],
    "cautious": [
        QAItem(
            question="What does cautious mean?",
            answer="Cautious means being careful and not rushing into something that could cause trouble.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from earlier in the past.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        )
    ],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("symbol", "mudroom", "mud", "cautious", "flashback", "rhyme") for item in WORLD_KNOWLEDGE[key]]


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
place(mudroom).
activity(search).
activity(sort).
symbol(sun).
symbol(key).
symbol(leaf).

valid(Place, Activity, Symbol) :- place(Place), activity(Activity), symbol(Symbol).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "mudroom")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for s in SYMBOLS:
        lines.append(asp.fact("symbol", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(p, a, s) for p in PLACES for a in ACTIVITIES for s in SYMBOLS if valid_combo(p, a, s)}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python valid combos ({len(python_set)}).")
        return 0
    print("MISMATCH between ASP and Python.")
    if python_set - clingo_set:
        print("Only in Python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("Only in ASP:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautious adventure in a mudroom with a symbol and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--symbol", choices=SYMBOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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
    place = args.place or "mudroom"
    activity = args.activity or rng.choice(list(ACTIVITIES))
    symbol = args.symbol or rng.choice(list(SYMBOLS))
    if place != "mudroom":
        raise StoryError("This world is set in the mudroom only.")
    if not valid_combo(place, activity, symbol):
        raise StoryError("No valid combination matches the given options.")
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, symbol=symbol, name=name, gender=gender, parent=parent, trait=trait)


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="mudroom", activity="search", symbol="sun", name="Mia", gender="girl", parent="mother", trait="cautious"),
    StoryParams(place="mudroom", activity="search", symbol="key", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="mudroom", activity="sort", symbol="leaf", name="Ivy", gender="girl", parent="grandparent", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
