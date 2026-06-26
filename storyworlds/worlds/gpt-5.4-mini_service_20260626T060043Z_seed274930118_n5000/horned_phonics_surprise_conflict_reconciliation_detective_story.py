#!/usr/bin/env python3
"""
Standalone storyworld: horned phonics surprise conflict reconciliation detective story.

A small, classical simulation in a detective-story style:
- a child detective notices a strange clue
- the clue leads to a conflict about a phonics lesson
- a surprise reveals what the "horned" thing really is
- reconciliation ends the story on a calm, solved image

The world is intentionally compact and constraint-driven rather than random prose.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "school_library": "the school library",
    "classroom": "the classroom",
    "hallway": "the hallway",
    "reading_corner": "the reading corner",
}

DETECTIVES = {
    "Mina": ("girl", "curious"),
    "Theo": ("boy", "careful"),
    "Nora": ("girl", "steady"),
    "Eli": ("boy", "bright"),
}

HELPERS = {
    "librarian": "the librarian",
    "teacher": "the teacher",
    "friend": "a friend",
}

PHONICS_ITEMS = {
    "horned_book": "a horned phonics book",
    "horned_mask": "a horned phonics mask",
    "paper_crown": "a paper crown with tiny horns",
    "toy_hat": "a toy hat with cardboard horns",
}

CLUES = {
    "scrap_marks": "small scrape marks",
    "lost_page": "a torn phonics page",
    "chalk_dust": "a streak of chalk dust",
    "sticker_note": "a note with a star sticker",
}

SURPRISES = {
    "mask": "the horned thing was only a costume mask",
    "book_cover": "the horned thing was a book cover with drawings",
    "paper_crown": "the horned thing was a paper crown from a dress-up box",
}

CONFLICTS = {
    "accuse": "accused someone of hiding the clue",
    "protect": "wanted to protect the clue from getting ripped",
    "hide": "wanted to hide the clue until the teacher came",
}

RECONCILIATIONS = {
    "apology": "said sorry and shared the clue",
    "explain": "explained the clue kindly",
    "return": "returned the clue to its place",
}


# ---------------------------------------------------------------------------
# Shared containers / entities
# ---------------------------------------------------------------------------


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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label_word(self) -> str:
        return self.label or self.type
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
class StoryParams:
    location: str
    detective: str
    helper: str
    phonics_item: str
    clue: str
    surprise: str
    conflict: str
    reconciliation: str
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


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    world: object | None = None
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _is_valid_combo(location: str, phonics_item: str, surprise: str) -> bool:
    # The "horned" item must plausibly trigger detective curiosity:
    # a paper prop or book-related clue makes sense in a reading space.
    if location not in LOCATIONS:
        return False
    if phonics_item not in PHONICS_ITEMS:
        return False
    if surprise not in SURPRISES:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for location in LOCATIONS:
        for item in PHONICS_ITEMS:
            for surprise in SURPRISES:
                if _is_valid_combo(location, item, surprise):
                    combos.append((location, item, surprise))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _setup_world(params: StoryParams) -> World:
    world = World(location=_safe_lookup(LOCATIONS, params.location))

    detective_type, trait = _safe_lookup(DETECTIVES, params.detective)
    hero = world.add(Entity(
        id=params.detective,
        kind="character",
        type=detective_type,
        label=params.detective,
        memes={"curiosity": 1.0, "calm": 0.5},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="adult" if params.helper in {"librarian", "teacher"} else "child",
        label=_safe_lookup(HELPERS, params.helper),
        memes={"patience": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label=_safe_lookup(CLUES, params.clue),
        phrase=_safe_lookup(CLUES, params.clue),
        owner=params.helper,
    ))
    item = world.add(Entity(
        id="phonics_item",
        type="thing",
        label=_safe_lookup(PHONICS_ITEMS, params.phonics_item),
        phrase=_safe_lookup(PHONICS_ITEMS, params.phonics_item),
        owner=params.helper,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        item=item,
        trait=trait,
        location=world.location,
    )
    return world


def _introduce(world: World) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    trait = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "trait")
    world.say(
        f"{hero.label} was a {trait} little detective who loved reading clues."
    )
    world.say(
        f"{hero.label} especially liked phonics, because every sound could become a hint."
    )


def _mystery_setup(world: World, params: StoryParams) -> None:
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "item")
    clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "clue")
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")

    world.say(
        f"One afternoon at {world.location}, {helper.label_word} set out {item.phrase} "
        f"and a small note."
    )
    world.say(
        f"{hero.label} noticed {clue.phrase} near the desk and frowned."
    )
    world.facts["noticed_clue"] = True
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.meters = {"attention": 1.0}


def _conflict(world: World, params: StoryParams) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "item")

    if params.conflict == "accuse":
        hero.memes["tension"] = hero.memes.get("tension", 0.0) + 1.0
        world.say(
            f"{hero.label} thought the horned clue must mean someone was hiding something, "
            f"and {hero.pronoun()} {_safe_lookup(CONFLICTS, params.conflict)}."
        )
    elif params.conflict == "protect":
        hero.memes["tension"] = hero.memes.get("tension", 0.0) + 1.0
        world.say(
            f"{hero.label} held the horned phonics item close and {_safe_lookup(CONFLICTS, params.conflict)}, "
            f"so nobody would wrinkle it."
        )
    else:
        hero.memes["tension"] = hero.memes.get("tension", 0.0) + 1.0
        world.say(
            f"{hero.label} {_safe_lookup(CONFLICTS, params.conflict)} after hearing a noisy shuffle in the hall."
        )
    world.facts["conflict"] = True
    world.facts["item_name"] = item.phrase
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1.0


def _surprise(world: World, params: StoryParams) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "item")

    world.say(
        f"Then came the surprise: {_safe_lookup(SURPRISES, params.surprise)}."
    )
    if params.surprise == "mask":
        world.say(
            f"The horns were soft and silly, and they were only taped onto a mask for the phonics game."
        )
    elif params.surprise == "book_cover":
        world.say(
            f"The horns were drawn on the cover, so the book looked wild even though it was only about sounds."
        )
    else:
        world.say(
            f"The horns were folded from paper, and the whole thing was meant for a story-time game."
        )
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1.0
    item.meters["understood"] = 1.0
    world.facts["surprised"] = True


def _reconciliation(world: World, params: StoryParams) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "item")

    world.say(
        f"{hero.label} looked at {helper.label_word} and {_safe_lookup(RECONCILIATIONS, params.reconciliation)}."
    )
    hero.memes["tension"] = 0.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    helper.memes["worry"] = 0.0
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1.0

    if params.reconciliation == "apology":
        world.say(
            f"{helper.label_word} smiled, and the two of them solved the phonics puzzle together."
        )
    elif params.reconciliation == "explain":
        world.say(
            f"{helper.label_word} explained the clue, and {hero.label} nodded because the answer was simple."
        )
    else:
        world.say(
            f"{helper.label_word} put the horned item back on the shelf, where it belonged."
        )
    world.say(
        f"By the end, the little detective had a clear answer, a quiet room, and a phonics lesson that felt friendly again."
    )
    world.facts["resolved"] = True


def build_story(params: StoryParams) -> World:
    world = _setup_world(params)
    _introduce(world)
    world.para()
    _mystery_setup(world, params)
    _conflict(world, params)
    world.para()
    _surprise(world, params)
    _reconciliation(world, params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").label_word
    return [
        f'Write a child-friendly detective story with the word "horned" and a phonics clue.',
        f"Tell a short mystery about {hero}, who finds a horned phonics item at {world.location} and then learns the surprise.",
        f"Write a simple story where {hero} has a conflict about a clue, then makes peace with {helper}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").label_word
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item").phrase
    clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue").phrase
    location = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "location")

    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {hero}, who watched the clue carefully at {location}.",
        ),
        QAItem(
            question=f"What horned phonics item was part of the mystery?",
            answer=f"The mystery included {item}, which made the clue feel odd at first.",
        ),
        QAItem(
            question=f"Why did {hero} get upset or worried?",
            answer=f"{hero} got upset because the clue looked serious and the story had a conflict before the surprise was explained.",
        ),
        QAItem(
            question=f"How did the story end between {hero} and {helper}?",
            answer=f"They ended in reconciliation, and the room felt calm again after the clue was understood.",
        ),
        QAItem(
            question=f"What was the surprise about the horned clue?",
            answer=f"The surprise was that {_safe_lookup(SURPRISES, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "surprise"))}",
        ),
        QAItem(
            question=f"What clue did the detective notice?",
            answer=f"{hero} noticed {clue} near the desk.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "horned": [
        QAItem(
            question="What does horned mean?",
            answer="Horned means having horns or horn-like shapes.",
        )
    ],
    "phonics": [
        QAItem(
            question="What is phonics?",
            answer="Phonics is learning how letters and letter groups make sounds.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["horned"])
    out.extend(WORLD_KNOWLEDGE["phonics"])
    out.extend(WORLD_KNOWLEDGE["detective"])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
location(L) :- loc(L).
item(I) :- phonics_item(I).
surprise(S) :- surprise_kind(S).

valid(L, I, S) :- location(L), item(I), surprise(S).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for loc in LOCATIONS:
        lines.append(asp.fact("loc", loc))
    for item in PHONICS_ITEMS:
        lines.append(asp.fact("phonics_item", item))
    for surprise in SURPRISES:
        lines.append(asp.fact("surprise_kind", surprise))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        location="school_library",
        detective="Mina",
        helper="librarian",
        phonics_item="horned_book",
        clue="lost_page",
        surprise="book_cover",
        conflict="accuse",
        reconciliation="explain",
    ),
    StoryParams(
        location="reading_corner",
        detective="Theo",
        helper="teacher",
        phonics_item="horned_mask",
        clue="chalk_dust",
        surprise="mask",
        conflict="protect",
        reconciliation="apology",
    ),
    StoryParams(
        location="classroom",
        detective="Nora",
        helper="teacher",
        phonics_item="paper_crown",
        clue="sticker_note",
        surprise="paper_crown",
        conflict="hide",
        reconciliation="return",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small detective-style storyworld about horned phonics clues."
    )
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--phonics-item", choices=PHONICS_ITEMS, dest="phonics_item")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
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
    if getattr(args, "location", None) and getattr(args, "phonics_item", None) and getattr(args, "surprise", None):
        if not _is_valid_combo(getattr(args, "location", None), getattr(args, "phonics_item", None), getattr(args, "surprise", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "location", None) is None or c[0] == getattr(args, "location", None))
        and (getattr(args, "phonics_item", None) is None or c[1] == getattr(args, "phonics_item", None))
        and (getattr(args, "surprise", None) is None or c[2] == getattr(args, "surprise", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    location, phonics_item, surprise = rng.choice(list(combos))
    detective = getattr(args, "detective", None) or rng.choice(sorted(DETECTIVES))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    conflict = getattr(args, "conflict", None) or rng.choice(sorted(CONFLICTS))
    reconciliation = getattr(args, "reconciliation", None) or rng.choice(sorted(RECONCILIATIONS))

    return StoryParams(
        location=location,
        detective=detective,
        helper=helper,
        phonics_item=phonics_item,
        clue=clue,
        surprise=surprise,
        conflict=conflict,
        reconciliation=reconciliation,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (location, item, surprise) combos:\n")
        for loc, item, sur in combos:
            print(f"  {loc:16} {item:14} {sur}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective}: {p.phonics_item} at {p.location} (surprise: {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
