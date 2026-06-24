#!/usr/bin/env python3
"""
A tiny detective-story world about a missing encyclopedia volume, a sharp clue,
a tense conversation, and a reconciliation at the end.

Seed tale:
---
Mina loved helping in the little library. One afternoon, the newest encyclopedia
volume went missing from the reading table. Mina noticed a pencil mark, a torn
bookmark, and a trail of dust, so she started asking questions. Her friend Theo
had been acting strange, and Mina thought he might have taken the book. But when
she followed the clues, she learned Theo had only moved the encyclopedia so he
could clean a spill near it. Mina apologized, Theo smiled, and they put the book
back together on the shelf.

The world is small on purpose:
- physical meters: location, ownership, dust, damage, distance
- emotional memes: worry, suspicion, guilt, trust, relief
- dialogue moves the story forward
- reconciliation resolves the mistaken suspicion
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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    book: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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


@dataclass
class Location:
    id: str
    label: str
    indoors: bool = True
    cluefulness: int = 1  # how easy it is to notice clues
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
class SuspectProfile:
    id: str
    label: str
    type: str
    temperament: str
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
    place: str
    hero: str
    hero_type: str
    suspect: str
    suspect_type: str
    clue: str
    seed: Optional[int] = None
    params: object | None = None
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


LOCATIONS = {
    "library": Location(id="library", label="the little library", indoors=True, cluefulness=2),
    "classroom": Location(id="classroom", label="the classroom", indoors=True, cluefulness=2),
    "study_room": Location(id="study_room", label="the study room", indoors=True, cluefulness=3),
}

HEROES = {
    "mina": SuspectProfile(id="Mina", label="Mina", type="girl", temperament="careful"),
    "leo": SuspectProfile(id="Leo", label="Leo", type="boy", temperament="quiet"),
    "nora": SuspectProfile(id="Nora", label="Nora", type="girl", temperament="curious"),
    "eli": SuspectProfile(id="Eli", label="Eli", type="boy", temperament="steady"),
}

SUSPECTS = {
    "theo": SuspectProfile(id="Theo", label="Theo", type="boy", temperament="nervous"),
    "ivy": SuspectProfile(id="Ivy", label="Ivy", type="girl", temperament="shy"),
    "sam": SuspectProfile(id="Sam", label="Sam", type="boy", temperament="busy"),
    "ava": SuspectProfile(id="Ava", label="Ava", type="girl", temperament="thoughtful"),
}

CLUES = {
    "pencil_mark": "a little pencil mark",
    "torn_bookmark": "a torn bookmark",
    "dust_trail": "a trail of dust",
    "spilled_ink": "a dark ink stain",
}

REASONS = {
    "pencil_mark": "someone had been reading carefully",
    "torn_bookmark": "the pages had been opened in a hurry",
    "dust_trail": "the book had been moved from a dusty shelf",
    "spilled_ink": "someone had cleaned a mess nearby",
}


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.location)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


def build_reasonable_pair(hero: SuspectProfile, suspect: SuspectProfile) -> bool:
    return hero.id != suspect.id and hero.type != suspect.type


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in LOCATIONS:
        for hero in HEROES:
            for suspect in SUSPECTS:
                if _safe_lookup(HEROES, hero).id == _safe_lookup(SUSPECTS, suspect).id:
                    continue
                for clue in CLUES:
                    combos.append((place, hero, suspect))
    return combos


def choose_book() -> str:
    return "encyclopedia"


def _do_clue(world: World, clue: str) -> None:
    book = world.get("book")
    if clue == "dust_trail":
        book.meters["dust"] += 1
    elif clue == "spilled_ink":
        book.meters["stained"] += 1
    elif clue == "torn_bookmark":
        book.meters["torn"] += 1
    elif clue == "pencil_mark":
        book.meters["marked"] += 1


def predict(world: World) -> dict[str, float]:
    sim = world.copy()
    book = sim.get("book")
    suspicion = sim.get("hero").memes.get("suspicion", 0.0)
    if book.meters.get("torn", 0) or book.meters.get("stained", 0):
        suspicion += 1
    if book.meters.get("dust", 0):
        suspicion += 0.5
    return {"suspicion": suspicion}


def reason_about_clue(world: World, clue: str) -> str:
    return _safe_lookup(REASONS, clue)


def introduce(world: World, hero: Entity, suspect: Entity) -> None:
    world.say(f"{hero.id} was a {hero.temperament} child who loved a good mystery.")
    world.say(f"{hero.id} liked asking questions, and {suspect.id} was the kind of friend who looked nervous when things went wrong.")


def opening(world: World, hero: Entity, book: Entity) -> None:
    world.say(
        f"One afternoon at {world.location.label}, the newest encyclopedia volume was missing from the reading table."
    )
    world.say(
        f"{hero.id} noticed right away, because {hero.pronoun('subject')} had been looking at {book.phrase} only a moment before."
    )


def inspect(world: World, hero: Entity, clue: str) -> None:
    _do_clue(world, clue)
    world.say(
        f"{hero.id} knelt beside the table and spotted {_safe_lookup(CLUES, clue)}."
    )
    world.say(
        f"That clue suggested {reason_about_clue(world, clue)}."
    )


def suspect_dialogue(world: World, hero: Entity, suspect: Entity) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + 1
    suspect.memes["worry"] = suspect.memes.get("worry", 0) + 1
    world.say(
        f'"Did you move the encyclopedia?" {hero.id} asked softly.'
    )
    world.say(
        f'"I did move it," {suspect.id} said, "but I did not take it."'
    )


def reveal(world: World, hero: Entity, suspect: Entity, book: Entity, clue: str) -> None:
    world.say(
        f"{hero.id} followed the clue to a nearby shelf and saw what had happened."
    )
    if clue == "spilled_ink":
        world.say(
            f"{suspect.id} had moved the encyclopedia only to clean a spill and keep the pages safe."
        )
    elif clue == "dust_trail":
        world.say(
            f"{suspect.id} had moved the encyclopedia to dust the table and then put it back."
        )
    elif clue == "torn_bookmark":
        world.say(
            f"{suspect.id} had opened the encyclopedia carefully and the bookmark had torn by accident."
        )
    else:
        world.say(
            f"{suspect.id} had been checking the page numbers and left a small pencil mark by mistake."
        )
    book.meters["found"] = 1
    hero.memes["suspicion"] = 0
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    suspect.memes["guilt"] = suspect.memes.get("guilt", 0) + 1


def reconcile(world: World, hero: Entity, suspect: Entity, book: Entity) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    suspect.memes["trust"] = suspect.memes.get("trust", 0) + 1
    suspect.memes["guilt"] = max(0, suspect.memes.get("guilt", 0) - 1)
    world.say(
        f'{hero.id} looked down and said, "I was wrong to jump to a conclusion."'
    )
    world.say(
        f'"It is okay," {suspect.id} said. "Next time, I will tell you first."'
    )
    world.say(
        f"They smiled, put the encyclopedia back in place, and the reading table looked calm again."
    )


def tell(location: Location, hero_prof: SuspectProfile, suspect_prof: SuspectProfile, clue: str) -> World:
    world = World(location)
    hero = world.add(Entity(id=hero_prof.id, kind="character", type=hero_prof.type, label=hero_prof.label))
    suspect = world.add(Entity(id=suspect_prof.id, kind="character", type=suspect_prof.type, label=suspect_prof.label))
    book = world.add(Entity(id="book", type="book", label="encyclopedia volume", phrase="the new encyclopedia volume", owner=hero.id))
    world.facts.update(hero=hero, suspect=suspect, book=book, clue=clue, location=location)

    introduce(world, hero, suspect)
    world.para()
    opening(world, hero, book)
    inspect(world, hero, clue)
    suspect_dialogue(world, hero, suspect)
    world.para()
    reveal(world, hero, suspect, book, clue)
    reconcile(world, hero, suspect, book)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    suspect: Entity = _safe_fact(world, f, "suspect")  # type: ignore[assignment]
    return [
        'Write a short detective story for a young child that includes an encyclopedia and ends with reconciliation.',
        f"Tell a gentle mystery where {hero.id} asks {suspect.id} about a missing encyclopedia volume.",
        f"Write a simple story with dialogue, a clue, and a happy apology around an encyclopedia.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    suspect: Entity = _safe_fact(world, f, "suspect")  # type: ignore[assignment]
    clue = _safe_fact(world, f, "clue")
    location: Location = _safe_fact(world, f, "location")  # type: ignore[assignment]
    book: Entity = _safe_fact(world, f, "book")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What kind of story is this one about {hero.id} and {suspect.id}?",
            answer=f"It is a small detective story about a missing encyclopedia volume at {location.label}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice near the encyclopedia?",
            answer=f"{hero.id} noticed {_safe_lookup(CLUES, clue)}, which helped point to what really happened.",
        ),
        QAItem(
            question=f"Why did {hero.id} think {suspect.id} might be involved at first?",
            answer=f"{hero.id} saw something unusual near the encyclopedia and felt suspicious before asking questions.",
        ),
        QAItem(
            question=f"How did the story end for the encyclopedia and the two friends?",
            answer=f"The encyclopedia was put back where it belonged, and {hero.id} and {suspect.id} made up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an encyclopedia?",
            answer="An encyclopedia is a big book or set of books filled with facts about many subjects.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues so they can figure out what happened by using careful thinking.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop arguing, talk kindly, and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
missing(book) :- book(book), not found(book).
suspect(hero) :- missing(book), clue(C), clue_involves(C).
reconcile(hero,suspect) :- confession(suspect), apology(hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in LOCATIONS:
        lines.append(asp.fact("location", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    _ = asp.one_model(asp_program("#show missing/1."))
    print("OK: ASP rules loaded and solved.")
    return 0


@dataclass
class Reg:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world with an encyclopedia clue and reconciliation.")
    ap.add_argument("--place", choices=sorted(LOCATIONS))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--clue", choices=sorted(CLUES))
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
    place = getattr(args, "place", None) or rng.choice(list(LOCATIONS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    if hero == suspect:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=_safe_lookup(HEROES, hero).type,
        suspect=suspect,
        suspect_type=_safe_lookup(SUSPECTS, suspect).type,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(LOCATIONS, params.place), _safe_lookup(HEROES, params.hero), _safe_lookup(SUSPECTS, params.suspect), params.clue)
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show missing/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in LOCATIONS:
            for hero in HEROES:
                for suspect in SUSPECTS:
                    if hero == suspect:
                        continue
                    for clue in CLUES:
                        params = StoryParams(
                            place=place,
                            hero=hero,
                            hero_type=_safe_lookup(HEROES, hero).type,
                            suspect=suspect,
                            suspect_type=_safe_lookup(SUSPECTS, suspect).type,
                            clue=clue,
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
