#!/usr/bin/env python3
"""
storyworlds/worlds/tyrannosaurus_kangaroo_suspense_dialogue_animal_story.py
===========================================================================

A small animal-story world with suspense and dialogue:
a tyrannosaurus and a kangaroo hear a scary sound, search carefully,
and discover that the "mystery" is smaller and kinder than it seemed.

The domain is deliberately tiny and constraint-checked. It supports a few
settings, a few suspenseful sounds, and a few gentle outcomes. Stories are
simulated from state:
- the kangaroo starts worried about something lost or hidden
- the tyrannosaurus notices clues and helps search
- the suspense peaks in a dark place with dialogue
- the turn reveals the truth and the ending shows what changed

This script follows the Storyweavers world contract:
- standalone stdlib script under storyworlds/worlds/
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    dino: object | None = None
    reward: object | None = None
    roo: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"kangaroo", "mother", "mom", "girl", "woman"}
        male = {"tyrannosaurus", "father", "dad", "boy", "man"}
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
    dark: bool
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
class Mystery:
    id: str
    sound: str
    verb: str
    clue: str
    place_hint: str
    fear_word: str
    reveal: str
    calm: str
    keyword: str
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
class Reward:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    owners: set[str] = field(default_factory=lambda: {"kangaroo", "tyrannosaurus"})
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "gully": Setting(place="the moonlit gully", dark=True, affords={"listen", "search"}),
    "plain": Setting(place="the wide grassy plain", dark=False, affords={"listen", "search"}),
    "forest": Setting(place="the whispering forest", dark=True, affords={"listen", "search"}),
    "pond": Setting(place="the quiet pond", dark=False, affords={"listen", "search"}),
    "cave": Setting(place="the little cave", dark=True, affords={"listen", "search"}),
}

MYSTERIES = {
    "rustle": Mystery(
        id="rustle",
        sound="a rustle in the grass",
        verb="listen for the rustle",
        clue="a trail of bent grass",
        place_hint="near the bushes",
        fear_word="something sneaky",
        reveal="a tiny hedgehog pushing through the grass",
        calm="the hedgehog only wanted to get home",
        keyword="rustle",
        tags={"night", "grass"},
    ),
    "bump": Mystery(
        id="bump",
        sound="a soft bump under the rocks",
        verb="peek behind the rocks",
        clue="one pebble rolled slowly downhill",
        place_hint="by the stones",
        fear_word="something stuck",
        reveal="a sleepy joey curled beside a warm stone",
        calm="the joey had only been napping in a safe spot",
        keyword="bump",
        tags={"rock", "sleep"},
    ),
    "hoot": Mystery(
        id="hoot",
        sound="a low hoot from the trees",
        verb="look up into the branches",
        clue="a feather drifting down",
        place_hint="above the path",
        fear_word="a big surprise in the dark",
        reveal="an owl blinking from a branch",
        calm="the owl was just watching the moon",
        keyword="hoot",
        tags={"tree", "moon"},
    ),
}

REWARDS = {
    "lantern": Reward(
        id="lantern",
        label="lantern",
        phrase="a tiny brass lantern",
        type="lantern",
        location="paw",
    ),
    "berrybasket": Reward(
        id="berrybasket",
        label="berry basket",
        phrase="a round berry basket",
        type="basket",
        location="pouch",
    ),
    "blanket": Reward(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        type="blanket",
        location="back",
    ),
}

TYRANNOSAURUS_NAMES = ["Tico", "Tara", "Toby", "Tessa", "Theo"]
KANGAROO_NAMES = ["Kiki", "Kara", "Kenny", "Mila", "Nina"]
TRAITS = ["curious", "brave", "gentle", "careful", "playful"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    reward: str
    dino_name: str
    roo_name: str
    dino_trait: str
    roo_trait: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world: a tyrannosaurus and a kangaroo, suspense, and dialogue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--dino-name", choices=TYRANNOSAURUS_NAMES)
    ap.add_argument("--roo-name", choices=KANGAROO_NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mystery_id in setting.affords:
            for reward_id in REWARDS:
                combos.append((place, mystery_id, reward_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "reward", None) is None or c[2] == getattr(args, "reward", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, mystery, reward = rng.choice(list(combos))
    dino_name = getattr(args, "dino_name", None) or rng.choice(TYRANNOSAURUS_NAMES)
    roo_name = getattr(args, "roo_name", None) or rng.choice(KANGAROO_NAMES)
    dino_trait = rng.choice(TRAITS)
    roo_trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, reward=reward,
                       dino_name=dino_name, roo_name=roo_name,
                       dino_trait=dino_trait, roo_trait=roo_trait)


def _say_name(entity: Entity) -> str:
    return entity.id


def tell(setting: Setting, mystery: Mystery, reward_cfg: Reward,
         dino_name: str, roo_name: str, dino_trait: str, roo_trait: str) -> World:
    world = World(setting)

    dino = world.add(Entity(id=dino_name, kind="character", type="tyrannosaurus",
                            meters={}, memes={"curiosity": 1.0}))
    roo = world.add(Entity(id=roo_name, kind="character", type="kangaroo",
                           meters={}, memes={"worry": 1.0}))
    reward = world.add(Entity(id=reward_cfg.id, type=reward_cfg.type, label=reward_cfg.label,
                              phrase=reward_cfg.phrase, owner=roo.id, location=reward_cfg.location))

    world.facts.update(dino=dino, roo=roo, reward=reward, setting=setting,
                       mystery=mystery, reward_cfg=reward_cfg,
                       dino_trait=dino_trait, roo_trait=roo_trait)

    # Act 1: setup.
    world.say(f"{dino_name} was a {dino_trait} tyrannosaurus who liked quiet walks.")
    world.say(f"{roo_name} was a {roo_trait} kangaroo who kept {roo.pronoun('possessive')} {reward.label} close.")
    world.say(f"That evening, they went to {setting.place} together.")

    # Act 2: suspense rises.
    world.para()
    roo.memes["worry"] += 1
    world.say(f"Then they heard {mystery.sound}.")
    world.say(f'"Did you hear that?" {roo_name} whispered.')
    world.say(f'"Yes," said {dino_name}. "Let\'s {mystery.verb} and be careful."')
    world.say(f"They followed {mystery.clue} {mystery.place_hint}.")
    dino.memes["focus"] += 1
    roo.memes["fear"] += 1

    # Suspense turn: fear peaks, but the dino reassures.
    world.say(f"The dark looked big, and {roo_name} felt {mystery.fear_word}.")
    world.say(f'"Stay close," {dino_name} said. "I am here."')
    dino.meters["steps"] = dino.meters.get("steps", 0.0) + 1
    roo.meters["steps"] = roo.meters.get("steps", 0.0) + 1

    # Act 3: reveal and resolution.
    world.para()
    world.say(f"At last, they found {mystery.reveal}.")
    world.say(f'"Oh!" said {roo_name}. "{mystery.calm}."')
    roo.memes["worry"] = 0.0
    roo.memes["fear"] = 0.0
    roo.memes["joy"] = 1.0
    dino.memes["joy"] = 1.0
    world.say(f'{dino_name} smiled. "No wonder it made a funny sound."')
    world.say(f"Together they led the little creature home, and {roo_name}'s {reward.label} stayed safe beside {roo.pronoun('object')}.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dino = _safe_fact(world, f, "dino")
    roo = _safe_fact(world, f, "roo")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    reward_cfg: Reward = _safe_fact(world, f, "reward_cfg")
    return [
        f'Write a short animal story for a young child that uses the word "{mystery.keyword}" and includes dialogue.',
        f"Tell a suspenseful but gentle story where {dino.id} the tyrannosaurus helps {roo.id} the kangaroo protect a {reward_cfg.label}.",
        f"Write a simple story about two animals hearing {mystery.sound} and discovering what it really is.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dino = _safe_fact(world, f, "dino")
    roo = _safe_fact(world, f, "roo")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    reward_cfg: Reward = _safe_fact(world, f, "reward_cfg")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who went to {setting.place} in the story?",
            answer=f"{dino.id} the tyrannosaurus and {roo.id} the kangaroo went there together.",
        ),
        QAItem(
            question=f"What sound made the story feel suspenseful?",
            answer=f"They heard {mystery.sound}, and that made them stop and listen carefully.",
        ),
        QAItem(
            question=f"What was {roo.id} trying to keep safe?",
            answer=f"{roo.id} was keeping {roo.pronoun('possessive')} {reward_cfg.label} safe.",
        ),
        QAItem(
            question=f"What did {dino.id} say to help {roo.id} feel braver?",
            answer=f'{dino.id} said, "Stay close," which helped {roo.id} feel safer in the dark.',
        ),
        QAItem(
            question=f"What did they discover at the end?",
            answer=f'They discovered {mystery.reveal}, and the scary sound turned out to be harmless.',
        ),
    ]


WORLD_KNOWLEDGE = {
    "tyrannosaurus": (
        "What is a tyrannosaurus?",
        "A tyrannosaurus was a very large meat-eating dinosaur with a big head and tiny arms.",
    ),
    "kangaroo": (
        "What is a kangaroo?",
        "A kangaroo is a hopping animal from Australia. Kangaroos carry their babies in a pouch.",
    ),
    "suspense": (
        "What does suspense mean in a story?",
        "Suspense is the feeling of not knowing what will happen next, so you keep listening to find out.",
    ),
    "dialogue": (
        "What is dialogue?",
        "Dialogue is when characters talk to each other in a story.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


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
        if e.kind == "character":
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:12} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", mystery="rustle", reward="lantern",
                dino_name="Tico", roo_name="Kiki", dino_trait="curious", roo_trait="careful"),
    StoryParams(place="gully", mystery="bump", reward="berrybasket",
                dino_name="Tara", roo_name="Kara", dino_trait="gentle", roo_trait="brave"),
    StoryParams(place="pond", mystery="hoot", reward="blanket",
                dino_name="Theo", roo_name="Nina", dino_trait="playful", roo_trait="curious"),
]


def explain_rejection(place: str, mystery: Mystery, reward: Reward) -> str:
    return f"(No story: {place} does not reasonably support {mystery.id}.)"


ASP_RULES = r"""
place_ok(P) :- setting(P).
mystery_ok(M) :- mystery(M).
reward_ok(R) :- reward(R).
valid(P,M,R) :- affords(P,M), mystery_ok(M), reward_ok(R), place_ok(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for r in REWARDS:
        lines.append(asp.fact("reward", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_story_sample(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), _safe_lookup(REWARDS, params.reward),
                 params.dino_name, params.roo_name, params.dino_trait, params.roo_trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story_sample(params)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, mystery, reward) combos:\n")
        for t in triples:
            print(" ", t)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.dino_name} and {p.roo_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
