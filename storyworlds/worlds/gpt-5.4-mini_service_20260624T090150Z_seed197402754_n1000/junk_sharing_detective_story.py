#!/usr/bin/env python3
"""
junk_sharing_detective_story.py
===============================

A small storyworld about a young detective who investigates a mystery around
junk, sharing, and a fair choice.

The child-facing tale is built from a simulated world:
- physical meters track where junk piles are, what is hidden, and who is using what
- emotional memes track suspicion, worry, relief, pride, and trust

The story shape is detective-like:
- a problem appears
- clues are gathered
- a suspect is questioned
- the truth is found
- the shared junk is handled in a fair, satisfying way
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
    used_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"junk": 0.0, "hidden": 0.0, "sorted": 0.0, "shared": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "suspicion": 0.0, "worry": 0.0, "relief": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def was(self) -> str:
        return "were" if self.plural else "was"


@dataclass
class Place:
    name: str
    clue_words: list[str] = field(default_factory=list)
    junk_places: list[str] = field(default_factory=list)


@dataclass
class JunkItem:
    id: str
    label: str
    phrase: str
    useful_for: str
    sharable: bool = True
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    junk_item: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tone_of_detective() -> str:
    return "Detective"


def is_reasonable(item: JunkItem, helper_type: str) -> bool:
    return item.sharable and helper_type in {"girl", "boy", "mother", "father"}


def clue_place_words(place: Place) -> str:
    return ", ".join(place.clue_words) if place.clue_words else "quiet corners"


def set_scene(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"It was a {world.place.name} kind of day, and {hero.id} had the sharp eyes of a little detective."
    )
    world.say(
        f"At {world.place.name}, {hero.id} noticed {item.phrase} near {clue_place_words(world.place)}."
    )
    world.say(
        f"{helper.id} was nearby too, and {helper.pronoun().capitalize()} looked ready to help."
    )


def notice_problem(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["curiosity"] += 1
    item.meters["hidden"] += 1
    world.say(
        f"{hero.id} found that the {item.label} had gone missing from the shared pile of junk."
    )
    world.say(
        f"{hero.id} knew this was not just any mess; it was a mystery about who had taken what."
    )


def inspect_clues(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.memes["suspicion"] += 1
    world.say(
        f"{hero.id} looked at tiny clues on the floor and asked gentle questions instead of jumping to blame."
    )
    world.say(
        f"{helper.id} pointed toward {world.place.name}'s {clue_place_words(world.place)}."
    )
    world.facts["clue_place"] = world.place.name


def question_suspect(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    helper.memes["worry"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{hero.id} asked {helper.id} about the missing {item.label}, and {helper.id} answered carefully."
    )
    world.say(
        f"{helper.id} said {helper.pronoun('subject')} had only moved the junk to make room for sharing."
    )


def reveal_truth(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    item.meters["sorted"] += 1
    item.meters["hidden"] = 0.0
    item.meters["shared"] += 1
    helper.memes["relief"] += 1
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"Then the truth came out: nobody had stolen the {item.label}."
    )
    world.say(
        f"It had been tucked aside so everyone could share the rest of the junk in a fair way."
    )


def solve_case(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} smiled like a proud detective and suggested sharing the {item.label} so no one would feel left out."
    )
    world.say(
        f"{helper.id} agreed, and soon the junk pile was sorted, shared, and easy to use."
    )
    world.say(
        f"By the end, {hero.id} had solved the mystery and {helper.id} was {hero.was()} glad to share."
    )


PLACE_REGISTRY = {
    "garage": Place(name="the garage", clue_words=["old boxes", "dusty shelves", "a bent cart"]),
    "shed": Place(name="the shed", clue_words=["a rattle", "a narrow shelf", "a scrap basket"]),
    "attic": Place(name="the attic", clue_words=["a low beam", "a trunk", "a tiny window"]),
    "playroom": Place(name="the playroom", clue_words=["toy bins", "a rug", "a bright corner"]),
}

JUNK_REGISTRY = {
    "paper": JunkItem(id="paper", label="paper scraps", phrase="a stack of paper scraps", useful_for="drawing"),
    "buttons": JunkItem(id="buttons", label="buttons", phrase="a jar of buttons", useful_for="sorting"),
    "boxes": JunkItem(id="boxes", label="cardboard boxes", phrase="some cardboard boxes", useful_for="building", plural=True),
    "cords": JunkItem(id="cords", label="string cords", phrase="a bundle of string cords", useful_for="tying", plural=True),
    "caps": JunkItem(id="caps", label="bottle caps", phrase="a little cup of bottle caps", useful_for="counting", plural=True),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "June", "Poppy"]
BOY_NAMES = ["Leo", "Max", "Finn", "Noah", "Eli", "Theo", "Sam", "Jack"]
HELPERS = ["mother", "father", "friend", "neighbor", "sister", "brother"]
TRAITS = ["brave", "curious", "careful", "quick-thinking", "kind"]


@dataclass
class ASPChoice:
    place: str
    junk_item: str
    helper: str
    gender: str


ASP_RULES = r"""
% A case is valid when the junk item can be shared and the helper can help.
valid_case(P, J, H, G) :- place(P), junk(J), helper(H), gender(G), sharable(J), suitable(H, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACE_REGISTRY:
        lines.append(asp.fact("place", pid))
    for jid, item in JUNK_REGISTRY.items():
        lines.append(asp.fact("junk", jid))
        if item.sharable:
            lines.append(asp.fact("sharable", jid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for h in HELPERS:
        for g in ["girl", "boy"]:
            lines.append(asp.fact("suitable", h, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/4."))
    return sorted(set(asp.atoms(model, "valid_case")))


def verify_asp() -> int:
    python_set = set(valid_cases())
    asp_set = set(asp_valid_cases())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} cases).")
        return 0
    print("Mismatch between ASP and Python.")
    if python_set - asp_set:
        print("Only in Python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("Only in ASP:", sorted(asp_set - python_set))
    return 1


def valid_cases() -> list[tuple[str, str, str, str]]:
    out = []
    for p in PLACE_REGISTRY:
        for j in JUNK_REGISTRY:
            for h in HELPERS:
                for g in ["girl", "boy"]:
                    if JUNK_REGISTRY[j].sharable:
                        out.append((p, j, h, g))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective-style storyworld about junk and sharing.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--junk-item", choices=JUNK_REGISTRY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = valid_cases()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.junk_item:
        combos = [c for c in combos if c[1] == args.junk_item]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        raise StoryError("No valid junk-sharing detective case matches those options.")
    place, junk_item, helper, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, junk_item=junk_item, name=name, gender=gender, helper=helper)


def build_story(params: StoryParams) -> StorySample:
    place = PLACE_REGISTRY[params.place]
    junk = JUNK_REGISTRY[params.junk_item]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id=params.helper.capitalize(), kind="character", type=params.helper, label=params.helper))
    item = world.add(Entity(id=junk.id, type="thing", label=junk.label, phrase=junk.phrase, plural=junk.plural))
    item.owner = hero.id

    set_scene(world, hero, helper, item)
    world.para()
    notice_problem(world, hero, item)
    inspect_clues(world, hero, helper, item)
    question_suspect(world, hero, helper, item)
    world.para()
    reveal_truth(world, hero, helper, item)
    solve_case(world, hero, helper, item)

    world.facts.update(hero=hero, helper=helper, item=item, params=params, place=place, junk=junk)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    junk = world.facts["junk"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a short detective story for a young child about "{junk.label}" and sharing.',
        f"Tell a mystery where {hero.id} and {helper.id} solve a problem by sharing junk at {world.place.name}.",
        f"Write a simple detective tale that ends with {junk.phrase} being shared fairly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} notice at {place.name}?",
            answer=f"{hero.id} noticed that the {item.label} was missing from the shared junk pile at {place.name}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the junk-sharing mystery?",
            answer=f"{helper.id} helped {hero.id} look for clues and solve the mystery.",
        ),
        QAItem(
            question=f"How was the problem solved in the end?",
            answer=f"The problem was solved by sharing the {item.label} fairly instead of letting it stay hidden.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    item = world.facts["item"]
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use something, enjoy something, or have a turn with it.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues to solve a mystery.",
        ),
        QAItem(
            question=f"Why can {item.label} be useful even if it looks like junk?",
            answer=f"{item.label.capitalize()} can still be useful because someone may use it for a job like building, counting, or sorting.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
    StoryParams(place="garage", junk_item="buttons", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="shed", junk_item="boxes", name="Leo", gender="boy", helper="father"),
    StoryParams(place="attic", junk_item="paper", name="Nora", gender="girl", helper="neighbor"),
    StoryParams(place="playroom", junk_item="caps", name="Max", gender="boy", helper="sister"),
]


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/4."))
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        cases = asp_valid_cases()
        print(f"{len(cases)} compatible cases:")
        for c in cases:
            print(" ", c)
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
            header = f"### {p.name}: {p.junk_item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
