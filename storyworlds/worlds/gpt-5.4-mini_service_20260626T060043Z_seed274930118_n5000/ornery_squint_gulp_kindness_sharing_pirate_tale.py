#!/usr/bin/env python3
"""
A small pirate-tale storyworld about an ornery squint, a gulp of worry, and a
kindness-sharing turn that saves the day.

Seed tale sketch:
---
On a little ship at sea, an ornery young pirate named Pip found a shiny chest.
Pip wanted it all. When the crew asked to share, Pip squinted hard and gulped,
because the chest looked bigger than one sailor's hands could carry.

Then the cabin child saw that the chest held cookies, maps, and a lantern for
everyone. The crew showed kindness, shared the load, and Pip learned that a
shared treasure could feel richer than a stolen one.
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
# Core domain model
# ---------------------------------------------------------------------------
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chest: object | None = None
    crewmate: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["weight", "safe", "shared", "risk", "worry"]:
            self.meters.setdefault(k, 0.0)
        for k in ["kindness", "sharing", "ornery", "squint", "gulp", "joy", "trust"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captainess"}
        male = {"boy", "father", "man", "captain", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Setting:
    place: str = "the little ship"
    place_detail: str = "the deck"
    sea: str = "calm blue water"
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
class Treasure:
    label: str
    phrase: str
    contents: list[str]
    weight: int = 1
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
class CrewRole:
    id: str
    label: str
    kind: str
    traits: list[str] = field(default_factory=list)
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
    treasure: str
    hero: str
    hero_kind: str
    crewmate: str
    crew_kind: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ship": Setting(place="the little ship", place_detail="the deck", sea="calm blue water"),
    "harbor": Setting(place="the harbor boat", place_detail="the dock", sea="gentle harbor waves"),
    "island": Setting(place="the island camp", place_detail="the sandy shore", sea="bright lagoon water"),
}

TREASURES = {
    "chest": Treasure(
        label="chest",
        phrase="a shiny little chest",
        contents=["cookies", "a map", "a lantern"],
        weight=2,
    ),
    "sack": Treasure(
        label="sack",
        phrase="a rope-tied sack",
        contents=["apples", "buttons", "a little bell"],
        weight=1,
    ),
    "crate": Treasure(
        label="crate",
        phrase="a wooden crate",
        contents=["pearls", "peaches", "a compass"],
        weight=2,
    ),
}

CREW = {
    "pirate": CrewRole(id="pirate", label="pirate", kind="boy", traits=["ornery", "brave"]),
    "mate": CrewRole(id="mate", label="mate", kind="girl", traits=["kind", "steady"]),
    "deckhand": CrewRole(id="deckhand", label="deckhand", kind="boy", traits=["curious", "helpful"]),
    "captain": CrewRole(id="captain", label="captain", kind="girl", traits=["calm", "fair"]),
}

NAMES = {
    "boy": ["Pip", "Finn", "Jory", "Tom", "Ned", "Rory"],
    "girl": ["Mina", "Ada", "Lia", "Tess", "June", "Wren"],
}

TRAITS = ["ornery", "squinty", "brave", "curious", "stubborn", "kind"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure is at risk when it is heavy enough that one stubborn sailor will not
% want to share it, and a kindness-based fix exists when another crew member can
% help carry or split it.
ornery_hero(H) :- hero(H), has_trait(H, ornery).
can_share(T) :- treasure(T), contents(T, N), N >= 2.
needs_kindness(H, T) :- ornery_hero(H), treasure(T), can_share(T).
shared_ok(H, T) :- needs_kindness(H, T), mate(M), helper(M).

valid_story(P, T, H, C) :- setting(P), treasure(T), hero(H), crew(C),
                           needs_kindness(H, T), shared_ok(H, T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("contents", tid, len(t.contents)))
    for cid, c in CREW.items():
        lines.append(asp.fact("crew", cid))
        lines.append(asp.fact("has_trait", cid, c.traits[0]))
        if "kind" in c.traits:
            lines.append(asp.fact("helper", cid))
        if c.kind == "boy":
            lines.append(asp.fact("hero_kind", cid, "boy"))
        else:
            lines.append(asp.fact("hero_kind", cid, "girl"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in SETTINGS:
        for t in TREASURES:
            for h in CREW:
                for c in CREW:
                    if "kind" in CREW[c].traits:
                        combos.append((p, t, h, c))
    return combos


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    py_set = set(python_valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python ({len(py_set)} story tuples).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(clingo_set - py_set))
    print(" only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, crewmate: Entity, treasure: Entity) -> None:
    world.say(
        f"On {world.setting.place}, {hero.id} was an ornery little {hero.type} who loved shiny things."
    )
    world.say(
        f"{crewmate.id} was the kind of crewmate who noticed when someone needed help, and {treasure.phrase} soon caught every eye."
    )


def desire(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["ornery"] += 1
    hero.memes["sharing"] += 0.0
    world.say(
        f"{hero.id} wanted the {treasure.label} all to {hero.pronoun('object')}self, and {hero.pronoun().capitalize()} clutched the lid tight."
    )


def warning(world: World, hero: Entity, crewmate: Entity, treasure: Entity) -> None:
    hero.memes["squint"] += 1
    hero.memes["gulp"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} gave a squint at the crowd and let out a gulp, because the {treasure.label} looked heavy enough to cause a fuss."
    )
    world.say(
        f'"If you keep it all," {crewmate.id} said, "you may lose the joy of what is inside."'
    )


def show_contents(world: World, treasure: Treasure) -> None:
    if len(treasure.contents) >= 2:
        items = ", ".join(treasure.contents[:-1]) + f", and {treasure.contents[-1]}"
    else:
        items = treasure.contents[0]
    world.say(
        f"When they peeked inside, they found {items}, enough for the whole crew."
    )


def sharing_turn(world: World, hero: Entity, crewmate: Entity, treasure: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["sharing"] += 1
    hero.memes["ornery"] = max(0.0, hero.memes["ornery"] - 1.0)
    world.say(
        f"{hero.id} paused, then nodded. {hero.pronoun().capitalize()} chose kindness over grumbling and began to share."
    )
    world.say(
        f"{crewmate.id} helped carry the {treasure.label}, and together they opened it for everyone on the deck."
    )


def ending(world: World, hero: Entity, crewmate: Entity, treasure: Treasure) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"In the end, the {treasure.label} stayed on the ship, but the best part was how the crew laughed while sharing it."
    )
    world.say(
        f"{hero.id} still had an ornery spark, yet now {hero.pronoun()} knew a shared treasure could make the whole sea feel bigger."
    )


def tell(setting: Setting, treasure: Treasure, hero_name: str, hero_kind: str, crew_name: str, crew_kind: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_kind,
        label=hero_kind,
        traits=["ornery", "squint", "gulp"],
    ))
    crewmate = world.add(Entity(
        id=crew_name,
        kind="character",
        type=crew_kind,
        label=crew_kind,
        traits=["kind", "sharing"],
    ))
    chest = world.add(Entity(
        id="treasure",
        type="thing",
        label=treasure.label,
        phrase=treasure.phrase,
        plural=False,
        owner=hero.id,
    ))

    intro(world, hero, crewmate, chest)
    world.para()
    desire(world, hero, chest)
    warning(world, hero, crewmate, chest)
    show_contents(world, treasure)
    world.para()
    sharing_turn(world, hero, crewmate, chest)
    ending(world, hero, crewmate, chest)

    world.facts.update(hero=hero, crewmate=crewmate, treasure=chest, treasure_cfg=treasure)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    crew = _safe_fact(world, f, "crewmate")
    treasure = _safe_fact(world, f, "treasure_cfg")
    return [
        'Write a short pirate tale for a small child that includes the words "ornery", "squint", and "gulp".',
        f"Tell a story where {hero.id} first wants the {treasure.label} all to {hero.pronoun('object')}self, but {crew.id} answers with kindness and sharing.",
        f"Write a gentle sea story about treasure, where the crew learns that sharing makes the chest's contents better for everyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    crew = _safe_fact(world, f, "crewmate")
    treasure = _safe_fact(world, f, "treasure_cfg")
    return [
        QAItem(
            question=f"Who was ornery at the start of the story?",
            answer=f"{hero.id} was the ornery little {hero.type} who wanted the {treasure.label} all to {hero.pronoun('object')}self.",
        ),
        QAItem(
            question=f"What did {hero.id} do before choosing kindness?",
            answer=f"{hero.id} squinted at the crew and gave a gulp because the {treasure.label} felt like it might cause a fuss.",
        ),
        QAItem(
            question=f"How did {crew.id} help solve the problem?",
            answer=f"{crew.id} answered with kindness and helped {hero.id} share the {treasure.label} with everyone on the deck.",
        ),
        QAItem(
            question=f"What was inside the {treasure.label}?",
            answer=f"It held {', '.join(treasure.contents[:-1])}, and {treasure.contents[-1]}, which was enough for the whole crew.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful toward someone else.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, enjoy, or have some of what you have.",
        ),
        QAItem(
            question="Why do pirates use a chest?",
            answer="A chest is a strong box that can keep treasure safe while a ship is sailing.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with kindness and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero", choices=[k for k in CREW if CREW[k].kind == "boy"] + [k for k in CREW if CREW[k].kind == "girl"])
    ap.add_argument("--hero-kind", choices=["boy", "girl"])
    ap.add_argument("--crewmate", choices=CREW)
    ap.add_argument("--crew-kind", choices=["boy", "girl"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(["boy", "girl"])
    crew_kind = getattr(args, "crew_kind", None) or rng.choice(["boy", "girl"])

    hero_opts = [k for k, v in CREW.items() if v.kind == hero_kind]
    crew_opts = [k for k, v in CREW.items() if "kind" in v.traits]

    hero = getattr(args, "hero", None) or rng.choice(hero_opts)
    crewmate = getattr(args, "crewmate", None) or rng.choice(crew_opts)

    if getattr(args, "hero", None) and CREW[getattr(args, "hero", None)].kind != hero_kind:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "crewmate", None) and "kind" not in CREW[getattr(args, "crewmate", None)].traits:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        place=place,
        treasure=treasure,
        hero=hero,
        hero_kind=hero_kind,
        crewmate=crewmate,
        crew_kind=crew_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TREASURES, params.treasure),
        params.hero,
        params.hero_kind,
        params.crewmate,
        params.crew_kind,
    )
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
    StoryParams(place="ship", treasure="chest", hero="Pip", hero_kind="boy", crewmate="Mina", crew_kind="girl"),
    StoryParams(place="harbor", treasure="sack", hero="Finn", hero_kind="boy", crewmate="Ada", crew_kind="girl"),
    StoryParams(place="island", treasure="crate", hero="Rory", hero_kind="boy", crewmate="Wren", crew_kind="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.hero}: {p.treasure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
