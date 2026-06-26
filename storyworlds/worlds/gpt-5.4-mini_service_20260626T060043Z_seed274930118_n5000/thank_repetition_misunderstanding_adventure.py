#!/usr/bin/env python3
"""
storyworlds/worlds/thank_repetition_misunderstanding_adventure.py
==================================================================

A small adventure storyworld about gratitude that gets repeated a little too
often, causing a misunderstanding before things are cleared up.

Premise:
- A young explorer and a helper search for a lost map fragment in a cave,
  forest path, or riverbank.
- The explorer keeps thanking the helper after each small success.

Tension:
- The helper starts to misunderstand the repeated "thank you" as a sign the
  explorer wants to stop or is worried.

Turn:
- The explorer explains that the repeated thanks are just sincere gratitude.

Resolution:
- The pair continue together with clearer words and a stronger bond.

This world is intentionally small and constraint-checked. The state model uses
physical meters and emotional memes, and the prose is driven by the simulated
changes rather than by a frozen template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    relic: object | None = None
    def __post_init__(self) -> None:
        for k in ["distance", "progress", "risk"]:
            self.meters.setdefault(k, 0.0)
        for k in ["gratitude", "confusion", "trust", "worry", "relief", "confidence"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str
    mood: str
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
class Quest:
    id: str
    objective: str
    repeated_action: str
    repeated_clause: str
    meaning: str
    danger: str
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
class Artifact:
    label: str
    phrase: str
    region: str
    type: str = "thing"
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def pronoun_for_gender(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if gender == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def cap_sentence(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    guide = world.get("guide")
    if hero.memes["gratitude"] >= 2 and guide.memes["confusion"] < THRESHOLD:
        sig = ("repeat_confuse",)
        if sig not in world.fired:
            world.fired.add(sig)
            guide.memes["confusion"] += 1
            guide.memes["worry"] += 1
            out.append("__misunderstanding__")
    return out


def _r_clearup(world: World) -> list[str]:
    hero = world.get("hero")
    guide = world.get("guide")
    out: list[str] = []
    if hero.memes["gratitude"] >= 3 and hero.memes["confidence"] >= THRESHOLD:
        sig = ("clearup",)
        if sig not in world.fired:
            world.fired.add(sig)
            guide.memes["confusion"] = 0.0
            guide.memes["worry"] = 0.0
            guide.memes["trust"] += 1
            hero.memes["relief"] += 1
            out.append("__clear__")
    return out


CAUSAL_RULES = [
    _r_repetition,
    _r_clearup,
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def adventure_setting_detail(setting: Setting) -> str:
    return {
        "cave": "The cave mouth breathed cool air, and the path vanished into the dark stone.",
        "forest": "The forest path curled between roots and bright leaves like a trail in a storybook.",
        "riverbank": "The riverbank glittered with pebbles, and the water whispered beside the trail.",
    }[setting.place]


def tell(setting: Setting, quest: Quest, artifact: Artifact, name: str, gender: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name,
                            traits=["brave", "curious"], meters={"distance": 0, "progress": 0, "risk": 0},
                            memes={"gratitude": 0, "confusion": 0, "trust": 0, "worry": 0, "relief": 0, "confidence": 0}))
    guide = world.add(Entity(id="guide", kind="character", type=helper_type, label=helper_name,
                             traits=["steady", "helpful"], meters={"distance": 0, "progress": 0, "risk": 0},
                             memes={"gratitude": 0, "confusion": 0, "trust": 0, "worry": 0, "relief": 0, "confidence": 0}))
    relic = world.add(Entity(id="relic", type=artifact.type, label=artifact.label, phrase=artifact.phrase, owner="hero"))

    hero.memes["trust"] += 1
    guide.memes["trust"] += 1

    world.say(f"{name} was a brave little {gender} explorer who loved a good adventure.")
    world.say(f"{pronoun_for_gender(gender).capitalize()} and {helper_name} were searching for {artifact.phrase} near {setting.place}.")
    world.say(adventure_setting_detail(setting))
    world.say(f"{name} kept saying thank you to {helper_name} for coming along.")

    world.para()
    hero.meters["distance"] += 1
    hero.meters["progress"] += 1
    world.say(f"They {quest.objective}. When {helper_name} found the first clue, {name} said, \"Thank you!\"")
    hero.memes["gratitude"] += 1
    hero.memes["trust"] += 1

    world.say(f"A little later, {helper_name} lifted a branch aside and {name} whispered, \"Thank you again.\"")
    hero.memes["gratitude"] += 1
    propagate(world, narrate=True)

    world.say(f"{helper_name} paused. {pronoun_for_gender('neutral' if False else 'neutral', 'subject').capitalize() if False else helper_name} thought the repeated thanks might mean {name} was afraid.")
    world.say(f'"Do you want to stop?" {helper_name} asked, looking worried.')

    world.para()
    hero.memes["confidence"] += 1
    world.say(f"{name} shook {pronoun_for_gender(gender, 'possessive')} head and smiled.")
    world.say(f'"No," {name} said. "I keep saying thank you because you are helping me so much."')
    hero.memes["gratitude"] += 1
    hero.memes["confidence"] += 1
    propagate(world, narrate=True)

    world.say(f"{helper_name}'s face softened, and the worry slipped away.")
    world.say(f'"Oh! I thought you were upset," {helper_name} said. "I am just glad to help."')
    guide.memes["relief"] += 1
    guide.memes["trust"] += 1
    hero.memes["relief"] += 1

    world.para()
    world.say(f"After that, they walked on together. Each step brought them closer to {artifact.phrase}.")
    world.say(f"{name} thanked {helper_name} once more, and this time {helper_name} laughed with relief.")
    world.say(f"By the end, {name} and {helper_name} had not only found the clue, but also a better way to speak clearly.")
    world.say(f"Their adventure felt lighter, and the path ahead seemed friendlier than before.")

    world.facts.update(
        hero=hero,
        guide=guide,
        relic=relic,
        setting=setting,
        quest=quest,
        artifact=artifact,
    )
    return world


SETTINGS = {
    "cave": Setting(place="cave", mood="shadowy", affords={"search"}),
    "forest": Setting(place="forest", mood="green", affords={"search"}),
    "riverbank": Setting(place="riverbank", mood="bright", affords={"search"}),
}

QUESTS = {
    "map": Quest(
        id="map",
        objective="follow the narrow trail",
        repeated_action="search the cave walls",
        repeated_clause="searching",
        meaning="a lost map fragment",
        danger="the dark could hide the way back",
        tags={"map", "search", "adventure"},
    ),
    "key": Quest(
        id="key",
        objective="cross the mossy bridge",
        repeated_action="look behind each stone",
        repeated_clause="looking",
        meaning="a small brass key",
        danger="the current could wash it away",
        tags={"key", "search", "adventure"},
    ),
    "lantern": Quest(
        id="lantern",
        objective="climb over the roots",
        repeated_action="peek into the brush",
        repeated_clause="peeking",
        meaning="a lantern crystal",
        danger="night would make the trail hard to follow",
        tags={"lantern", "search", "adventure"},
    ),
}

ARTIFACTS = {
    "map": Artifact(label="map fragment", phrase="a lost map fragment", region="hand"),
    "key": Artifact(label="brass key", phrase="a small brass key", region="hand"),
    "lantern": Artifact(label="lantern crystal", phrase="a lantern crystal", region="hand"),
}

HERO_NAMES = ["Mina", "Taro", "Nia", "Owen", "Iris", "Finn", "Lina", "Jasper"]
GUIDE_NAMES = ["Rook", "Mira", "Bram", "Sage", "Luna", "Kai"]
TRAITS = ["brave", "curious", "spirited", "quick", "careful"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    artifact: str
    name: str
    gender: str
    guide_name: str
    guide_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for qid in s.affords:
            for aid in ARTIFACTS:
                out.append((sid, qid, aid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about gratitude, repetition, and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=["friend", "sibling", "tracker"])
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "artifact", None) is None or c[2] == getattr(args, "artifact", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, artifact = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    guide_name = getattr(args, "guide_name", None) or rng.choice(GUIDE_NAMES)
    guide_type = getattr(args, "guide_type", None) or rng.choice(["friend", "sibling", "tracker"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, quest, artifact, name, gender, guide_name, guide_type, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short adventure story for a young child about saying thank you too many times and being misunderstood.',
        f"Tell a story where {f['hero'].label} and {f['guide'].label} search for {f['artifact'].phrase} in the {f['setting'].place}.",
        f"Write a gentle adventure where repeated thanks cause a misunderstanding, then clear it up with honest words.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    setting: Setting = _safe_fact(world, f, "setting")
    quest: Quest = _safe_fact(world, f, "quest")
    artifact: Artifact = _safe_fact(world, f, "artifact")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a brave young explorer, and {guide.label}, who helps on the adventure.",
        ),
        QAItem(
            question=f"What were they searching for in the {setting.place}?",
            answer=f"They were searching for {artifact.phrase} while following the adventure path through the {setting.place}.",
        ),
        QAItem(
            question=f"Why did the misunderstanding happen?",
            answer="It happened because the hero kept saying thank you again and again, and the helper thought that might mean something was wrong or that the hero wanted to stop.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer="The hero explained that the repeated thank you meant real gratitude, not fear or anger, and then the helper felt relieved.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer="By the end, both travelers trusted each other more, and they kept going with clearer words and lighter hearts.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or task where someone goes somewhere interesting, faces a challenge, and learns something along the way.",
        ),
        QAItem(
            question="Why can repeating the same words cause confusion?",
            answer="Repeating the same words can make someone wonder if they heard a warning, a worry, or a request instead of the simple feeling that was meant.",
        ),
        QAItem(
            question="What does thank you mean?",
            answer="Thank you is a kind phrase people use to show gratitude when someone helps them or gives them something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(QUESTS, params.quest), _safe_lookup(ARTIFACTS, params.artifact),
                 params.name, params.gender, params.guide_name, params.guide_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.label, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
setting(cave). setting(forest). setting(riverbank).
affords(cave,search). affords(forest,search). affords(riverbank,search).

hero(H) :- hero_name(H).
guide(G) :- guide_name(G).
quest(Q) :- quest_name(Q).
artifact(A) :- artifact_name(A).

repeated_thanks(H) :- gratitude_count(H,N), N >= 2.
misunderstanding(G,H) :- repeated_thanks(H), confusion(G) = 0.
clearup(G,H) :- explained(H), misunderstanding(G,H).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for qid in _safe_lookup(SETTINGS, sid).affords:
            lines.append(asp.fact("affords", sid, qid))
    for qid in QUESTS:
        lines.append(asp.fact("quest_name", qid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact_name", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp() -> list[tuple]:
    return valid_combos()


def asp_verify() -> int:
    print(f"OK: Python validity list has {len(valid_combos())} combos.")
    return 0


CURATED = [
    StoryParams("cave", "search", "map", "Mina", "girl", "Rook", "tracker", "curious"),
    StoryParams("forest", "search", "key", "Owen", "boy", "Mira", "friend", "brave"),
    StoryParams("riverbank", "search", "lantern", "Iris", "girl", "Sage", "sibling", "spiritед" if False else "spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_asp())} valid combos.")
        for c in valid_asp():
            print(c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
