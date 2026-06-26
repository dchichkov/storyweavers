#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/bandit_theme_raffia_moral_value_ghost_story.py
=====================================================================================================================

A standalone *story world* sketch in the style of a gentle Ghost Story, built
around a tiny moral lesson.  The hero of the tale is a young sibling of a
traveling storyteller (the Bard) who keeps a small museum of tucked-away
objects.  A masked bandit has been sneaking into the village by night, and the
hero must learn that a "Ghost Story" is really a way of teaching a moral value,
not a way of frightening people.

The drama is shaped by four pillars:

    Setting     - the Bard's little open-air museum, full of small themed cases
                  (a "theme room"), in the village square.
    Theme       - the moral value picked from a small registry (honesty, kind-
                  ness, courage, sharing, patience).  Each theme gets its own
                  moral message and the matching "moral tag" used by the story.
    Raffia      - the twine the hero uses to bind the broken lock on the
                  bandit-snare.  Raffia is a coarse natural fiber, easy for a
                  child to tie and gentle on wood.  Every story includes at
                  least one tactile "raffia" beat (tying, untying, holding).
    Bandit      - the masked stranger in a tattered scarf whose two motives are
                  always a *prize* (something fragile the hero loves) and a
                  *demand* (a small task or lesson the bandit insists on).

The simulated world is driven by typed entities (meters, memeplex), a forward-
chaining rule engine, and a screenplay of named beats.  All prose is generated
from world state, not from frozen templates.

The script also carries the standard storyworld surface:
    build_parser / resolve_params / generate / emit / main
plus the optional clingo (ASP) twin, gated behind `--verify` / `--show-asp`.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# A small set of "moral meters" that propagate when the child is mean to others
# (the bandit keeps a "moral ledger" of what they have done).  These are the
# only emotional accumulators the bandit reacts to.
MORAL_KINDS = {"honesty", "kindness", "courage", "sharing", "patience"}


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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    fragile: bool = False          # the prize is delicate and must be respected
    worn_by: Optional[str] = None
    bound_with: Optional[str] = None   # what kind of cord binds/holds the thing
    plural: bool = False
    # Two numeric dimensions, treated uniformly.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    bandit: object | None = None
    bard: object | None = None
    case: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "bard", "storyteller"}
        male = {"boy", "father", "dad", "man", "bandit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad",
                "storyteller": "the Bard", "bandit": "the masked one",
                "bard": "the Bard"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    place: str = "the village square"
    indoor: bool = False
    night: bool = False
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
class Theme:
    """A moral value the Ghost Story teaches; bandit uses it as their 'demand'."""
    id: str
    label: str
    keyword: str                # noun: "honesty", "kindness", ...
    moral: str                  # the line of moral the bandit insists on
    demand: str                 # the small task the bandit assigns
    good: str                   # what the hero does well (the moral good)
    bad: str                    # what the bandit wants the hero NOT to do
    tags: set[str] = field(default_factory=set)
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
class Prize:
    """The fragile, much-loved object the hero guards in the museum."""
    label: str
    phrase: str
    type: str
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
class Case:
    """A themed display case in the little open-air museum."""
    id: str
    theme: str                  # what theme room this case belongs to
    label: str
    phrase: str
    fragile: bool = True


# ---------------------------------------------------------------------------
# World: entity store + narration history
# ---------------------------------------------------------------------------
    fits: set[str] = field(default_factory=set)
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

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_bandit_watches(world: World) -> list[str]:
    """When the hero is greedy with the prize, the bandit notices and grows bold."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("greed", 0.0) < THRESHOLD:
            continue
        sig = ("watch", "bandit", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        bandit = world.get("Bandit")
        bandit.memes["boldness"] += 1
        out.append("__bandit_bold__")
    return out


def _r_bandit_steals(world: World) -> list[str]:
    """When the bandit is bold and the lock is still bound with raffia, the
    bandit slips in and snatches the fragile prize."""
    out: list[str] = []
    bandit = world.entities.get("Bandit")
    prize = world.entities.get("prize")
    case = world.entities.get("case")
    if not (bandit and prize and case):
        return out
    if bandit.memes.get("boldness", 0.0) < THRESHOLD:
        return out
    if case.memes.get("raffia_lock", 0.0) < THRESHOLD:
        return out
    sig = ("steal", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.memes["snatched"] += 1
    case.memes["broken_lock"] += 1
    out.append("__snatch__")
    return out


def _r_moral_drift(world: World) -> list[str]:
    """When the hero is rude to the bandit, the moral ledger loses points."""
    out: list[str] = []
    hero = world.entities.get("hero")
    bandit = world.entities.get("Bandit")
    if not (hero and bandit):
        return out
    if hero.memes.get("rudeness", 0.0) < THRESHOLD:
        return out
    for k in MORAL_KINDS:
        if hero.memes.get(k, 0.0) > 0.0:
            sig = ("drift", k, hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            hero.memes[k] = max(0.0, hero.memes[k] - 0.5)
            out.append("__moral_drift__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bandit_watches", tag="social", apply=_r_bandit_watches),
    Rule(name="bandit_steals", tag="physical", apply=_r_bandit_steals),
    Rule(name="moral_drift", tag="moral", apply=_r_moral_drift),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def theme_matches_case(theme: Theme, case: Case) -> bool:
    """The displayed case must actually match the moral theme of the story."""
    return theme.id == case.theme


def select_case(theme: Theme) -> Optional[Case]:
    for c in CASES:
        if theme_matches_case(theme, c):
            return c
    return None


def prize_is_fragile(prize: Prize) -> bool:
    return prize.type in {"mask", "lantern", "spool", "cup", "vase", "bell"}


def prize_ok_for_case(prize: Prize, case: Case) -> bool:
    """A reasonable prize must be both fragile and small enough to fit in the
    theme room's display case."""
    if not prize_is_fragile(prize):
        return False
    if prize.type not in case.fits:
        return False
    return True


# ---------------------------------------------------------------------------
# Verbs (state mutators + narration)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"{hero.id} was a {desc} who helped {hero.pronoun('possessive')} sibling "
        f"the Bard keep the open-air museum tidy."
    )


def bard_opens(world: World, bard: Entity, theme: Theme, case: Entity) -> None:
    world.say(
        f"That evening, the Bard lit the museum lanterns and said, \"Today we "
        f"open the {theme.label} room, and the case inside must be bound with "
        f"the soft raffia twine, the way a careful story is.\""
    )
    world.say(f"Inside the glass case, the {case.label} waited in its cradle.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"Beside the case sat a small {prize.label} that {hero.id} loved very "
        f"much, and every morning {hero.pronoun()} checked it for chips or dust."
    )


def binds_with_raffia(world: World, hero: Entity, case: Entity) -> None:
    case.memes["raffia_lock"] += 1
    world.say(
        f"{hero.id} wound a length of pale raffia around the case latch and "
        f"tied a careful square knot, the kind that holds even in a wind."
    )


def night_falls(world: World) -> None:
    world.setting.night = True
    world.say(
        "When the museum closed, the lanterns grew small and the village went "
        "quiet, the way a page turns before the next chapter."
    )


def bandit_appears(world: World, hero: Entity) -> None:
    bandit = world.get("Bandit")
    bandit.memes["arrived"] += 1
    world.say(
        f"From the dark between the stalls stepped a masked bandit in a "
        f"tattered scarf, moving as soft as a turned page."
    )
    world.say(
        f'"{hero.id}," the bandit whispered, "I know what you love, and I know '
        f'the moral your sibling keeps on a card inside the case."'
    )


def bandit_offers(world: World, hero: Entity, theme: Theme) -> None:
    bandit = world.get("Bandit")
    world.say(
        f'The bandit held up a coin and said, "I will trade one {theme.keyword} '
        f'lesson for the thing you love. {theme.demand.capitalize()}, and the '
        f'{theme.label.lower()} card stays yours. Refuse, and I will slip in '
        f'when the raffia loosens."'
    )


def hero_weighs(world: World, hero: Entity, theme: Theme) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} clutched the small {world.get('prize').label} and felt the "
        f"pull of {theme.bad} tugging at {hero.pronoun('object')}."
    )


def hero_rude(world: World, hero: Entity, theme: Theme) -> None:
    hero.memes["rudeness"] += 1
    hero.memes["greed"] += 1
    world.say(
        f'"No," {hero.id} said sharply, "go away, you masked thief!"'
    )
    world.say(
        f"That was {theme.bad}, and the bandit only smiled, because {theme.bad} "
        f"was exactly what the moral ledger did not want to see."
    )


def raffia_test(world: World, hero: Entity) -> None:
    """The hero checks the raffia knot -- if the case is still bound, the
    bandit cannot slip in."""
    case = world.get("case")
    world.say(
        f"{hero.id} crouched by the case and tugged the raffia knot, the way "
        f"{hero.pronoun()} had been taught."
    )
    if case.memes["raffia_lock"] >= THRESHOLD:
        world.say(
            f"The knot held. The pale raffia did not slip, and the case sat "
            f"still as a closed book."
        )
        propagate(world, narrate=False)            # no snatch fires


def bandit_snatches(world: World, hero: Entity, theme: Theme) -> None:
    """If the moral ledger is low, the bandit slips in (causal rule fires)."""
    propagate(world, narrate=False)
    prize = world.get("prize")
    if prize.memes.get("snatched", 0.0) >= THRESHOLD:
        world.say(
            f"With a soft scrape of cloth, the bandit slipped the latch and "
            f"scooped the {prize.label} into the scarf."
        )
        world.say(
            f'"{hero.id}," the bandit whispered, "the {prize.label} is mine '
            f'until the moral card is earned. {theme.demand.capitalize()}, '
            f'and I will set it back on its cradle before the dawn."'
        )


def hero_thinks(world: World, hero: Entity, theme: Theme) -> None:
    hero.memes["thought"] += 1
    world.say(
        f"{hero.id} sat back on {hero.pronoun('possessive')} heels and thought "
        f"of what the Bard would say: a Ghost Story is not a threat, it is a "
        f"moral value wearing a sheet."
    )


def hero_learns(world: World, hero: Entity, theme: Theme) -> None:
    """The hero actually does the moral demand, earning the moral and the prize."""
    hero.memes[theme.id] += 1
    hero.memes["greed"] = 0.0
    hero.memes["rudeness"] = 0.0
    world.say(
        f"So {hero.id} did the thing the moral demanded: {theme.demand}."
    )
    world.say(
        f"That was {theme.good}, and the bandit pulled the mask down a finger "
        f"and bowed, the way a careful villain bows at the end of a tale."
    )


def bandit_returns(world: World, hero: Entity, prize: Entity) -> None:
    bandit = world.get("Bandit")
    prize.memes["snatched"] = 0.0
    world.say(
        f'The bandit set the {prize.label} back on its cradle, brushed off a '
        f'speck of dust with a careful thumb, and stepped into the dark again.'
    )


def dawn(world: World, hero: Entity, bard: Entity, theme: Theme) -> None:
    world.setting.night = False
    world.say(
        f"At dawn, the Bard found {hero.id} sitting beside the case, smiling "
        f"in a way that meant a story had been learned."
    )
    world.say(
        f'"{hero.id}," the Bard said, "what did the Ghost Story teach?"'
    )
    world.say(
        f'"{theme.label}," {hero.id} answered, "because a Ghost Story is just a '
        f'moral value wearing a sheet, and the sheet slips off when the moral '
        f'is kept."'
    )
    world.say(
        f"The Bard nodded, and the pale raffia knot still held in the morning "
        f"light."
    )


def teller_moral(world: World, theme: Theme) -> None:
    """Final caption-style sentence that names the moral in a single line."""
    world.say(f"Moral of the tale: {theme.moral}")


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, theme: Theme, prize_cfg: Prize,
         hero_name: str = "Mira", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    case_def = select_case(theme)
    if case_def is None:
        pass

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["careful", "shy"]),
    ))
    bard = world.add(Entity(id="Bard", kind="character", type="bard", label="the Bard"))
    bandit = world.add(Entity(id="Bandit", kind="character", type="bandit", label="the bandit"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, fragile=True, plural=prize_cfg.plural,
    ))
    case = world.add(Entity(
        id="case", type="case", label=case_def.label, phrase=case_def.phrase,
        owner="museum", fragile=True,
    ))

    # Act 1 -- the museum and the prize
    introduce(world, hero)
    bard_opens(world, bard, theme, case)
    loves_prize(world, hero, prize)
    binds_with_raffia(world, hero, case)

    # Act 2 -- the bandit appears, the moral is weighed
    world.para()
    night_falls(world)
    bandit_appears(world, hero)
    bandit_offers(world, hero, theme)
    hero_weighs(world, hero, theme)

    # If the hero is rude, the bandit slips in; if the hero is gentle, the
    # raffia lock holds and the bandit never gets a grip.
    if theme.id == "honesty":
        # honesty -> do not lie to the bandit
        hero_rude(world, hero, theme)
        raffia_test(world, hero)
        bandit_snatches(world, hero, theme)
    elif theme.id == "kindness":
        hero_rude(world, hero, theme)
        raffia_test(world, hero)
        bandit_snatches(world, hero, theme)
    elif theme.id == "courage":
        # courage -> do not run away
        hero_rude(world, hero, theme)
        raffia_test(world, hero)
        bandit_snatches(world, hero, theme)
    elif theme.id == "sharing":
        hero_rude(world, hero, theme)
        raffia_test(world, hero)
        bandit_snatches(world, hero, theme)
    elif theme.id == "patience":
        hero_rude(world, hero, theme)
        raffia_test(world, hero)
        bandit_snatches(world, hero, theme)

    # Act 3 -- the moral is learned, the bandit returns the prize, dawn
    world.para()
    hero_thinks(world, hero, theme)
    hero_learns(world, hero, theme)
    bandit_returns(world, hero, prize)
    dawn(world, hero, bard, theme)
    teller_moral(world, theme)

    world.facts.update(
        hero=hero, bard=bard, bandit=bandit, prize=prize, prize_cfg=prize_cfg,
        case=case, case_def=case_def, theme=theme, setting=setting,
        conflict=bandit.memes.get("arrived", 0.0) >= THRESHOLD,
        resolved=prize.memes.get("snatched", 0.0) < THRESHOLD
        or hero.memes.get(theme.id, 0.0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries (content)
# ---------------------------------------------------------------------------
SETTINGS = {
    "square": Setting(place="the village square", indoor=False, night=False,
                      affords={"honesty", "kindness", "courage", "sharing", "patience"}),
    "lanes": Setting(place="the museum lanes", indoor=False, night=False,
                     affords={"honesty", "kindness", "courage", "sharing", "patience"}),
    "garden": Setting(place="the Bard's garden", indoor=False, night=False,
                      affords={"honesty", "kindness", "courage", "sharing", "patience"}),
}

THEMES = {
    "honesty": Theme(
        id="honesty", label="Honesty", keyword="honesty",
        moral="a truth told gently is the strongest knot there is.",
        demand="tell one true thing about how you feel before dawn",
        good="honesty, soft-spoken but brave",
        bad="a sharp lie",
        tags={"honesty"},
    ),
    "kindness": Theme(
        id="kindness", label="Kindness", keyword="kindness",
        moral="kindness is the raffia that holds a story together.",
        demand="share the second cup of tea with the bandit",
        good="kindness, offered even to a stranger",
        bad="a cruel word",
        tags={"kindness"},
    ),
    "courage": Theme(
        id="courage", label="Courage", keyword="courage",
        moral="courage is staying when the dark says to run.",
        demand="hold the lantern steady while the bandit crosses the lane",
        good="courage, steady and unhurried",
        bad="a fearful shout",
        tags={"courage"},
    ),
    "sharing": Theme(
        id="sharing", label="Sharing", keyword="sharing",
        moral="what you share twice is yours forever.",
        demand="lend the bandit's scarf to the small cousin for the night",
        good="sharing, even when the night is cold",
        bad="a greedy grip",
        tags={"sharing"},
    ),
    "patience": Theme(
        id="patience", label="Patience", keyword="patience",
        moral="patience ties a knot the storm cannot untie.",
        demand="untie and retie the raffia knot three times, slowly",
        good="patience, careful and unhurried",
        bad="a hurried hand",
        tags={"patience"},
    ),
}

PRIZES = {
    "mask": Prize(label="mask", phrase="a small wooden mask",
                  type="mask", plural=False),
    "lantern": Prize(label="lantern", phrase="a tiny paper lantern",
                     type="lantern", plural=False),
    "spool": Prize(label="spool", phrase="a silver story spool",
                   type="spool", plural=False),
    "cup": Prize(label="cup", phrase="a fragile china cup",
                 type="cup", plural=False),
    "vase": Prize(label="vase", phrase="a thin glass vase",
                  type="vase", plural=False),
    "bell": Prize(label="bell", phrase="a soft brass bell",
                  type="bell", plural=False),
}

# Each case lists which prize types fit; only fragile prizes fit at all.
CASES = [
    Case(id="honesty_case", theme="honesty", label="honesty case",
         phrase="a glass case lined with blue felt",
         fits={"mask", "lantern", "spool", "cup", "vase", "bell"}),
    Case(id="kindness_case", theme="kindness", label="kindness case",
         phrase="a glass case lined with green felt",
         fits={"mask", "lantern", "spool", "cup", "vase", "bell"}),
    Case(id="courage_case", theme="courage", label="courage case",
         phrase="a glass case lined with red felt",
         fits={"mask", "lantern", "spool", "cup", "vase", "bell"}),
    Case(id="sharing_case", theme="sharing", label="sharing case",
         phrase="a glass case lined with yellow felt",
         fits={"mask", "lantern", "spool", "cup", "vase", "bell"}),
    Case(id="patience_case", theme="patience", label="patience case",
         phrase="a glass case lined with brown felt",
         fits={"mask", "lantern", "spool", "cup", "vase", "bell"}),
]

GIRL_NAMES = ["Mira", "Lila", "Wren", "Anya", "Hester", "Rose", "Nell", "Iris"]
BOY_NAMES = ["Theo", "Joss", "Pip", "Rowan", "Oren", "Lyle", "Kit", "Bram"]
TRAITS = ["careful", "shy", "thoughtful", "earnest", "quiet", "watchful"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, theme, prize) triples that pass the reasonableness constraint."""
    combos = []
    for place, setting in SETTINGS.items():
        for tid in setting.affords:
            theme = _safe_lookup(THEMES, tid)
            case_def = select_case(theme)
            if case_def is None:
                continue
            for pid, prize in PRIZES.items():
                if prize_ok_for_case(prize, case_def):
                    combos.append((place, tid, pid))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    theme: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
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


KNOWLEDGE = {
    "honesty": [("What is honesty?",
                 "Honesty means telling the truth in a kind way, even when a "
                 "lie would be easier.")],
    "kindness": [("What is kindness?",
                  "Kindness is the gentle choice to help someone feel safe, "
                  "warm, and listened to.")],
    "courage": [("What is courage?",
                 "Courage is staying calm and doing the right thing when "
                 "something feels scary.")],
    "sharing": [("What does it mean to share?",
                 "Sharing is letting someone else use or enjoy a thing you "
                 "love, so you both have a turn.")],
    "patience": [("What is patience?",
                  "Patience is being willing to wait, take your time, and not "
                  "rush a careful thing.")],
    "bandit": [("Who is a bandit in a story?",
                "A bandit is a character who takes things that are not theirs, "
                "but in a gentle story the bandit is usually teaching a "
                "lesson, not really being mean.")],
    "raffia": [("What is raffia?",
                "Raffia is a coarse natural fiber that comes from palm leaves; "
                "it is soft on wood, easy to tie, and often used for crafts.")],
    "ghost_story": [("What is a Ghost Story?",
                     "A Ghost Story is a tale told to teach a moral value, "
                     "using a spooky frame to make the lesson stick.")],
    "museum": [("What is a museum?",
                "A museum is a place where careful people keep precious things "
                "so others can come and learn from them.")],
    "moral": [("What is a moral in a story?",
               "A moral is the small lesson the storyteller wants you to "
               "carry away after the story ends.")],
}
KNOWLEDGE_ORDER = ["ghost_story", "moral", "bandit", "raffia", "museum",
                   "honesty", "kindness", "courage", "sharing", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, theme, prize = f["hero"], f["theme"], f["prize_cfg"]
    place = world.setting.place
    return [
        f'Write a short story for a 5-to-8-year-old in the style of a gentle '
        f'Ghost Story that includes the words "bandit", "theme", and "raffia", '
        f'and ends with the moral "{theme.moral}"',
        f'Tell a story where a little {hero.type} named {hero.id} guards a '
        f'{prize.phrase} at {place}, meets a masked bandit at night, and '
        f'learns the moral value of {theme.label} through a small task.',
        f'Write a moral tale about {theme.keyword} in which a Ghost Story is '
        f'revealed to be a moral value wearing a sheet, and the soft '
        f'raffia knot is the symbol of the lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, bard, prize, theme = f["hero"], f["bard"], f["prize"], f["theme"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    case = _safe_fact(world, f, "case_def")
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who tends the {case.label} beside the small {prize.label} at "
                f"{place} in the gentle Ghost Story?"
            ),
            answer=(
                f"A little {trait} {hero.type} named {hero.id} helps {pos} "
                f"sibling the Bard keep the {case.label} tidy at {place}. "
                f"{hero.id} also keeps a careful eye on the {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What three things does the story say belong together at the "
                f"museum: the bandit, the theme, and which craft supply?"
            ),
            answer=(
                f"The story ties together the masked bandit, the moral theme of "
                f"{theme.label}, and the soft raffia twine that binds the "
                f"{case.label} latch."
            ),
        ),
        QAItem(
            question=(
                f"What moral value does the bandit ask the little "
                f"{hero.type} to keep, and why does the bandit bow at the end?"
            ),
            answer=(
                f"The bandit asks {hero.id} to keep the moral value of "
                f"{theme.label}. When {sub} does, the bandit pulls the mask "
                f"down and bows, because the moral is what the Ghost Story "
                f"was always teaching."
            ),
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=(
                f"How does the bandit win the {prize.label} from the {case.label} "
                f"before {trait} {hero.id} learns the moral of {theme.label}?"
            ),
            answer=(
                f"When {hero.id} is rude and grabs at the {prize.label}, the "
                f"moral ledger slips and the bandit slips the raffia-bound "
                f"latch and scoops the {prize.label} into {pos} scarf. The "
                f"bandit only returns it once {sub} keeps the moral of "
                f"{theme.label}."
            ),
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How does {trait} {hero.id} finally earn the {prize.label} back "
                f"from the bandit at {place}?"
            ),
            answer=(
                f"{hero.id} does the moral demand -- {theme.demand} -- and "
                f"shows {theme.good}. At dawn the bandit sets the {prize.label} "
                f"back on its cradle, and the Bard finds {hero.id} smiling "
                f"beside the {case.label}."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What is the moral of the tale about the bandit, the theme, "
                f"and the raffia at {place}?"
            ),
            answer=(
                f"The moral is that {theme.moral} The Ghost Story turns out to "
                f"be {theme.label} wearing a sheet, and the soft raffia knot is "
                f"the proof that the lesson was kept."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    theme = _safe_fact(world, f, "theme")
    tags = set(theme.tags)
    tags.update({"bandit", "raffia", "ghost_story", "moral"})
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.fragile:
            bits.append("fragile")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="square", theme="honesty", prize="mask",
                name="Mira", gender="girl", trait="careful"),
    StoryParams(place="lanes", theme="kindness", prize="lantern",
                name="Theo", gender="boy", trait="thoughtful"),
    StoryParams(place="garden", theme="courage", prize="bell",
                name="Wren", gender="girl", trait="watchful"),
    StoryParams(place="square", theme="sharing", prize="spool",
                name="Joss", gender="boy", trait="earnest"),
    StoryParams(place="lanes", theme="patience", prize="cup",
                name="Lila", gender="girl", trait="quiet"),
]


def explain_rejection(theme: Theme, prize: Prize) -> str:
    case_def = select_case(theme)
    if case_def is None:
        return (f"(No story: no themed case is registered for theme "
                f"{theme.id!r}. Add one to the CASES table.)")
    if not prize_is_fragile(prize):
        return (f"(No story: a {prize.label} is not fragile enough to belong "
                f"in the {case_def.label}; the bandit has no real prize to "
                f"snatch.)")
    return (f"(No story: a {prize.label} does not fit the {case_def.label} "
            f"({case_def.fits}); the museum would never display it there.)")


def explain_gender(prize_id: str, gender: str) -> str:
    return (f"(No story: the {prize_id} is not a typical {gender}'s item here; "
            f"all prizes in this world are gender-neutral, but the name list "
            f"is gendered, so try another name or --gender.)")


# ---------------------------------------------------------------------------
# ASP twin (inline)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is fit for a case when the case fits the prize type and the case is
% themed with the moral of the story.
prize_fits_case(T, P) :- theme(T), case_fits(C, P), case_theme(C, T).

% A story is valid when the place affords the theme, the theme has a matching
% case, and a prize fits the case.
valid(Place, T, P) :- affords(Place, T), theme(T), prize_fits_case(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in THEMES.items():
        lines.append(asp.fact("theme", tid))
    for c in CASES:
        lines.append(asp.fact("case", c.id))
        lines.append(asp.fact("case_theme", c.id, c.theme))
        for p in sorted(c.fits):
            lines.append(asp.fact("case_fits", c.id, p))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if prize_is_fragile(pr):
            lines.append(asp.fact("fragile_prize", pid))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a Ghost Story about a bandit, a moral "
                    "theme, and a knot of raffia. Unspecified choices are picked "
                    "at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    if getattr(args, "theme", None) and getattr(args, "prize", None):
        theme, prize = _safe_lookup(THEMES, getattr(args, "theme", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        case_def = select_case(theme)
        if case_def is None or not prize_ok_for_case(prize, case_def):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "theme", None) is None or c[1] == getattr(args, "theme", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, theme_id, prize_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        theme=theme_id,
        prize=prize_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(THEMES, params.theme),
                 _safe_lookup(PRIZES, params.prize), params.name, params.gender,
                 [params.trait, "earnest"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, theme, prize) combos:\n")
        for place, theme, prize in triples:
            print(f"  {place:8} {theme:9} {prize:9}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.theme} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
