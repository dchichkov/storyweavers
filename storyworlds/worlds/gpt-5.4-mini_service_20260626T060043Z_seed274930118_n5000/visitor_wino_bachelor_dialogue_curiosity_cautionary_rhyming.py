#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/visitor_wino_bachelor_dialogue_curiosity_cautionary.py
==============================================================================================================

A small standalone story world for a rhyming, dialogue-rich, cautionary tale
about a visitor, a wino, and a bachelor.

The seed premise:
- A curious visitor comes calling.
- A bachelor and a wino live nearby.
- The visitor wants to peek, sip, or stray.
- The wiser voices answer with dialogue, caution, and a tidy ending.

The world is intentionally tiny and state-driven:
- meters track physical conditions like distance, spill, lantern-light, and snack level
- memes track emotional conditions like curiosity, caution, relief, and trust

The story aims for a child-facing rhyming style without raw event logs or
scaffold language. It stays grounded in the simulated world and resolves with
a clear change in state.
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

RHYME_ENDINGS = [
    "light",
    "night",
    "way",
    "glow",
    "door",
    "near",
    "tune",
    "home",
]

NAMES = ["Mina", "June", "Toby", "Pip", "Nora", "Finn", "Luna", "Ollie"]
BACHELOR_NAMES = ["Mr. Bramble", "Mr. Finch", "Mr. Alder", "Mr. Vale"]
WINO_NAMES = ["Wino Will", "Wino Wes", "Wino Wren", "Wino Walt"]

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    setting_word: str
    indoors: bool = True


@dataclass
class StoryParams:
    place: str
    visitor_name: str
    visitor_type: str
    bachelor_name: str
    wino_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "cottage": Place(name="a little cottage", setting_word="cottage", indoors=True),
    "cellar": Place(name="a cool cellar", setting_word="cellar", indoors=True),
    "porch": Place(name="a small porch", setting_word="porch", indoors=False),
}

# ---------------------------------------------------------------------------
# World-building helpers
# ---------------------------------------------------------------------------
def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    visitor = world.add(Entity(
        id="visitor",
        kind="character",
        type=params.visitor_type,
        label=params.visitor_name,
        meters={"distance": 0.0, "spilled": 0.0, "lantern": 0.0},
        memes={"curiosity": 0.0, "caution": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    bachelor = world.add(Entity(
        id="bachelor",
        kind="character",
        type="man",
        label=params.bachelor_name,
        meters={"tidy": 1.0, "cup": 0.0, "door": 1.0},
        memes={"lonely": 1.0, "warmth": 0.0, "caution": 0.0},
    ))
    wino = world.add(Entity(
        id="wino",
        kind="character",
        type="man",
        label=params.wino_name,
        meters={"lantern": 1.0, "step": 0.0},
        memes={"mirth": 1.0, "caution": 1.0, "wit": 1.0},
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        label="a plate of grapes",
        type="food",
        meters={"sweet": 1.0},
    ))
    tea = world.add(Entity(
        id="tea",
        kind="thing",
        label="a cup of warm tea",
        type="drink",
        meters={"warm": 1.0},
    ))
    world.facts.update(visitor=visitor, bachelor=bachelor, wino=wino, snack=snack, tea=tea)
    return world


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def intro(world: World) -> None:
    v = world.get("visitor")
    b = world.get("bachelor")
    w = world.get("wino")
    world.say(
        f"In {world.place.name}, {v.label} came to roam, "
        f"to meet {b.label} near the bright front dome."
    )
    world.say(
        f"{w.label} was there too, with a wink and a grin; "
        f"the air felt quiet, but full of a spin."
    )
    v.memes["curiosity"] += 1.0
    b.memes["lonely"] += 0.5
    w.memes["wit"] += 0.5


def dialogue_question(world: World) -> None:
    v = world.get("visitor")
    b = world.get("bachelor")
    world.say(
        f'"May I look in the room?" asked {v.label} with cheer. '
        f'"I want to see what is hidden in here."'
    )
    v.meters["distance"] += 1.0
    b.memes["caution"] += 1.0
    world.say(
        f'"The door is not open for guessing," said {b.label}. '
        f'"Things can get wobbly, so tread with care, yes?"'
    )
    v.memes["curiosity"] += 1.0
    v.memes["caution"] += 0.5


def caution_turn(world: World) -> None:
    v = world.get("visitor")
    b = world.get("bachelor")
    w = world.get("wino")
    world.say(
        f'"A curious nose can wander astray," said {w.label}, '
        f'"so ask before stepping, and you will stay safe today."'
    )
    world.say(
        f'{b.label} set out {world.facts["tea"].label} with grace, '
        f'and {w.label} slid the grapes to the place.'
    )
    v.meters["lantern"] += 1.0
    v.memes["caution"] += 1.0
    b.meters["tidy"] += 0.5
    world.facts["offered"] = "tea"
    world.facts["warning"] = "peek before permission can bring a fright"


def resolve(world: World) -> None:
    v = world.get("visitor")
    b = world.get("bachelor")
    w = world.get("wino")
    world.say(
        f'{v.label} nodded and smiled, then chose the tea; '
        f'"I can be curious, but careful," said {v.label} with glee.'
    )
    v.memes["trust"] += 1.0
    v.memes["relief"] += 1.0
    b.memes["warmth"] += 1.0
    world.say(
        f"So they sipped in the glow, with a soft little tune; "
        f"the evening was gentle, and ending too soon."
    )
    world.say(
        f"The door stayed shut, the cups stayed neat, "
        f"and {v.label} went home with a safer beat."
    )
    world.facts["resolved"] = True
    world.facts["ending_image"] = "tea, grapes, and a shut door in lamplight"


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.say("")
    dialogue_question(world)
    world.say("")
    caution_turn(world)
    world.say("")
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------
def valid_places() -> list[str]:
    return list(PLACES.keys())


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    visitor_name = args.visitor_name or rng.choice(NAMES)
    visitor_type = args.visitor_type or rng.choice(["girl", "boy"])
    bachelor_name = args.bachelor_name or rng.choice(BACHELOR_NAMES)
    wino_name = args.wino_name or rng.choice(WINO_NAMES)
    return StoryParams(
        place=place,
        visitor_name=visitor_name,
        visitor_type=visitor_type,
        bachelor_name=bachelor_name,
        wino_name=wino_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    prompts = [
        f"Write a short rhyming story about a visitor, a wino, and a bachelor, with a gentle cautionary tone.",
        f"Tell a dialogue-rich story where {params.visitor_name} learns to be curious and careful in {PLACES[params.place].name}.",
        f"Write a tiny story for children that rhymes and ends with tea, grapes, and a safe choice.",
    ]
    story_qa = [
        QAItem(
            question=f"Who came to visit in the story?",
            answer=f"{params.visitor_name} came to visit and met {params.bachelor_name} and {params.wino_name}.",
        ),
        QAItem(
            question=f"What did the visitor want to do at first?",
            answer=f"{params.visitor_name} wanted to look around and peek into the room out of curiosity.",
        ),
        QAItem(
            question="What safer choice ended the story?",
            answer="The visitor chose warm tea and stayed careful instead of wandering into trouble.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a bachelor?",
            answer="A bachelor is a man who lives on his own and has not married.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before you act so you can stay safe.",
        ),
        QAItem(
            question="What is a visitor?",
            answer="A visitor is someone who comes to see a place or meet someone there.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


# Inline ASP twin
ASP_RULES = r"""
place(cottage).
place(cellar).
place(porch).

visitor_type(girl).
visitor_type(boy).

compatible(P) :- place(P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("feature", "dialogue"))
    lines.append(asp.fact("feature", "curiosity"))
    lines.append(asp.fact("feature", "cautionary"))
    lines.append(asp.fact("style", "rhyming_story"))
    lines.append(asp.fact("seed_word", "visitor"))
    lines.append(asp.fact("seed_word", "wino"))
    lines.append(asp.fact("seed_word", "bachelor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Minimal parity check: the ASP twin should list the same places as Python.
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show compatible/1."))
    asp_places = sorted({args[0] for args in asp.atoms(model, "compatible")})
    py_places = sorted(valid_places())
    if asp_places != py_places:
        print("MISMATCH between ASP and Python place registry:")
        print("ASP:", asp_places)
        print("PY :", py_places)
        return 1

    # Exercise generation end-to-end.
    params = StoryParams(place="cottage", visitor_name="Mina", visitor_type="girl", bachelor_name="Mr. Bramble", wino_name="Wino Will")
    sample = generate(params)
    if not sample.story or "tea" not in sample.story.lower():
        print("Generated story failed sanity check.")
        return 1

    print(f"OK: ASP parity verified; story length={len(sample.story)}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a visitor, a wino, and a bachelor in a cautionary dialogue."
    )
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--visitor-name")
    ap.add_argument("--visitor-type", choices=["girl", "boy"])
    ap.add_argument("--bachelor-name")
    ap.add_argument("--wino-name")
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
    StoryParams(place="cottage", visitor_name="Mina", visitor_type="girl", bachelor_name="Mr. Bramble", wino_name="Wino Will"),
    StoryParams(place="porch", visitor_name="Toby", visitor_type="boy", bachelor_name="Mr. Finch", wino_name="Wino Wes"),
    StoryParams(place="cellar", visitor_name="Luna", visitor_type="girl", bachelor_name="Mr. Alder", wino_name="Wino Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/1."))
        print("Places:")
        for p in sorted(asp.atoms(model, "compatible")):
            print(" ", p[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
