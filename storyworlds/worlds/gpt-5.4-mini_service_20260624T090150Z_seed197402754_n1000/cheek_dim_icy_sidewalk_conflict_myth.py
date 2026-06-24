#!/usr/bin/env python3
"""
A mythic tiny-story world about a child-sized conflict on an icy sidewalk.
The seed image is a cheek-dim, shy kind of myth: a small hero, a hard path,
a worried helper, a proud refusal, and a wiser turn that changes the ending.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    name: str = ""
    title: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    label: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "sister"}
        male = {"boy", "father", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the icy sidewalk"
    cold: bool = True
    affords: set[str] = field(default_factory=set)
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
class Omen:
    id: str
    label: str
    phrase: str
    risk: str
    remedy: str
    tags: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    phrase: str
    protects: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "icy_sidewalk": Setting(place="the icy sidewalk", cold=True, affords={"slip", "march"}),
}

OMENS = {
    "ice": Omen(
        id="ice",
        label="ice",
        phrase="the icy sidewalk",
        risk="slip",
        remedy="grip",
        tags={"cold", "slip", "icy"},
    ),
    "frost": Omen(
        id="frost",
        label="frost",
        phrase="a silver frost",
        risk="cold",
        remedy="warmth",
        tags={"cold", "icy"},
    ),
}

CHARMS = [
    Charm(
        id="boots",
        label="winter boots",
        phrase="winter boots with rough soles",
        protects={"slip"},
        prep="put on winter boots first",
        tail="went back for the winter boots",
    ),
    Charm(
        id="cloak",
        label="a wool cloak",
        phrase="a wool cloak",
        protects={"cold"},
        prep="wrap a wool cloak around the shoulders",
        tail="found the wool cloak",
    ),
]

TRAITS = ["cheek-dim", "quiet", "brave", "curious", "small", "thoughtful"]
NAMES = ["Mara", "Ivo", "Nia", "Pere", "Lina", "Oren", "Suri", "Kellan"]
PARENTS = ["mother", "father", "aunt", "uncle", "grandmother", "guardian"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    trait: str
    omen: str
    seed: Optional[int] = None


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


def omen_is_risky(omen: Omen, setting: Setting) -> bool:
    return setting.cold and omen.id in OMENS


def select_charm(omen: Omen) -> Optional[Charm]:
    for charm in CHARMS:
        if omen.remedy in charm.protects:
            return charm
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for omen_id, omen in OMENS.items():
            if omen_is_risky(omen, setting) and select_charm(omen):
                out.append((place, omen_id))
    return out


# ---------------------------------------------------------------------------
# Mythic narration helpers
# ---------------------------------------------------------------------------

def intro_line(hero: Entity, parent: Entity) -> str:
    return (
        f"Long ago, on the {hero.title}, there lived a {hero.memes.get('trait', 'small')} "
        f"{hero.type} named {hero.name}, and {parent.pronoun('possessive')} {parent.type} watched "
        f"over {hero.pronoun('object')} with a gentle eye."
    )


def omen_line(omen: Omen) -> str:
    return f"The air carried {omen.phrase}, and the ground promised a hard lesson."


def predict_trouble(world: World, hero: Entity, omen: Omen) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters[omen.risk] = sim.get(hero.id).meters.get(omen.risk, 0) + 1
    if omen.risk == "slip":
        return {"slip": True, "cold": False}
    return {"slip": False, "cold": True}


def do_step(world: World, hero: Entity, omen: Omen) -> None:
    hero.meters[omen.risk] = hero.meters.get(omen.risk, 0) + 1
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1


def warn(world: World, parent: Entity, hero: Entity, omen: Omen) -> bool:
    pred = predict_trouble(world, hero, omen)
    if not pred["slip"]:
        return False
    world.facts["predicted"] = omen.risk
    world.say(
        f'"Careful," {parent.name} said. "This road is {omen.label}-slick, and one careless step could bring you down."'
    )
    return True


def conflict(world: World, hero: Entity, parent: Entity, omen: Omen) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    world.say(
        f"{hero.name} lifted a chin and wanted to prove {hero.pronoun('object')} could pass the trial alone."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tried to march on, but the {parent.type} caught up beside {hero.pronoun('object')}."
    )
    world.say(
        f"That made a small conflict, sharp as a pebble under winter shoes."
    )


def offer_charm(world: World, parent: Entity, hero: Entity, omen: Omen) -> Optional[Charm]:
    charm = select_charm(omen)
    if charm is None:
        return None
    world.say(
        f"Then {parent.name} smiled and said, \"Let us take the safer path: {charm.prep}.\""
    )
    return charm


def accept(world: World, hero: Entity, parent: Entity, omen: Omen, charm: Charm) -> None:
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.name}'s face softened, almost cheek-dim in the winter light, and {hero.pronoun()} nodded."
    )
    world.say(
        f"They {charm.tail}. Soon {hero.name} was crossing the {world.setting.place} with steady feet, "
        f"the cold wind biting, yet no fall came."
    )


def tell(setting: Setting, omen: Omen, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        name=hero_name,
        title=setting.place,
        meters={},
        memes={"trait": trait, "curiosity": 1},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        name=parent_type,
        title=setting.place,
    ))

    world.say(
        f"Long ago, on {setting.place}, there was a {trait} {hero_type} named {hero_name}."
    )
    world.say(
        f"{hero_name} loved the wind and the bright hush of winter, but most of all {hero.pronoun()} loved moving forward."
    )
    world.say(omen_line(omen))

    world.para()
    world.say(
        f"One day, {hero_name} and {parent.name} stood at the edge of the {setting.place}."
    )
    warn(world, parent, hero, omen)
    conflict(world, hero, parent, omen)

    world.para()
    charm = offer_charm(world, parent, hero, omen)
    if charm is not None:
        do_step(world, hero, omen)
        accept(world, hero, parent, omen, charm)
    else:
        world.say(
            f"At last they turned away from the hard road, for no charm in the house could truly answer the omen."
        )

    world.facts.update(
        hero=hero,
        parent=parent,
        omen=omen,
        charm=charm,
        resolved=charm is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    omen = _safe_fact(world, f, "omen")
    return [
        f'Write a short myth for a child about a "{omen.label}" day on {world.setting.place}.',
        f"Tell a gentle story where {hero.name} faces a small conflict on the icy sidewalk and learns a wiser way forward.",
        f'Write a myth-like tale that includes the word "cheek-dim" and ends with a safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    omen = _safe_fact(world, f, "omen")
    charm = _safe_fact(world, f, "charm")

    qs = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.name}, a {hero.memes.get('trait', 'small')} {hero.type} walking on {world.setting.place} with {parent.name}.",
        ),
        QAItem(
            question=f"What made the sidewalk feel dangerous?",
            answer=f"The sidewalk felt dangerous because {omen.phrase} made it easy to slip.",
        ),
        QAItem(
            question=f"What did {parent.name} suggest to help?",
            answer=(
                f"{parent.name} suggested a safer choice: "
                f"{charm.prep if charm else 'turning back for a safer path'}."
            ),
        ),
    ]
    if f.get("resolved"):
        qs.append(
            QAItem(
                question=f"How did the story end?",
                answer=(
                    f"It ended with {hero.name} choosing the safer way, so the conflict faded and {hero.name} crossed the icy sidewalk without falling."
                ),
            )
        )
    else:
        qs.append(
            QAItem(
                question=f"How did the story end?",
                answer="It ended with the danger still ahead, because the household had no charm that truly matched the omen.",
            )
        )
    return qs


WORLD_KNOWLEDGE = {
    "ice": [
        QAItem(
            question="What is ice?",
            answer="Ice is frozen water. It can be very slippery under shoes and boots.",
        )
    ],
    "winter boots": [
        QAItem(
            question="What are winter boots for?",
            answer="Winter boots help keep feet warm and give them more grip on slippery ground.",
        )
    ],
    "wool cloak": [
        QAItem(
            question="What does a wool cloak do?",
            answer="A wool cloak helps hold in warmth when the air is cold and sharp.",
        )
    ],
    "conflict": [
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes the characters choose what to do next.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["omen"].tags)
    if world.facts.get("charm"):
        tags.add(world.facts["charm"].label)
    out: list[QAItem] = []
    for key, items in WORLD_KNOWLEDGE.items():
        if key in tags or key == "conflict":
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(icy_sidewalk).
setting(icy_sidewalk).
cold(icy_sidewalk).

omen(ice).
omen(frost).
risky(icy_sidewalk, ice).
risky(icy_sidewalk, frost).

charm(boots).
charm(cloak).

protects(boots, slip).
protects(cloak, cold).

compatible(P, O) :- risky(P, O), omen(O), setting(P), charm(C), protects(C, slip).
compatible(P, O) :- risky(P, O), omen(O), setting(P), charm(C), protects(C, cold).

#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "icy_sidewalk"), asp.fact("setting", "icy_sidewalk"), asp.fact("cold", "icy_sidewalk")]
    for oid, omen in OMENS.items():
        lines.append(asp.fact("omen", oid))
        if omen.risk == "slip":
            lines.append(asp.fact("risky", "icy_sidewalk", oid))
        if omen.risk == "cold":
            lines.append(asp.fact("risky", "icy_sidewalk", oid))
    for charm in CHARMS:
        lines.append(asp.fact("charm", charm.id))
        for p in charm.protects:
            lines.append(asp.fact("protects", charm.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" python-only:", sorted(py - cl))
    print(" asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: cheek-dim conflict on an icy sidewalk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "omen", None) and getattr(args, "omen", None) not in OMENS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "omen", None):
        combos = [c for c in combos if c[1] == getattr(args, "omen", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, omen = rng.choice(list(combos))
    return StoryParams(
        place=place,
        hero_name=getattr(args, "name", None) or rng.choice(NAMES),
        hero_type=getattr(args, "gender", None) or rng.choice(["girl", "boy"]),
        parent_type=getattr(args, "parent", None) or rng.choice(PARENTS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
        omen=omen,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(OMENS, params.omen), params.hero_name, params.hero_type, params.parent_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
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


CURATED = [
    StoryParams(place="icy_sidewalk", hero_name="Mara", hero_type="girl", parent_type="mother", trait="cheek-dim", omen="ice"),
    StoryParams(place="icy_sidewalk", hero_name="Ivo", hero_type="boy", parent_type="father", trait="curious", omen="frost"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, omen in combos:
            print(f"  {place} {omen}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
