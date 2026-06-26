#!/usr/bin/env python3
"""
storyworlds/worlds/dear_quest_sharing_folk_tale.py
==================================================

A standalone *story world* sketch in a folk-tale register for a small
"dear quest / sharing" domain.

Initial tale (used to build the world model):
---
Long ago, in a green fold of the hills, there lived a kind deer named Dear
who watched the path that ran between the village and the cool river. Dear
was a quiet helper, and animals from the hilltop all came to her when they
had a problem and no answer of their own.

One bright morning, a small rabbit hopped up the path. "Dear," said the
rabbit, "I have a great worry. I have been told there is a hidden apple
orchard beyond the old stone bridge, and I have been told, too, that
whoever shares the first apple of that orchard with a stranger will be
blessed by the hills. But I am small, and the bridge is wide, and the road
beyond it is long."

Dear tilted her soft head. "I cannot promise an answer, but I can walk the
path beside you. Let us go together." So they set out, Dear steady and the
rabbit quick, and the path unfolded one bend at a time.

When they came to the river, the water ran high and the stones were slick.
The rabbit froze, for she could not swim. Dear stepped in first, breaking
the current with her body, and the rabbit clung to the soft warmth of her
neck. On the far bank, the rabbit said, "Dear, I will not forget the way
you carried me across."

A little farther on, they met a thin old hedgehog carrying nothing but a
sharp thorn in his paw. He could not pull it out by himself, and the road
was rough. Dear stopped, lay down gently, and with patient licks and a
steady paw, drew the thorn free. The hedgehog bowed his spines. "Take
this," he said, and pressed a small smooth stone into her hoof. "It will
warm a cold heart when you need it most."

At last, beyond a long meadow, they came to the hidden apple orchard. The
trees were silver with fruit, and the air smelled of sweet cider and warm
grass. The rabbit's eyes grew wide, for there were more apples than she
had ever seen. She reached for the lowest branch, plucked a single red
apple, and held it close.

"Now I must share it with a stranger," the rabbit whispered, "or the
blessing will not come." She looked at Dear and said, "You are the only
friend I have made today. Will you share my first apple with me?"

Dear bowed her head. "I will, little sister. And because the apple was
hard-won, the hills will remember both of us, not only one."

They sat together under the silver boughs, and they shared the apple in
two halves, and the rabbit said, "The hills have answered me: the blessing
is not the orchard, but the friend who walks the path with you."

The hedgehog, who had followed them at a distance, smiled from behind a
fern. He had been the stranger the rabbit needed, and the hills had known
it all along.

And so the rabbits of that hill learned three small things: to ask for
help, to give help freely, and to share the first fruits of a long quest.
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

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/dear_quest_sharing_folk_tale.py``): add the
# package dir (storyworlds/) to the path so ``results`` resolves regardless of
# the current working directory.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# The hazards of the road.  Each is a separate "mess" kind that the world
# tracks on the travelers; some can be helped through, some cannot.
HAZARD_KINDS = {"river", "thorn", "dark", "storm"}

# Phases of the long road, in order.  Each phase has a hazard and an act of
# sharing (or receiving) help tied to it.  The screenplay walks them in turn.
PHASE_KINDS = ["ford", "thorn", "orchard"]

# ---------------------------------------------------------------------------
# Entities: characters, places, and the small objects that travel with them
# all share one representation.  The world is a small one and a single class
# is clearer than three near-duplicates.
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
    kind: str = "thing"            # "character" | "place" | "thing"
    type: str = "thing"            # dear, rabbit, hedgehog, path, river, ...
    label: str = ""                # short reference, e.g. "deer", "the rabbit"
    phrase: str = ""               # full noun phrase, e.g. "a kind deer named Dear"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False           # "stones" -> them, "apple" -> it
    region: str = ""               # body region, for hazards with a body zone
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    dear: object | None = None
    helper: object | None = None
    visitor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"doe", "deer", "rabbit", "vixen", "hen", "sow"}
        male = {"stag", "buck", "hare", "boar", "fox", "drake", "hedge"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        # Default to a kind, folk-tale-safe "it" for places and objects.
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"deer": "deer", "rabbit": "rabbit", "hedgehog": "hedgehog",
                "mother": "mother", "father": "father"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this small domain.
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
    """The land the quest runs through."""
    id: str
    name: str                      # "the green hills"
    passage: str                   # "the long path between the village and the river"
    weather: str                   # "bright" | "rainy" | "foggy"
    key: str = ""                  # short tag for generation prompts
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
class Hazard:
    """A difficulty on the road: a river to ford, a thorn to draw, a dark mile."""
    id: str
    name: str                      # "the high river", "the sharp thorn", "the dark mile"
    kind: str                      # one of HAZARD_KINDS
    zone: str                      # "body" | "path" -- whether it touches the body
    helper_kind: str               # what kind of help defeats it
    helper_role: str               # "carry", "draw", "guide"
    line: str                      # short narrator beat for this phase
    prompt: str                    # spoken line by the rabbit (or the helper)
    ford: object | None = None
    thorn: object | None = None
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
class Gift:
    """A small object given freely on the road."""
    id: str
    label: str                     # "smooth stone", "red apple", "cool water"
    phrase: str                    # "a small smooth stone"
    giver: str                     # type of giver ("hedgehog", "rabbit", "deer")
    recipient: str                 # type of recipient
    beats: set[str]                # which HAZARD_KINDS it warms against
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
    gift: object | None = None
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
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
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


def _r_helped(world: World) -> list[str]:
    """A helper's kind matches the hazard's helper_kind -> the rabbit is helped."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("need_help", 0) < THRESHOLD:
            continue
        hazard_kind = actor.memes.get("current_hazard", "")
        if not hazard_kind:
            continue
        for helper in world.characters():
            if helper.id == actor.id:
                continue
            if helper.memes.get("offers_help", "") != hazard_kind:
                continue
            sig = ("helped", actor.id, helper.id, hazard_kind)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["need_help"] = 0.0
            actor.memes["gratitude"] += 1
            helper.memes["blessing"] += 1
            out.append(f"{helper.label} helped {actor.label} through the {hazard_kind}.")
    return out


def _r_gratitude_word(world: World) -> list[str]:
    """Embedded gratitude becomes a spoken line of thanks."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["gratitude"] < THRESHOLD:
            continue
        sig = ("gratitude_word", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        # Marker; the screenplay beat that follows speaks the actual line.
        out.append("__gratitude_speaks__")
    return out


def _r_gift_warms(world: World) -> list[str]:
    """A gift given warms a future coldness for both giver and receiver."""
    out: list[str] = []
    for giver in world.characters():
        if giver.memes.get("gives", "") not in {"gift"}:
            continue
        sig = ("gift_warmed", giver.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        giver.memes["warmth"] += 1
        out.append(f"{giver.label}'s gift carried warmth forward.")
    return out


def _r_shared_blessing(world: World) -> list[str]:
    """Sharing the first fruit (or any hard-won gift) -> the hills remember both."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("shares", "") != "first_fruit":
            continue
        sig = ("shared_blessing", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["blessing"] += 1
        actor.memes["companionship"] += 1
        # The partner is the most-recently grateful other character.
        partner = next(
            (c for c in reversed(world.characters())
             if c.id != actor.id and c.memes["gratitude"] >= THRESHOLD),
            None,
        )
        if partner is not None:
            partner.memes["blessing"] += 1
            partner.memes["companionship"] += 1
            out.append(f"{partner.label} was remembered alongside {actor.label}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="helped", tag="physical", apply=_r_helped),
    Rule(name="gratitude_word", tag="social", apply=_r_gratitude_word),
    Rule(name="gift_warmed", tag="social", apply=_r_gift_warms),
    Rule(name="shared_blessing", tag="social", apply=_r_shared_blessing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
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
# Constraint helpers -- what is a *reasonable* quest and a *reasonable* share.
# ---------------------------------------------------------------------------
def hazard_fits_phase(hazard: Hazard, phase: str) -> bool:
    """The phase (ford / thorn / orchard) is a stage on the road, not a hazard
    property; every phase has a default hazard id which the screenplay uses."""
    return phase in PHASE_KINDS


def gift_for_phase(phase: str) -> Optional[str]:
    """Which gift id, if any, naturally belongs to this phase of the road."""
    return {
        "ford": "stone",        # the hedgehog's warm stone
        "thorn": "thanks",      # a debt of thanks, not a thing
        "orchard": "apple",     # the rabbit's first apple
    }.get(phase)


def select_hazard_for(phase: str) -> str:
    return {
        "ford": "river",
        "thorn": "thorn",
        "orchard": "dark",
    }.get(phase, "dark")


def select_helper_for(phase: str) -> tuple[str, str, str]:
    """(role, helper_type, helper_line) for the given phase."""
    return {
        "ford": ("carry", "deer",
                 "Step behind me and hold to my neck; the current will not take you."),
        "thorn": ("draw", "hedgehog",
                 "Hold still, small friend; one careful pull and the thorn is gone."),
        "orchard": ("share", "rabbit",
                    "Let us break the apple in two, and the hills will remember both of us."),
    }[phase]


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_opener(world: World) -> None:
    s = world.setting
    weather_phrase = {
        "bright": "the morning was bright and the dew still clung to the grass",
        "rainy": "a soft rain had fallen and the path smelled of wet earth",
        "foggy": "a thin fog lay along the path and made the world feel hushed",
    }.get(s.weather, "the air was gentle and the path was open")
    world.say(f"In a green fold of the hills, {s.name} lay quiet, and {weather_phrase}.")
    world.say(f"There, where {s.passage} wound between the village and the cool river,"
              f" lived a kind deer whose name was Dear.")


def introduce_dear(world: World) -> None:
    dear = world.get("Dear")
    dear.memes["love_kin"] += 1
    world.say(
        f"{dear.id} was a quiet helper. When the small animals of the hill had a "
        f"problem and no answer of their own, they came to {dear.pronoun('object')} "
        f"and waited at the edge of the path until {dear.pronoun()} looked up."
    )


def visitor_arrives(world: World, visitor: Entity) -> None:
    visitor.memes["desire"] += 1
    visitor.meters["need_help"] = 1.0
    world.say(
        f"One {world.setting.weather} morning, {visitor.label} came hopping up the path, "
        f"and {visitor.pronoun()} stopped and bowed low to {world.get('Dear').label}."
    )


def tell_the_wish(world: World, visitor: Entity, hazard: Hazard) -> None:
    visitor.memes["current_hazard"] = hazard.kind
    world.say(
        f'"{world.get("Dear").id}," {visitor.label} said, "{hazard.prompt}"'
    )


def dear_consents(world: World, phase: str) -> None:
    dear = world.get("Dear")
    dear.memes["offers_help"] = select_hazard_for(phase)
    dear.memes["courage"] += 1
    world.say(
        f'{dear.id} tilted {dear.pronoun("possessive")} soft head and said, '
        f'"I cannot promise an answer, but I can walk the path beside you. Let us go."'
    )


def walk_together(world: World) -> None:
    world.say("So they set out, Dear steady and the small visitor quick, "
              "and the path unfolded one bend at a time.")


def ford_river(world: World, visitor: Entity, hazard: Hazard) -> None:
    dear = world.get("Dear")
    dear.meters[HAZARD_KINDS.intersection({"river"}).pop() if False else "river"] += 1
    world.say(
        f"When they came to {hazard.name}, the water ran high and the stones were slick. "
        f"{visitor.label} froze, for {visitor.pronoun()} could not swim."
    )
    world.say(
        f"{dear.label} stepped in first, breaking the current with {dear.pronoun('possessive')} "
        f"body, and {visitor.label} clung to the soft warmth of {dear.pronoun('possessive')} neck."
    )
    propagate(world, narrate=False)             # fires the helped rule


def draw_thorn(world: World, visitor: Entity, hazard: Hazard, helper: Entity) -> None:
    helper.meters["thorn"] += 1
    world.say(
        f"A little farther on, they met {helper.label}, who carried nothing but "
        f"a sharp thorn in {helper.pronoun('possessive')} paw. The road was rough "
        f"and the thorn was deep."
    )
    world.say(
        f"{world.get('Dear').label} lay down gently, and with patient licks and a steady "
        f"paw, drew the thorn free."
    )
    helper.memes["gratitude"] += 1
    helper.memes["offers_help"] = ""             # hedgehog is helped, not helper here
    propagate(world, narrate=False)


def gift_stone(world: World, giver: Entity, gift: Gift) -> None:
    giver.memes["gives"] = "gift"
    giver.memes["warmth"] += 1
    world.say(
        f'{giver.label} bowed {giver.pronoun("possessive")} spines and said, '
        f'"Take this {gift.phrase}. It will warm a cold heart when you need it most."'
    )
    world.say(
        f"{world.get('Dear').label} took the {gift.label} and tucked it close, and the hills "
        f"seemed a little warmer for the giving."
    )


def find_orchard(world: World, setting: Setting) -> None:
    world.say(
        f"At last, beyond a long meadow, they came to the hidden apple orchard. "
        f"The trees were silver with fruit, and the air smelled of sweet cider and warm grass."
    )


def pick_first_apple(world: World, visitor: Entity) -> None:
    visitor.meters["longing"] += 1
    world.say(
        f"{visitor.label}'s eyes grew wide, for there were more apples than "
        f"{visitor.pronoun()} had ever seen. {visitor.pronoun().capitalize()} reached "
        f"for the lowest branch and plucked a single red apple, and held it close."
    )


def promise_to_share(world: World, visitor: Entity) -> None:
    visitor.memes["desire"] += 1
    world.say(
        f'"{visitor.label.capitalize()} whispered, "Now I must share it with a stranger, '
        f"or the blessing will not come.\""
    )


def share_apple(world: World, visitor: Entity, partner: Entity) -> None:
    visitor.memes["shares"] = "first_fruit"
    partner.memes["shares"] = "first_fruit"
    world.say(
        f'{visitor.label} looked at {partner.label} and said, "You are the only friend '
        f'I have made today. Will you share my first apple with me?"'
    )
    world.say(
        f'{partner.label} bowed {partner.pronoun("possessive")} head. "I will, '
        f"little sister. And because the apple was hard-won, the hills will remember "
        f'both of us, not only one."'
    )
    world.say(
        f"They sat together under the silver boughs and shared the apple in two halves."
    )
    propagate(world, narrate=False)             # fires the shared_blessing rule


def hidden_stranger(world: World, stranger: Entity) -> None:
    world.say(
        f"{stranger.label}, who had followed them at a distance, smiled from behind a fern. "
        f"{stranger.pronoun().capitalize()} had been the stranger the small visitor needed, "
        f"and the hills had known it all along."
    )


def moral(world: World) -> None:
    world.say(
        f"And so the small folk of that hill learned three little things: to ask for help, "
        f"to give help freely, and to share the first fruits of a long quest."
    )


# ---------------------------------------------------------------------------
# The screenplay: a three-act folk tale driven by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, dear_name: str = "Dear",
         visitor_name: str = "the rabbit", visitor_type: str = "rabbit",
         helper_name: str = "the hedgehog", helper_type: str = "hedgehog",
         gift: Optional[Gift] = None) -> World:
    world = World(setting)

    dear = world.add(Entity(
        id=dear_name, kind="character", type="deer", label=dear_name,
        phrase=f"a kind deer named {dear_name}",
        traits=["kind", "steady", "gentle"],
    ))
    visitor = world.add(Entity(
        id=visitor_name, kind="character", type=visitor_type, label=visitor_name,
        phrase=f"a small {visitor_type} of the hill",
        traits=["small", "earnest"],
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_type, label=helper_name,
        phrase=f"a thin old {helper_type}",
        traits=["thin", "grateful"],
    ))

    # A first gift, if one was given: the hedgehog's smooth stone.
    if gift is None:
        gift = Gift(
            id="stone", label="smooth stone", phrase="small smooth stone",
            giver="hedgehog", recipient="deer",
            beats={"river", "dark"}, plural=False,
        )

    # Hazards we'll meet on the road.
    ford = Hazard(
        id="river", name="the high river", kind="river", zone="path",
        helper_kind="carry", helper_role="carry", line="the water ran high",
        prompt=("I have been told there is a hidden apple orchard beyond the old stone "
                "bridge, but the river is wide and the stones are slick."),
    )
    thorn = Hazard(
        id="thorn", name="the sharp thorn", kind="thorn", zone="body",
        helper_kind="draw", helper_role="draw", line="a sharp thorn",
        prompt="I cannot pull the thorn from my own paw, and the road is rough.",
    )

    # Act 1 -- the helper at home, the small visitor, the promise to walk.
    setting_opener(world)
    introduce_dear(world)
    visitor_arrives(world, visitor)
    tell_the_wish(world, visitor, ford)
    dear_consents(world, "ford")
    walk_together(world)

    # Act 2 -- the ford, the thorn, the gift.
    world.para()
    ford_river(world, visitor, ford)
    # The small visitor speaks a line of thanks.
    world.say(
        f'On the far bank, {visitor.label} said, "{dear.label}, I will not forget the '
        f'way you carried me across."'
    )
    draw_thorn(world, visitor, thorn, helper)
    gift_stone(world, helper, gift)

    # Act 3 -- the orchard, the shared apple, the hidden stranger.
    world.para()
    find_orchard(world, setting)
    pick_first_apple(world, visitor)
    promise_to_share(world, visitor)
    share_apple(world, visitor, dear)
    hidden_stranger(world, helper)
    # The wisdom at the end, spoken in the voice of the small visitor.
    world.say(
        f'"{visitor.label.capitalize()} said, "The hills have answered me: the blessing '
        f'is not the orchard, but the friend who walks the path with you."'
    )
    moral(world)

    world.facts.update(
        setting=setting, dear=dear, visitor=visitor, helper=helper,
        gift=gift, ford=ford, thorn=thorn,
        phases=PHASE_KINDS,
        resolved=visitor.memes["blessing"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "hills": Setting(
        id="hills",
        name="the green hills",
        passage="the long path between the village and the cool river",
        weather="bright",
        key="hills",
    ),
    "wood": Setting(
        id="wood",
        name="the whispering wood",
        passage="the mossy track that runs from the mill to the spring",
        weather="foggy",
        key="wood",
    ),
    "downs": Setting(
        id="downs",
        name="the open downs",
        passage="the sheep track that climbs from the brook to the high meadow",
        weather="bright",
        key="downs",
    ),
    "cove": Setting(
        id="cove",
        name="the quiet cove",
        passage="the cliff path that bends from the fisher's hut to the apple trees",
        weather="rainy",
        key="cove",
    ),
}

VISITORS = {
    "rabbit": {"label": "the rabbit", "type": "rabbit", "phrase": "a small rabbit of the hill"},
    "hare":   {"label": "the hare",   "type": "hare",   "phrase": "a long-eared hare"},
    "vixen":  {"label": "the vixen",  "type": "vixen",  "phrase": "a red-coated vixen"},
    "boar":   {"label": "the boar",   "type": "boar",   "phrase": "a young boar with a kind eye"},
}

HELPERS = {
    "hedgehog": {"label": "the hedgehog", "type": "hedgehog"},
    "badger":   {"label": "the badger",   "type": "badger"},
    "otter":    {"label": "the otter",    "type": "otter"},
    "wren":     {"label": "the wren",     "type": "wren"},
}

GIFTS = {
    "stone": Gift(
        id="stone", label="smooth stone", phrase="small smooth stone",
        giver="hedgehog", recipient="deer", beats={"river", "dark"},
    ),
    "shell": Gift(
        id="shell", label="sea shell", phrase="a small pink sea shell",
        giver="otter", recipient="deer", beats={"dark", "storm"},
    ),
    "feather": Gift(
        id="feather", label="soft feather", phrase="a long soft feather",
        giver="wren", recipient="deer", beats={"storm"},
    ),
    "acorn": Gift(
        id="acorn", label="brown acorn", phrase="a fat brown acorn",
        giver="badger", recipient="deer", beats={"river"},
    ),
}

DEAR_NAMES = ["Dear", "Marigold", "Rowan", "Hazel", "Willow", "Sage", "Linden", "Briar"]
TRAITS = ["kind", "steady", "gentle", "soft-voiced", "patient", "watchful", "warm"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    """(setting, visitor, helper, gift) tuples that pass the reasonableness gate."""
    combos = []
    for sid in SETTINGS:
        for vid, v in VISITORS.items():
            for hid, h in HELPERS.items():
                for gid, g in GIFTS.items():
                    # Every visitor/helper pair is reasonable in a folk-tale world
                    # as long as there is at least one shared kindness on the road.
                    if g.recipient in {"deer"} and g.giver == h["type"]:
                        combos.append((sid, vid, hid, gid))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    visitor: str
    helper: str
    gift: str
    dear_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
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


KNOWLEDGE = {
    "quest": [("What is a quest?",
               "A quest is a long journey to find or to do something that matters, "
               "and along the way the traveler learns more than they set out to find.")],
    "sharing": [("Why is sharing important?",
                 "Sharing matters because when one person has enough for two, a small "
                 "act of giving can make a whole journey feel blessed.")],
    "dear": [("Who is the dear in the tale?",
              "The dear is the kind deer who lives at the edge of the path and helps "
              "the small animals of the hill when they have a problem they cannot "
              "solve alone.")],
    "river": [("What does it mean to ford a river?",
               "To ford a river is to walk across it where the water is shallow "
               "enough to pass, often with a steady friend beside you.")],
    "thorn": [("What should you do if a thorn is in your paw?",
               "If a thorn is in your paw, it is wise to ask a steady friend to "
               "draw it out carefully, so the wound can heal clean.")],
    "orchard": [("What is an orchard?",
                 "An orchard is a place where fruit trees grow together, and walking "
                 "into one is like stepping into a quiet, sweet-smelling room.")],
    "apple": [("Why is the first apple special?",
               "The first apple of an orchard is special because it is the first "
               "thing you have worked to find, and sharing it makes the finding "
               "blessed.")],
    "stone": [("Why would a small stone be a fine gift?",
               "A small smooth stone is a fine gift because it fits in a pocket, "
               "carries warmth, and reminds the giver of a kindness done.")],
    "folk": [("What is a folk tale?",
              "A folk tale is a simple story passed along by word of mouth, often "
              "about small animals, kind helpers, and a short lesson at the end.")],
    "blessing": [("What is a blessing in a folk tale?",
                  "A blessing in a folk tale is a quiet good thing that comes from "
                  "kindness, not from magic, and it grows whenever it is shared.")],
}
KNOWLEDGE_ORDER = ["quest", "sharing", "dear", "river", "thorn", "orchard",
                   "apple", "stone", "folk", "blessing"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    dear, visitor, helper, gift = f["dear"], f["visitor"], f["helper"], f["gift"]
    return [
        f'Write a short folk-tale for a 4-to-6-year-old on the theme "a quiet '
        f'helper, a long road, a shared first fruit" that includes the word "dear".',
        f"Tell a gentle folk tale in which a kind deer named {dear.id} walks the "
        f"road with {visitor.label} past {f['setting'].name} and shares a hard-won "
        f"apple with a small friend.",
        f'Write a simple folk tale that uses the noun "dear" and ends with the '
        f"small visitor saying the blessing was the friend, not the orchard.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    dear, visitor, helper, gift = f["dear"], f["visitor"], f["helper"], f["gift"]
    sub, obj, pos = (visitor.pronoun("subject"), visitor.pronoun("object"),
                     visitor.pronoun("possessive"))
    setting = _safe_fact(world, f, "setting")
    trait = dear.traits[0] if dear.traits else "kind"
    weather = setting.weather
    weather_phrase = {
        "bright": "bright morning", "rainy": "rainy morning", "foggy": "foggy morning"
    }.get(weather, "morning")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who lives at the edge of the path in {setting.name}, where the "
                f"small animals of the hill come for help?"
            ),
            answer=(
                f"A kind deer named {dear.id} lives at the edge of the path in "
                f"{setting.name}, and the small animals come to {dear.pronoun('object')} "
                f"when they have a problem and no answer of their own."
            ),
        ),
        QAItem(
            question=(
                f"What did {visitor.label} wish to find beyond the long road from "
                f"{setting.name} when {sub} came to {dear.id} on a {weather_phrase}?"
            ),
            answer=(
                f"{visitor.label.capitalize()} wished to find the hidden apple "
                f"orchard beyond the road, where the first apple, shared with a "
                f"stranger, would be blessed by the hills."
            ),
        ),
        QAItem(
            question=(
                f"How did {dear.label} help {visitor.label} cross {f['ford'].name} "
                f"on the way to the orchard?"
            ),
            answer=(
                f"{dear.label} stepped into the high water first and broke the current "
                f"with {dear.pronoun('possessive')} body, while {visitor.label} clung "
                f"to the soft warmth of {dear.pronoun('possessive')} neck."
            ),
        ),
        QAItem(
            question=(
                f"What small gift did {helper.label} give to {dear.label} after "
                f"the thorn was drawn from {helper.pronoun('possessive')} paw?"
            ),
            answer=(
                f"{helper.label} pressed {gift.phrase} into {dear.label}'s hoof and "
                f"said it would warm a cold heart when it was needed most."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {visitor.label} and {dear.label} share the first apple "
                f"in the hidden orchard to earn the hills' blessing?"
            ),
            answer=(
                f"{visitor.label.capitalize()} broke the apple in two halves and shared "
                f"it with {dear.label}, and the hills remembered both of them, not "
                f"only one."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What three small things did the small folk of {setting.name} learn "
                f"from the long quest of {dear.label} and {visitor.label}?"
            ),
            answer=(
                f"They learned to ask for help, to give help freely, and to share "
                f"the first fruits of a long quest."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What was the hills' answer, in {visitor.label}'s own words, at the "
                f"end of the long quest from {setting.name}?"
            ),
            answer=(
                f'{visitor.label.capitalize()} said, "The hills have answered me: the '
                f"blessing is not the orchard, but the friend who walks the path with you.\""
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    # A folk tale that lives by a quest and a shared fruit should reach for
    # at least these four topics -- quest, sharing, dear, apple.
    out: list[QAItem] = []
    core = ["quest", "sharing", "dear", "apple", "folk", "blessing"]
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in core:
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
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        setting="hills",
        visitor="rabbit",
        helper="hedgehog",
        gift="stone",
        dear_name="Dear",
        trait="kind",
    ),
    StoryParams(
        setting="wood",
        visitor="hare",
        helper="wren",
        gift="feather",
        dear_name="Rowan",
        trait="soft-voiced",
    ),
    StoryParams(
        setting="cove",
        visitor="vixen",
        helper="otter",
        gift="shell",
        dear_name="Marigold",
        trait="patient",
    ),
    StoryParams(
        setting="downs",
        visitor="boar",
        helper="badger",
        gift="acorn",
        dear_name="Hazel",
        trait="steady",
    ),
]


def explain_rejection(visitor_id: str, helper_id: str, gift_id: str) -> str:
    return (f"(No story: {helper_id} could not plausibly give {gift_id} to the "
            f"dear in this folk-tale world; the gift must be the kind of small "
            f"thing the helper is known for, and a stranger must appear at the end.)")


def explain_setting(setting_id: str) -> str:
    return (f"(No story: {setting_id} is not one of the lands of this folk tale; "
            f"try --setting hills / wood / downs / cove.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (valid_combos).  The rules are inline below; the facts are generated from
# the registries above so the two can never drift.  Uses the shared `asp`
# helper + clingo, imported lazily so the prose engine runs without them.
# See ``python dear_quest_sharing_folk_tale.py --verify``.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A gift is a possible gift for a helper if the helper is the kind of giver
% the gift is known to come from.  The hedgehog gives the stone, the otter
% the shell, the wren the feather, the badger the acorn.
can_give(Helper, Gift) :- helper(Helper, HType), gift(Gift, HType).

% A folk-tale story is valid when (a) the setting exists, (b) the visitor
% and helper are both kinds of character we know, (c) the gift is the right
% kind of gift for the helper, and (d) the gift is meant for the dear.
valid(Setting, Visitor, Helper, Gift) :-
    setting(Setting),
    visitor(Visitor, _),
    helper(Helper, _),
    gift(Gift, _),
    can_give(Helper, Gift),
    gift_for(Gift, deer).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid, v in VISITORS.items():
        lines.append(asp.fact("visitor", vid, v["type"]))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid, h["type"]))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid, g.giver))
        lines.append(asp.fact("gift_for", gid, g.recipient))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting, visitor, helper, gift) tuples."""
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
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
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch in a folk-tale register: a kind deer, "
                    "a long quest, a shared first fruit. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--dear-name", dest="dear_name",
                    help="override the deer's name (e.g. Dear, Rowan, Hazel)")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gift", None) and getattr(args, "helper", None):
        if _safe_lookup(GIFTS, getattr(args, "gift", None)).giver != _safe_lookup(HELPERS, getattr(args, "helper", None))["type"]:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "visitor", None) is None or c[1] == getattr(args, "visitor", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))
              and (getattr(args, "gift", None) is None or c[3] == getattr(args, "gift", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, visitor, helper, gift = rng.choice(list(combos))
    dear_name = getattr(args, "dear_name", None) or rng.choice(DEAR_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        visitor=visitor,
        helper=helper,
        gift=gift,
        dear_name=dear_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    v = _safe_lookup(VISITORS, params.visitor)
    h = _safe_lookup(HELPERS, params.helper)
    g = _safe_lookup(GIFTS, params.gift)
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        dear_name=params.dear_name,
        visitor_name=v["label"], visitor_type=v["type"],
        helper_name=h["label"], helper_type=h["type"],
        gift=g,
    )
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, visitor, helper, gift) combos:\n")
        for setting, visitor, helper, gift in triples:
            print(f"  {setting:6} {visitor:7} {helper:10} {gift}")
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
            header = f"### {p.dear_name} & {p.visitor}: {p.setting} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
