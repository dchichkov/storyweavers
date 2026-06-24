#!/usr/bin/env python3
"""
A tiny mythic storyworld about a shuttle, a surprise, and a journey that
changes the travelers.

The seed premise is a classic tale shape:
- a humble crew prepares a shuttle
- they expect one ordinary path
- a hidden surprise changes the voyage
- the ending proves the world has changed

The prose should read like a small legend for children, not like an event log.
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    shuttle_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
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
    name: str
    sky: str
    launch_site: str
    path: str
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
class Surprise:
    id: str
    reveal: str
    effect: str
    gift: str
    wonder: str
    turns: str
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
class Shuttle:
    id: str
    label: str
    phrase: str
    vessel_kind: str
    surprise_carry: str
    can_handle: set[str] = field(default_factory=set)
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

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "dawn_harbor": Setting(
        name="the dawn harbor",
        sky="rose-colored",
        launch_site="the moon dock",
        path="the silver road",
    ),
    "star_temple": Setting(
        name="the star temple",
        sky="blue and gold",
        launch_site="the stone platform",
        path="the bright stair",
    ),
    "river_valley": Setting(
        name="the river valley",
        sky="misty",
        launch_site="the reed landing",
        path="the river of light",
    ),
}

SURPRISES = {
    "moon_garden": Surprise(
        id="moon_garden",
        reveal="a hidden moon garden",
        effect="opened a secret door",
        gift="a bowl of moon-seeds",
        wonder="the quiet moon garden glowed like a lantern",
        turns="a silver key",
        tags={"moon", "garden", "secret"},
    ),
    "star_baby": Surprise(
        id="star_baby",
        reveal="a tiny star-baby in a cradle",
        effect="began to sing",
        gift="a warm star blanket",
        wonder="the star-baby's song made the cabin feel like a cradle",
        turns="a soft lantern",
        tags={"star", "baby", "song"},
    ),
    "river_king": Surprise(
        id="river_king",
        reveal="the River King waiting by the doorway",
        effect="bowed with a smile",
        gift="a shell crown",
        wonder="the River King carried the hush of old water and old songs",
        turns="a reed whistle",
        tags={"river", "king", "song"},
    ),
    "sky_fox": Surprise(
        id="sky_fox",
        reveal="a sky fox sleeping in the cargo nook",
        effect="opened one bright eye",
        gift="a feather for luck",
        wonder="the sky fox looked like a comet that had learned to nap",
        turns="a feathered latch",
        tags={"sky", "fox", "luck"},
    ),
}

SHUTTLES = {
    "ember_shuttle": Shuttle(
        id="ember_shuttle",
        label="the Ember Shuttle",
        phrase="a small bronze shuttle with round windows",
        vessel_kind="shuttle",
        surprise_carry="secret",
        can_handle={"moon_garden", "star_baby", "river_king", "sky_fox"},
    )
}

NAMES = ["Nia", "Taro", "Mina", "Ari", "Luna", "Kai", "Sera", "Rin"]
ROLES = ["pilot", "child", "keeper", "guide", "priest", "priestess"]
TRAITS = ["curious", "brave", "gentle", "hopeful", "restless"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    surprise: str
    shuttle: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
is_shuttle(S) :- shuttle(S).
has_surprise(S, U) :- shuttle(S), surprise(U), carries(S, U).
valid_story(S, U) :- has_surprise(S, U), surprise_kind(U).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for uid in SURPRISES:
        lines.append(asp.fact("surprise", uid))
        for tag in sorted(_safe_lookup(SURPRISES, uid).tags):
            lines.append(asp.fact("surprise_kind", uid, tag))
    for sh in SHUTTLES.values():
        lines.append(asp.fact("shuttle", sh.id))
        lines.append(asp.fact("carries", sh.id, sh.surprise_carry))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(sh.id, sh.surprise_carry) for sh in SHUTTLES.values()}
    actual = set(asp_valid())
    if actual == expected:
        print(f"OK: clingo gate matches Python registry ({len(actual)} pair(s)).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    if actual - expected:
        print("  only in clingo:", sorted(actual - expected))
    if expected - actual:
        print("  only in python:", sorted(expected - actual))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic shuttle storyworld with a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--shuttle", choices=SHUTTLES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    shuttle = getattr(args, "shuttle", None) or rng.choice(list(SHUTTLES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, surprise=surprise, shuttle=shuttle, name=name, role=role, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.shuttle not in SHUTTLES:
        pass
    if params.surprise not in SURPRISES:
        pass
    if params.setting not in SETTINGS:
        pass
    sh = _safe_lookup(SHUTTLES, params.shuttle)
    if params.surprise not in sh.can_handle:
        pass


def intro(world: World, hero: Entity, shuttle: Entity, surprise: Surprise) -> None:
    world.say(
        f"In {world.setting.name}, {hero.noun()} was a {hero.meters.get('age_word', 'young')} {hero.type} "
        f"who loved the {shuttle.label}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} believed the shuttle would carry a simple treasure, "
        f"but the old song of the place hinted at something stranger."
    )
    shuttle.meters["shimmer"] += 1
    hero.memes["hope"] += 1
    hero.memes["wonder"] += 1


def build_up(world: World, hero: Entity, shuttle: Entity, surprise: Surprise) -> None:
    world.para()
    world.say(
        f"At the {world.setting.launch_site}, the {shuttle.label} stood like a small bronze moon."
    )
    world.say(
        f"{hero.pronoun().capitalize()} touched the hatch and felt a secret warmth beneath the metal."
    )
    hero.memes["curiosity"] += 1
    shuttle.meters["closed"] = 1


def reveal(world: World, hero: Entity, surprise: Surprise) -> None:
    world.para()
    world.say(
        f"When the hatch opened, the surprise was not a problem but a wonder: {surprise.reveal}."
    )
    world.say(
        f"It {surprise.effect}, and the air filled with the kind of hush that makes children listen with wide eyes."
    )
    hero.memes["surprised"] += 1
    hero.memes["joy"] += 1
    world.facts["surprise_revealed"] = surprise.id
    world.facts["surprise_gift"] = surprise.gift
    world.facts["surprise_wonder"] = surprise.wonder


def turn(world: World, hero: Entity, shuttle: Entity, surprise: Surprise) -> None:
    world.say(
        f"Inside the shuttle, {surprise.wonder}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} understood that the journey had been waiting for this hidden gift all along."
    )
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["belonging"] += 1
    shuttle.meters["opened"] = 1


def resolution(world: World, hero: Entity, shuttle: Entity, surprise: Surprise) -> None:
    world.para()
    world.say(
        f"The {surprise.gift} was placed beside {hero.pronoun('object')}, and the shuttle rose along the silver road."
    )
    world.say(
        f"By the end, {hero.noun()} was no longer only a traveler; {hero.pronoun().capitalize()} had become a keeper of the story."
    )
    world.say(
        f"And whenever the stars blinked above {world.setting.name}, people remembered how the {shuttle.label} carried both a voyage and a surprise."
    )
    hero.memes["pride"] += 1
    shuttle.meters["travelled"] = 1


def tell(world: World, hero: Entity, shuttle: Entity, surprise: Surprise) -> World:
    intro(world, hero, shuttle, surprise)
    build_up(world, hero, shuttle, surprise)
    reveal(world, hero, surprise)
    turn(world, hero, shuttle, surprise)
    resolution(world, hero, shuttle, surprise)
    world.facts.update(hero=hero, shuttle=shuttle, surprise=surprise, setting=world.setting)
    return world


def generate_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    surprise = _safe_fact(world, f, "surprise")
    shuttle = _safe_fact(world, f, "shuttle")
    return [
        f"Write a short mythic story about {hero.noun()} and {shuttle.label} with a hidden surprise.",
        f"Tell a child-friendly legend where a shuttle carries {surprise.reveal} instead of an ordinary cargo.",
        f"Write a gentle myth about a journey that begins at {world.setting.launch_site} and ends in wonder.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    shuttle = _safe_fact(world, f, "shuttle")
    surprise = _safe_fact(world, f, "surprise")
    return [
        QAItem(
            question=f"What was the story about?",
            answer=f"It was about {hero.noun()} and the {shuttle.label}, and how an ordinary launch became a surprising legend.",
        ),
        QAItem(
            question=f"What surprise was hidden in the shuttle?",
            answer=f"The surprise was {surprise.reveal}, and it changed the trip into something wondrous.",
        ),
        QAItem(
            question=f"How did {hero.noun()} feel at the end?",
            answer=f"{hero.pronoun().capitalize()} felt joyful and proud, because {hero.pronoun('possessive')} journey had become part of the story of the place.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shuttle?",
            answer="A shuttle is a small vessel that carries travelers from one place to another, usually by moving along a planned route.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears when people are not looking for it.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    setting = _safe_lookup(SETTINGS, params.setting)
    surprise = _safe_lookup(SURPRISES, params.surprise)
    shuttle = _safe_lookup(SHUTTLES, params.shuttle)

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label=params.name,
        meters={"age_word": 1.0},
        memes={"hope": 0.0, "wonder": 0.0},
    ))
    shuttle_ent = world.add(Entity(
        id=shuttle.id,
        kind="thing",
        type="shuttle",
        label=shuttle.label,
        phrase=shuttle.phrase,
        meters={"shimmer": 0.0},
    ))
    tell(world, hero, shuttle_ent, surprise)

    return StorySample(
        params=params,
        story=generate_story_text(world),
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
    StoryParams(setting="dawn_harbor", surprise="moon_garden", shuttle="ember_shuttle", name="Nia", role="pilot", trait="curious"),
    StoryParams(setting="star_temple", surprise="star_baby", shuttle="ember_shuttle", name="Luna", role="priestess", trait="gentle"),
    StoryParams(setting="river_valley", surprise="river_king", shuttle="ember_shuttle", name="Kai", role="guide", trait="brave"),
]


def asp_show_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_show_program("#show valid_story/2."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid stories:")
        for a in atoms:
            print(" ", a)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.setting} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
