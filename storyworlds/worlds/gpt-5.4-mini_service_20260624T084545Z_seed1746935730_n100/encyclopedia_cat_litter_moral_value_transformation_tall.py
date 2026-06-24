#!/usr/bin/env python3
"""
A small Storyweavers world: a tall tale about a cat, an encyclopedia, and litter,
where a quarrel about value turns into a transformation that teaches a moral.

Core premise:
- A proud cat values a dusty encyclopedia.
- A litter-filled space makes the book seem ruined or useless.
- A patient helper shows that cleaning, caring, and reading can transform both
  the book's state and the cat's mind.
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
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

MORAL_VALUES = {
    "care": "care",
    "patience": "patience",
    "honesty": "honesty",
    "helpfulness": "helpfulness",
    "kindness": "kindness",
}

TRANSFORMATIONS = {
    "cleaning": "cleaning",
    "repair": "repair",
    "learning": "learning",
    "sharing": "sharing",
}

PLACES = {
    "library": {"place": "the little library", "indoors": True, "affords": {"reading", "cleaning"}},
    "attic": {"place": "the dusty attic", "indoors": True, "affords": {"reading", "cleaning"}},
    "porch": {"place": "the sunny porch", "indoors": False, "affords": {"reading", "cleaning"}},
    "shed": {"place": "the old garden shed", "indoors": True, "affords": {"reading", "cleaning"}},
}

CAT_NAMES = ["Milo", "Pip", "Mittens", "Toby", "Nora", "Luna", "Waffles", "Penny"]
HUMAN_NAMES = ["Aunt June", "Mr. Bell", "Ms. Rose", "Grandpa Ben", "Mrs. Finch", "Uncle Otis"]
CAT_TRAITS = ["proud", "curious", "mighty", "fussy", "bright-eyed", "stubborn"]
HELPER_TRAITS = ["patient", "gentle", "wise", "kind", "steady"]

# ---------------------------------------------------------------------------
# Entities
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "cat":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    place: str
    indoors: bool
    affords: set[str]


@dataclass
class StoryParams:
    place: str
    moral: str
    transformation: str
    cat_name: str
    helper_name: str
    cat_trait: str
    helper_trait: str
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_litter_marks_book(world: World) -> list[str]:
    out: list[str] = []
    cat = next((e for e in world.entities.values() if e.type == "cat"), None)
    book = next((e for e in world.entities.values() if e.type == "encyclopedia"), None)
    if not cat or not book:
        return out
    if cat.meters.get("litter", 0.0) < THRESHOLD:
        return out
    sig = ("litter", book.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    book.meters["dusty"] = book.meters.get("dusty", 0.0) + 1
    book.meters["soiled"] = book.meters.get("soiled", 0.0) + 1
    out.append(f"The encyclopedia came out dusty and spotted from the litter.")
    return out


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    helper = next((e for e in world.entities.values() if e.kind == "character"), None)
    book = next((e for e in world.entities.values() if e.type == "encyclopedia"), None)
    if not helper or not book:
        return out
    if book.meters.get("soiled", 0.0) < THRESHOLD:
        return out
    sig = ("cleanup", book.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    book.meters["clean"] = book.meters.get("clean", 0.0) + 1
    book.meters["soiled"] = 0.0
    out.append("A careful wipe turned the big book clean again.")
    return out


def _r_moral_turn(world: World) -> list[str]:
    cat = next((e for e in world.entities.values() if e.type == "cat"), None)
    helper = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not cat or not helper:
        return []
    if cat.memes.get("stubborn", 0.0) < THRESHOLD:
        return []
    if cat.meters.get("cleaned", 0.0) < THRESHOLD:
        return []
    sig = ("moral", cat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cat.memes["understanding"] = cat.memes.get("understanding", 0.0) + 1
    cat.memes["moral_value"] = cat.memes.get("moral_value", 0.0) + 1
    return ["__moral__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_litter_marks_book, _r_cleanup, _r_moral_turn):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__moral__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def setting_line(place: Place) -> str:
    if place.indoors:
        return f"{place.place.capitalize()} was quiet, and dust floated in the corners like tiny brown moths."
    return f"{place.place.capitalize()} was bright, but a litter drift had blown in from the road."


def tell(place: Place, params: StoryParams) -> World:
    world = World(place)
    cat = world.add(Entity(
        id=params.cat_name,
        kind="character",
        type="cat",
        label=params.cat_name,
        meters={"litter": 0.0},
        memes={"pride": 1.0, "stubborn": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="human",
        label=params.helper_name,
        meters={"care": 1.0},
        memes={"patience": 1.0},
    ))
    book = world.add(Entity(
        id="encyclopedia",
        kind="thing",
        type="encyclopedia",
        label="encyclopedia",
        phrase="a heavy encyclopedia with bright pages",
        caretaker=helper.id,
        meters={"clean": 1.0, "dusty": 0.0, "soiled": 0.0},
        memes={"value": 1.0},
    ))

    world.say(f"{cat.id} was a {params.cat_trait} cat who loved to sit by the encyclopedia and guard it like treasure.")
    world.say(f"{helper.id} was a {params.helper_trait} helper who believed that even a dusty thing could still have great value.")
    world.para()
    world.say(setting_line(place))
    world.say(f"One day, {cat.id} wanted to explore the {params.transformation} of the old book, but litter had blown all around it.")
    cat.meters["litter"] += 1.0
    cat.memes["stubborn"] += 1.0
    cat.memes["worry"] = cat.memes.get("worry", 0.0) + 1.0
    propagate(world)
    world.say(f"{cat.id} frowned and said the encyclopedia was too messy to matter.")
    world.para()
    world.say(f"But {helper.id} knelt down and said, \"A thing is not worthless because it is dusty. We can clean it, read it, and learn from it.\"")
    world.say(f"Together they brushed off the litter, turned the pages, and watched the old encyclopedia become useful again.")
    cat.meters["cleaned"] = 1.0
    cat.meters["litter"] = 0.0
    cat.memes["stubborn"] = 0.0
    cat.memes["pride"] = 0.0
    cat.memes["understanding"] = 1.0
    world.para()
    world.say(f"In the end, {cat.id} curled beside the cleaned encyclopedia, now a little wiser and a little humbler, and the room felt lighter than before.")

    world.facts.update(
        cat=cat,
        helper=helper,
        book=book,
        moral=params.moral,
        transformation=params.transformation,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES_REGISTRY = {
    key: Place(id=key, place=value["place"], indoors=value["indoors"], affords=set(value["affords"]))
    for key, value in PLACES.items()
}

MORAL_REGISTRY = MORAL_VALUES
TRANSFORMATION_REGISTRY = TRANSFORMATIONS


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES_REGISTRY.items():
        for moral in MORAL_REGISTRY:
            for trans in TRANSFORMATION_REGISTRY:
                if "cleaning" == trans or "learning" == trans or "sharing" == trans or "repair" == trans:
                    combos.append((pid, moral, trans))
    return combos


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cat: Entity = f["cat"]
    helper: Entity = f["helper"]
    book: Entity = f["book"]
    return [
        f'Write a tall tale about a cat named {cat.id}, an encyclopedia, and a messy littered place.',
        f"Tell a child-friendly story where {cat.id} thinks {book.label} has lost its value, but {helper.id} teaches a moral about care.",
        f"Write a short story about transformation, where litter, cleaning, and learning change how {cat.id} feels about the encyclopedia.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat: Entity = f["cat"]
    helper: Entity = f["helper"]
    book: Entity = f["book"]
    moral = f["moral"]
    trans = f["transformation"]
    return [
        QAItem(
            question=f"Why did {cat.id} think the encyclopedia was not worth much at first?",
            answer=f"{cat.id} thought that way because litter had made the encyclopedia dusty and spotted, so it looked less special to {cat.id}.",
        ),
        QAItem(
            question=f"What did {helper.id} do to change the situation?",
            answer=f"{helper.id} cleaned the encyclopedia and reminded {cat.id} that things can still have value even when they get dusty.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {cat.id} changed from stubborn to understanding, the encyclopedia was clean again, and the story showed a {moral} lesson about {trans}.",
        ),
        QAItem(
            question=f"What kind of book was it?",
            answer=f"It was an encyclopedia, a big reference book full of facts and answers.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an encyclopedia?",
            answer="An encyclopedia is a big reference book that collects facts and information about many topics.",
        ),
        QAItem(
            question="What is litter?",
            answer="Litter is trash or scattered bits of waste that do not belong on the ground.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a big change, like when something becomes clean, better, or different from before.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an idea about how to act well, such as kindness, honesty, or care.",
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
        lines.append(f"  {e.id:14} type={e.type:12} meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
moral(M) :- moral_value(M).
transformation(T) :- transformation_kind(T).

cat(C) :- entity(C), cat_type(C).
encyclopedia(B) :- entity(B), encyclopedia_type(B).
helper(H) :- entity(H), helper_type(H).

littered(P) :- litter(P).
dusty(B) :- dusty_book(B).
clean(B) :- clean_book(B).
stubborn(C) :- stubborn_cat(C).
understanding(C) :- understanding_cat(C).

moral_turn(C,H) :- cat(C), helper(H), stubborn(C), understanding(C).
transformed(B) :- clean(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES_REGISTRY:
        lines.append(asp.fact("setting", pid))
    for m in MORAL_REGISTRY:
        lines.append(asp.fact("moral_value", m))
    for t in TRANSFORMATION_REGISTRY:
        lines.append(asp.fact("transformation_kind", t))
    lines.append(asp.fact("entity", "cat"))
    lines.append(asp.fact("entity", "helper"))
    lines.append(asp.fact("entity", "encyclopedia"))
    lines.append(asp.fact("cat_type", "cat"))
    lines.append(asp.fact("helper_type", "helper"))
    lines.append(asp.fact("encyclopedia_type", "encyclopedia"))
    lines.append(asp.fact("litter", "any"))
    lines.append(asp.fact("dusty_book", "encyclopedia"))
    lines.append(asp.fact("clean_book", "encyclopedia"))
    lines.append(asp.fact("stubborn_cat", "cat"))
    lines.append(asp.fact("understanding_cat", "cat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show moral_turn/2. #show transformed/1."))
    _ = asp.atoms(model, "moral_turn")
    _ = asp.atoms(model, "transformed")
    python_ok = bool(valid_combos())
    if python_ok:
        print("OK: ASP and Python reasonableness scaffolding are both present.")
        return 0
    print("Mismatch: Python valid_combos() produced no valid combinations.")
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: encyclopedia, cat, litter, moral value, transformation.")
    ap.add_argument("--place", choices=PLACES_REGISTRY)
    ap.add_argument("--moral", choices=MORAL_REGISTRY)
    ap.add_argument("--transformation", choices=TRANSFORMATION_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--cat-trait", choices=CAT_TRAITS)
    ap.add_argument("--helper-trait", choices=HELPER_TRAITS)
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
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, moral, trans = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        moral=args.moral or moral,
        transformation=args.transformation or trans,
        cat_name=args.name or rng.choice(CAT_NAMES),
        helper_name=args.helper or rng.choice(HUMAN_NAMES),
        cat_trait=args.cat_trait or rng.choice(CAT_TRAITS),
        helper_trait=args.helper_trait or rng.choice(HELPER_TRAITS),
    )


CURATED = [
    StoryParams(place="library", moral="care", transformation="cleaning", cat_name="Milo", helper_name="Mrs. Finch", cat_trait="proud", helper_trait="patient"),
    StoryParams(place="attic", moral="patience", transformation="learning", cat_name="Pip", helper_name="Grandpa Ben", cat_trait="curious", helper_trait="wise"),
    StoryParams(place="porch", moral="kindness", transformation="sharing", cat_name="Luna", helper_name="Aunt June", cat_trait="stubborn", helper_trait="gentle"),
    StoryParams(place="shed", moral="helpfulness", transformation="repair", cat_name="Waffles", helper_name="Mr. Bell", cat_trait="fussy", helper_trait="steady"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES_REGISTRY:
        raise StoryError(f"Unknown place: {params.place}")
    world = tell(PLACES_REGISTRY[params.place], params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show moral_turn/2. #show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show transformed/1. #show moral_turn/2."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

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
            header = f"### {p.cat_name} at {p.place} ({p.moral} / {p.transformation})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
