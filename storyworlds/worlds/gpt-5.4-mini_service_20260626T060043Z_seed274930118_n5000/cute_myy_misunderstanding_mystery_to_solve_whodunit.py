#!/usr/bin/env python3
"""
storyworlds/worlds/cute_myy_misunderstanding_mystery_to_solve_whodunit.py
========================================================================

A small child-friendly whodunit storyworld about a cute misunderstanding
that turns into a mystery to solve.

Premise:
- A child notices something missing or "wrong."
- The first explanation is a misunderstanding.
- Clues accumulate in the world state.
- A gentle detective turn reveals who really moved the object and why.
- The ending image proves the truth and the problem is repaired.

This world keeps the prose concrete, state-driven, and lightly mystery-flavored
without becoming scary or cynical.
"""

from __future__ import annotations

import argparse
import copy
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

TRUST_KEYS = {"trust", "worry", "curiosity", "relief", "guilt", "hope"}
PHYSICAL_KEYS = {"seen", "moved", "hidden", "touched", "dirty", "crumbs"}

NAMES = ["Mia", "Lily", "Noah", "Ben", "Ava", "Theo", "Nora", "Zoe", "Milo"]
NICKNAMES = ["cute", "myy", "tiny", "brave", "curious", "gentle", "sleepy"]
PLACES = ["the kitchen", "the hallway", "the playroom", "the garden shed", "the front step"]
TIMES = ["one morning", "one afternoon", "at twilight", "after lunch", "before bedtime"]


# ---------------------------------------------------------------------------
# Entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_in: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    detective: object | None = None
    helper: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
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
class Mystery:
    item: str
    clue_kind: str
    culprit: str
    reason: str
    place: str
    solution_item: str
    reveal_phrase: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting("the kitchen", {"crumbs", "hidden", "moved"}),
    "hallway": Setting("the hallway", {"moved", "hidden"}),
    "playroom": Setting("the playroom", {"moved", "hidden", "touched"}),
    "shed": Setting("the garden shed", {"hidden", "moved", "dirty"}),
    "step": Setting("the front step", {"moved", "hidden", "touched"}),
}

CHARACTER_TYPES = {
    "child": "girl",
    "kid": "boy",
    "parent": "mother",
    "helper": "cat",
    "pet": "cat",
}

MYSTERIES = {
    "cookie": Mystery(
        item="cookie",
        clue_kind="crumbs",
        culprit="helper",
        reason="was carrying it to a safer place",
        place="behind the tea tin",
        solution_item="crumbs",
        reveal_phrase="the cookie was not stolen at all",
    ),
    "key": Mystery(
        item="key",
        clue_kind="moved",
        culprit="parent",
        reason="needed it for the shed",
        place="on the hook by the door",
        solution_item="hook",
        reveal_phrase="the key had been moved on purpose",
    ),
    "toy": Mystery(
        item="toy train",
        clue_kind="touched",
        culprit="child",
        reason="wanted to fix the wheels",
        place="under the cushion",
        solution_item="cloth",
        reveal_phrase="the toy had only been tucked away for a quick repair",
    ),
}

LOCATIONS = ["table", "shelf", "basket", "drawer", "cushion", "hook"]
TRAITS = ["cute", "myy", "curious", "gentle", "careful", "brave"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    role: str
    helper_name: str
    helper_role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------
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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")  # type: ignore[assignment]
    culprit: Entity = world.get(mystery.culprit_id)  # type: ignore[index]
    item: Entity = world.get(mystery.item_id)  # type: ignore[index]
    clue_sig = ("clue", mystery.item, mystery.clue_kind)
    if clue_sig in world.fired:
        return []
    if mystery.clue_kind == "crumbs":
        if item.meters.get("crumbs", 0.0) >= THRESHOLD:
            world.fired.add(clue_sig)
            out.append(f"There were tiny crumbs near the place where {item.label} had been.")
    elif mystery.clue_kind == "moved":
        if item.meters.get("moved", 0.0) >= THRESHOLD:
            world.fired.add(clue_sig)
            out.append(f"A small trail showed that {item.label} had been moved carefully.")
    elif mystery.clue_kind == "touched":
        if item.meters.get("touched", 0.0) >= THRESHOLD:
            world.fired.add(clue_sig)
            out.append(f"The surface nearby had little smudges, as if someone had touched it in a hurry.")
    if culprit.memes.get("guilt", 0.0) >= THRESHOLD:
        out.append(f"{culprit.label} looked uneasy, but not because of a bad deed.")
    return out


def _r_reveal(world: World) -> list[str]:
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")  # type: ignore[assignment]
    detective: Entity = world.get(world.facts["detective_id"])  # type: ignore[index]
    culprit: Entity = world.get(mystery.culprit_id)  # type: ignore[index]
    item: Entity = world.get(mystery.item_id)  # type: ignore[index]
    sig = ("reveal", mystery.item)
    if sig in world.fired:
        return []
    clues = item.meters.get(mystery.clue_kind, 0.0) >= THRESHOLD or item.meters.get("moved", 0.0) >= THRESHOLD or item.meters.get("touched", 0.0) >= THRESHOLD
    if clues and detective.memes.get("curiosity", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
        return [f"{mystery.reveal_phrase}, and {culprit.label} had a simple reason."]
    return []


RULES = [
    ("clue", _r_clue),
    ("reveal", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def choice(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def actor_desc(entity: Entity) -> str:
    trait = next((t for t in entity.traits if t in {"cute", "myy"}), entity.traits[0] if entity.traits else entity.type)
    return f"{trait} {entity.type}" if trait else entity.type


def inspect(world: World, detective: Entity, item: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    world.say(f"{detective.label} looked very closely at {item.label}.")


def misunderstand(world: World, detective: Entity, suspect: Entity, item: Entity) -> None:
    detective.memes["worry"] = detective.memes.get("worry", 0.0) + 1
    suspect.memes["guilt"] = suspect.memes.get("guilt", 0.0) + 1
    world.say(f"At first, {detective.label} thought {suspect.label} had done something wrong.")
    world.say(f'"Did you take {item.label}?" {detective.label} asked softly.')


def explain(world: World, culprit: Entity, item: Entity, reason: str) -> None:
    culprit.memes["hope"] = culprit.memes.get("hope", 0.0) + 1
    world.say(f"But {culprit.label} shook {culprit.pronoun('possessive')} head.")
    world.say(f'"I moved {item.label} because {reason}," {culprit.label} said.')


def end_image(world: World, item: Entity, culprit: Entity, detective: Entity) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
    world.say(f"In the end, {item.label} was back where it belonged, and everyone knew the honest answer.")
    world.say(f"{detective.label} smiled at {culprit.label}, and the little mystery felt solved at last.")


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery_key: str, name: str, role: str, helper_name: str, helper_role: str, trait: str) -> World:
    rng = random.Random()
    world = World(setting)

    mystery = _safe_lookup(MYSTERIES, mystery_key)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=CHARACTER_TYPES.get(role, "girl"),
        label=name,
        traits=[trait, "little"],
        meters={},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=CHARACTER_TYPES.get(helper_role, "cat"),
        label=helper_name,
        traits=["soft", "quiet"],
        meters={},
        memes={"hope": 0.0, "guilt": 0.0},
    ))
    item = world.add(Entity(
        id="item",
        type=mystery.item,
        label=mystery.item,
        kind="thing",
        meters={mystery.clue_kind: 0.0, "moved": 0.0, "touched": 0.0, "crumbs": 0.0},
        memes={},
    ))
    culprit = helper if mystery.culprit == "helper" else detective
    mystery_obj = mystery
    world.facts["mystery"] = mystery_obj
    world.facts["detective_id"] = detective.id
    world.facts["culprit_id"] = culprit.id
    world.facts["item_id"] = item.id

    # Setup
    world.say(f"{detective.label} was a {actor_desc(detective)} who liked solving small puzzles.")
    world.say(f"That day, {detective.label} noticed that {item.label} was missing from {setting.place}.")
    world.say(f"The missing thing made the room feel oddly quiet.")
    world.para()

    # Misunderstanding
    misunderstand(world, detective, culprit, item)
    if mystery.culprit == "helper":
        item.meters[mystery.clue_kind] += 1
        item.meters["moved"] += 1
    elif mystery.culprit == "child":
        item.meters["touched"] += 1
    else:
        item.meters["moved"] += 1
    inspect(world, detective, item)
    propagate(world, narrate=True)
    world.para()

    # Turn
    explain(world, culprit, item, mystery.reason)
    world.say(f"{detective.label} listened carefully and looked at the little clue again.")
    if mystery.clue_kind == "crumbs":
        world.say(f"The crumbs pointed to a harmless snack-and-hide sort of secret.")
    elif mystery.clue_kind == "moved":
        world.say(f"The neat trail showed that the item had not vanished at all.")
    else:
        world.say(f"The smudges made the story feel less like trouble and more like a quick fix.")
    propagate(world, narrate=True)
    world.para()

    # Resolution
    end_image(world, item, culprit, detective)
    world.say(f'It was a {trait} little mystery, but the answer was simple in the end.')

    world.facts.update(
        detective=detective,
        culprit=culprit,
        item=item,
        setting=setting,
        mystery=mystery_obj,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% If the item is moved, touched, or crumbed, there is evidence.
evidence(I, moved) :- moved(I).
evidence(I, touched) :- touched(I).
evidence(I, crumbs) :- crumbs(I).

% A misunderstanding happens when the detective sees evidence but does not yet
% know the reason.
misunderstanding(D, I) :- detective(D), item(I), evidence(I, _), not explained(I).

% The mystery is solved when the clue and the reason both exist.
solved(I) :- item(I), evidence(I, K), clue_kind(I, K), reasoned(I).

#show misunderstanding/2.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("item", mid))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        lines.append(asp.fact("reasoned", mid))
        lines.append(asp.fact("moved", mid))
        if m.clue_kind == "crumbs":
            lines.append(asp.fact("crumbs", mid))
        elif m.clue_kind == "touched":
            lines.append(asp.fact("touched", mid))
    lines.append(asp.fact("detective", "detective"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show solved/1."))
    misunderstandings = asp.atoms(model, "misunderstanding")
    solved = asp.atoms(model, "solved")
    ok = bool(misunderstandings) and bool(solved)
    if ok:
        print("OK: ASP model produces misunderstanding and solved signals.")
        return 0
    print("Mismatch: ASP model did not produce expected signals.")
    return 1


# ---------------------------------------------------------------------------
# Validation / resolution
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            combos.append((place, mystery))
    return combos


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the selected setting and mystery cannot make a clear clue-and-reveal chain: {place}, {mystery}.)"


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    role: str
    helper_name: str
    helper_role: str
    trait: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cute whodunit storyworld with a misunderstanding mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["child", "kid"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-role", choices=["helper", "pet"])
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
    setting = getattr(args, "setting", None) or choice(rng, list(SETTINGS.keys()))
    mystery = getattr(args, "mystery", None) or choice(rng, list(MYSTERIES.keys()))
    if (setting, mystery) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or choice(rng, NAMES)
    role = getattr(args, "role", None) or "child"
    helper_name = getattr(args, "helper_name", None) or choice(rng, ["Miso", "Pip", "Mimi", "Nico", "Poppy"])
    helper_role = getattr(args, "helper_role", None) or "helper"
    trait = getattr(args, "trait", None) or choice(rng, ["cute", "myy", "curious", "gentle"])
    return StoryParams(setting, mystery, name, role, helper_name, helper_role, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = _safe_fact(world, f, "mystery")  # type: ignore[assignment]
    detective: Entity = _safe_fact(world, f, "detective")  # type: ignore[assignment]
    culprit: Entity = _safe_fact(world, f, "culprit")  # type: ignore[assignment]
    return [
        f'Write a cute whodunit about {detective.label} and a small misunderstanding involving {m.item}.',
        f"Tell a child-friendly mystery where {detective.label} thinks {culprit.label} caused a problem, but the clue is harmless.",
        f'Write a short story with the words "cute" and "myy" where a mystery gets solved by looking closely at a clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")  # type: ignore[assignment]
    culprit: Entity = _safe_fact(world, f, "culprit")  # type: ignore[assignment]
    item: Entity = _safe_fact(world, f, "item")  # type: ignore[assignment]
    mystery: Mystery = _safe_fact(world, f, "mystery")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was the mystery in {setting.place}?",
            answer=f"The mystery was that {item.label} seemed to be missing, which made {detective.label} worry for a moment.",
        ),
        QAItem(
            question=f"Why did {detective.label} first misunderstand {culprit.label}?",
            answer=f"{detective.label} saw a clue near {item.label} and thought {culprit.label} had done something wrong before the full reason was known.",
        ),
        QAItem(
            question=f"What solved the mystery of {item.label}?",
            answer=f"The small clue, plus {culprit.label}'s kind explanation that {mystery.reason}, solved it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where someone tries to figure out who moved something, made a mess, or caused a problem.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first and then learns the true reason later.",
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer="Detectives look at clues because little details can help them understand what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id} ({e.type}): {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "cookie", "Mia", "child", "Miso", "helper", "cute"),
    StoryParams("playroom", "toy", "Noah", "kid", "Pip", "helper", "myy"),
    StoryParams("hallway", "key", "Ava", "child", "Poppy", "helper", "curious"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show solved/1."))
    return sorted(set(asp.atoms(model, "misunderstanding") + asp.atoms(model, "solved")))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.mystery, params.name, params.role, params.helper_name, params.helper_role, params.trait)
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
        print(asp_program("#show misunderstanding/2.\n#show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show misunderstanding/2.\n#show solved/1."))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
