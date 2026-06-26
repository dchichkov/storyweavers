#!/usr/bin/env python3
"""
storyworlds/worlds/belabor_carb_mystery_to_solve_fable.py
==========================================================

A small fable-style story world about a puzzling missing carb and the danger
of belaboring a mystery instead of following the simple clues.

Premise:
- In a little animal village, a shared carb loaf goes missing before supper.
- One character keeps belaboring every guess.
- Another notices the true clue and solves the mystery with calm care.

Style:
- Child-facing fable prose
- Clear beginning, middle turn, and resolution
- Moral at the end
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "dog", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hare", "rabbit", "mouse", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = False
    clue_kind: str = "crumb"


@dataclass
class Mystery:
    id: str
    missing: str
    risk: str
    clue: str
    culprit: str
    solved_by: str
    method: str
    moral: str


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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# Registries
PLACES = {
    "meadow": Place("the meadow"),
    "barn": Place("the barn", indoor=True, clue_kind="hay"),
    "kitchen": Place("the kitchen", indoor=True, clue_kind="crumb"),
}

MYSTERIES = {
    "carb": Mystery(
        id="carb",
        missing="carb loaf",
        risk="supper would be plain",
        clue="tiny flour crumbs",
        culprit="mice",
        solved_by="a trail of crumbs on the floor",
        method="followed the crumbs to the pantry",
        moral="When a mystery looks big, start with the small clues.",
    ),
}

CHAR_TYPES = ["fox", "hare", "owl", "mouse", "badger", "rabbit"]
TRAITS = ["wise", "curious", "patient", "proud", "gentle", "hasty"]


def valid_combos() -> list[tuple[str, str]]:
    # Only one core mystery, but all places are valid: the clues fit each setting.
    return [(place, "carb") for place in PLACES]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    hero_trait: str
    belaborer_name: str
    belaborer_type: str
    culprit_name: str
    culprit_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable-style mystery about a missing carb and the danger of belaboring clues."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=CHAR_TYPES)
    ap.add_argument("--belaborer-name")
    ap.add_argument("--belaborer-type", choices=CHAR_TYPES)
    ap.add_argument("--culprit-name")
    ap.add_argument("--culprit-type", choices=CHAR_TYPES)
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
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or "carb"
    hero_type = args.hero_type or rng.choice(["hare", "fox", "owl"])
    belaborer_type = args.belaborer_type or rng.choice([t for t in CHAR_TYPES if t != hero_type])
    culprit_type = args.culprit_type or "mouse"
    if len({hero_type, belaborer_type, culprit_type}) < 2:
        raise StoryError("Need a few distinct characters for the mystery.")
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=args.hero_name or rng.choice(["Milo", "Nina", "Pip", "Tessa", "Wren"]),
        hero_type=hero_type,
        hero_trait=rng.choice(TRAITS),
        belaborer_name=args.belaborer_name or rng.choice(["Bram", "Ivy", "Sage", "Otis", "Luna"]),
        belaborer_type=belaborer_type,
        culprit_name=args.culprit_name or rng.choice(["Twitch", "Nib", "Moss", "Penny", "Dot"]),
        culprit_type=culprit_type,
    )


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,M) :- place(P), mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_type,
        traits=[params.hero_trait, "kind"],
    ))
    belaborer = world.add(Entity(
        id=params.belaborer_name, kind="character", type=params.belaborer_type,
        traits=["belaboring", "anxious"],
    ))
    culprit = world.add(Entity(
        id=params.culprit_name, kind="character", type=params.culprit_type,
        traits=["small", "quick"],
    ))
    loaf = world.add(Entity(
        id="loaf", type="food", label=mystery.missing, phrase=f"a warm {mystery.missing}",
        owner=hero.id, caretaker=hero.id,
    ))

    # Setup
    world.say(
        f"In {place.name}, {hero.id} the {hero.type} loved the supper bell and the smell of warm bread."
    )
    world.say(
        f"That evening, the neighbors had set out {loaf.phrase} for everyone, but before supper, it was gone."
    )

    # Middle turn
    world.para()
    world.say(
        f"{belaborer.id} the {belaborer.type} began to belabor every guess."
    )
    world.say(
        f'"Maybe it was the wind," {belaborer.pronoun("subject")} said. '
        f'"Maybe it was a hawk. Maybe it was a shadow. Maybe it was three different thieves."'
    )
    hero.memes["patience"] = hero.memes.get("patience", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1

    # Clue and solution
    world.para()
    world.say(
        f"{hero.id} did not argue. {hero.pronoun().capitalize()} looked at the floor and saw {mystery.clue}."
    )
    world.say(
        f"{hero.id} followed the clue and {mystery.method}, where {culprit.id} the {culprit.type} was nibbling the last corner of the {mystery.missing}."
    )
    world.say(
        f"{culprit.id} blinked and admitted that {culprit.pronoun('subject')} had carried it away because the smell was too tempting."
    )

    # Resolution
    world.para()
    world.say(
        f"{hero.id} made a fair plan: the {mystery.missing} would be shared, and the next loaf would be baked with enough for all."
    )
    world.say(
        f"{belaborer.id} finally stopped talking in circles and nodded. {belaborer.pronoun().capitalize()} saw that one clear clue was better than ten fancy guesses."
    )
    world.say(
        f"From then on, the little animals remembered the moral: {mystery.moral}"
    )

    world.facts.update(
        hero=hero,
        belaborer=belaborer,
        culprit=culprit,
        loaf=loaf,
        mystery=mystery,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a missing {f["mystery"].missing} in {f["place"].name} that includes the word "belabor".',
        f"Tell a gentle mystery where {f['hero'].id} solves a missing-carb problem without getting lost in too many guesses.",
        f"Write a child-friendly fable about a small clue, a shared loaf, and a character who keeps belaboring the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    belaborer = f["belaborer"]
    culprit = f["culprit"]
    mystery = f["mystery"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who solved the mystery in {place.name}?",
            answer=f"{hero.id} solved it by noticing {mystery.clue} and following the clue to the pantry.",
        ),
        QAItem(
            question=f"What did {belaborer.id} keep doing at first?",
            answer=f"{belaborer.id} kept belaboring every guess instead of looking closely at the floor.",
        ),
        QAItem(
            question=f"Who had taken the {mystery.missing}?",
            answer=f"It was {culprit.id} the {culprit.type}, who had carried it away and started nibbling it.",
        ),
        QAItem(
            question=f"What lesson did the animals learn?",
            answer=f"They learned that when a mystery looks big, it helps to start with the small clues.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or unknown that people try to understand by looking for clues.",
        ),
        QAItem(
            question="What does it mean to belabor something?",
            answer="To belabor something means to talk about it too much or keep repeating it in a way that makes it feel heavy.",
        ),
        QAItem(
            question="What is a carb?",
            answer="A carb is a kind of food nutrient, and in stories it can also mean a breadlike food made from grains.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} traits={e.traits}")
    return "\n".join(lines)


def valid_combos_py() -> list[tuple[str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos_py())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - ac))
    print("asp only:", sorted(ac - py))
    return 1


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
    StoryParams(
        place="meadow",
        mystery="carb",
        hero_name="Milo",
        hero_type="hare",
        hero_trait="curious",
        belaborer_name="Bram",
        belaborer_type="owl",
        culprit_name="Nib",
        culprit_type="mouse",
    ),
    StoryParams(
        place="barn",
        mystery="carb",
        hero_name="Tessa",
        hero_type="fox",
        hero_trait="patient",
        belaborer_name="Sage",
        belaborer_type="rabbit",
        culprit_name="Dot",
        culprit_type="mouse",
    ),
    StoryParams(
        place="kitchen",
        mystery="carb",
        hero_name="Wren",
        hero_type="owl",
        hero_trait="wise",
        belaborer_name="Ivy",
        belaborer_type="fox",
        culprit_name="Penny",
        culprit_type="mouse",
    ),
]


def resolve_invalid_reason(args: argparse.Namespace) -> None:
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name} in {p.place} (mystery: {p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
