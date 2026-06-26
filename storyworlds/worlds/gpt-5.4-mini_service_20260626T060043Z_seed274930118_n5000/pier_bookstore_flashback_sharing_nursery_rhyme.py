#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pier_bookstore_flashback_sharing_nursery_rhyme.py
===============================================================================================================================

A tiny story world in a bookstore, styled like a nursery rhyme, with a pier memory,
a flashback turn, and a sharing resolution.

Premise imagined from the seed:
---
A child visits a bookstore with a small keepsake from the pier. The child wants a
book, but a remembered scene from the pier makes the child cling to the keepsake.
A gentle sharing moment helps the child and a helper choose a book together.

World model:
---
- Typed entities have physical meters and emotional memes.
- A memory of the pier can raise longing and worry.
- Sharing a book or a keepsake can lower worry and raise joy.
- The story must include a flashback beat and a sharing beat.
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

BOOK_TYPES = {
    "picture": ("picture book", "a bright picture book", "pages"),
    "poem": ("nursery rhyme book", "a small nursery rhyme book", "pages"),
    "story": ("storybook", "a cozy storybook", "pages"),
    "song": ("songbook", "a cheerful songbook", "pages"),
}

NAMES = ["Mina", "Lulu", "Ned", "Poppy", "Toby", "June", "Iris", "Finn"]
HELPERS = ["librarian", "mother", "father", "grandma", "grandpa"]
TRAITS = ["small", "bright-eyed", "gentle", "curious", "cheery", "soft-spoken"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bookstore"
    affordance: str = "sharing"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    shelf: str = "children's shelf"


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def child_name(gender: str = "girl", rng: Optional[random.Random] = None) -> str:
    rng = rng or random
    return rng.choice(NAMES)


PRIZES = {
    "picture": Prize(*BOOK_TYPES["picture"], type="book"),
    "poem": Prize(*BOOK_TYPES["poem"], type="book"),
    "story": Prize(*BOOK_TYPES["story"], type="book"),
    "song": Prize(*BOOK_TYPES["song"], type="book"),
}


def flashback_text(hero: Entity) -> str:
    return (
        f"Then memory came, like gulls in a row: at the pier, {hero.id} had held "
        f"a tiny shell and listened to the sea go \"shoo, shoo, shoo.\""
    )


def setup_story(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["yearning"] += 1
    world.say(
        f"{hero.id} was a {next((t for t in [hero.type] if t), 'child')} with "
        f"a {world.facts['trait']} smile who came to {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the shelves and the hush, and "
        f"{hero.pronoun()} wanted {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"{helper.label.capitalize()} stood by the desk with a warm look, "
        f"holding a stack of books."
    )


def trigger_flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] += 1
    hero.memes["worry"] += 1
    world.say(flashback_text(hero))


def sharing_turn(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
    hero.memes["sharing"] += 1
    helper.memes["sharing"] = helper.memes.get("sharing", 0.0) + 1
    world.say(
        f"{helper.label.capitalize()} said, \"We can share the book and your memory too.\""
    )
    world.say(
        f"So {hero.id} and {helper.label} chose {prize.phrase} together, page by page, "
        f"nice and slow."
    )


def ending_image(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f"In the end, {hero.id} sat by the window, {prize.phrase} open wide, "
        f"and the old pier felt close as a song."
    )
    world.say(
        f"{helper.label.capitalize()} smiled, and the two of them shared the book "
        f"as the little bell on the door went ting-a-ling."
    )


def tell(place: str, prize_key: str, hero_name: str, helper_kind: str, trait: str) -> World:
    world = World(Setting(place=place))
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id=helper_kind, kind="character", type=helper_kind, label=helper_kind))
    prize = world.add(Entity(id="book", kind="thing", type="book", label=PRIZES[prize_key].label,
                             phrase=PRIZES[prize_key].phrase, caretaker=helper.id))
    world.facts.update(hero=hero, helper=helper, prize=prize, trait=trait, place=place, prize_key=prize_key)

    setup_story(world, hero, helper, prize)
    world.para()
    trigger_flashback(world, hero)
    world.say(
        f"At once, the child grew quiet, for the pier memory made the little heart hold tight."
    )
    world.para()
    sharing_turn(world, hero, helper, prize)
    ending_image(world, hero, helper, prize)
    hero.meters["book"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["sharing"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a nursery-rhyme-style story set in a bookstore, with a soft flashback to a pier and a sharing ending.',
        f"Tell a gentle story about {f['hero'].id} in {f['place']} who remembers the pier and learns to share {f['prize'].phrase}.",
        f"Write a short rhyming story where a {f['trait']} child and a {f['helper'].label} share a book after a memory from the pier.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    return [
        QAItem(
            question=f"Where does {hero.id} go in the story?",
            answer=f"{hero.id} goes to {f['place']}, which is the bookstore in the story.",
        ),
        QAItem(
            question=f"What did {hero.id} remember that came from the pier?",
            answer="The child remembered sitting by the pier and listening to the sea.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} solve the problem?",
            answer=f"They shared {prize.phrase} together, page by page, and that made the child calm again.",
        ),
        QAItem(
            question=f"What was the ending image?",
            answer=f"In the end, {hero.id} was sitting with {prize.phrase} open wide, and the bookstore felt warm and peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bookstore?",
            answer="A bookstore is a place where people can look at books and choose one to read or buy.",
        ),
        QAItem(
            question="What is a pier?",
            answer="A pier is a long wooden walkway that sticks out over water, like the sea or a lake.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, hold, or enjoy something together with you.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly goes back to something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bookstore nursery-rhyme world with pier flashback and sharing.")
    ap.add_argument("--place", default="bookstore", choices=["bookstore"])
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    prize = args.prize or rng.choice(list(PRIZES.keys()))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="bookstore", prize=prize, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.prize, params.name, params.helper, params.trait)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
% The tiny declarative twin:
% a child can be helped when sharing is possible in the bookstore.
place(bookstore).
feature(flashback).
feature(sharing).

compatible_story(P) :- place(P), feature(flashback), feature(sharing).
#show compatible_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "bookstore"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "sharing"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/1."))
    ok = any(atom.name == "compatible_story" for atom in model)
    if ok:
        print("OK: ASP gate recognizes the bookstore flashback-sharing world.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="bookstore", prize="picture", name="Mina", helper="librarian", trait="curious"),
        StoryParams(place="bookstore", prize="poem", name="Lulu", helper="mother", trait="cheery"),
        StoryParams(place="bookstore", prize="story", name="Toby", helper="grandma", trait="gentle"),
        StoryParams(place="bookstore", prize="song", name="June", helper="father", trait="bright-eyed"),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/1."))
        print("compatible stories:")
        for atom in model:
            if atom.name == "compatible_story":
                print(f"  {atom.arguments[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
