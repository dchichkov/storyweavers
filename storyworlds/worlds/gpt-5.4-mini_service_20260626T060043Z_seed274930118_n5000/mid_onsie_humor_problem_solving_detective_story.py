#!/usr/bin/env python3
"""
A small detective-story world with a humorous, problem-solving toddler mystery.

Seed notion:
- "mid" and "onsie" suggest a mid-day mishap involving a baby's onesie.
- The story stays child-facing and classical: a clue trail, a mistaken suspect,
  a careful deduction, and a tidy ending image.

The world models:
- a detective child with curiosity and a sense of humor
- a tiny setting with a misplaced onesie
- clues that can be found in places
- a simple resolution that proves what changed
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Place:
    key: str
    label: str
    detail: str


@dataclass(frozen=True)
class ObjectItem:
    key: str
    label: str
    phrase: str
    owner: str
    found_in: str
    clue: str


@dataclass(frozen=True)
class Suspect:
    key: str
    label: str
    quirk: str
    innocence_hint: str


PLACES = {
    "nursery": Place("nursery", "the nursery", "a bright room with blocks, books, and a tiny chair"),
    "laundry": Place("laundry", "the laundry room", "a warm room that hummed with the washer"),
    "hall": Place("hall", "the hallway", "a long stretch of floor with little shoe prints"),
    "sofa": Place("sofa", "the sofa corner", "a soft corner with blankets and a sleepy lamp"),
    "mudroom": Place("mudroom", "the mudroom", "a room of boots, baskets, and hanging coats"),
}

OBJECTS = {
    "onsie": ObjectItem(
        key="onsie",
        label="onsie",
        phrase="the blue onsie",
        owner="baby",
        found_in="laundry",
        clue="a tiny button was stuck in the basket",
    ),
    "pacifier": ObjectItem(
        key="pacifier",
        label="pacifier",
        phrase="the red pacifier",
        owner="baby",
        found_in="sofa",
        clue="it was wedged between two cushions",
    ),
    "bear": ObjectItem(
        key="bear",
        label="bear",
        phrase="the plush bear",
        owner="child",
        found_in="nursery",
        clue="one ear had a bit of ribbon caught on it",
    ),
}

SUSPECTS = {
    "dog": Suspect(
        key="dog",
        label="the dog",
        quirk="loved sniffing every basket and blanket",
        innocence_hint="its paws were clean and it was asleep by the door",
    ),
    "cat": Suspect(
        key="cat",
        label="the cat",
        quirk="liked sleeping on warm folded clothes",
        innocence_hint="it was curled in a sunny spot and never left it",
    ),
    "sibling": Suspect(
        key="sibling",
        label="the big sibling",
        quirk="was famous for trying to help before thinking",
        innocence_hint="they had only carried snacks, not laundry",
    ),
}

DETECTIVE_NAMES = ["Mina", "Leo", "Nora", "Ivy", "Theo", "June", "Milo", "Ada"]
HELPER_NAMES = ["Mama", "Papa", "Auntie", "Uncle", "Grandma", "Grandpa"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    detective_name: str
    helper_name: str
    place: str
    missing_item: str
    suspect: str
    seed: Optional[int] = None


@dataclass
class Entity:
    key: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def bump_meter(self, name: str, amount: float = 1.0) -> None:
        self.meters[name] = self.meters.get(name, 0.0) + amount

    def bump_meme(self, name: str, amount: float = 1.0) -> None:
        self.memes[name] = self.memes.get(name, 0.0) + amount


@dataclass
class World:
    detective: Entity
    helper: Entity
    missing_item: ObjectItem
    suspect: Suspect
    place: Place
    suspects_seen: list[str] = field(default_factory=list)
    clues_found: list[str] = field(default_factory=list)
    solved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
missing_item(onsie).
place(nursery;laundry;hall;sofa;mudroom).
suspect(dog;cat;sibling).

good_solve(Place,Item,Suspect) :- missing_item(Item), place(Place), suspect(Suspect).
#show good_solve/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
    for o in OBJECTS.values():
        lines.append(asp.fact("missing_item", o.key))
    for s in SUSPECTS.values():
        lines.append(asp.fact("suspect", s.key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_solve/3."))
    return sorted(set(asp.atoms(model, "good_solve")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.missing_item not in OBJECTS:
        raise StoryError("Unknown missing item.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if params.place == "mudroom" and params.missing_item == "onsie":
        return
    if params.place == "laundry" and params.missing_item == "onsie":
        return
    if params.place == "nursery" and params.missing_item == "onsie":
        return
    if params.place == "sofa" and params.missing_item == "pacifier":
        return
    raise StoryError("This clue trail would be too weak to support a clean detective story.")


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = {(p.key, o.key, s.key) for p in PLACES.values() for o in OBJECTS.values() for s in SUSPECTS.values()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python registry.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    detective = Entity(
        key=params.detective_name,
        label=params.detective_name,
        kind="character",
        meters={"curiosity": 0.0, "confidence": 0.0},
        memes={"humor": 0.0, "problem_solving": 0.0},
        location=params.place,
    )
    helper = Entity(
        key=params.helper_name,
        label=params.helper_name,
        kind="character",
        meters={"patience": 1.0},
        memes={"warmth": 1.0},
        location=params.place,
    )
    return World(
        detective=detective,
        helper=helper,
        missing_item=OBJECTS[params.missing_item],
        suspect=SUSPECTS[params.suspect],
        place=PLACES[params.place],
        entities={detective.key: detective, helper.key: helper},
    )


def intro(world: World) -> None:
    d = world.detective
    world.say(
        f"{d.label} was a little detective who noticed everything in {world.place.label}."
    )
    world.say(
        f"{d.label} liked jokes, sticky notes, and solving puzzles with a grin."
    )
    d.bump_meter("curiosity", 1)
    d.bump_meme("humor", 1)


def incident(world: World) -> None:
    item = world.missing_item
    d = world.detective
    world.para()
    world.say(
        f"One mid-morning, {item.phrase} was gone."
    )
    world.say(
        f"{d.label} found only one clue at first: {item.clue}."
    )
    d.bump_meter("curiosity", 1)
    d.bump_meme("problem_solving", 1)


def investigate(world: World) -> None:
    d = world.detective
    item = world.missing_item
    suspect = world.suspect

    world.para()
    world.say(
        f"{d.label} checked {world.place.detail} and asked, 'Who would hide an {item.label}?'"
    )
    world.say(
        f"Then {d.label} looked at {suspect.label}, who {suspect.quirk}."
    )
    world.say(
        f"But that was funny, not guilty: {suspect.innocence_hint}."
    )
    d.bump_meter("curiosity", 1)
    d.bump_meme("humor", 1)
    d.bump_meme("problem_solving", 1)
    world.suspects_seen.append(suspect.key)


def solve(world: World) -> None:
    d = world.detective
    item = world.missing_item
    world.para()
    if item.found_in == "laundry":
        world.say(
            f"{d.label} followed the button clue to the laundry room."
        )
        world.say(
            f"The {item.label} had slipped into the warm basket while someone folded tiny clothes."
        )
    elif item.found_in == "sofa":
        world.say(
            f"{d.label} spotted a little bump in the sofa corner."
        )
        world.say(
            f"The {item.label} was wedged between the cushions, as quiet as a secret."
        )
    elif item.found_in == "nursery":
        world.say(
            f"{d.label} returned to the nursery and checked the toy pile again."
        )
        world.say(
            f"There was the {item.label}, tucked under a blanket like it was hiding from bedtime."
        )
    elif item.found_in == "mudroom":
        world.say(
            f"{d.label} marched to the mudroom and peeked in the basket by the boots."
        )
        world.say(
            f"There was the {item.label}, folded under a coat where nobody had looked twice."
        )
    else:
        world.say(f"{d.label} solved the puzzle with careful thinking.")
        world.say(f"The {item.label} turned up right where the clues pointed.")

    d.bump_meter("confidence", 1)
    d.bump_meme("problem_solving", 2)
    world.clues_found.append(item.clue)
    world.solved = True


def ending(world: World) -> None:
    d = world.detective
    h = world.helper
    item = world.missing_item
    world.para()
    world.say(
        f"{h.label} laughed and said, 'Well, detective, you cracked the case.'"
    )
    world.say(
        f"{d.label} gave a proud smile and held up the {item.label} like a tiny trophy."
    )
    world.say(
        f"Before long, the {item.label} was back where it belonged, and the room felt neat again."
    )
    world.say(
        f"{d.label} even told a joke about a dramatic sock to make {h.label} laugh one more time."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    incident(world)
    investigate(world)
    solve(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a humorous detective story for children about {world.detective.label} finding a missing {world.missing_item.label}.",
        f"Tell a problem-solving mystery set in {world.place.label} where a child detective follows a clue and discovers where the {world.missing_item.label} went.",
        f"Write a short story with a playful detective tone, a silly suspect, and a tidy ending that includes the word 'mid' or 'onsie'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.detective
    h = world.helper
    item = world.missing_item
    suspect = world.suspect
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing item was {item.phrase}.",
        ),
        QAItem(
            question=f"Who was solving the mystery?",
            answer=f"{d.label} was solving the mystery with a detective's curiosity and a funny smile.",
        ),
        QAItem(
            question=f"Why did {d.label} think {suspect.label} was not guilty?",
            answer=f"{suspect.label} seemed suspicious at first, but {suspect.innocence_hint}. That made the clue trail point somewhere else.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{d.label} followed the clue and found {item.phrase} in {world.place.detail.split(' with ')[0] if world.place.key != 'sofa' else 'the sofa cushions'}. Then {h.label} praised the careful detective work.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks smart questions, and uses careful thinking to solve a mystery.",
        ),
        QAItem(
            question="Why can a onesie get misplaced in a busy home?",
            answer="A onesie can get misplaced when someone carries laundry, folds clothes, or puts tiny things down in the wrong spot.",
        ),
        QAItem(
            question="Why is humor useful in a mystery story?",
            answer="Humor helps the story feel friendly and lively, and it can make problem-solving feel less scary and more fun.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.kind}:{e.label} meters={e.meters} memes={e.memes} location={e.location}")
    lines.append(f"solved={world.solved}")
    lines.append(f"clues_found={world.clues_found}")
    lines.append(f"suspects_seen={world.suspects_seen}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous child detective story world about a missing onsie.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--missing-item", dest="missing_item", choices=sorted(OBJECTS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--detective-name", dest="detective_name")
    ap.add_argument("--helper-name", dest="helper_name")
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
    missing_item = args.missing_item or "onsie"
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)

    params = StoryParams(
        detective_name=detective_name,
        helper_name=helper_name,
        place=place,
        missing_item=missing_item,
        suspect=suspect,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_solve/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_solve/3."))
        atoms = sorted(set(asp.atoms(model, "good_solve")))
        print(f"{len(atoms)} compatible combos:")
        for a in atoms:
            print(a)
        return

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("Mina", "Mama", "laundry", "onsie", "sibling"),
            StoryParams("Leo", "Papa", "mudroom", "onsie", "dog"),
            StoryParams("Nora", "Grandma", "nursery", "onsie", "cat"),
            StoryParams("Ivy", "Auntie", "sofa", "pacifier", "dog"),
        ]
        for p in curated:
            reasonableness_gate(p)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.missing_item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
