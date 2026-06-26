#!/usr/bin/env python3
"""
A small detective-story world where a curious child detective solves a far, dismal
mystery by noticing kindness, a twist, and a careful clue trail.
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


@dataclass
class Place:
    id: str
    name: str
    far: bool = False
    dismal: bool = False
    clues: list[str] = field(default_factory=list)
    mood: str = "quiet"


@dataclass
class Character:
    id: str
    name: str
    role: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    possessions: list[str] = field(default_factory=list)


@dataclass
class ObjectItem:
    id: str
    name: str
    owner: Optional[str] = None
    hidden: bool = False
    clue: str = ""
    twist: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    detective_name: str
    helper_name: str
    missing_item: str
    seed: Optional[int] = None


PLACES = {
    "lane": Place(
        id="lane",
        name="the far lane behind the station",
        far=True,
        dismal=True,
        clues=["muddy boots", "a torn note", "a dropped key"],
        mood="dismal",
    ),
    "dock": Place(
        id="dock",
        name="the far dock by the gray water",
        far=True,
        dismal=True,
        clues=["wet rope", "salt on the rail", "a small button"],
        mood="foggy",
    ),
    "alley": Place(
        id="alley",
        name="the narrow alley beside the bakery",
        far=False,
        dismal=True,
        clues=["crumbs", "a coin", "a bent spoon"],
        mood="hushed",
    ),
}

MISSING_ITEMS = {
    "kite": "red kite",
    "book": "picture book",
    "bell": "brass bell",
}

DETECTIVE_NAMES = ["Mina", "Toby", "Lena", "Arlo", "Nia", "Eli"]
HELPER_NAMES = ["Moss", "Pip", "June", "Owen", "Tess", "Rae"]


@dataclass
class World:
    place: Place
    detective: Character
    helper: Character
    item: ObjectItem
    clues_found: list[str] = field(default_factory=list)
    truth_found: bool = False
    kindness_spent: bool = False
    twist_revealed: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    entities: dict[str, object] = field(default_factory=dict)

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
        clone = World(
            place=copy.deepcopy(self.place),
            detective=copy.deepcopy(self.detective),
            helper=copy.deepcopy(self.helper),
            item=copy.deepcopy(self.item),
        )
        clone.clues_found = list(self.clues_found)
        clone.truth_found = self.truth_found
        clone.kindness_spent = self.kindness_spent
        clone.twist_revealed = self.twist_revealed
        clone.paragraphs = [[]]
        return clone


def _build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    detective = Character(
        id="detective",
        name=params.detective_name,
        role="detective",
        type="child",
        meters={"attention": 1.0},
        memes={"curiosity": 2.0, "kindness": 1.0},
    )
    helper = Character(
        id="helper",
        name=params.helper_name,
        role="helper",
        type="friend",
        meters={"attention": 1.0},
        memes={"kindness": 2.0},
    )
    item = ObjectItem(
        id="missing",
        name=MISSING_ITEMS[params.missing_item],
        owner=helper.id,
        hidden=True,
        clue="",
        twist=False,
        meters={"distance": 1.0 if place.far else 0.5},
        memes={"mystery": 2.0},
    )
    world = World(place=place, detective=detective, helper=helper, item=item)
    world.entities = {
        detective.id: detective,
        helper.id: helper,
        item.id: item,
    }
    return world


def _investigate(world: World) -> None:
    d = world.detective
    p = world.place
    d.memes["curiosity"] += 1.0
    world.say(
        f"{d.name} was a little detective who liked quiet questions and clean answers."
    )
    world.say(
        f"One dismal day, {d.name} and {world.helper.name} went to {p.name} to look for "
        f"the missing {world.item.name}."
    )
    world.say(
        f"The place felt far away, and the gray air made every step sound small."
    )
    world.para()


def _find_clues(world: World) -> None:
    d = world.detective
    h = world.helper
    for clue in world.place.clues[:2]:
        world.clues_found.append(clue)
        d.meters["attention"] += 1.0
        world.say(
            f"{d.name} spotted {clue} and wrote it down. "
            f"{h.name} looked too, because two careful eyes were better than one."
        )
    world.say(
        f"{d.name} felt the case pulling forward, but something still did not fit."
    )
    world.para()


def _twist(world: World) -> None:
    d = world.detective
    h = world.helper
    world.twist_revealed = True
    world.item.twist = True
    world.say(
        f"Then came a twist: the missing {world.item.name} was not stolen at all."
    )
    world.say(
        f"It had been left as a surprise for {h.name}, who had helped a tired neighbor "
        f"carry boxes in the rain."
    )
    world.kindness_spent = True
    h.memes["kindness"] += 1.0
    d.memes["kindness"] += 1.0
    world.say(
        f"The clue trail pointed to kindness, not trouble."
    )
    world.para()


def _resolve(world: World) -> None:
    d = world.detective
    h = world.helper
    world.truth_found = True
    world.item.hidden = False
    world.say(
        f"{d.name} smiled, because the answer was simple at last."
    )
    world.say(
        f"{h.name} got the {world.item.name} back, and the little detectives "
        f"walked home through the dismal streets with warm hearts and tidy notes."
    )
    world.say(
        f"By the end, the far place felt less lonely, because kindness had solved the mystery."
    )


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    _investigate(world)
    _find_clues(world)
    _twist(world)
    _resolve(world)
    world.facts.update(
        place=world.place,
        detective=world.detective,
        helper=world.helper,
        item=world.item,
        clues=list(world.clues_found),
        truth=world.truth_found,
        twist=world.twist_revealed,
    )
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.far:
            lines.append(asp.fact("far", pid))
        if p.dismal:
            lines.append(asp.fact("dismal", pid))
        for c in p.clues:
            lines.append(asp.fact("clue", pid, c))
    for mid, name in MISSING_ITEMS.items():
        lines.append(asp.fact("missing_item", mid))
        lines.append(asp.fact("item_name", mid, name))
    return "\n".join(lines)


ASP_RULES = r"""
mystery(Place, Item) :- far(Place), dismal(Place), missing_item(Item).
twist(Item) :- missing_item(Item).
kindness_solves(Place, Item) :- mystery(Place, Item), clue(Place, _), twist(Item).
#show mystery/2.
#show kindness_solves/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/2.\n#show kindness_solves/2."))
    asp_mystery = set(asp.atoms(model, "mystery"))
    asp_kindness = set(asp.atoms(model, "kindness_solves"))
    py_mystery = {(pid, mid) for pid, p in PLACES.items() for mid in MISSING_ITEMS if p.far and p.dismal}
    py_kindness = {(pid, mid) for pid, p in PLACES.items() for mid in MISSING_ITEMS if p.far and p.dismal and p.clues}
    if asp_mystery == py_mystery and asp_kindness == py_kindness:
        print(f"OK: ASP matches Python on {len(py_mystery)} mysteries.")
        return 0
    print("MISMATCH between ASP and Python")
    print("only ASP mystery:", sorted(asp_mystery - py_mystery))
    print("only PY mystery:", sorted(py_mystery - asp_mystery))
    print("only ASP kindness:", sorted(asp_kindness - py_kindness))
    print("only PY kindness:", sorted(py_kindness - asp_kindness))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--missing-item", choices=MISSING_ITEMS)
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
    place = args.place or rng.choice(list(PLACES))
    missing_item = args.missing_item or rng.choice(list(MISSING_ITEMS))
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if detective_name == helper_name:
        raise StoryError("detective and helper must be different names")
    return StoryParams(
        place=place,
        detective_name=detective_name,
        helper_name=helper_name,
        missing_item=missing_item,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short detective story for children about a far, dismal place and a missing {world.item.name}.",
        f"Tell a gentle mystery where {world.detective.name} follows clues, notices kindness, and finds the truth.",
        f"Write a child-friendly detective tale with a twist of curiosity and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.detective
    h = world.helper
    item = world.item
    place = world.place
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {d.name}, a curious child who liked to solve puzzles.",
        ),
        QAItem(
            question=f"What was missing at {place.name}?",
            answer=f"The missing thing was the {item.name}.",
        ),
        QAItem(
            question=f"What twist changed the mystery?",
            answer=f"The twist was that the {item.name} was not stolen. It had been left as a surprise after a kind act.",
        ),
        QAItem(
            question=f"How did kindness help solve the case?",
            answer=f"Kindness mattered because the clues led to a helpful surprise, not a crime, and that made the mystery clear.",
        ),
        QAItem(
            question=f"Who helped {d.name} investigate?",
            answer=f"{h.name} helped {d.name} look for clues and understand what really happened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to find the truth.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more and find out why something happened.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world trace ---",
            f"place={world.place}",
            f"detective={world.detective}",
            f"helper={world.helper}",
            f"item={world.item}",
            f"clues_found={world.clues_found}",
            f"truth_found={world.truth_found}",
            f"twist_revealed={world.twist_revealed}",
        ]
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/2.\n#show kindness_solves/2."))
        print("mysteries:", sorted(set(asp.atoms(model, "mystery"))))
        print("kindness_solutions:", sorted(set(asp.atoms(model, "kindness_solves"))))
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="lane", detective_name="Mina", helper_name="Pip", missing_item="kite"),
            StoryParams(place="dock", detective_name="Toby", helper_name="June", missing_item="book"),
            StoryParams(place="alley", detective_name="Lena", helper_name="Rae", missing_item="bell"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
