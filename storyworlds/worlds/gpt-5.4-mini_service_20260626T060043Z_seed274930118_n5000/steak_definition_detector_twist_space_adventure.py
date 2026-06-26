#!/usr/bin/env python3
"""
storyworlds/worlds/steak_definition_detector_twist_space_adventure.py
=====================================================================

A small space-adventure story world about a crew, a strange detector, and a
twist involving a steak definition.

The premise is simple: aboard a little starship, a child-like explorer wants to
use a detector to solve a mystery about a "steak definition" found in the ship's
training room. The detector is useful, but it cannot read a meaning by itself;
it can only react to what is physically present. The twist comes when the crew
learns that the "steak definition" is not a food emergency at all, but a label
for a star-map entry, a note, or a misread item aboard the ship.

This world keeps the prose concrete and state-driven:
- meters track physical things like scanner charge, drift, distance, and mess
- memes track feelings like worry, curiosity, relief, and delight

The story structure:
1) setup: who the crew is and why the detector matters
2) tension: the detector points at a suspicious "steak definition"
3) twist: the crew realizes the clue means something else
4) resolution: the crew uses the detector correctly and the ship is safe again
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    card: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for key in ["charge", "drift", "distance", "mess", "damage", "dust"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "relief", "joy", "conflict", "pride"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
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
    place: str = "the starship"
    name: str = "the starship"
    affords: set[str] = field(default_factory=set)
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
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    clue: str
    mess: str
    keyword: str
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
class Detector:
    id: str
    label: str
    prepared: str
    uses: str
    reset: str
    reads: set[str]
    reveals: set[str]
    helps_on: set[str]
    clue: str
    DETECTOR: object | None = None
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.current_artifact: Optional[str] = None
        self.detector_active: bool = False
        self.detector_result: str = ""

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.current_artifact = self.current_artifact
        clone.detector_active = self.detector_active
        clone.detector_result = self.detector_result
        clone.paragraphs = [[]]
        return clone


def _r_scan(world: World) -> list[str]:
    out: list[str] = []
    if not world.detector_active or not world.current_artifact:
        return out
    art = world.get(world.current_artifact)
    for crew in world.characters():
        if crew.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("scan", art.id, crew.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if art.label in DETECTOR.reveals:
            world.detector_result = "definition"
            out.append(f"The detector beeped softly and pointed at the label on the screen.")
        else:
            world.detector_result = "ordinary"
            out.append(f"The detector hummed, but it did not find anything unusual.")
    return out


def _r_twist(world: World) -> list[str]:
    if not world.current_artifact:
        return []
    art = world.get(world.current_artifact)
    if world.detector_result != "definition":
        return []
    sig = ("twist", art.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["twist"] = True
    return ["__twist__"]


CAUSAL_RULES = [
    _r_scan,
    _r_twist,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__twist__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    if "bridge" in setting.place:
        return "The bridge lights glowed blue, and the windows held a dark ribbon of stars."
    if "cargo" in setting.place:
        return "The cargo bay was quiet, with crates tied down so they would not drift."
    return "The ship moved gently, as if it were floating on a calm black sea."


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a young explorer aboard {world.setting.name}, and {helper.label} "
        f"was the friendly detector that always made tiny beeps."
    )
    world.say(
        f"{hero.id} loved solving little mysteries in space, because every clue made "
        f"the ship feel bigger and brighter."
    )


def show_artifact(world: World, art: Artifact, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.current_artifact = art.id
    world.say(
        f"One day, {hero.id} found a strange note in the training room. It said "
        f'"{art.phrase}," and the words looked important.'
    )
    world.say(
        f"{hero.id} frowned and looked at the note again. The phrase sounded like "
        f"a problem, and {hero.pronoun('possessive')} hand tightened around the detector."
    )


def ask_definition(world: World, hero: Entity, art: Artifact) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'"What does {art.label} mean?" {hero.id} asked. "Is it a warning? A code? '
        f'A secret from the ship?"'
    )


def prepare_detector(world: World, helper: Entity, hero: Entity) -> None:
    world.detector_active = True
    hero.memes["curiosity"] += 1
    world.say(
        f'{helper.label.capitalize()} blinked on and gave a happy chirp. "{DETECTOR.prepared}," '
        f"it said, and {hero.id} held it close to the note."
    )


def use_detector(world: World, hero: Entity, art: Artifact) -> None:
    world.say(
        f"{hero.id} slowly moved the detector over the strange note. It scanned the page, "
        f"then the screen, then the sticky corner where someone had left a smudge."
    )
    propagate(world, narrate=True)


def twist_reveal(world: World, hero: Entity, art: Artifact) -> None:
    if not world.facts.get("twist"):
        return
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["relief"] += 1
    world.say(
        f"Then came the twist: {art.clue}. The note was not about dinner at all."
    )
    world.say(
        f"It was a definition card from the ship's lesson box, and the word {art.label} "
        f"meant a star-map nickname, not a meal."
    )


def resolve(world: World, hero: Entity, helper: Entity, art: Artifact) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f'{hero.id} laughed with relief. "{art.label} is just a word on a card," '
        f'{hero.id} said, and {helper.label} gave one last pleased beep.'
    )
    world.say(
        f"Together they put the card back into its slot. The detector rested quiet again, "
        f"and the ship's windows still shone with stars."
    )


def tell(setting: Setting, art: Artifact, hero_name: str = "Mina", hero_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Detector", kind="thing", type="detector", label="the detector"))
    card = world.add(Entity(id="Card", kind="thing", type=art.type, label=art.label, phrase=art.phrase))
    world.facts["artifact"] = art
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["card"] = card
    world.facts["setting"] = setting

    introduce(world, hero, helper)
    world.para()
    world.say(setting_detail(setting))
    show_artifact(world, art, hero)
    ask_definition(world, hero, art)
    prepare_detector(world, helper, hero)
    use_detector(world, hero, art)
    world.para()
    twist_reveal(world, hero, art)
    resolve(world, hero, helper, art)
    return world


SETTINGS = {
    "bridge": Setting(place="the bridge", name="the starship Dawn Runner", affords={"scan"}),
    "cargo": Setting(place="the cargo bay", name="the starship Dawn Runner", affords={"scan"}),
    "observation": Setting(place="the observation deck", name="the starship Dawn Runner", affords={"scan"}),
}

ARTIFACTS = {
    "steak": Artifact(
        id="steak",
        label="steak",
        phrase="steak definition, lower the heat",
        type="card",
        risk="a burned dinner",
        clue="the 'steak' was a lesson-box label, not food",
        mess="grease",
        keyword="steak",
        tags={"steak", "definition", "twist"},
    ),
    "definition": Artifact(
        id="definition",
        label="definition",
        phrase="definition detector, match the symbol",
        type="card",
        risk="a confused search",
        clue="the 'definition' was a sample word the lesson needed",
        mess="ink",
        keyword="definition",
        tags={"definition", "detector", "twist"},
    ),
    "detector": Artifact(
        id="detector",
        label="detector",
        phrase="detector definition, read the panel",
        type="card",
        risk="a false alarm",
        clue="the 'detector' was the tool, but the card explained the tool's name",
        mess="dust",
        keyword="detector",
        tags={"detector", "definition", "twist"},
    ),
}

DETECTOR = Detector(
    id="Detector",
    label="detector",
    prepared="I am ready to scan the clue",
    uses="scan",
    reset="go quiet",
    reads={"label", "ink", "screen"},
    reveals={"steak", "definition", "detector"},
    helps_on={"twist"},
    clue="a definition card can look scary until you read it closely",
)


@dataclass
class StoryParams:
    place: str
    artifact: str
    name: str
    gender: str
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


NAMES_GIRL = ["Mina", "Nia", "Tala", "Luna", "Aria", "Ivy"]
NAMES_BOY = ["Rex", "Toby", "Noah", "Eli", "Finn", "Jace"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place in SETTINGS:
        for art in ARTIFACTS:
            combos.append((place, art))
    return combos


def prize_at_risk(artifact: Artifact) -> bool:
    return True


def explain_rejection(artifact: Artifact) -> str:
    return f"(No story: the space mystery around {artifact.label} is too thin to support a twist.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a detector twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "artifact", None) is None or c[1] == getattr(args, "artifact", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, artifact = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(place=place, artifact=artifact, name=name, gender=gender)


def _story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    art: Artifact = _safe_fact(world, world.facts, "artifact")
    return [
        QAItem(
            question=f"Who was trying to solve the mystery of {art.label}?",
            answer=f"{hero.id} was the explorer who wanted to understand what {art.label} meant.",
        ),
        QAItem(
            question=f"What did the detector do when it scanned the note?",
            answer="It beeped and pointed toward the label, which helped reveal the twist.",
        ),
        QAItem(
            question=f"What was the twist about the word {art.label}?",
            answer=f"The twist was that {art.label} was a definition-card clue, not a real dinner problem.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The crew put the card back, and the detector grew quiet while the ship stayed safe.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detector for?",
            answer="A detector is a tool that helps notice signals, labels, or patterns that are hard to spot by eye.",
        ),
        QAItem(
            question="What is a definition?",
            answer="A definition is a short explanation of what a word means.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how you understand what is happening.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    art: Artifact = _safe_fact(world, world.facts, "artifact")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    return [
        f"Write a short space adventure for young children that includes the words '{art.label}', 'definition', and 'detector'.",
        f"Tell a gentle spaceship mystery where {hero.id} uses a detector to understand what '{art.phrase}' really means.",
        f"Make the story end with a twist that changes the meaning of the word '{art.label}'.",
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
artifact(A) :- artifact_name(A).
valid_story(P,A) :- place(P), artifact(A).
twist(A) :- artifact(A), clue_word(A).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ARTIFACTS:
        lines.append(asp.fact("artifact_name", a))
        lines.append(asp.fact("clue_word", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - py))
    print("  only in python:", sorted(py - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ARTIFACTS, params.artifact), params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
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
    StoryParams(place="bridge", artifact="steak", name="Mina", gender="girl"),
    StoryParams(place="cargo", artifact="definition", name="Rex", gender="boy"),
    StoryParams(place="observation", artifact="detector", name="Luna", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/2."))
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
            header = f"### {p.name}: {p.artifact} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
