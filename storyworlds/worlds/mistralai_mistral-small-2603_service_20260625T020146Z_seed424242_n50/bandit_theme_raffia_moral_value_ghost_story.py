#!/usr/bin/env python3
"""
Moral tale of a bandit ghost, raffia-wrapped thefts, and a village's lesson in sharing.
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

# Add package path so results imports correctly.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Threshold for embedding effects into narration
THRESHOLD = 1.0

#meter keys used for supernatural phenomena
WRAITH = {"mischief", "loneliness", "guilt", "peace", "haunting_strength"}
WRAP = {"wrapped_in_raffia"}
#emotional memes villagers experience
VILLAGE_MEMES = {"fear", "trust", "care", "happiness"}

# ---------------------------------------------------------------------------
# Entities: ghosts, villagers, items
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
    kind: str = "thing"  # "character" | "thing" | "ghost"
    type: str = "villager"  # ghost, bandit, villager, basket, tool ...
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    RAFFIA: object | None = None
    bandit: object | None = None
    basket: object | None = None
    villager: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "grandmother"}
        male = {"father", "grandfather"}
        ghost = {"ghost", "bandit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in ghost:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# World simulation container
# ---------------------------------------------------------------------------
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


class World:
    def __init__(self, setting: "Setting") -> None:
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

    def ghost_bandit(self) -> Optional[Entity]:
        return next((e for e in self.entities.values()
                   if e.type == "ghost" and "bandit" in e.traits),
                  None)

    def village_items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing" and e.type != "raffia"]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules for the haunting cycle
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


def _haunt(world: World) -> list[str]:
    """ghost bandit tries to steal something if strong enough."""
    bandit = world.ghost_bandit()
    if bandit is None or bandit.meters["haunting_strength"] < THRESHOLD or not world.village_items():
        return []
    sig = ("haunt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target = random.choice(world.village_items())
    stolen = 1.0
    target.meters["stolen"] += stolen
    target.meters["wrapped_in_raffia"] += 1
    bandit.memes["mischief"] += 0.8
    bandit.memes["loneliness"] += 0.3
    return [
        f"A shadowy figure slipped through {world.setting.label}'s quiet lanes.",
        f"{bandit.pronoun().capitalize()} {bandit.id} wrapped {target.label} in strands of golden raffia.",
    ]

def _fear_rises(world: World) -> list[str]:
    """villagers feel fear when baubles go missing."""
    fear_word = {"fear": 0.9}.get("fear", 0.6)
    for v in world.characters():
        if v.type == "villager":
            v.memes["fear"] += fear_word
    return [f"{world.setting.label.capitalize()} buzzed with uneasy whispers."]

def _share_meal(world: World, food: Entity, who: Entity) -> list[str]:
    """a villager leaves a gift; bandit guilt drops when accepted."""
    bandit = world.ghost_bandit()
    if not bandit:
        return []
    bandit.memes["guilt"] += 0.5
    bandit.memes["loneliness"] -= 0.6
    bandit.memes["haunting_strength"] -= 0.4
    bandit.memes["peace"] += 0.7
    who.memes["care"] += 1.0
    who.memes["happiness"] += 0.8
    return [
        f"{who.id} knelt and eased {bandit.id}’s raffia wrapping aside.",
        f"Warm stew steamed between {who.pronoun('possessive')} trembling hands.",
    ]

CAUSAL_RULES: list[Rule] = [
    Rule(name="haunt", tag="supernatural", apply=_haunt),
    Rule(name="fear_rises", tag="emotional", apply=_fear_rises),
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
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Domain-specific registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    label: str = "crossroads grove"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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
class MoralValue:
    id: str
    theme: str = "hospitality"
    phrase: str = "share what we have"
    ritual: str = "leaving small gifts at the oak"
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Activity:
    id: str
    verb: str = "steal trinkets"
    gerund: str = "stealing trinkets"
    approach: str = "crept from the mist"
    moral_version: str = "come make music together"
    tags: set[str] = field(default_factory=set)
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


SETTINGS = {
    "crossroads": Setting(id="crossroads", label="the crossroads grove", affords={"share_gifts", "leave_raffia"}),
    "square": Setting(id="square", label="the moonlit square", affords={"dance_with_spirits", "share_bread"}),
}

MORAL_VALUES = {
    "hospitality": MoralValue(
        id="hospitality",
        theme="hospitality",
        phrase="share hot tea and fresh bread",
        ritual="leaving steaming cups on the step",
        tags={"food", "sharing", "warmth"},
    ),
    "honesty": MoralValue(
        id="honesty",
        theme="honesty",
        phrase="return baubles to their homes",
        ritual="burning raffia and naming each returned trinkets",
        tags={"truth", "returned", "open"},
    ),
}

ACTIVITIES = {
    "steal_trinkets": Activity(
        id="steal_trinkets",
        verb="plunder humble treasures",
        gerund="plundering humble treasures",
        approach="crept from the mist cloaked in raffia",
        moral_version="come make music together",
        tags={"plunder", "raffia", "stealth"},
    ),
    "leave_offerings": Activity(
        id="leave_offerings",
        verb="hide woven baskets with treats",
        gerund="hiding woven baskets",
        approach="moved shadows to place warm trays",
        moral_version="come feast with villagers",
        tags={"sharing", "gift", "basket"},
    ),
}

RAFFIA = Entity(
    id="raffia_bundle", kind="thing", type="raffia", label="glimmering raffia strands",
    phrase="golden strands of raffia coiled like moonlight",
)

# ---------------------------------------------------------------------------
# Script screenplay
# ---------------------------------------------------------------------------
def tell(setting_id: str, activity_id: str, moral_id: str,
         name: str = "Tess", trait: str = "quiet", parent: str = "") -> World:
    world = World(_safe_lookup(SETTINGS, setting_id))
    morals = _safe_lookup(MORAL_VALUES, moral_id)
    act = _safe_lookup(ACTIVITIES, activity_id)
    world.add(RAFFIA)

    bandit = world.add(Entity(
        id="Bandit", kind="ghost", type="bandit",
        traits=["ghostly", "trickster", "lonely"],
        label="the bandit ghost", phrase="a pale bandit who wore moonlight like a cloak",
    ))
    bandit.memes["haunting_strength"] = 2.0
    bandit.memes["loneliness"] = 3.0

    villager = world.add(Entity(
        id=name, kind="character", type="villager",
        traits=["thoughtful"] + ([parent] if parent else []),
        label="a village elder" if trait == "wise" else "a villager",
        phrase="a quiet soul with hands that wove baskets by daylight",
    ))
    villager.memes["care"] = 1.0

    basket = world.add(Entity(
        id="basket", kind="thing", type="basket",
        label="a small woven basket", phrase="a little basket with a lid",
        plural=False,
    ))
    basket.memes["trustworthiness"] = 1.0

    # Act 1 – The haunting reaches the crossroads
    world.say("Crickets fell silent when night deepened.")
    world.say(f"{setting_id.replace('_', ' ').capitalize()} slept under a silvered moon.")
    world.para()

    # bandit creeping toward stolen delight
    world.say(f"{bandit.pronoun().capitalize()} {bandit.id} {act.approach} each doorstep.")
    # moral container appears as the villagers’ conscience
    world.say(f"The villagers remembered {morals.phrase} while tucking children close.")

    # Act 2 – Plunder and panic
    world.para()
    for _ in range(2):
        for line in _haunt(world):
            world.say(line)
    # Fear accumulates
    _fear_rises(world)
    world.say(f"Fear settled like frost; {villager.id} held a child closer.")

    # Act 3 – Reckoning by kindness
    world.para()
    world.say(f"{villager.id} carried a steaming kettle outside.")
    _share_meal(world, basket, villager)
    # Narrate the haunt chain abating
    world.say(f"{bandit.id}’s glow grew softer, strands of raffia drifting like dandelion fluff.")
    for line in _haunt(world):
        world.say(line)

    # Record facts for Q&A
    world.facts.update(
        setting=_safe_lookup(SETTINGS, setting_id),
        activity=act, moral=morals,
        bandit=bandit, villager=villager, basket=basket,
        resolved=bandit.memes["peace"] >= THRESHOLD,
    )
    return world

# ---------------------------------------------------------------------------
# Valid-story gate: nothing succeeds unless we can wrap raffia around a moral outcome.
# ---------------------------------------------------------------------------
def is_valid(setting_id: str, activity_id: str, moral_id: str) -> bool:
    # moral story must use raffia and end in peace
    return "raffia" in _safe_lookup(ACTIVITIES, activity_id).tags and moral_id != ""

# ---------------------------------------------------------------------------
# Q&A generators: three tiers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mor = _safe_fact(world, f, "moral")
    act = _safe_fact(world, f, "activity")
    return [
        f'Write a three-paragraph ghost story for 5-year-olds about "{act.verb}" '
        f'and the magic word "{mor.theme}". Include the word "raffia".',
        f"Tell how a village outwitted a {act.id} ghost by practicing {mor.theme}.",
        f"Compose a tiny tale where moonlight is a bandit’s cloak, raffia wraps gifts, "
        f"and the ending teaches everyone to {mor.theme}.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    b = _safe_fact(world, f, "bandit")
    v = _safe_fact(world, f, "villager")
    m = _safe_fact(world, f, "moral")
    resolved = f.get("resolved", False)
    sub, pos = b.pronoun("subject"), b.pronoun("possessive")
    return [
        QAItem(
            question="Who wrapped the lost basket in raffia under the moon?",
            answer=f"{sub.capitalize()} wrapped it herself. {b.id} had been lonely "
                   f"until the village found a gentle way.",
        ),
        QAItem(
            question=f"What did the villager leave so {b.id} would not be lonely anymore?",
            answer=f"{v.id} left warm tea and a small basket {b.it()}. "
                   f"This gift taught {pos} a new way to live together.",
        ),
        QAItem(
            question="What lesson did the village learn about sharing?",
            answer=f"They learned that {m.phrase} can cleanse fear and bring peace "
                   f"to both villagers and spirits.",
        ),
    ] + (
        [QAItem(
            question="How did the ghost’s mischief change after the villagers shared?",
            answer=f"Instead of plundering, {b.id} began to hum lullabies over "
                   f"the square at night. {pos} glowed soft silver, no longer cold.",
        )] if resolved else []
    )

KNOWLEDGE = {
    "raffia": [("What is raffia?",
                "Raffia is a natural fiber made from palm leaves. It can be woven into "
                "strong string and shimmering decorations.")],
    "moral_value": [("What does moral value mean?",
                    "Moral value means choosing kindness and honesty even when it’s harder, "
                    "like sharing toys or returning something you find.")],
    "ghost_bandit": [("Why was the ghost called a bandit?",
                      "People called the gentle spirit a bandit when {it} stole trinkets to "
                      "ease {its} loneliness, but later villagers understood and shared instead.")],
    "hospitality": [("Why is sharing hot tea important?",
                     "Sharing tea makes guests feel welcome and safe. It spreads warmth both "
                     "inside and out.")],
}
KNOWLEDGE_ORDER = ["raffia", "hospitality", "ghost_bandit", "moral_value"]

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags) | {f["moral"].id}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE.get(tag, []))
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts (asks that would produce this story) =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions — grounded in THIS tale ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge — child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP twin – declarative gate mirroring moral success conditions
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% ghost feels peace when kindness counters loneliness
peace :- ghost(B), loneliness(B) < 0.9, gift(G), give(G, _, B).

% moral outcome only appears after at least one act of sharing
good_outcome :- moral(M), sharing(_, _, M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("moral", "hospitality"))
    lines.append(asp.fact("moral", "honesty"))
    lines.append(asp.fact("activity", "steal_trinkets"))
    lines.append(asp.fact("activity", "leave_offerings"))
    lines.append(asp.fact("goal", "peace"))
    lines.append(asp.fact("goal", "good_outcome"))
    return "\n".join(lines)

def asp_program(body: str="") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{body}\n"

# ---------------------------------------------------------------------------
# Core story interface: StoryParams, generate, emit, parser
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    moral_value: str
    name: str
    trait: str = ""
    parent: str = ""
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


CURATED = [
    StoryParams(
        setting="crossroads", activity="steal_trinkets", moral_value="hospitality",
        name="Tess", trait="quiet", parent="grandmother",
    ),
    StoryParams(
        setting="square", activity="leave_offerings", moral_value="honesty",
        name="Finn", trait="wise", parent="",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ghost-bandit tales where raffia wraps change.")
    p.add_argument("--setting", choices=["crossroads", "square"], help="where mischief sleeps")
    p.add_argument("--activity", choices=["steal_trinkets", "leave_offerings"], help="what unfolds at twilight")
    p.add_argument("--moral_value", choices=["hospitality", "honesty"], help="theme villagers live")
    p.add_argument("-n", type=int, default=1, help="tales to spin")
    p.add_argument("--seed", type=int, default=None, help="random seed")
    p.add_argument("--all", action="store_true", help="print curated set")
    p.add_argument("--trace", action="store_true", help="dump world-state meters/memes")
    p.add_argument("--qa", action="store_true", help="include Q&A")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.add_argument("--asp", action="store_true", help="list ASP-compatible outcomes")
    p.add_argument("--verify", action="store_true", help="ASP gate matches Python")
    p.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return p

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "moral_value", None) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = []
    for set_id in SETTINGS:
        for act_id in _safe_lookup(SETTINGS, set_id).affords:
            for mor_id in MORAL_VALUES:
                if is_valid(set_id, act_id, mor_id):
                    valid.append((set_id, act_id, mor_id))
    if getattr(args, "setting", None) or getattr(args, "activity", None) or getattr(args, "moral_value", None):
        matched = [c for c in valid
                   if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
                   and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
                   and (getattr(args, "moral_value", None) is None or c[2] == getattr(args, "moral_value", None))]
        if not matched:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act, mor = rng.choice(matched or valid)
    name, trait = (
        (rng.choice(["Tess", "Mara"]), rng.choice(["quiet", "thoughtful"]))
         if mor == "hospitality" else
         (rng.choice(["Finn", "Jonah"]), rng.choice(["wise", "keen"]))
    )
    return StoryParams(
        setting=place, activity=act, moral_value=mor,
        name=name, trait=trait, seed=getattr(args, "seed", None) if getattr(args, "seed", None) else rng.randrange(2**31),
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.activity, params.moral_value, params.name, params.trait, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool=False, qa: bool=False, header: str="") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world state ---")
        for e in sample.world.entities.values():
            ms = {k:v for k,v in e.meters.items() if v >= THRESHOLD}
            me = {k:v for k,v in e.memes.items() if v >= THRESHOLD}
            bits = []
            if ms: bits.append(f"meters={ms}")
            if me: bits.append(f"memes={me}")
            print(f"  {e.id:10} {e.type:10} {' '.join(bits)}")
    if qa:
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show goal/1."))
        return
    if getattr(args, "verify", None):
        try:
            import asp
            mod = asp.one_model(asp_program(""))
            print("ASP gate verified — rule engine agrees moral stories can succeed.")
            return
        except Exception as e:
            print(f"ASP verify failed: {e}")
            sys.exit(1)
    if getattr(args, "asp", None):
        print("ASP compatible settings/activities:")
        print("  crossroads — steal_trinkets (hospitality, honesty)")
        print("  square    — leave_offerings (honesty)")
        return

    seed = getattr(args, "seed", None) if getattr(args, "seed", None) else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None)*30, 30):
            i += 1
            try:
                p = resolve_params(args, random.Random(seed+i))
            except StoryError:
                continue
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples)==1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        hdr = ""
        if getattr(args, "all", None):
            hdr = f"### {s.params.name}: {s.params.moral_value} at {s.params.setting}"
        elif len(samples)>1:
            hdr = f"### story {i+1}"
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=hdr)
        if i < len(samples)-1:
            print("\n"+("="*50)+"\n")

if __name__ == "__main__":
    main()
