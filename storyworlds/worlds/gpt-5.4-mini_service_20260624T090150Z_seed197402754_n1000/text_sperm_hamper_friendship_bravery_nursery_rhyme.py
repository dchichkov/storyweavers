#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a lost text card, a hamper, and a brave
friendship around a science word.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    friend: object | None = None
    hero: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = False
    note: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str = "nursery"
    note: str = "text"
    item: str = "hamper"
    topic: str = "sperm"
    hero: str = "Mina"
    friend: str = "Pip"
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "nursery": Place(name="the nursery room", mood="soft and bright", affords={"search", "share"}),
    "garden": Place(name="the garden", mood="green and breezy", affords={"search", "share"}),
    "playroom": Place(name="the playroom", mood="warm and cozy", affords={"search", "share"}),
}

ITEMS = {
    "hamper": Item(id="hamper", label="a wicker hamper", phrase="a wicker hamper with a round lid", location="corner", fragile=False),
    "box": Item(id="box", label="a small box", phrase="a small box with a ribbon", location="shelf", fragile=False),
}

NAMES = ["Mina", "Pip", "Toby", "Luna", "Nora", "Rae"]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[list[str]] = [[]]

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


ASP_RULES = r"""
place(X) :- setting(X).
item(X) :- basket(X).
topic(sperm) :- word(sperm).
topic(text) :- word(text).
topic(hamper) :- word(hamper).
safe_story(P, N, I, T) :- place(P), note(N), item(I), topic(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for iid in ITEMS:
        lines.append(asp.fact("basket", iid))
    for w in ("text", "sperm", "hamper"):
        lines.append(asp.fact("word", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about friendship and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--note", choices=["text"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--topic", choices=["sperm"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != name])
    return StoryParams(
        place=place,
        note=getattr(args, "note", None) or "text",
        item=item,
        topic=getattr(args, "topic", None) or "sperm",
        hero=name,
        friend=friend,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add_entity(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    friend = world.add_entity(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    hamper = world.add_item(_safe_lookup(ITEMS, params.item))
    note = world.add_item(Item(id="note", label="a text card", phrase="a little text card", location="hand", fragile=True))
    world.facts.update(hero=hero, friend=friend, hamper=hamper, note=note, topic=params.topic, place=world.place)

    world.say(
        f"In {world.place.name}, all soft and bright, {hero.id} found {note.phrase} tucked near {hamper.label}."
    )
    world.say(
        f'It spoke of "{params.topic}", a word from a science text, and {hero.id} gave a tiny nod.'
    )
    world.para()
    world.say(
        f"But the hamper lid shut with a bump, and the text card slipped inside like a mouse in the night."
    )
    world.say(
        f'{friend.id} said, "Be brave, dear friend, we can lift it well, and we can help the word take flight."'
    )
    world.para()
    world.say(
        f"So {hero.id} and {friend.id} worked as one, with friendship warm and true."
        if False else f"So {hero.id} and {friend.id} worked as one, with friendship warm and true."
    )
    world.say(
        f"They lifted the hamper lid, and there was the text card, smiling bright and neat."
    )
    world.say(
        f'And {hero.id} read the little science line about {params.topic}, with bravery in a gentle beat.'
    )
    world.say(
        f"Then both friends laughed and shared the card, and the nursery room grew merry."
    )

    prompts = [
        f"Write a short nursery-rhyme story about friendship and bravery in {world.place.name}.",
        f"Tell a gentle tale where a child finds a text card near {hamper.label} and reads the word '{params.topic}'.",
        "Make the ending show that friendship helped the children solve the problem.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {hero.id} find near the hamper?",
            answer=f"{hero.id} found a little text card near the hamper, and it held a science word.",
        ),
        QAItem(
            question=f"Who helped {hero.id} be brave when the text card slipped away?",
            answer=f"{friend.id} helped {hero.id}, and together they lifted the hamper lid.",
        ),
        QAItem(
            question=f"What word did the story mention from the science text?",
            answer=f"The story mentioned the word '{params.topic}'.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a text card?",
            answer="A text card is a small card with words on it.",
        ),
        QAItem(
            question="What is a hamper?",
            answer="A hamper is a basket or container that can hold things.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when your heart feels wobbly.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        print(f"place={sample.world.place.name}")
        print(f"hero={sample.params.hero}")
        print(f"friend={sample.params.friend}")
        print(f"topic={sample.params.topic}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    import asp
    program = asp_program("#show safe_story/4.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "safe_story"))
    python = {(p, "text", i, "sperm") for p in PLACES for i in ITEMS}
    if atoms == python:
        print(f"OK: ASP parity holds for {len(atoms)} safe stories.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, "text", i, "sperm") for p in PLACES for i in ITEMS]


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    out: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(out) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
        rng = random.Random(base + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        out.append(sample)
    return out


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_combos()
        print(f"{len(combos)} compatible stories")
        for c in combos:
            print(c)
        return

    samples = [generate(resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + 1)))] if not getattr(args, "all", None) else [
        generate(StoryParams(place="nursery", note="text", item="hamper", topic="sperm", hero="Mina", friend="Pip")),
        generate(StoryParams(place="garden", note="text", item="box", topic="sperm", hero="Luna", friend="Toby")),
    ]
    if not getattr(args, "all", None):
        samples = generate_many(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
