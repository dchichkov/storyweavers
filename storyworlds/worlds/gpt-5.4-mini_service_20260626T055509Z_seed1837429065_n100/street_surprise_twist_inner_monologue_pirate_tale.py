#!/usr/bin/env python3
"""
storyworlds/worlds/street_surprise_twist_inner_monologue_pirate_tale.py
=======================================================================

A tiny pirate tale world set on a street, with a surprise, a twist, and an
inner monologue that changes the ending.

Premise:
- A young pirate is on a street in town, chasing a simple goal.
- A surprise appears: a map, a key, or a strange note.
- A twist follows: the first guess is wrong, and the pirate must think again.
- Inner monologue drives the turn from panic to clever action.

The world is intentionally small and classical: a few entities, physical meters,
emotional memes, state-driven narration, and a compatible fixpoint ASP twin for
reasonableness checks.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    openable: bool = False
    opened: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    on_street: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    surprise_kind: str  # map | key | note
    twist_kind: str     # wrong_turn | false_guess | hidden_truth
    clue: str
    resolution: str


@dataclass
class StoryParams:
    place: str
    surprise: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _hero_name(hero: Entity) -> str:
    return hero.id


def _place_line(place: Place) -> str:
    if place.name == "harbor street":
        return "The harbor street smelled like salt and tar, and gulls cried over the roofs."
    if place.name == "market street":
        return "The market street was busy, with carts, apples, and bright awnings."
    return "The street was narrow and sunlit, with stone steps and tiny shop doors."


def _do_surprise(world: World, hero: Entity, s: Surprise) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.add(Entity(id="surprise", kind="thing", type=s.surprise_kind, label=s.label, phrase=s.phrase))
    world.say(
        f"Then came a surprise: {hero.id} found {s.phrase} beside the street."
    )


def _twist(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0) + 1
    world.say(
        f"At first, {hero.id} guessed wrong. "
        f"The clue seemed to point one way, but the street had a twist."
    )
    world.say(
        f"{hero.id} frowned and listened to {hero.pronoun('possessive')} own thoughts: "
        f'"Maybe I am looking at this the wrong way," {hero.pronoun()} thought. '
        f'"Pirates do not win by rushing; they win by noticing."'
    )


def _resolve(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["worry"] = 0
    hero.memes["confusion"] = 0
    world.say(
        f"Then the truth clicked. {surprise.resolution} "
        f"{hero.id} grinned, tucked the clue away, and hurried onward with brave steps."
    )


def tale(place: Place, surprise: Surprise, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    hero.memes["brave"] = 1
    hero.memes["curiosity"] = 0

    world.say(
        f"{hero.id} was a {trait} little pirate who loved finding strange things on a street."
    )
    world.say(_place_line(place))
    world.say(
        f"{hero.id} wanted to follow the rumor of {surprise.phrase}, because pirate stories always began with a clue."
    )

    world.para()
    _do_surprise(world, hero, surprise)
    world.say(surprise.clue)

    world.para()
    _twist(world, hero, surprise)

    world.para()
    _resolve(world, hero, surprise)

    world.facts.update(hero=hero, surprise=surprise, place=place)
    return world


PLACES = {
    "harbor street": Place(name="harbor street", on_street=True, affords={"map", "key", "note"}),
    "market street": Place(name="market street", on_street=True, affords={"map", "note"}),
    "old street": Place(name="old street", on_street=True, affords={"key", "note"}),
}

SURPRISES = {
    "map": Surprise(
        id="map",
        label="a folded map",
        phrase="a folded map under a crate",
        surprise_kind="map",
        twist_kind="false_guess",
        clue="The map had a red X, but the X was not for treasure—it marked a shop sign.",
        resolution="The X was a sign for a tiny shop with a secret door in the back.",
    ),
    "key": Surprise(
        id="key",
        label="a brass key",
        phrase="a brass key shining near the curb",
        surprise_kind="key",
        twist_kind="hidden_truth",
        clue="The key did not open a chest. It fit a narrow box in a doorway instead.",
        resolution="The key opened a weathered little box that held the real route ahead.",
    ),
    "note": Surprise(
        id="note",
        label="a salty note",
        phrase="a salty note tucked in a barrel hoop",
        surprise_kind="note",
        twist_kind="wrong_turn",
        clue="The note sounded like a warning, but it was really a directions puzzle.",
        resolution="The note led to a hidden lane where the next clue waited in plain sight.",
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Finn", "Jude", "Pip", "Theo", "Nico", "Arlo"]
TRAITS = ["curious", "brave", "clever", "spry", "bold"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for surprise_id in place.affords:
            combos.append((place_id, surprise_id))
    return combos


def explain_rejection(place: str, surprise: str) -> str:
    return (
        f"(No story: {PLACES[place].name} does not naturally afford {surprise} on the street. "
        f"Choose a surprise that fits the place.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A street pirate tale with surprise, twist, and inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.place and args.surprise:
        if args.surprise not in PLACES[args.place].affords:
            raise StoryError(explain_rejection(args.place, args.surprise))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.surprise is None or c[1] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, surprise=surprise, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    surprise = f["surprise"]
    place = f["place"]
    return [
        f'Write a short pirate tale for a child about a surprise on {place.name}.',
        f"Tell a story where {hero.id} finds {surprise.phrase} and thinks about what it means.",
        f'Write a gentle street adventure with a surprise, a twist, and a clever ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, surprise, place = f["hero"], f["surprise"], f["place"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {hero.memes.get('curiosity', 0) >= 1 and 'curious' or 'brave'} little pirate on {place.name}.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find?",
            answer=f"{hero.id} found {surprise.phrase}.",
        ),
        QAItem(
            question=f"What changed after the twist?",
            answer=(
                f"{hero.id} stopped guessing too fast, listened to {hero.pronoun('possessive')} own thoughts, "
                f"and found the real meaning of the clue."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a seafaring adventurer who chases treasure, maps, and hidden routes.",
        ),
        QAItem(
            question="What is a street?",
            answer="A street is a path in a town where people walk, travel, and visit shops.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly appears or happens.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a turn in the story that changes what the character thought was true.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside a character's mind that says what they are thinking.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
place_ok(P,S) :- place(P), surprise(S), affords(P,S).
valid_story(P,S) :- place_ok(P,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(place.affords):
            lines.append(asp.fact("affords", pid, s))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("kind", sid, s.surprise_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tale(PLACES[params.place], SURPRISES[params.surprise], params.name, params.gender, params.trait)
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
    StoryParams(place="harbor street", surprise="map", name="Mira", gender="girl", trait="curious"),
    StoryParams(place="market street", surprise="note", name="Finn", gender="boy", trait="clever"),
    StoryParams(place="old street", surprise="key", name="Nora", gender="girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for place, surprise in combos:
            print(f"  {place:14} {surprise}")
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
            header = f"### {p.name}: {p.surprise} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
