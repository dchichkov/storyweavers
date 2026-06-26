#!/usr/bin/env python3
"""
storyworlds/worlds/rainded_make_gerund_sharing_bravery_moral_value.py
======================================================================

A tiny detective-style storyworld about sharing, bravery, and moral choices.

Premise:
- A child detective notices that something small has gone missing after it rainded.
- A friend had borrowed a special item, and the case turns on sharing it back.
- The hero must be brave enough to ask, listen, and tell the truth.

This world is designed to produce short, complete, child-facing mystery stories
with a beginning, a turn, and a resolution.
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
    borrowed_from: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    clue: str
    missing: str
    borrowed_item: str
    tell: str
    verb: str
    gerund: str
    moral: str
    weather: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    gender: str
    partner: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather = ""
        self.fired: set[str] = set()

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


SETTINGS = {
    "library": Setting(place="the library", indoor=True, affords={"search"}),
    "garden": Setting(place="the garden", indoor=False, affords={"search"}),
    "schoolyard": Setting(place="the schoolyard", indoor=False, affords={"search"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"search"}),
}

CASES = {
    "lost_note": Case(
        id="lost_note",
        clue="a damp note under a bench",
        missing="note",
        borrowed_item="pencil",
        tell="the truth about borrowing it",
        verb="look for the note",
        gerund="looking for the note",
        moral="sharing means returning what you borrowed",
        weather="rainded",
        tags={"sharing", "bravery", "moral_value"},
    ),
    "missing_lantern": Case(
        id="missing_lantern",
        clue="a bright lantern in the wrong crate",
        missing="lantern",
        borrowed_item="lantern",
        tell="where the lantern had been moved",
        verb="find the lantern",
        gerund="finding the lantern",
        moral="being brave means speaking up kindly",
        weather="rainded",
        tags={"sharing", "bravery", "moral_value"},
    ),
    "borrowed_book": Case(
        id="borrowed_book",
        clue="a muddy bookmark by the steps",
        missing="book",
        borrowed_item="book",
        tell="that the book was borrowed and not stolen",
        verb="search for the book",
        gerund="searching for the book",
        moral="good friends share back what they use",
        weather="rainded",
        tags={"sharing", "bravery", "moral_value"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ada", "Ivy", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Max", "Leo", "Owen", "Eli"]
PARTNERS = ["friend", "classmate", "neighbor", "cousin"]
TRAITS = ["curious", "careful", "brave", "gentle", "smart"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, case) for place in SETTINGS for case in CASES]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("unknown place")
    if params.case not in CASES:
        raise StoryError("unknown case")


def make_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style storyworld about sharing, bravery, and moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=PARTNERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    case = args.case or rng.choice(list(CASES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or make_name(gender, rng)
    partner = args.partner or rng.choice(PARTNERS)
    params = StoryParams(place=place, case=case, name=name, gender=gender, partner=partner)
    reasonableness_gate(params)
    return params


def intro(world: World, hero: Entity, partner: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} was a little detective who liked noticing small things."
    )
    world.say(
        f"{hero.pronoun().capitalize()} often worked with a {partner.label} and always tried to be fair."
    )
    world.say(
        f"After it {case.weather}, the ground looked shiny, and {hero.id} spotted a clue near {world.setting.place}."
    )


def mystery(world: World, hero: Entity, partner: Entity, case: Case, item: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} wanted to {case.verb}, because {item.label} was missing."
    )
    world.say(
        f"Then {hero.id} found {case.clue}, and that made the case feel less scary."
    )
    world.say(
        f"{hero.id} noticed {partner.label} near the clue, so {hero.id} took a deep breath and asked a kind question."
    )


def reveal(world: World, hero: Entity, partner: Entity, case: Case, item: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"{partner.label.capitalize()} admitted the truth: {case.tell}."
    )
    world.say(
        f"{partner.label.capitalize()} had borrowed the {item.label} and meant to give {item.it()} back, but forgot when the day got busy."
    )
    world.say(
        f"{hero.id} did not scold {partner.label}. Instead, {hero.id} helped put the {item.label} back where it belonged."
    )
    hero.memes["moral_value"] = hero.memes.get("moral_value", 0) + 1


def ending(world: World, hero: Entity, partner: Entity, case: Case, item: Entity) -> None:
    world.say(
        f"In the end, {hero.id} learned that sharing means returning what you borrowed, and that being brave can also mean telling the truth."
    )
    world.say(
        f"{hero.id} and {partner.label} left together, with the missing {item.label} safe again and the little mystery solved."
    )
    world.say(
        f"The rainy day felt bright now, and {hero.id} was proud of {hero.pronoun('possessive')} kind choice."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    case = CASES[params.case]
    world.weather = case.weather

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    partner = world.add(Entity(id="partner", kind="character", type="friend", label=params.partner))
    item = world.add(Entity(id="item", type="thing", label=case.borrowed_item, phrase=case.borrowed_item, owner=hero.id))

    intro(world, hero, partner, case)
    world.para()
    mystery(world, hero, partner, case, item)
    world.para()
    reveal(world, hero, partner, case, item)
    world.para()
    ending(world, hero, partner, case, item)

    world.facts.update(hero=hero, partner=partner, case=case, item=item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    hero: Entity = f["hero"]
    return [
        f'Write a short detective story for a young child about sharing, bravery, and moral value, and include the word "{case.weather}".',
        f"Tell a gentle mystery where {hero.id} must {case.verb} after something goes missing.",
        f"Write a simple story where a child detective notices a clue, asks a brave question, and learns a moral lesson about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    case: Case = f["case"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id}?",
            answer=f"It is a detective story about {hero.id} solving a small mystery with {partner.label}."
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was the {item.label}."
        ),
        QAItem(
            question=f"What clue helped {hero.id} understand the case?",
            answer=f"The clue was {case.clue}, and it helped {hero.id} think more carefully."
        ),
        QAItem(
            question=f"What did {partner.label} admit at the end?",
            answer=f"{partner.label.capitalize()} admitted that {case.tell}."
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {case.moral}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery."
        ),
        QAItem(
            question="What does it mean to share something?",
            answer="To share something means to let someone else use it, and to give it back when you are done."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary, like asking a truthful question politely."
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
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A story is valid when a place can host a case and the case carries the
% values needed by this world.
valid_story(Place, Case) :- place(Place), mystery(Case), affords(Place, search).
important(Case) :- mystery(Case), needs(Case, sharing), needs(Case, bravery), needs(Case, moral_value).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        if "search" in setting.affords:
            lines.append(asp.fact("affords", place, "search"))
    for cid, case in CASES.items():
        lines.append(asp.fact("mystery", cid))
        for tag in sorted(case.tags):
            lines.append(asp.fact("needs", cid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((p, c) for p, c in valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_story_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, case in valid_combos():
            p = StoryParams(place=place, case=case, name="Mina", gender="girl", partner="friend")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = build_story_from_args(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
