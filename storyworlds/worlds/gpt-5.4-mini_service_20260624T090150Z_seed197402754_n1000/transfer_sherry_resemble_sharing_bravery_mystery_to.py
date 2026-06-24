#!/usr/bin/env python3
"""
A small superhero storyworld about sharing, bravery, and a mystery to solve.

Premise:
- A young hero wants to help by transferring a treasured item.
- The item belongs to Sherry, whose concern starts the mystery.
- The hero and Sherry must notice what things resemble each other to solve
  the puzzle without a big fight.

This world keeps a tiny, state-driven shape:
- sharing creates trust
- bravery lets the hero speak up and investigate
- resemblance helps identify the right object and resolve the mystery
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
# World model
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
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    gadget: object | None = None
    hero: object | None = None
    sherry: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Setting:
    place: str
    indoor: bool = False
    supports: set[str] = field(default_factory=set)
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
class Gadget:
    id: str
    label: str
    phrase: str
    supports: set[str]
    helps_with: set[str]
    plural: bool = False
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
class MysteryClue:
    id: str
    label: str
    resembles: str
    truth: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "city": Setting(place="the city rooftop", indoor=False, supports={"search", "share"}),
    "library": Setting(place="the library hall", indoor=True, supports={"search", "share"}),
    "alley": Setting(place="the quiet alley", indoor=False, supports={"search"}),
}

HEROES = [
    ("Nova", "girl", "bold"),
    ("Arrow", "boy", "curious"),
    ("Spark", "girl", "brave"),
    ("Bolt", "boy", "kind"),
]

GADGETS = {
    "gloves": Gadget(
        id="gloves",
        label="glow gloves",
        phrase="a pair of glow gloves",
        supports={"share", "search"},
        helps_with={"carry", "transfer"},
    ),
    "lens": Gadget(
        id="lens",
        label="mystery lens",
        phrase="a tiny mystery lens",
        supports={"search"},
        helps_with={"resemble"},
    ),
    "cape": Gadget(
        id="cape",
        label="helper cape",
        phrase="a bright helper cape",
        supports={"share", "brave"},
        helps_with={"share"},
    ),
}

CLUES = {
    "badge": MysteryClue(
        id="badge",
        label="silver badge",
        resembles="a shiny coin",
        truth="It belonged to Sherry's missing helper kit.",
    ),
    "ring": MysteryClue(
        id="ring",
        label="small ring",
        resembles="a tiny bracelet",
        truth="It was only a toy that looked important.",
    ),
    "key": MysteryClue(
        id="key",
        label="blue key",
        resembles="a fish-shaped charm",
        truth="It opened the old locker where the shared supplies waited.",
    ),
}

COMBOS = [
    ("city", "badge"),
    ("library", "ring"),
    ("alley", "key"),
]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def mystery_is_reasonable(setting: Setting, clue: MysteryClue) -> bool:
    return "search" in setting.supports and clue.resembles != ""


def sharing_is_reasonable(gadget: Gadget, clue: MysteryClue) -> bool:
    return "share" in gadget.supports and ("search" in gadget.supports or "transfer" in gadget.helps_with)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, clue_id in COMBOS:
        setting = _safe_lookup(SETTINGS, place)
        clue = _safe_lookup(CLUES, clue_id)
        if mystery_is_reasonable(setting, clue):
            out.append((place, clue_id))
    return out


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    hero_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World events
# ---------------------------------------------------------------------------
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


def _setup(world: World, hero: Entity, sherry: Entity, clue: Entity, gadget: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('age_word', 'young')} hero who liked to help "
        f"in {world.setting.place}."
    )
    world.say(
        f"One day {hero.id} met Sherry, who was worried because her {clue.label} was missing."
    )
    world.say(
        f"{hero.id} also carried {gadget.phrase}, because a hero should be ready to share tools."
    )
    world.say(
        f"Sherry said the missing thing might resemble {clue.resembles}, and that made the problem feel mysterious."
    )


def _transfer(world: World, hero: Entity, sherry: Entity, clue: Entity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0) + 1
    sherry.memes["worry"] = sherry.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} did not rush away. Instead, {hero.pronoun()} offered to transfer the clue to Sherry once it was found."
    )
    world.say(
        f"That small promise made Sherry trust {hero.id} a little more."
    )


def _search(world: World, hero: Entity, clue: Entity, gadget: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"With brave steps, {hero.id} searched the floor and the shelves, using {gadget.label} to look closely."
    )
    world.say(
        f"The little light showed that one object did not quite resemble the missing {clue.label} at all."
    )


def _mystery_turn(world: World, hero: Entity, sherry: Entity, clue: Entity) -> None:
    hero.memes["mystery"] = hero.memes.get("mystery", 0) + 1
    world.say(
        f"Then {hero.id} noticed the truth: the shiny thing was only pretending to be the missing piece."
    )
    world.say(
        f"It resembled {clue.resembles}, but it was not the same thing."
    )
    world.say(
        f"{hero.id} told Sherry the clue, and Sherry pointed to the real place where the missing item had been tucked away."
    )


def _share_and_resolve(world: World, hero: Entity, sherry: Entity, clue: Entity, gadget: Entity) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    sherry.memes["joy"] = sherry.memes.get("joy", 0) + 1
    clue.held_by = sherry.id
    world.say(
        f"{hero.id} handed the found {clue.label} to Sherry with both hands so it would be safe."
    )
    world.say(
        f"Sherry smiled, because the mystery was solved, the right thing was shared, and the whole room felt lighter."
    )
    world.say(
        f"At the end, {hero.id} and Sherry stood together like a real team, and {gadget.label} shone like a tiny badge of bravery."
    )


def tell(setting: Setting, clue_cfg: MysteryClue, hero_name: str, hero_type: str, hero_trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.meters["age_word"] = 0
    sherry = world.add(Entity(id="Sherry", kind="character", type="girl"))
    clue = world.add(Entity(id=clue_cfg.id, kind="thing", label=clue_cfg.label))
    gadget = world.add(Entity(id="gadget", kind="thing", label="mystery lens"))

    hero.memes["bravery"] = 0
    hero.memes["sharing"] = 0
    hero.memes["mystery"] = 0
    sherry.memes["worry"] = 0

    _setup(world, hero, sherry, clue, gadget)
    world.para()
    _transfer(world, hero, sherry, clue)
    _search(world, hero, clue, gadget)
    world.para()
    _mystery_turn(world, hero, sherry, clue)
    _share_and_resolve(world, hero, sherry, clue, gadget)

    world.facts.update(
        hero=hero,
        sherry=sherry,
        clue=clue,
        gadget=gadget,
        setting=setting,
        clue_cfg=clue_cfg,
        hero_trait=hero_trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    clue_cfg = _safe_fact(world, world.facts, "clue_cfg")
    return [
        f"Write a short superhero story for a child named {hero.id} who learns to share and solve a mystery.",
        f"Tell a brave little story where Sherry loses {clue_cfg.label} and the hero uses a clue that resembles something else.",
        f"Write a gentle superhero tale about transfer, sharing, and bravery in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    sherry = _safe_fact(world, world.facts, "sherry")
    clue_cfg = _safe_fact(world, world.facts, "clue_cfg")
    hero_trait = _safe_fact(world, world.facts, "hero_trait")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero_trait} superhero kid, and Sherry, who needed help finding her {clue_cfg.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help Sherry?",
            answer=f"{hero.id} searched carefully, noticed what things resembled each other, and shared the found {clue_cfg.label} back with Sherry.",
        ),
        QAItem(
            question=f"Why was the problem a mystery?",
            answer=f"It was a mystery because the missing item was hard to spot and one thing resembled {clue_cfg.resembles}, which could fool someone at first.",
        ),
        QAItem(
            question=f"How did Sherry feel at the end?",
            answer=f"Sherry felt happy and relieved because {hero.id} solved the mystery and gave the {clue_cfg.label} back safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or have something for a while or giving it back kindly.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being ready to do something hard or scary when it is the right thing to do.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or question that you have to think about and solve by looking for clues.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
reasonably_valid(Place, Clue) :- setting(Place), clue(Clue),
                                 supports(Place, search),
                                 resembles(Clue, _).
valid_story(Place, Clue) :- reasonably_valid(Place, Clue).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for sup in sorted(s.supports):
            lines.append(asp.fact("supports", sid, sup))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("resembles", cid, c.resembles))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small superhero storyworld about sharing, bravery, and a mystery to solve."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait")
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "clue", None):
        if (getattr(args, "place", None), getattr(args, "clue", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, clue = rng.choice(combos)
    if getattr(args, "place", None):
        place = getattr(args, "place", None)
    if getattr(args, "clue", None):
        clue = getattr(args, "clue", None)

    hero_name, hero_gender, hero_trait = rng.choice(HEROES)
    if getattr(args, "name", None):
        hero_name = getattr(args, "name", None)
    if getattr(args, "gender", None):
        hero_gender = getattr(args, "gender", None)
    if getattr(args, "trait", None):
        hero_trait = getattr(args, "trait", None)

    return StoryParams(
        place=place,
        clue=clue,
        hero_name=hero_name,
        hero_type=hero_gender,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), params.hero_name, params.hero_type, params.hero_trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind}, label={e.label}, type={e.type}, held_by={e.held_by}, owner={e.owner}")
        if e.meters:
            lines.append(f"  meters={e.meters}")
        if e.memes:
            lines.append(f"  memes={e.memes}")
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, clue in combos:
            print(f"  {place:10} {clue}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, clue in valid_combos():
            params = StoryParams(place=place, clue=clue, hero_name="Nova", hero_type="girl", hero_trait="bold")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
