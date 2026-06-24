#!/usr/bin/env python3
"""
A small storyworld about an animal in a church who grows less cowardly and
takes initiative, with sound effects and gentle humor.

Initial seed tale:
---
A tiny mouse named Milo was a coward. On Sunday, the church bell rang loud
and long, and all the animals walked inside the little church. Milo hid
behind a pew because every creak and cough made him jump.

Then the choir's drum rolled, "BOOM-boom!" A sparrow chirped, "Tweet!" and
the candles flickered. When the offering basket tipped, it went "clink!"
Milo wanted to run away, but he saw a kitten trying to ring the tiny bell
all by herself. The kitten slipped, the bell rang "DING!" and everyone
laughed kindly.

Milo took a breath, stepped out, and said he could help. He held the bell
steady while the kitten rang it again, and together they made a bright,
happy sound that filled the church.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "cat", "kitten", "dog", "bird", "sparrow"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str = "the church"
    bells: bool = True
    pews: bool = True
    choir: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    sound: str
    effect: str
    humor: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
    protects_against: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    name: str
    animal: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


PLACES = {
    "church": Place(name="the church", affords={"bell", "song", "drum"}),
}

ACTIONS = {
    "bell": Action(
        id="bell",
        verb="ring the bell",
        sound="DING!",
        effect="a bright bell sound",
        humor="the bell went off so loudly that even the hymnbook looked surprised",
        keyword="bell",
        tags={"sound", "church", "humor"},
    ),
    "song": Action(
        id="song",
        verb="start the song",
        sound="LA-la-la!",
        effect="a happy chorus",
        humor="the sparrows sang so high they almost tickled the ceiling",
        keyword="song",
        tags={"sound", "church", "humor"},
    ),
    "drum": Action(
        id="drum",
        verb="beat the drum",
        sound="BOOM-boom!",
        effect="a bouncy rhythm",
        humor="the drum puffed out such a brave boom that the mice blinked twice",
        keyword="drum",
        tags={"sound", "church", "humor"},
    ),
}

ITEMS = {
    "bell": Item(
        id="bell",
        label="tiny bell",
        phrase="a tiny silver bell",
        region="paw",
        fragile=True,
        protects_against={"drop"},
    ),
    "basket": Item(
        id="basket",
        label="offering basket",
        phrase="a woven offering basket",
        region="paw",
        fragile=True,
        protects_against={"drop"},
    ),
}

ANIMAL_NAMES = ["Milo", "Pip", "Luna", "Nell", "Otis", "Toby", "Clover", "Mabel"]
ANIMALS = ["mouse", "rabbit", "cat", "kitten", "bird", "sparrow", "dog"]
TRAITS = ["tiny", "shy", "curious", "gentle", "nervous", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_name, place in PLACES.items():
        for action_id in place.affords:
            for item_id in ITEMS:
                combos.append((place_name, action_id, item_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal church storyworld with sound effects and humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMALS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, item = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(ANIMALS)
    name = args.name or rng.choice(ANIMAL_NAMES)
    return StoryParams(place=place, action=action, item=item, name=name, animal=animal)


def _intro(world: World, hero: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who lived near {world.place.name}."
    )
    world.say(
        f"{hero.id} liked to peek at {item.phrase}, but {hero.pronoun('possessive')} knees shook whenever the big bell rang."
    )


def _setup_church(world: World) -> None:
    world.say(
        f"On Sunday morning, the animals tiptoed into {world.place.name} and sat on the pews."
    )
    world.say(
        f"The candles glowed, the hymnbook pages rustled, and the room felt quiet enough to hear a whisker twitch."
    )


def _fear(world: World, hero: Entity, action: Action) -> None:
    hero.memes["cowardice"] = hero.memes.get("cowardice", 0) + 1
    world.say(
        f"Then something made a sound: {action.sound} The little {hero.type} gulped and nearly hid under a pew."
    )
    world.say(
        f"{hero.id} was a coward about the noise, even though everyone else only blinked and smiled."
    )


def _turn(world: World, hero: Entity, item: Entity, action: Action) -> None:
    hero.memes["initiative"] = hero.memes.get("initiative", 0) + 1
    hero.memes["cowardice"] = max(0.0, hero.memes.get("cowardice", 0) - 1)
    item.touched = True
    world.say(
        f"Then a kitten tried to {action.verb} and slipped a little."
    )
    world.say(
        f"{action.sound} went the bell, and {action.humor}."
    )
    world.say(
        f"{hero.id} took a deep breath and decided to help instead of hiding."
    )


def _resolve(world: World, hero: Entity, item: Entity, action: Action) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"{hero.id} held {item.phrase} steady with careful paws while the kitten tried again."
    )
    world.say(
        f"This time the bell made {action.sound} and the whole church filled with {action.effect}."
    )
    world.say(
        f"Even the serious old crow at the back gave a tiny caw of approval, as if to say that was a very good job."
    )
    world.say(
        f"By the end, {hero.id} was no longer hiding. {hero.id} stood straight, helpful and proud, right beside the bright bell."
    )


def tell(place: Place, action: Action, item_cfg: Item, name: str, animal: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=animal,
        traits=["shy", "tiny"],
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type="thing",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
    ))
    _intro(world, hero, item)
    world.para()
    _setup_church(world)
    _fear(world, hero, action)
    world.para()
    _turn(world, hero, item, action)
    _resolve(world, hero, item, action)
    world.facts.update(hero=hero, item=item, action=action, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    return [
        f'Write a short Animal Story about a {hero.traits[0]} {hero.type} who shows initiative in the church.',
        f"Tell a gentle story where {hero.id} is a coward at first but then helps with {action.keyword} sounds.",
        f'Write a simple church story with the sound "{action.sound}" and a funny but kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.traits[0]} little {hero.type} who learned to be helpful at church.",
        ),
        QAItem(
            question=f"Why was {hero.id} scared at first?",
            answer=f"{hero.id} was scared because {action.sound} was loud, and {hero.id} acted like a coward before deciding to help.",
        ),
        QAItem(
            question=f"What did {hero.id} do with {item.label} at the end?",
            answer=f"{hero.id} held {item.phrase} steady so the kitten could ring it safely.",
        ),
        QAItem(
            question=f"What changed about {hero.id} by the end of the story?",
            answer=f"{hero.id} showed initiative, stopped hiding, and became brave enough to help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a church?",
            answer="A church is a place where people and sometimes animals gather quietly to sing, listen, and share a peaceful time together.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word that helps the reader hear a noise, like DING, BOOM, or clink.",
        ),
        QAItem(
            question="What does initiative mean?",
            answer="Initiative means doing something helpful without waiting for someone else to tell you first.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.touched:
            bits.append("touched=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(church).
affords(church,bell).
affords(church,song).
affords(church,drum).

action(bell). action(song). action(drum).
item(bell). item(basket).

valid(Place,Action,Item) :- affords(Place,Action), item(Item).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pname, place in PLACES.items():
        lines.append(asp.fact("place", pname))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pname, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "(No story: this church story needs a valid place, action, and item.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.action], ITEMS[params.item], params.name, params.animal)
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
    StoryParams(place="church", action="bell", item="bell", name="Milo", animal="mouse"),
    StoryParams(place="church", action="song", item="basket", name="Pip", animal="rabbit"),
    StoryParams(place="church", action="drum", item="bell", name="Luna", animal="kitten"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_asp()
        print(f"{len(combos)} compatible (place, action, item) combos:\n")
        for c in combos:
            print(f"  {c[0]:8} {c[1]:8} {c[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                combos = [c for c in valid_combos()
                          if (args.place is None or c[0] == args.place)
                          and (args.action is None or c[1] == args.action)
                          and (args.item is None or c[2] == args.item)]
                if not combos:
                    raise StoryError(explain_rejection())
                place, action, item = rng.choice(sorted(combos))
                animal = args.animal or rng.choice(ANIMALS)
                name = args.name or rng.choice(ANIMAL_NAMES)
                params = StoryParams(place=place, action=action, item=item, name=name, animal=animal, seed=seed)
            except StoryError as err:
                print(err)
                return
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
