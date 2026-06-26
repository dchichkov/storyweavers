#!/usr/bin/env python3
"""
Standalone storyworld: a bookstore tall tale about a scare, a flashback, a
friendship, and a reconciliation.

A child enters a bookstore, gets startled by a dramatic "monster" in the
story corner, remembers a past fear from a flashback, and then makes friends
with the very thing that scared them after learning it was only a trick of
shadows and a helper in costume.
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

BOOKS = [
    "picture books",
    "fairy tales",
    "adventure stories",
    "animal books",
    "giant atlas books",
]

KIDS = [
    ("Milo", "boy"),
    ("June", "girl"),
    ("Pip", "nonbinary"),
    ("Nia", "girl"),
    ("Theo", "boy"),
    ("Rae", "nonbinary"),
]

ADULTS = [
    ("Aunt Rosa", "aunt"),
    ("Mr. Bell", "bookseller"),
    ("Ms. Wren", "bookseller"),
    ("Uncle Jasper", "uncle"),
]

FEATURES = ("Flashback", "Reconciliation", "Friendship")


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
        if self.type in {"girl", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "uncle", "bookseller"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the bookstore"
    shelves: list[str] = field(default_factory=lambda: ["front shelf", "story corner", "window nook"])


@dataclass
class StoryParams:
    place: str = "bookstore"
    child_name: str = "Milo"
    child_gender: str = "boy"
    adult_name: str = "Mr. Bell"
    adult_type: str = "bookseller"
    book: str = "picture books"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _tall_tale_detail(book: str) -> str:
    return {
        "picture books": "a stack so tall it could tickle the ceiling",
        "fairy tales": "pages that seemed to whisper like wind through a keyhole",
        "adventure stories": "covers that looked brave enough to wrestle a storm",
        "animal books": "pictures with eyes so lively they nearly blinked",
        "giant atlas books": "maps so large they could have covered a wagon",
    }[book]


def _flashback_sentence(child: Entity) -> str:
    return (
        f"{child.id} remembered an old afternoon when a cloak on a chair had looked "
        f"like a wolf with a crooked back."
    )


def _scare_trigger(world: World, child: Entity, adult: Entity, book: str) -> None:
    child.memes["startled"] = child.memes.get("startled", 0) + 1
    world.say(
        f"In the story corner of the bookstore, {child.id} spotted {book} stacked "
        f"under a lamp, and the shadow behind it looked as long as a canoe."
    )
    world.say(
        f"{child.id} gave a little gasp so sharp it could have split a bean in two."
    )


def _flashback(world: World, child: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    world.say(_flashback_sentence(child))
    world.say(
        f"That memory made {child.id}'s knees wobble, because old fears can gallop "
        f"back faster than a rabbit on a slide whistle."
    )


def _reveal_trick(world: World, child: Entity, adult: Entity) -> None:
    world.say(
        f"{adult.id} laughed kindly and lifted the cloth away. Underneath was only "
        f"a cardboard dragon, painted bright red, with a string of paper stars on its nose."
    )
    world.say(
        f"'Why, that's not a beast at all,' {adult.id} said. 'It's the bookstore's "
        f"reading mascot, and it likes to guard the quiet corner.'"
    )


def _reconciliation(world: World, child: Entity, adult: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["fear"] = 0
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    world.say(
        f"{child.id} blinked, then laughed at the size of the mistake. "
        f"The fear melted like butter on a warm biscuit."
    )
    world.say(
        f"{adult.id} and {child.id} sat together on the rug between the shelves and "
        f"read the dragon's story aloud until the room felt friendly again."
    )


def _friendship(world: World, child: Entity, adult: Entity) -> None:
    child.memes["friendship"] = child.memes.get("friendship", 0) + 1
    adult.memes["friendship"] = adult.memes.get("friendship", 0) + 1
    world.say(
        f"By the time the last page turned, {child.id} and {adult.id} were grinning "
        f"like two fireflies sharing one lantern."
    )
    world.say(
        f"They promised to keep the dragon company on rainy afternoons, and the "
        f"bookstore seemed to stand a little taller for it."
    )


def tell(params: StoryParams) -> World:
    world = World(Setting(place="the bookstore"))

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    adult = world.add(Entity(id=params.adult_name, kind="character", type=params.adult_type))

    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["book"] = params.book

    world.say(
        f"{child.id} went into the bookstore where {params.book} were stacked so high "
        f"they looked like a paper mountain."
    )
    world.say(
        f"Every shelf had a different treasure, and {child.id} liked the smell of ink, "
        f"dust, and stories."
    )
    world.say(f"The tallest wonder was {_tall_tale_detail(params.book)}.")

    world.para()
    _scare_trigger(world, child, adult, params.book)
    _flashback(world, child)

    world.para()
    world.say(
        f"{adult.id} noticed the scare at once and walked over slow as a friendly turtle."
    )
    _reveal_trick(world, child, adult)
    _reconciliation(world, child, adult)

    world.para()
    _friendship(world, child, adult)

    world.facts["resolved"] = True
    return world


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    book = world.facts["book"]
    return [
        f"Write a tall-tale story set in a bookstore where {child.id} gets a scare, remembers a past fear, and then makes a new friend.",
        f"Tell a child-friendly bookstore story in which {adult.id} helps {child.id} understand a shadowy surprise near the {book}.",
        "Write a story with a flashback, reconciliation, and friendship that ends with everyone feeling safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    book = world.facts["book"]
    return [
        QAItem(
            question=f"Where did {child.id} get scared?",
            answer=f"{child.id} got scared in the bookstore, near the story corner and the tall stacks of books.",
        ),
        QAItem(
            question=f"What did {child.id} remember in the flashback?",
            answer=f"{child.id} remembered an old day when a cloak on a chair had looked like a wolf.",
        ),
        QAItem(
            question=f"How did {adult.id} help after the scare?",
            answer=f"{adult.id} showed that the scary shape was only a cardboard dragon and then sat with {child.id} to read together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the fear was gone and {child.id} and {adult.id} had become friendly story companions.",
        ),
        QAItem(
            question=f"What book theme was in the bookstore scene?",
            answer=f"The story mentioned {book} and used them to make the bookstore feel tall and grand.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bookstore?",
            answer="A bookstore is a place where people go to buy, browse, and read books.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that remembers something that happened earlier.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and become friendly again.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind way of caring about someone and enjoying time together.",
        ),
        QAItem(
            question="Why can shadows look scary?",
            answer="Shadows can look scary because they change shapes and can seem bigger or stranger than the thing that made them.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
child_scared(C) :- scared(C).
has_flashback(C) :- remembers_past_fear(C).
reconciled(C,A) :- friend(C,A), calm_after_reveal(C,A).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "bookstore"),
            asp.fact("feature", "flashback"),
            asp.fact("feature", "reconciliation"),
            asp.fact("feature", "friendship"),
            asp.fact("theme", "scare"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld set in a bookstore.")
    ap.add_argument("--place", choices=["bookstore"], default="bookstore")
    ap.add_argument("--name", choices=[n for n, _ in KIDS], default=None)
    ap.add_argument("--adult", choices=[n for n, _ in ADULTS], default=None)
    ap.add_argument("--book", choices=BOOKS, default=None)
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
    name = args.name or rng.choice([n for n, _ in KIDS])
    child_gender = dict(KIDS)[name]
    adult = args.adult or rng.choice([n for n, _ in ADULTS])
    adult_type = dict(ADULTS)[adult]
    book = args.book or rng.choice(BOOKS)
    return StoryParams(
        place="bookstore",
        child_name=name,
        child_gender=child_gender,
        adult_name=adult,
        adult_type=adult_type,
        book=book,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _asp_verify() -> int:
    try:
        import asp
    except Exception as ex:
        print(f"ASP unavailable: {ex}")
        return 1
    model = asp.one_model(asp_program("#show feature/1."))
    if model is None:
        print("No ASP model found.")
        return 1
    print("OK: ASP twin loads successfully.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciled/2."))
        return

    if args.verify:
        sys.exit(_asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as ex:
            print(f"ASP unavailable: {ex}")
            return
        model = asp.one_model(asp_program("#show feature/1."))
        atoms = sorted(set(asp.atoms(model, "feature")))
        print(f"{len(atoms)} ASP feature facts: {atoms}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(child_name="Milo", child_gender="boy", adult_name="Mr. Bell", adult_type="bookseller", book="picture books"),
            StoryParams(child_name="June", child_gender="girl", adult_name="Aunt Rosa", adult_type="aunt", book="fairy tales"),
            StoryParams(child_name="Rae", child_gender="nonbinary", adult_name="Ms. Wren", adult_type="bookseller", book="adventure stories"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.child_name} / {p.book}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
