#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/return_problem_solving_misunderstanding_mystery_to_solve.py
==============================================================================================================

A small standalone story world about a returned item, a misunderstanding, and
a mystery that gets solved through careful looking and kind asking.

The style is rhyming-story inspired: short, child-facing prose with a lilting
sound and a clear problem/solution shape.
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
    found_by: Optional[str] = None
    returned_to: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    clue: str
    kind: str = "outdoor"


@dataclass
class Mystery:
    id: str
    item_label: str
    owner_label: str
    clue_type: str
    rhyming_hint: str
    answer: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_notice_tag(world: World) -> list[str]:
    out = []
    child = world.get("hero")
    item = world.get("mystery_item")
    if child.memes.get("curious", 0) >= THRESHOLD and item.hidden_in:
        sig = ("notice", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["puzzle"] = child.memes.get("puzzle", 0) + 1
            out.append("The child leaned in and noticed a small tag tucked in the seam.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    child = world.get("hero")
    item = world.get("mystery_item")
    if item.found_by == child.id and not item.returned_to and child.memes.get("assume", 0) >= THRESHOLD:
        sig = ("misunderstand", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = child.memes.get("worry", 0) + 1
            out.append("The child thought the lost thing might be theirs for the taking.")
    return out


def _r_return(world: World) -> list[str]:
    out = []
    child = world.get("hero")
    item = world.get("mystery_item")
    owner = world.get("owner")
    if item.found_by == child.id and item.returned_to == owner.id:
        sig = ("return", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["joy"] = child.memes.get("joy", 0) + 1
            owner.memes["relief"] = owner.memes.get("relief", 0) + 1
            out.append("The mystery was solved, and the item was safely returned.")
    return out


RULES = [_r_notice_tag, _r_misunderstanding, _r_return]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s != "The mystery was solved, and the item was safely returned.":
                world.say(s)
    return produced


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label="the helper"))
    owner = world.add(Entity(id="owner", kind="character", type="neighbor", label="the neighbor"))
    item = world.add(Entity(
        id="mystery_item",
        kind="thing",
        type="thing",
        label=mystery.item_label,
        phrase=mystery.item_label,
        owner=owner.id,
        hidden_in=place.id,
    ))

    hero.memes["curious"] = 1
    hero.memes["assume"] = 1
    helper.memes["kind"] = 1
    return world


def tell_story(world: World) -> World:
    hero = world.get("hero")
    helper = world.get("helper")
    owner = world.get("owner")
    item = world.get("mystery_item")
    mystery = next(m for m in MYSTERIES.values() if m.item_label == item.label)

    world.say(
        f"At {world.place.label}, {hero.label} found a {item.label} one bright, breezy day. "
        f"It shimmered and swayed in a puzzly way."
    )
    world.say(
        f"{hero.label} said, “Is it mine? It fits my hand so fine!” "
        f"But a little tag peeked out, so the question started to shine."
    )

    world.para()
    hero.memes["assume"] += 1
    item.found_by = hero.id
    propagate(world, narrate=True)

    world.say(
        f"{helper.label} came near and said, “Let’s not guess too fast or near. "
        f"Let’s look for clues and ask with care, and the truth will soon appear.”"
    )
    world.say(
        f"They checked the tag, then followed the path, in a soft and thoughtful trance. "
        f"The tag named {owner.label}, so the mystery gave a clue-filled dance."
    )

    world.para()
    item.returned_to = owner.id
    owner.memes["relief"] = 1
    propagate(world, narrate=True)

    world.say(
        f"{hero.label} took the {item.label} back where it belonged, with a grin so wide and bright. "
        f"{owner.label} smiled, “That was mine indeed—thank you for your kind, careful light.”"
    )
    world.say(
        f"So the lost thing went home, and the day felt warm and tame. "
        f"With a solved little mystery, everyone cheered the same."
    )

    world.facts.update(hero=hero, helper=helper, owner=owner, item=item, mystery=mystery)
    return world


PLACES = {
    "park": Place(id="park", label="the park", clue="a bench near the swing set"),
    "library": Place(id="library", label="the library steps", clue="a quiet shelf by the door"),
    "garden": Place(id="garden", label="the garden gate", clue="a flower pot beside the path"),
}

MYSTERIES = {
    "scarf": Mystery(
        id="scarf",
        item_label="striped scarf",
        owner_label="neighbor",
        clue_type="tag",
        rhyming_hint="soft and warm",
        answer="It belongs to the neighbor.",
    ),
    "glove": Mystery(
        id="glove",
        item_label="blue glove",
        owner_label="neighbor",
        clue_type="tag",
        rhyming_hint="small and snug",
        answer="It belongs to the neighbor.",
    ),
    "book": Mystery(
        id="book",
        item_label="library book",
        owner_label="neighbor",
        clue_type="tag",
        rhyming_hint="quiet and neat",
        answer="It belongs to the neighbor.",
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Eli", "Finn", "Toby", "Milo", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in PLACES for m in MYSTERIES]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming story world about a mystery to solve and a return.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "friend"])
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
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "friend"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(place=place, mystery=mystery, hero_name=hero_name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    return [
        f'Write a short rhyming story about a child finding a {mystery.item_label} and solving a little mystery.',
        f"Tell a gentle story where {f['hero'].label} does not rush, but checks clues and returns the lost thing.",
        f"Write a child-friendly rhyme about misunderstanding, problem solving, and a happy return at {world.place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    owner = f["owner"]
    item = f["item"]
    place = world.place.label
    return [
        QAItem(
            question=f"What did {hero.label} find at {place}?",
            answer=f"{hero.label} found a {item.label} at {place}. It turned the walk into a little mystery to solve.",
        ),
        QAItem(
            question=f"Why was the lost {item.label} confusing at first?",
            answer=f"It was confusing because {hero.label} thought it might be theirs at first, but then the tag showed it belonged to {owner.label}.",
        ),
        QAItem(
            question=f"What happened after the clue was found?",
            answer=f"{hero.label} returned the {item.label} to {owner.label}, and the mystery ended with smiles and relief.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What should you do if you find something that looks lost?",
            answer="You should look for a name, ask a grown-up, and try to give it back to the person it belongs to.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a little bit of information that helps you figure out an answer to a mystery.",
        ),
        QAItem(
            question="Why is returning lost things kind?",
            answer="Returning lost things is kind because it helps the owner get back something they were missing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        if e.returned_to:
            bits.append(f"returned_to={e.returned_to}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
found_mystery(P,M) :- place(P), mystery(M).
misunderstanding(M) :- found_mystery(_,M), tag_clue(M).
solved(M) :- misunderstanding(M), returned(M).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("tag_clue", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show place/1.\n#show mystery/1.\n"))
    if model is None:
        print("ASP verification failed: no model.")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show place/1.\n#show mystery/1.\n"))
    return [] if model is None else [(a[0], b[0]) for a in asp.atoms(model, "place") for b in asp.atoms(model, "mystery")]


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
    StoryParams(place="park", mystery="scarf", hero_name="Mia", hero_type="girl", helper_type="mother"),
    StoryParams(place="library", mystery="book", hero_name="Eli", hero_type="boy", helper_type="father"),
    StoryParams(place="garden", mystery="glove", hero_name="Nora", hero_type="girl", helper_type="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show place/1.\n#show mystery/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show place/1.\n#show mystery/1.\n"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
