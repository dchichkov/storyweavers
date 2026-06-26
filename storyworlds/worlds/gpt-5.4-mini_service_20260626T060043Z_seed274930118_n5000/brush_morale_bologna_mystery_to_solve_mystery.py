#!/usr/bin/env python3
"""
A small mystery storyworld where a child detective solves a tiny problem with a
brush, a lift in morale, and a bologna clue.

Seed idea:
- A child notices something strange.
- A brush and some bologna become the important clues.
- The child follows the clues, solves the mystery, and morale rises.

This is a standalone storyworld script for the Storyweavers repo.
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
    kind: str = "thing"
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
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    kind: str = "place"
    clues: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class ClueItem:
    id: str
    label: str
    phrase: str
    clue_tag: str
    location: str = ""
    holder: str = ""
    hidden: bool = False


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Location) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, ClueItem] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: ClueItem) -> ClueItem:
        self.items[i.id] = i
        return i

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def _m(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _x(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def _story_about(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} loved noticing little odd things at {world.place.label}. "
        f"{hero.pronoun().capitalize()} called {hero.pronoun('object')} a detective."
    )


def _mystery_setup(world: World, hero: Entity, helper: Entity, mystery: ClueItem) -> None:
    _add_meme(hero, "curiosity", 1)
    _add_meme(helper, "support", 1)
    world.say(
        f"One morning, {hero.id} found a strange sign near the {world.place.label}. "
        f"It looked like a mystery that wanted to be solved."
    )
    world.say(
        f"{helper.id} came over with a worried face and said, "
        f'"Something is off. Can you help?"'
    )
    world.say(
        f"On the table sat a {mystery.label}. It did not belong there."
    )


def _brush_clue(world: World, hero: Entity, brush: ClueItem) -> None:
    _add_meme(hero, "focus", 1)
    brush.hidden = False
    world.say(
        f"{hero.id} found a {brush.label} with a tiny smear on it. "
        f"The brush seemed important, so {hero.id} held it very carefully."
    )


def _search(world: World, hero: Entity, helper: Entity, mystery: ClueItem) -> None:
    _add_meme(hero, "determination", 1)
    _add_meme(helper, "hope", 1)
    world.say(
        f"{hero.id} looked under the chair, behind the box, and beside the sink. "
        f"Every place gave one more clue."
    )


def _reveal(world: World, hero: Entity, brush: ClueItem, mystery: ClueItem) -> None:
    _add_meter(hero, "solution", 1)
    world.say(
        f"Then {hero.id} remembered the brush. The smear on it matched the "
        f"{mystery.label} exactly."
    )
    world.say(
        f"The mystery was solved: the {mystery.label} had been used to make the "
        f"mark, and the brush had carried the clue all along."
    )


def _morale_rise(world: World, hero: Entity, helper: Entity) -> None:
    _add_meme(hero, "morale", 2)
    _add_meme(helper, "morale", 2)
    world.say(
        f"{helper.id} smiled so big that the whole room felt lighter. "
        f"{hero.id}'s morale rose right up, like a kite catching wind."
    )
    world.say(
        f"Now everyone could breathe again, because the mystery was no longer hiding."
    )


def tell(place: Location, mystery: ClueItem, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add_entity(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add_entity(Entity(id=helper_name, kind="character", type=helper_type))
    brush = world.add_item(ClueItem(
        id="brush", label="brush", phrase="a little brush", clue_tag="brush", hidden=True
    ))
    bologna = world.add_item(ClueItem(
        id="bologna", label="bologna", phrase="a slice of bologna", clue_tag="bologna", hidden=False
    ))

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["brush"] = brush
    world.facts["mystery"] = mystery
    world.facts["bologna"] = bologna
    world.facts["place"] = place

    _story_about(world, hero)
    world.say(
        f"{hero.id} noticed {mystery.phrase} where it did not belong. "
        f"That was the first clue."
    )
    world.say(
        f"Near it was {bologna.phrase}. At first, it looked guilty."
    )
    _mystery_setup(world, hero, helper, mystery)
    world.say("")
    _brush_clue(world, hero, brush)
    _search(world, hero, helper, mystery)
    world.say("")
    _reveal(world, hero, brush, mystery)
    world.say(
        f"The odd bologna clue turned out to be only a snack wrapper trail, not the real answer."
    )
    _morale_rise(world, hero, helper)
    world.say(
        f"By the end, {hero.id} had a solved mystery, {helper.id} had a happier heart, "
        f"and the {world.place.label} felt safe again."
    )
    return world


LOCATIONS = {
    "kitchen": Location(
        id="kitchen",
        label="kitchen",
        clues={"brush", "bologna"},
        affords={"solve"},
    ),
    "classroom": Location(
        id="classroom",
        label="classroom",
        clues={"brush", "bologna"},
        affords={"solve"},
    ),
    "hallway": Location(
        id="hallway",
        label="hallway",
        clues={"brush", "bologna"},
        affords={"solve"},
    ),
}

MYSTERIES = {
    "marks": ClueItem(
        id="marks",
        label="mystery mark",
        phrase="a mystery mark",
        clue_tag="brush",
    ),
    "missing_note": ClueItem(
        id="missing_note",
        label="missing note",
        phrase="a missing note",
        clue_tag="bologna",
    ),
}

HERO_NAMES = ["Mia", "Noah", "Lina", "Theo", "Ivy", "Ben"]
HELPER_NAMES = ["Aunt May", "Mr. Lee", "Mom", "Dad", "Mrs. Green", "Grandpa"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in LOCATIONS:
        for mystery in MYSTERIES:
            out.append((place, mystery, "solve"))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny mystery storyworld with a brush clue and rising morale.")
    ap.add_argument("--place", choices=sorted(LOCATIONS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
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
    place = args.place or rng.choice(list(LOCATIONS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_type = "girl" if gender == "girl" else "boy"
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "woman", "man"])
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"].label
    mystery = f["mystery"].label
    return [
        f'Write a short mystery story for children where {hero.id} solves a clue at the {place}.',
        f"Tell a gentle detective story about {hero.id}, {helper.id}, and a {mystery} with a brush clue.",
        f'Write a story that uses the words "brush" and "bologna" and ends with the mystery being solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    place = f["place"].label
    return [
        QAItem(
            question=f"Who solved the mystery at the {place}?",
            answer=f"{hero.id} solved the mystery with help from {helper.id}.",
        ),
        QAItem(
            question=f"What clue made the answer clear?",
            answer="The brush was the important clue because its tiny smear matched the mystery.",
        ),
        QAItem(
            question=f"What happened to the bologna clue?",
            answer="The bologna clue turned out to be only a distracting snack trail, not the real answer.",
        ),
        QAItem(
            question=f"How did the helper feel at the end?",
            answer=f"{helper.id} felt much happier, because the mystery was solved and the room felt safe again.",
        ),
        QAItem(
            question=f"How did {hero.id}'s morale change?",
            answer=f"{hero.id}'s morale rose after the mystery was solved, and the victory made the day feel brighter.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure out a mystery.",
        ),
        QAItem(
            question="Why can a brush matter in a mystery?",
            answer="A brush can hold a mark or a smear, and that mark can point to what happened.",
        ),
        QAItem(
            question="What is morale?",
            answer="Morale means how hopeful and brave someone feels inside.",
        ),
        QAItem(
            question="What is bologna?",
            answer="Bologna is a type of sliced meat that people can put in sandwiches or eat as a snack.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, loc in LOCATIONS.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(loc.clues):
            lines.append(asp.fact("has_clue", pid, c))
        for a in sorted(loc.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("needs", mid, m.clue_tag))
    lines.append(asp.fact("item", "brush"))
    lines.append(asp.fact("item", "bologna"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Mystery) :- place(Place), mystery(Mystery), has_clue(Place, brush), needs(Mystery, brush).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, m) for p, m, _ in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    for i in world.items.values():
        lines.append(f"{i.id}: hidden={i.hidden} location={i.location} holder={i.holder}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = LOCATIONS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = tell(place, mystery, params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="kitchen", mystery="marks", hero_name="Mia", hero_type="girl", helper_name="Mom", helper_type="mother"),
    StoryParams(place="classroom", mystery="missing_note", hero_name="Theo", hero_type="boy", helper_name="Mrs. Green", helper_type="woman"),
    StoryParams(place="hallway", mystery="marks", hero_name="Ivy", hero_type="girl", helper_name="Dad", helper_type="father"),
]


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
        print(f"{len(asp_valid_combos())} compatible mystery combos:")
        for p, m in asp_valid_combos():
            print(f"  {p} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: mystery={p.mystery} place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
