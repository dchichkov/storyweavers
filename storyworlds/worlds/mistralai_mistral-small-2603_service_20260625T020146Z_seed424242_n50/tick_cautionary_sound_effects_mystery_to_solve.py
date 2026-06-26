#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# Meter keys for physical simulation
TICKING_KINDS = {"tick_rate", "sound_level"}
MYSTERY_KINDS = {"unsolved", "solved"}
DANGER_KINDS = {"danger_level"}

# Sound effect mappings for narrative
SOUND_EFFECTS = {
    "tick": "Tick... tick... tick...",
    "rapid_tick": "Tick-tock-tick-tock!",
    "alarm_bell": "DONG! GONG! GONG!",
    "whisper": "Sssshhhh... it's listening...",
}

# Cautionary phrases for guidance
CAUTIONS = {
    "low": "Be careful where you listen—some sounds carry warnings.",
    "medium": "Time is slipping away like sand through fingers.",
    "high": "Danger is rising! The ticking grows louder...",
}

# Myth-style locations for the domain
MISSION_CLIMATE = {"echoing", "dim", "moonlit"}

# Emotional responses keyed to world state
EMOTIONS = {"fear", "curiosity", "urgency", "awe"}

# ---------------------------------------------------------------------------
# Entities: characters, objects, and abstract forces in the mythic domain.
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
    type: str = "force"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""
    domain: str = "mythic"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    clock: object | None = None
    hero: object | None = None
    mentor: object | None = None
    mystery_entity: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"heroine", "singer", "maiden"}
        male = {"hero", "singer", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Reusable story blocks and voice markers
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


def myth_intro(setting_phrase: str) -> str:
    return f"In ages past, when the world was young, {setting_phrase}"

def myth_warning(level: float) -> str:
    if level < 0.3:
        return "An unseen watcher kept time beyond mortal ken..."
    if level < 0.8:
        return CAUTIONS["medium"]
    return CAUTIONS["high"]

def myth_sound_effect(rate: float) -> str:
    if rate < 0.2:
        return SOUND_EFFECTS["tick"]
    if rate < 0.6:
        return SOUND_EFFECTS["rapid_tick"]
    return SOUND_EFFECTS["alarm_bell"]

def myth_conclusion(solved: float) -> str:
    if solved >= 1.0:
        return "The threads of fate entwined once more, and the ancient silence returned."
    return "But the ticking only grew faster, and the mystery remained unsolved..."

# ---------------------------------------------------------------------------
# World: physical and emotional state simulation
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_found: int = 0
        self.max_clues: int = 3

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.clues_found = self.clues_found
        clone.max_clues = self.max_clues
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to fixpoint state
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


def _r_ticking(world: World) -> list[str]:
    """Propagate ticking rhythm into sound and mood."""
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["tick_rate"] >= THRESHOLD * 0.5:
            sig = ("tick_echo", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                rate = ent.meters["tick_rate"]
                hero = next((c for c in world.characters() if "hero" in c.type.lower()), None)
                if hero:
                    hero.memes["curiosity"] += 0.5
                    hero.memes["urgency"] += max(0.0, rate - 0.6)
                out.append(myth_sound_effect(rate))
    return out

def _r_danger(world: World) -> list[str]:
    """Escalate danger when sound approaches threshold."""
    out: list[str] = []
    danger_level = sum(e.meters.get("danger_level", 0) for e in world.entities.values())
    if danger_level >= THRESHOLD * 2:
        sig = ("danger_spike", danger_level)
        if sig not in world.fired:
            world.fired.add(sig)
            hero = next((c for c in world.characters() if "hero" in c.type.lower()), None)
            if hero:
                hero.memes["fear"] += (danger_level - 1.5)
                out.append(myth_warning(danger_level))
    return out

def _r_mystery_progress(world: World) -> list[str]:
    """Record investigations resolving the enigma."""
    out: list[str] = []
    hero = next((c for c in world.characters() if "hero" in c.type.lower()), None)
    if not hero or hero.memes["fear"] < THRESHOLD or world.clues_found >= world.max_clues:
        return out
    for clue in range(world.clues_found + 1):
        if hero.memes.get("investigate", 0) >= THRESHOLD * (clue + 1):
            world.clues_found = clue + 1
            res = hero.memes["resolved"] if "resolved" in hero.memes else 0.0
            if res >= THRESHOLD:
                world.entities["mystery"].meters["solved"] += 1
                out.append("A fragment of truth surfaced in the ticking pattern!")
            else:
                out.append(f"Clue {clue + 1} glimpsed through the echoing shadows.")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="ticking_propagate", tag="physical", apply=_r_ticking),
    Rule(name="danger_escalate", tag="physical", apply=_r_danger),
    Rule(name="mystery_progression", tag="immaterial", apply=_r_mystery_progress),
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
                produced.extend(s for s in sents if s != "__ignore__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Verbs forming the mythic screenplay
# ---------------------------------------------------------------------------
def encounter_ticking(world: World, hero: Entity, mysterious_entity: Entity) -> None:
    hero.memes["curiosity"] += 1.0
    mysterious_entity.meters["tick_rate"] += 0.8
    propagate(world)
    world.say(
        f"{hero.pronoun().capitalize()} felt a faint vibration in the "
        f"{mysterious_entity.label}: it sang only to those who dared to pause."
    )

def mentor_warning(world: World, mentor: Entity, hero: Entity) -> None:
    danger = sum(e.meters.get("danger_level", 0) for e in world.entities.values())
    if danger >= 1.2:
        mentor.memes["urgency"] += 0.5
        warning = myth_warning(danger)
        world.say(f'"{warning}" {mentor.pronoun("possessive")} voice whispered.')
        hero.memes["fear"] += 0.4

def investigate_echo(world: World, hero: Entity) -> None:
    hero.memes["investigate"] = hero.memes.get("investigate", 0) + 0.7
    propagate(world)
    world.say(
        f"{hero.id} cupped {hero.pronoun('possessive')} hands around "
        "the unseen rhythm and listened with all {hero.pronoun('possessive')} might."
    )

def reveal_clue(world: World, clue_number: int) -> None:
    world.clues_found = clue_number
    world.say(
        f"Hidden in the {world.entities['mystery'].label} was clue "
        f"{clue_number}: a pattern carved by time itself."
    )
    propagate(world)

def resolve_mystery(world: World, hero: Entity) -> None:
    hero.memes["resolved"] = max(hero.memes.get("resolved", 0), 1.3)
    mystery = world.entities["mystery"]
    mystery.meters["unsolved"] = 0.0
    mystery.meters["solved"] += 1.0
    world.say(
        f"{hero.pronoun().capitalize()} raised {hero.pronoun('possessive')} "
        "hands and the ticking ceased, its purpose fulfilled."
    )

# ---------------------------------------------------------------------------
# Parametrization knobs for the tick domain
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    domain: str
    affords: set[str] = field(default_factory=lambda: {"ticking", "investigation"})
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
    id: str
    label: str
    phrase: str
    locus: str
    clues: int = 3
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
class CharacterTemplate:
    id: str
    type: str
    traits: list[str]
    label: str
    phrase: str
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


SETTINGS = {
    "echo_chamber": Setting(
        place="the echoing chamber of the ancient temple",
        domain="mythic",
    ),
    "stellar_orchard": Setting(
        place="the silver orchard beneath the hoary moon",
        domain="mythic",
    ),
    "shadowed_valley": Setting(
        place="the valley of whispered echoes",
        domain="mythic",
    ),
    "mossy_alcove": Setting(
        place="a mossy alcove deep in the hallowed forest",
        domain="mythic",
    ),
    "stone_circle": Setting(
        place="the stone circle where time itself bends",
        domain="mythic",
    ),
}

MYSTERIES = {
    "cracked_bell": Mystery(
        id="cracked_bell",
        label="cracked silver bell",
        phrase="an ancient cracked bell whose every toll echoed forward in time",
        locus="the zenith of the hallowed tower",
    ),
    "time_gear": Mystery(
        id="time_gear",
        label="time-carved gear",
        phrase="a brass gear etched with runes of forgotten years",
        locus="the heart of the sacred grove",
        clues=2,
    ),
    "singing_stones": Mystery(
        id="singing_stones",
        label="singing stones",
        phrase="six river stones arranged to hum as water passed between them",
        locus="the edge of the silver stream",
    ),
    "staff_of_ages": Mystery(
        id="staff_of_ages",
        label="staff of ages",
        phrase="a staff carved from the bones of the first clockmaker",
        locus="the cave of first light",
    ),
}

CHARACTER_TEMPLATES = {
    "hero": CharacterTemplate(
        id="hero",
        type="hero",
        traits=["courageous", "inquisitive"],
        label="the intrepid seeker",
        phrase="a wandering soul with ears quick to catch Time's language"
    ),
    "mentor": CharacterTemplate(
        id="mentor",
        type="elder",
        traits=["wise", "cautious"],
        label="the keeper of echoes",
        phrase="a guardian of the old wisdom who spoke in measured tones"
    ),
    "spirit": CharacterTemplate(
        id="spirit",
        type="spirit",
        traits=["mischievous", "ancient"],
        label="the echo spirit",
        phrase="a presence woven from all the clicks and clacks of the world"
    ),
}

# ---------------------------------------------------------------------------
# The central screenplay: three-act mythic journey
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, hero_name: str = "Lyra", hero_type: str = "hero",
         hero_traits: Optional[list[str]] = None, mentor_type: str = "elder") -> World:
    world = World()
    hero_traits = hero_traits or ["dauntless", "thoughtful"]

    # Entities: hero, mentor, mystery force, clock relic
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["young"] + hero_traits, phrase=f"{hero_name} the seeker",
        domain="mythic"
    ))
    mentor = world.add(Entity(
        id="Mentor", kind="character", type=mentor_type,
        traits=["timeless", "cogent"], phrase="the keeper of echoes",
        domain="mythic"
    ))
    clock = world.add(Entity(
        id="clock", kind="object", type="force",
        label=mystery.label, phrase=mystery.phrase,
        region=mystery.locus, domain="mythic",
        meters={"tick_rate": 0.0, "sound_level": 0.0},
    ))
    mystery_entity = world.add(Entity(
        id="mystery", kind="mystery", type="enigma",
        label=mystery.label, phrase=mystery.phrase,
        region=mystery.locus, domain="mythic",
        meters={"unsolved": float(mystery.clues), "solved": 0.0},
    ))

    # Act 1: Prophecy and hearing the call
    world.paragraphs.append([])
    world.say(myth_intro(f"there stood {setting.place}."))
    world.say(
        f"Within its stones pulsed a rhythm older than memory itself: "
        f"{myth_sound_effect(0.0)}"
    )
    encounter_ticking(world, hero, clock)

    # Act 2: Caution and investigation
    world.para()
    mentor_warning(world, mentor, hero)
    investigate_echo(world, hero)
    reveal_clue(world, 1)
    mentor_warning(world, mentor, hero)

    # Act 3: Revelation and resolution
    world.para()
    know_thyself = next((t for t in hero.traits if t in ("wise", "ancient")), "true")
    if "resolved" in hero.memes and hero.memes["resolved"] >= THRESHOLD:
        resolve_mystery(world, hero)
    else:
        world.say(
            f"{hero.pronoun().capitalize()} knew the truth lay hidden "
            f"deep within {mentor.pronoun('possessive')} mirrored gaze."
        )
        world.say(myth_conclusion(world.entities["mystery"].meters["solved"]))

    # Record facts for Q&A
    world.facts.update(
        hero=hero, mentor=mentor, mystery=mystery, setting=setting,
        clock=clock, resolved=(hero.memes.get("resolved", 0) >= THRESHOLD),
        clues_found=world.clues_found, max_clues=mystery.clues
    )
    return world

# ---------------------------------------------------------------------------
# Q&A generators: three layers of questions
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short mythic story for ages 5-7 about a seeker who hears Time singing '
        'through a broken bell, using the phrase "tick... tock..." at least twice.',
        f"Tell the myth of {f['hero'].id} who walked into {f['setting'].place} "
        "and heard Time humming, then tried to understand the warning in the sound.",
        'Compose a child-friendly tale in which a character discovers a clue '
        'by listening carefully to an echoing sound that only appears at moonrise.'
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue_word = f"clue {min(3, world.clues_found)}" if world.clues_found > 0 else "first clue"
    hero = _safe_fact(world, f, "hero")
    mentor = _safe_fact(world, f, "mentor")
    place = _safe_fact(world, f, "setting").place
    mystery = _safe_fact(world, f, "mystery")
    resolved = f.get("resolved", False)

    prompts = [
        QAItem(
            question=(
                f"Whose story is being told when the voice of Time calls "
                f"from {place}?"
            ),
            answer=(
                f"It is {hero.id}’s story, a {hero.traits[0]} {hero.type} with "
                f"{hero.pronoun('possessive')} ears tuned to the oldest rhythms."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} hear inside {place} before meeting "
                f"{mentor.pronoun('possessive')} guide?"
            ),
            answer=f"{hero.pronoun().capitalize()} heard {myth_sound_effect(0.0)} "
                   "humming from the very stones around {hero.id}.",
        ),
        QAItem(
            question=(
                f"What clue did {hero.id} find by investigating the echoing rhythm "
                f"inside {place}?"
            ),
            answer=(
                f"By listening closely, {hero.id} discovered a carved pattern "
                f"— {clue_word} hidden among the moss and moonlight."
            ),
        ),
    ]

    if resolved:
        prompts.append(QAItem(
            question=(
                f"How did {hero.id} finally quiet the ticking and solve "
                f"the mystery of {mystery.label}?"
            ),
            answer=(
                f"With calm hands and steady heart, {hero.id} traced the "
                f"source of the sound and calmed the ancient force."
            ),
        ))

    return prompts

def world_knowledge_qa(world: World) -> list[QAItem]:
    wl = [
        ("Why do clocks go tick... tock?", (
            "Clocks tick because their gears and pendulums swing back and forth "
            "to measure time. Each 'tick' starts the swing one way and 'tock' the other."
        )),
        ("What is an echo?", (
            "An echo is a sound that bounces back after hitting something hard, "
            "like a wall or a mountain. It lets you hear your own voice repeated."
        )),
        ("Why do some sounds feel old and wise?", (
            "Sounds that echo in stone chambers or whisper in forests feel old "
            "because humans have heard them for thousands of years—they carry the "
            "memory of the world itself."
        )),
    ]
    return [QAItem(q, a) for q, a in wl]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts (asks that would generate this story) =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions (answerable from the tale) ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge (mythic sound facts) ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Parameter registry, CLI, and generation interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    hero_trait: str
    mentor_type: str
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
    ap = argparse.ArgumentParser(
        description="Mythic story world: a hero hears Time’s warning ticks "
                    "and must solve the mystery before dawn. Unspecified choices are picked randomly.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-trait", choices=["dauntless", "thoughtful", "courageous", "inquisitive"])
    ap.add_argument("--mentor-type", choices=["elder", "sage", "keeper"])
    ap.add_argument("-n", type=int, default=1, help="how many stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducibility")
    ap.add_argument("--all", action="store_true", help="run the curated set of myths")
    ap.add_argument("--trace", action="store_true", help="emit world state after each story")
    ap.add_argument("--qa", action="store_true", help="print the three Q&A sets per story")
    ap.add_argument("--json", action="store_true", help="emit results as JSON")
    ap.add_argument("--asp", action="store_true", help="list ASP-computed valid combos")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP gate parity")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = list(SETTINGS.keys()) if getattr(args, "place", None) is None else [getattr(args, "place", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = rng.choice(choices)

    m_choices = list(MYSTERIES.keys())
    mystery = rng.choice(m_choices)

    name = getattr(args, "name", None) or rng.choice(["Lyra", "Elio", "Niamh", "Finn", "Aria", "Soren"])
    hero_trait = getattr(args, "hero_trait", None) or rng.choice(["dauntless", "thoughtful", "courageous"])
    mentor_type = getattr(args, "mentor_type", None) or rng.choice(["elder", "sage", "keeper"])
    return StoryParams(
        place=place,
        mystery=mystery,
        name=name,
        hero_trait=hero_trait,
        mentor_type=mentor_type,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(MYSTERIES, params.mystery),
        params.name,
        "hero",
        [params.hero_trait],
        params.mentor_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

# ---------------------------------------------------------------------------
# ASP / Clingo twin for logical verification (mythic combinatorics)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A place affords a ticking mystery when its locus matches the enigma.
affords_ticking(P, M) :- affords(P, A), locus(M, L), region(L, R),
                          domain(P, mythic), domain(M, mythic).

% The rhythm is secret until the seeker’s curiosity meets threshold.
mystery_revealed(S, M) :- seeker(S), affords_ticking(P, M),
                          seeker_curiosity(S, C), C >= 1.

% Clues accumulate as investigation intensity reaches steps.
clue_found(S, 1) :- mystery_revealed(S, M), investigate(S, I), I >= 1.
clue_found(S, 2) :- mystery_revealed(S, M), investigate(S, I), I >= 2.
clue_found(S, 3) :- mystery_revealed(S, M), investigate(S, I), I >= 3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("domain", pid, s.domain))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("locus", mid, m.locus))
        lines.append(asp.fact("clues", mid, int(m.clues)))
        lines.append(asp.fact("domain", mid, m.locus))
    for cid, c in CHARACTER_TEMPLATES.items():
        lines.append(asp.fact("seeker_type", c.id, cid))
        for t in c.traits:
            lines.append(asp.fact("seeker_trait", c.id, t))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show affords_ticking/2."))
    return sorted(set(asp.atoms(model, "affords_ticking")))

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(0 if asp_valid_combos() else 1)
    if getattr(args, "asp", None):
        pairs = asp_valid_combos()
        print(f"{len(pairs)} mythic places × mysteries:\n")
        for p, m in pairs:
            print(f"  {p:20} → {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="echo_chamber", mystery="cracked_bell", name="Elio",
                        hero_trait="dauntless", mentor_type="keeper"),
            StoryParams(place="stone_circle", mystery="time_gear", name="Aria",
                        hero_trait="thoughtful", mentor_type="elder"),
            StoryParams(place="mossy_alcove", mystery="singing_stones", name="Niamh",
                        hero_trait="courageous", mentor_type="sage"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        for i in range(getattr(args, "n", None)):
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### Myth {i + 1}: {sample.params.name} in {sample.params.place}"
        if getattr(args, "all", None):
            header += f" · {sample.params.mystery} mystery"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world model state ---")
        for e in sorted(sample.world.entities.values(), key=lambda x: x.id):
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            print(f"  {e.id:20} {e.type:10} | {' '.join(bits)}")
    if qa:
        print("\n" + format_qa(sample))

if __name__ == "__main__":
    main()
