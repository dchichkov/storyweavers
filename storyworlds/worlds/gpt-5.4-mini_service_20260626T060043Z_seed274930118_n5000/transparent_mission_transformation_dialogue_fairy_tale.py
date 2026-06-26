#!/usr/bin/env python3
"""
A small fairy-tale story world about a transparent mission, a spoken promise,
and a gentle transformation.

The premise:
- A young helper is sent on a mission to carry a transparent token through the
  woods.
- The token can reveal what is hidden, but only if the helper stays kind and
  listens.
- A tiny transformation happens when the helper chooses honesty over haste.

The story stays state-driven: meters track physical progress and magical
change, while memes track courage, worry, trust, and relief.
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
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    relic: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "witch", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "wizard"}:
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
    place: str = "the mossy wood"
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
class Mission:
    id: str
    verb: str
    gerund: str
    risk: str
    reveal: str
    goal: str
    keyword: str = "mission"
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


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    value: str
    fragile: bool = False
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
class Spell:
    id: str
    label: str
    dialogue: str
    effect: str
    turns_into: str
    guards: set[str] = field(default_factory=set)
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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "wood": Setting(place="the mossy wood", affords={"seek", "carry", "speak"}),
    "castle": Setting(place="the bright castle garden", affords={"seek", "carry", "speak"}),
    "lake": Setting(place="the silver lake shore", affords={"seek", "carry", "speak"}),
}

MISSIONS = {
    "mirror": Mission(
        id="mirror",
        verb="carry the transparent mirror",
        gerund="carrying the transparent mirror",
        risk="fog",
        reveal="show hidden paths",
        goal="find the lost gate",
        keyword="transparent",
        tags={"transparent", "reveal", "mission"},
    ),
    "lantern": Mission(
        id="lantern",
        verb="bring the clear lantern",
        gerund="bringing the clear lantern",
        risk="wind",
        reveal="light hidden trails",
        goal="reach the sleeping tower",
        keyword="mission",
        tags={"light", "mission"},
    ),
    "bottle": Mission(
        id="bottle",
        verb="deliver the glass bottle",
        gerund="delivering the glass bottle",
        risk="rock",
        reveal="catch a secret message",
        goal="find the river sprite",
        keyword="transparent",
        tags={"glass", "transparent", "mission"},
    ),
}

RELICS = {
    "pearl": Relic(
        id="pearl",
        label="pearl",
        phrase="a little pearl key",
        value="the hidden gate",
        fragile=True,
    ),
    "seed": Relic(
        id="seed",
        label="seed",
        phrase="a bright seed of hope",
        value="the garden door",
        fragile=False,
    ),
}

SPELLS = {
    "frog": Spell(
        id="frog",
        label="frog spell",
        dialogue="Ribbit, ribbit",
        effect="transform",
        turns_into="a friendly little prince",
        guards={"fear"},
    ),
    "glass": Spell(
        id="glass",
        label="glass-shine spell",
        dialogue="Let truth shine clear",
        effect="reveal",
        turns_into="a shining path",
        guards={"fog"},
    ),
}

HERO_NAMES = ["Lena", "Milo", "Nia", "Theo", "Pia", "Oren", "Lumi", "Rowan"]
HELPER_NAMES = ["the fairy", "the queen", "the old owl", "the river sprite"]
TRAITS = ["brave", "gentle", "curious", "patient", "kind"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mission: str
    relic: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
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


def mission_reaches_risk(mission: Mission, setting: Setting) -> bool:
    return "seek" in setting.affords and mission.risk in {"fog", "wind", "rock"}


def compatible_spell(mission: Mission, relic: Relic) -> Optional[Spell]:
    if mission.id == "mirror" and relic.id == "pearl":
        return SPELLS["glass"]
    if mission.id == "bottle" and relic.id == "seed":
        return SPELLS["frog"]
    if mission.id == "lantern" and relic.id == "seed":
        return SPELLS["glass"]
    return None


def predict_transformation(world: World, mission: Mission, relic: Relic) -> bool:
    return compatible_spell(mission, relic) is not None


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, helper: Entity, mission: Mission, relic: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, {hero.id} was a {world.facts['trait']} child "
        f"who loved a true and transparent mission."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {helper.id} promised to {mission.verb} "
        f"and keep {relic.phrase} safe on the way."
    )


def set_out(world: World, hero: Entity, mission: Mission, relic: Entity) -> None:
    hero.meters["travel"] += 1
    hero.memes["hope"] = hero.meme("hope") + 1
    world.say(
        f"One morning, {hero.id} took the first steps toward {mission.goal}. "
        f"{hero.pronoun().capitalize()} held {relic.it()} close and listened for signs in the trees."
    )


def warning(world: World, helper: Entity, hero: Entity, mission: Mission, relic: Entity) -> bool:
    if not mission_reaches_risk(mission, world.setting):
        return False
    hero.memes["worry"] = hero.meme("worry") + 1
    world.say(
        f'"Careful," said {helper.id}. "If the mist gets into {relic.it()}, '
        f'you may not see the way to {mission.goal}."'
    )
    world.facts["risk"] = mission.risk
    return True


def ask_question(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    hero.memes["curiosity"] = hero.meme("curiosity") + 1
    world.say(
        f'"Why must I go on this mission?" asked {hero.id}. '
        f'"Because some paths stay hidden until a kind heart walks them," replied {helper.id}.'
    )
    world.say(
        f'{hero.id} looked at the dark branches, then nodded. '
        f'{hero.pronoun().capitalize()} would keep going.'
    )


def transformation_scene(world: World, hero: Entity, helper: Entity, mission: Mission, relic: Entity) -> Optional[Spell]:
    spell = compatible_spell(mission, relic)
    if spell is None:
        return None
    hero.memes["trust"] = hero.meme("trust") + 1
    world.say(
        f"When the mist thickened, {helper.id} lifted {helper.pronoun('possessive')} paws and sang, "
        f'"{spell.dialogue}!"'
    )
    world.say(
        f"The {relic.label} glowed clear. A soft light touched {hero.id}, "
        f"and {hero.pronoun()} changed into {spell.turns_into} for a single shining moment."
    )
    hero.meters["transformed"] = 1
    hero.meters["path"] += 1
    world.facts["spell"] = spell.id
    return spell


def resolve(world: World, hero: Entity, helper: Entity, mission: Mission, relic: Entity, spell: Spell) -> None:
    hero.memes["joy"] = hero.meme("joy") + 1
    world.say(
        f"Now the clear path opened, and {hero.id} could see {mission.goal}. "
        f'{hero.id} smiled at {helper.id} and said, "I will remember this mission forever."'
    )
    world.say(
        f"By evening, the transformation faded, but the lesson stayed: "
        f'{hero.id} had learned that a transparent truth could lead to a brave ending.'
    )
    world.facts["resolved"] = True


def tell(setting: Setting, mission: Mission, relic_cfg: Relic, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Lena", "Nia", "Pia", "Lumi"} else "boy"))
    helper = world.add(Entity(id=helper_name, kind="character", type="fairy"))
    relic = world.add(Entity(id=relic_cfg.id, type=relic_cfg.label, label=relic_cfg.label, phrase=relic_cfg.phrase))
    world.facts.update(hero=hero, helper=helper, mission=mission, relic=relic_cfg, trait=trait, setting=setting)

    introduce(world, hero, helper, mission, relic)
    world.para()
    set_out(world, hero, mission, relic)
    warning(world, helper, hero, mission, relic)
    ask_question(world, hero, helper, mission)
    world.para()
    spell = transformation_scene(world, hero, helper, mission, relic)
    if spell:
        resolve(world, hero, helper, mission, relic, spell)
    else:
        world.say(
            f"The woods stayed silent, and the mission ended before a true change could begin."
        )
        world.facts["resolved"] = False
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission: Mission = _safe_fact(world, f, "mission")
    return [
        f"Write a fairy-tale story about a transparent mission that ends in a transformation.",
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} speak in dialogue while carrying {f['relic'].phrase}.",
        f"Write a short story for children in which a kind character follows a clear mission and learns something magical.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    mission: Mission = _safe_fact(world, f, "mission")
    relic: Relic = _safe_fact(world, f, "relic")
    qa = [
        QAItem(
            question=f"Who went on the transparent mission in the story?",
            answer=f"{hero.id} went on the mission with {helper.id} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} need to carry safely?",
            answer=f"{hero.id} needed to carry {relic.phrase} safely while following the mission.",
        ),
        QAItem(
            question=f"What changed when the mist grew thick?",
            answer=f"{hero.id} changed into a friendlier shape for a moment, because the clear spell opened the way.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end after the dialogue and transformation?",
                answer=f"The path opened, {hero.id} reached {mission.goal}, and the lesson stayed with them.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "transparent": [
        QAItem(
            question="What does transparent mean?",
            answer="Transparent means you can see through it, like clear glass or clean water.",
        )
    ],
    "mission": [
        QAItem(
            question="What is a mission?",
            answer="A mission is a special job or task that someone tries to finish with care.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when the characters speak to each other in words inside quotation marks.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another, often in a magical way.",
        )
    ],
    "fairy": [
        QAItem(
            question="What is a fairy in a fairy tale?",
            answer="A fairy is a small magical being found in many fairy tales.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mission"].tags) | {"dialogue", "transformation"}
    out: list[QAItem] = []
    for tag in ["transparent", "mission", "dialogue", "transformation", "fairy"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mission is valid when the setting can host it and the relic can be
% protected by the matching spell.
mission_valid(S, M, R) :- setting(S), mission(M), relic(R), can_host(S, M), protects(M, R).

% A spell protects a relic if its guards match the mission's risk and it is the
% compatible counterpart for the mission/relic pair.
protects(M, R) :- mission(M), relic(R), spell(P), matches(M, R, P).

% A story is a fairy-tale compatible story if it has a valid mission.
story_ok(S, M, R) :- mission_valid(S, M, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("can_host", sid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_keyword", mid, m.keyword))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r.fragile:
            lines.append(asp.fact("fragile", rid))
    for spid, sp in SPELLS.items():
        lines.append(asp.fact("spell", spid))
    lines.append(asp.fact("matches", "mirror", "pearl", "glass"))
    lines.append(asp.fact("matches", "lantern", "seed", "glass"))
    lines.append(asp.fact("matches", "bottle", "seed", "frog"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_triples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {
        (sid, mid, rid)
        for sid, s in SETTINGS.items()
        for mid, m in MISSIONS.items()
        for rid, r in RELICS.items()
        if mission_reaches_risk(m, s) and compatible_spell(m, r) is not None
    }
    cl = set(asp_valid_triples())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: transparent mission and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    combos = []
    for sid, s in SETTINGS.items():
        for mid, m in MISSIONS.items():
            for rid, r in RELICS.items():
                if mission_reaches_risk(m, s) and compatible_spell(m, r) is not None:
                    combos.append((sid, mid, rid))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
        and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, mission, relic = rng.choice(list(filtered))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, mission=mission, relic=relic, hero=hero, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MISSIONS, params.mission), _safe_lookup(RELICS, params.relic), params.hero, params.helper, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
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
    StoryParams(setting="wood", mission="mirror", relic="pearl", hero="Lena", helper="the fairy", trait="brave"),
    StoryParams(setting="castle", mission="lantern", relic="seed", hero="Milo", helper="the queen", trait="gentle"),
    StoryParams(setting="lake", mission="bottle", relic="seed", hero="Nia", helper="the river sprite", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_triples()
        print(f"{len(triples)} compatible fairy-tale stories:\n")
        for sid, mid, rid in triples:
            print(f"  {sid:8} {mid:8} {rid:8}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
            header = f"### {p.hero}: {p.mission} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
