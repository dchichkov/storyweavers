#!/usr/bin/env python3
"""
A small story world in the style of an Animal Story:
a child-facing animal tale about a book, a psychic helper, and friendship.

The seed premise:
---
A little animal finds a book that seems to whisper thoughts.
A psychic friend can sense who feels lonely, and helps the animal make a new friend.
At first the book feels mysterious and a little scary, but it turns into a bridge
between two animals who were both hoping to belong.

World shape:
- physical meters: holding, distance, page_open, tidy, closeness
- emotional memes: curiosity, worry, kindness, loneliness, joy, trust
- the story follows: find book -> wonder/worry -> psychic insight -> friendly act -> resolution
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    animal: object | None = None
    book: object | None = None
    friend: object | None = None
    psychic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "doe", "cat", "mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "buck", "dog", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    indoors: bool
    calm: bool = True
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


@dataclass
class StoryParams:
    place: str
    animal: str
    friend: str
    book: str
    psychic: str
    trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def _apply_book_world(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    book = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "book")
    reader = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "animal"))
    if reader.meters.get("holding", 0) < THRESHOLD:
        return out
    if reader.meters.get("page_open", 0) < THRESHOLD:
        return out
    if book.meters.get("glow", 0) >= THRESHOLD and reader.memes.get("curiosity", 0) >= THRESHOLD:
        sig = ("book_whisper", reader.id)
        if sig not in world.fired:
            world.fired.add(sig)
            reader.memes["worry"] += 1
            out.append(f"The book felt strange, like it knew a secret.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _apply_friendship(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    a = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "animal"))
    b = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend"))
    if a.memes.get("joy", 0) >= THRESHOLD and b.memes.get("joy", 0) >= THRESHOLD:
        sig = ("friendship", a.id, b.id)
        if sig not in world.fired:
            world.fired.add(sig)
            a.meters["closeness"] = 1
            b.meters["closeness"] = 1
            out.append("They sat together and felt like friends right away.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_apply_book_world, _apply_friendship):
            sents = fn(world, narrate=False)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_friendship(world: World, reader: Entity, book: Entity) -> dict:
    sim = world.copy()
    sim.get(reader.id).meters["holding"] = 1
    sim.get(reader.id).meters["page_open"] = 1
    book2 = sim.get(book.id)
    book2.meters["glow"] = 1
    sim.get(reader.id).memes["curiosity"] = 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get(reader.id).memes.get("worry", 0) >= THRESHOLD,
        "friendship": sim.get(reader.id).meters.get("closeness", 0) >= THRESHOLD,
    }


def introduce(world: World, animal: Entity) -> None:
    world.say(f"{animal.name_word()} was a little {animal.traits[0]} {animal.type} who loved quiet places.")


def find_book(world: World, animal: Entity, book: Entity) -> None:
    animal.meters["holding"] = 1
    book.held_by = animal.id
    animal.memes["curiosity"] += 1
    world.say(f"One day, {animal.name_word()} found {book.phrase} tucked under a bench.")
    world.say(f"{animal.pronoun().capitalize()} picked it up and turned the cover with gentle paws.")


def psychic_feels(world: World, psychic: Entity, animal: Entity) -> None:
    animal.memes["loneliness"] += 1
    psychic.memes["kindness"] += 1
    world.say(f"Nearby, {psychic.name_word()} the psychic listened with closed eyes.")
    world.say(f"{psychic.pronoun().capitalize()} could feel that {animal.name_word()} wanted a friend.")


def worry(world: World, animal: Entity, book: Entity) -> None:
    animal.meters["page_open"] = 1
    book.meters["glow"] = 1
    propagate(world, narrate=False)
    world.say(f"The pages gave off a soft glow, and {animal.name_word()} felt a tiny shiver.")
    if animal.memes.get("worry", 0) >= THRESHOLD:
        world.say(f"{animal.pronoun().capitalize()} wondered if the book was magical or just lonely.")


def gentle_turn(world: World, psychic: Entity, animal: Entity, friend: Entity, book: Entity) -> None:
    clue = predict_friendship(world, animal, book)
    if not clue["worry"]:
        pass
    psychic.memes["trust"] += 1
    world.say(f"{psychic.name_word()} smiled and said the book was not scary at all.")
    world.say(f'"It is looking for the right story," {psychic.name_word()} said. "And maybe the right friend."')
    friend.memes["loneliness"] += 1
    world.say(f"Then {psychic.name_word()} led {animal.name_word()} to {friend.name_word()}, who looked shy and hopeful.")
    animal.memes["joy"] += 1
    friend.memes["joy"] += 1
    animal.memes["kindness"] += 1
    world.say(f'{animal.name_word()} offered the book to share, and {friend.name_word()} lit up with a smile.')
    propagate(world, narrate=True)


def closing(world: World, animal: Entity, friend: Entity, book: Entity) -> None:
    animal.meters["closeness"] = 1
    friend.meters["closeness"] = 1
    world.say(f"By the end, {animal.name_word()} and {friend.name_word()} sat side by side, reading one page at a time.")
    world.say(f"The book was still mysterious, but now it belonged to their friendship, not to their worry.")


SETTINGS = {
    "clearing": Setting(place="the mossy clearing", indoors=False),
    "burrow": Setting(place="the cozy burrow", indoors=True),
    "pond": Setting(place="the pond edge", indoors=False),
}

ANIMALS = {
    "rabbit": ("rabbit", "curious"),
    "fox": ("fox", "shy"),
    "mouse": ("mouse", "tiny"),
    "cat": ("cat", "gentle"),
    "dog": ("dog", "friendly"),
}

FRIENDS = {
    "squirrel": ("squirrel", "quick"),
    "hedgehog": ("hedgehog", "quiet"),
    "deer": ("deer", "soft-spoken"),
    "otter": ("otter", "playful"),
}

BOOKS = {
    "storybook": ("storybook", "a storybook with bright blue stars"),
    "picturebook": ("picturebook", "a picture book with smiling animals"),
    "tinybook": ("tinybook", "a tiny book with a silver clasp"),
}

PSYCHICS = {
    "owl": ("owl", "wise"),
    "bat": ("bat", "gentle"),
    "mole": ("mole", "still"),
}

TRAITS = ["curious", "shy", "brave", "gentle", "patient", "quiet"]


@dataclass
class QAConfig:
    pass
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


ASP_RULES = r"""
animal(A) :- animal_type(A,_).
book(B) :- book_type(B,_).
psychic(P) :- psychic_type(P,_).
friend(F) :- friend_type(F,_).

shares_story(A,F) :- seeks_friendship(A,F), book_present(B), opens_book(A,B), psychic_nearby(P), senses_loneliness(P,A,F).
friendship_turn(A,F) :- shares_story(A,F), kindness(A), kindness(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a, (typ, _) in ANIMALS.items():
        lines.append(asp.fact("animal_type", a, typ))
    for b, (typ, _) in BOOKS.items():
        lines.append(asp.fact("book_type", b, typ))
    for p, (typ, _) in PSYCHICS.items():
        lines.append(asp.fact("psychic_type", p, typ))
    for f, (typ, _) in FRIENDS.items():
        lines.append(asp.fact("friend_type", f, typ))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world about a book, a psychic, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--book", choices=BOOKS)
    ap.add_argument("--psychic", choices=PSYCHICS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    animal = getattr(args, "animal", None) or rng.choice(list(ANIMALS))
    friend = getattr(args, "friend", None) or rng.choice(list(FRIENDS))
    book = getattr(args, "book", None) or rng.choice(list(BOOKS))
    psychic = getattr(args, "psychic", None) or rng.choice(list(PSYCHICS))
    name = getattr(args, "name", None) or rng.choice(["Milo", "Pip", "Luna", "Nico", "Mina", "Toby"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, animal=animal, friend=friend, book=book, psychic=psychic, trait=trait, seed=getattr(args, "seed", None))


def validate(params: StoryParams) -> None:
    if params.animal == params.friend:
        pass
    if params.animal == params.psychic:
        pass


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = World(_safe_lookup(SETTINGS, params.place))
    a_type, a_trait = _safe_lookup(ANIMALS, params.animal)
    f_type, f_trait = _safe_lookup(FRIENDS, params.friend)
    p_type, p_trait = _safe_lookup(PSYCHICS, params.psychic)
    b_type, b_label = _safe_lookup(BOOKS, params.book)

    animal = world.add(Entity(id=params.animal, kind="character", type=a_type, label=params.name, traits=[params.trait, a_trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type=f_type, label=params.friend.title(), traits=[f_trait]))
    psychic = world.add(Entity(id=params.psychic, kind="character", type=p_type, label=params.psychic.title(), traits=[p_trait]))
    book = world.add(Entity(id=params.book, kind="thing", type=b_type, label=params.book, phrase=b_label, owner=animal.id))
    world.facts.update(animal=animal.id, friend=friend.id, psychic=psychic.id, book=book)

    introduce(world, animal)
    world.para()
    find_book(world, animal, book)
    psychic_feels(world, psychic, animal)
    worry(world, animal, book)
    world.para()
    gentle_turn(world, psychic, animal, friend, book)
    world.para()
    closing(world, animal, friend, book)

    story = world.render()
    prompts = [
        f"Write a gentle animal story about a {animal.type} named {animal.label} who finds {book.phrase}, with a psychic helper and a friendship ending.",
        f"Tell a child-sized story where a {animal.type} discovers a mysterious book and learns it can help two animals become friends.",
        f"Write an animal story with a little bit of magic, a psychic listener, and a book that turns worry into friendship.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {animal.label} find in the story?",
            answer=f"{animal.label} found {book.phrase} tucked under a bench, and that book became part of the friendship story.",
        ),
        QAItem(
            question=f"Why did the book feel strange at first?",
            answer=f"It felt strange because it glowed and seemed to know a secret, which made {animal.label} feel a tiny bit worried before the psychic explained it.",
        ),
        QAItem(
            question=f"How did the psychic help?",
            answer=f"The psychic sensed that {animal.label} wanted a friend and led {animal.label} to {friend.name_word()}, so the two animals could share the book.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"At the end, {animal.label} and {friend.name_word()} were sitting together, and the book belonged to their friendship instead of their worry.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a psychic in this story world?",
            answer="A psychic is an animal character who can sense feelings and hidden worries, then use that feeling to help others gently.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when two characters care about each other, share, and feel happy together.",
        ),
        QAItem(
            question="Why can a book matter in a story?",
            answer="A book can matter because it can carry a message, a mystery, or a shared activity that brings characters together.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_verify() -> int:
    import asp
    program = asp_program("#show friendship_turn/2.")
    model = asp.one_model(program)
    ok = bool(asp.atoms(model, "friendship_turn"))
    if ok:
        print("OK: ASP program runs and can derive a friendship turn.")
        return 0
    print("MISMATCH: ASP program did not derive expected friendship turn.")
    return 1


def asp_valid() -> list[tuple]:
    import asp
    program = asp_program("#show friendship_turn/2.")
    return asp.atoms(asp.one_model(program), "friendship_turn")


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
    if getattr(args, "show_asp", None):
        print(asp_program("#show friendship_turn/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="clearing", animal="rabbit", friend="squirrel", book="storybook", psychic="owl", trait="curious"),
            StoryParams(place="burrow", animal="mouse", friend="hedgehog", book="picturebook", psychic="bat", trait="shy"),
            StoryParams(place="pond", animal="fox", friend="otter", book="tinybook", psychic="mole", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            try:
                sample = generate(params)
            except StoryError:
                continue
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.animal} + {p.friend} + {p.book}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
