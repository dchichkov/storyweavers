#!/usr/bin/env python3
"""
A standalone story world for a small Adventure tale with foreshadowing.

Premise:
A brave child-adventurer explores a place, finds a blocked path, notices a clue
that foreshadows the solution, and uses a shove plus a good answer to move
forward.

The simulation tracks:
- physical meters: block, dust, progress, clue, key, etc.
- emotional memes: love, worry, courage, surprise, relief

The story variants stay close to one tiny Adventure-style pattern:
setup -> foreshadowing -> obstacle -> shove + answer -> resolution.
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

    hero: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    affords: set[str] = field(default_factory=set)
    mood: str = "mysterious"
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
class Challenge:
    id: str
    verb: str
    gerund: str
    shove: str
    answer: str
    obstacle: str
    clue: str
    foreshadow: str
    progress_gain: float = 1.0
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
class Reward:
    id: str
    label: str
    phrase: str
    region: str
    glow: str
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
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "cave": Setting(place="the cave", affords={"maze", "door", "riddle"}, mood="echoing"),
    "ruins": Setting(place="the old ruins", affords={"maze", "door", "riddle"}, mood="ancient"),
    "forest": Setting(place="the deep forest", affords={"maze", "door", "riddle"}, mood="green"),
    "tower": Setting(place="the stone tower", affords={"door", "riddle"}, mood="windy"),
}


CHALLENGES = {
    "boulder": Challenge(
        id="boulder",
        verb="push through the blocked path",
        gerund="exploring the hidden trail",
        shove="shove the boulder aside",
        answer="answer the stone riddle",
        obstacle="a boulder blocked the way",
        clue="a small arrow scratched into the rock pointed left",
        foreshadow="the scratched arrow was a clue that the path would turn on its own",
        progress_gain=1.0,
    ),
    "door": Challenge(
        id="door",
        verb="open the sealed door",
        gerund="following the map",
        shove="shove the door until it gave",
        answer="answer the door's carved question",
        obstacle="a sealed door stood shut",
        clue="a tiny keyhole glittered in the torchlight",
        foreshadow="the little keyhole hinted that one careful answer would matter later",
        progress_gain=1.0,
    ),
    "riddle": Challenge(
        id="riddle",
        verb="cross the whispering hall",
        gerund="listening for secret sounds",
        shove="shove the loose stone",
        answer="answer the guardian's riddle",
        obstacle="a guardian blocked the hall with a riddle",
        clue="three marks on the wall matched the riddle's answer",
        foreshadow="the three marks were a hint that the answer was waiting in plain sight",
        progress_gain=1.0,
    ),
}


REWARDS = {
    "gem": Reward(
        id="gem",
        label="gem",
        phrase="a bright river gem",
        region="hand",
        glow="warm",
    ),
    "map": Reward(
        id="map",
        label="map",
        phrase="an old treasure map",
        region="pocket",
        glow="pale",
    ),
    "bell": Reward(
        id="bell",
        label="bell",
        phrase="a tiny silver bell",
        region="palm",
        glow="soft",
    ),
}


@dataclass
class StoryParams:
    place: str
    challenge: str
    reward: str
    name: str
    gender: str
    sidekick: str
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


GIRL_NAMES = ["Mia", "Luna", "Zoe", "Nina", "Ava", "Iris", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Noah", "Eli", "Kai"]
SIDEKICKS = ["fox", "bird", "dog", "cat", "sparrow"]
TRAITS = ["curious", "brave", "spry", "bold", "bright"]


class WorldState:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch in setting.affords:
            for reward in REWARDS:
                combos.append((place, ch, reward))
    return combos


def explain_rejection() -> str:
    return "(No story: that combination does not fit this Adventure world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
        and (getattr(args, "reward", None) is None or c[2] == getattr(args, "reward", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, reward = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, reward=reward, name=name, gender=gender, sidekick=sidekick, trait=trait)


def _hero_title(hero: Entity) -> str:
    return f"little {next((t for t in hero.traits if t != 'little'), 'brave')} {hero.type}"


def narrate_story(world: World, params: StoryParams) -> World:
    ch = _safe_lookup(CHALLENGES, params.challenge)
    reward = _safe_lookup(REWARDS, params.reward)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait, "stubborn"]))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="animal", label=params.sidekick))
    prize = world.add(Entity(id=reward.id, type=reward.id, label=reward.label, phrase=reward.phrase, owner=hero.id))
    prize.meters["glow"] = 1.0

    hero.memes["love"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.meters["progress"] = 0.0

    world.say(f"{hero.id} was a {_hero_title(hero)} who loved {ch.gerund}.")
    world.say(f"{hero.pronoun().capitalize()} carried {reward.phrase} in {hero.pronoun('possessive')} pack, and {sidekick.label or params.sidekick} padded along beside {hero.pronoun('object')}.")
    world.say(f"The place was {world.setting.mood}, and {ch.foreshadow}.")

    world.para()
    world.say(f"At {world.setting.place}, {ch.obstacle}.")
    world.say(f"Then {hero.id} noticed that {ch.clue}.")
    hero.memes["wonder"] = 1.0

    world.para()
    world.say(f"{hero.id} took a breath and decided to {ch.shove}.")
    hero.meters["effort"] = 1.0
    hero.meters["progress"] += ch.progress_gain
    world.say(f"{hero.id} also remembered to {ch.answer}, because the clue had already given away the secret.")
    hero.memes["courage"] = 1.0
    world.facts["answered"] = True

    world.para()
    prize.meters["glow"] = 2.0
    hero.memes["relief"] = 1.0
    hero.meters["progress"] += 1.0
    world.say(f"The boulder moved, the door opened, or the guardian stepped aside, and the way ahead at {world.setting.place} finally shone open.")
    world.say(f"At last, {hero.id} reached {reward.phrase}, and {hero.id} smiled because {hero.pronoun('possessive')} brave {ch.verb} had worked.")
    world.say(f"The little {params.sidekick} hopped in a circle while {hero.id} held the {reward.label} up like a tiny treasure.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        prize=prize,
        challenge=ch,
        reward=reward,
        params=params,
        resolved=True,
        foreshadowing=True,
        place=world.setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    reward = _safe_fact(world, f, "reward")
    return [
        f"Write a short Adventure story for a child named {hero.id} who loves to {ch.gerund} and finds {reward.phrase}.",
        f"Tell a foreshadowing tale where a clue hints that {hero.id} must {ch.answer} before {hero.id} can go on.",
        f"Write a child-friendly adventure story that includes a shove, an answer, and a hidden clue at {f['place']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    reward = _safe_fact(world, f, "reward")
    qa = [
        QAItem(
            question=f"What did {hero.id} love to do in this adventure?",
            answer=f"{hero.id} loved {ch.gerund}, even before the blocked path appeared.",
        ),
        QAItem(
            question=f"What clue foreshadowed the solution?",
            answer=f"The clue was that {ch.clue}. It hinted that the answer would matter later.",
        ),
        QAItem(
            question=f"What did {hero.id} need to do to get past the obstacle?",
            answer=f"{hero.id} needed to {ch.shove} and then {ch.answer}. That let the path open and the {reward.label} be reached.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with {hero.id} reaching {reward.phrase} and smiling because the foreshadowed clue had helped the adventure succeed.",
            )
        )
    return qa


KNOWLEDGE = {
    "shove": [
        (
            "What does it mean to shove something?",
            "To shove something means to push it with a lot of force, usually with your hands or body.",
        )
    ],
    "answer": [
        (
            "What is an answer?",
            "An answer is what you say or do to solve a question or a problem.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a small clue that hints at something important that will happen later.",
        )
    ],
    "adventure": [
        (
            "What is an adventure?",
            "An adventure is a story or trip with exciting challenges, surprises, and brave choices.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["shove"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["answer"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["foreshadowing"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["adventure"])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = narrate_story(World(_safe_lookup(SETTINGS, params.place)), params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="cave", challenge="boulder", reward="gem", name="Mia", gender="girl", sidekick="fox", trait="brave"),
    StoryParams(place="forest", challenge="riddle", reward="map", name="Leo", gender="boy", sidekick="bird", trait="curious"),
    StoryParams(place="ruins", challenge="door", reward="bell", name="Ava", gender="girl", sidekick="dog", trait="bold"),
]


ASP_RULES = r"""
% A story is valid when the setting supports the challenge.
valid(Place, Ch, R) :- affords(Place, Ch), reward(R).

% Foreshadowing is present for every supported challenge.
foreshadowed(Place, Ch) :- affords(Place, Ch).

% The adventure twin: a supported challenge with a reward is a story-worthy combo.
story(Place, Ch, R) :- valid(Place, Ch, R), foreshadowed(Place, Ch).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for ch in sorted(setting.affords):
            lines.append(asp.fact("affords", place, ch))
    for ch in CHALLENGES:
        lines.append(asp.fact("challenge", ch))
    for r in REWARDS:
        lines.append(asp.fact("reward", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    return sorted(set(asp.atoms(model, "story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid adventure combos:")
        for place, ch, reward in combos:
            print(f"  {place:8} {ch:8} {reward:6}")
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
            header = f"### {p.name}: {p.challenge} at {p.place} (reward: {p.reward})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
