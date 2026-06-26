#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/synthesize_humor_inner_monologue_happy_ending_ghost.py
===============================================================================================================================

A tiny ghost-story world with humor, inner monologue, and a happy ending.

Premise:
- A child spends a night in a small old house that seems haunted.
- The "ghost" causes harmless spooky trouble: creaks, floating sheets, cold spots, and whispery noises.
- The child narrates their own brave, funny thoughts while investigating.
- The reveal turns the fear into a friendly, warm ending.

The world is state-driven:
- A ghost's "spook" meter makes the house feel eerie.
- A child's "curiosity", "fear", and "bravery" meters drive the turn.
- A lantern, blanket, and bedtime snack can reduce fear and reveal the ghost's harmless cause.

The story always resolves with a kind ending image: the ghost is not scary after all,
and the child feels proud, cozy, and a little amused.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoors: bool = True
    mood: str = "spooky"
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
class Ghost:
    id: str
    name: str
    style: str
    spook_kind: str
    tell: str
    cause: str
    reveal: str
    humored_by: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    soothes: set[str] = field(default_factory=set)
    cover: str = ""
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _synthesise_spook(world: World) -> list[str]:
    out: list[str] = []
    ghost = _safe_fact(world, world.facts, "ghost")
    child = _safe_fact(world, world.facts, "child")
    if child.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if ghost.id in world.fired:
        return out
    world.fired.add((ghost.id, "spook"))
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    ghost.meters["spook"] = ghost.meters.get("spook", 0) + 1
    out.append("A cold hush slid through the hallway, as if the house had remembered a secret.")
    out.append(f"{child.id} swallowed a gulp and thought, 'Okay. This is either a ghost or a very dramatic draft.'")
    return out


def _bump_lantern(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    lantern = world.entities.get("lantern")
    if not lantern:
        return out
    if child.memes.get("fear", 0) < THRESHOLD:
        return out
    if ("lantern", "bump") in world.fired:
        return out
    world.fired.add(("lantern", "bump"))
    child.memes["bravery"] = child.memes.get("bravery", 0) + 1
    out.append("The little lantern bobbed in the dark, bright as a brave crayon.")
    out.append(f"{child.id} told {child.pronoun('object')}self, 'If I can hold a light, I can hold my feet too.'")
    return out


def _reveal_harmless(world: World) -> list[str]:
    out: list[str] = []
    ghost = _safe_fact(world, world.facts, "ghost")
    child = _safe_fact(world, world.facts, "child")
    if child.memes.get("bravery", 0) < THRESHOLD:
        return out
    if ("ghost", "reveal") in world.fired:
        return out
    world.fired.add(("ghost", "reveal"))
    ghost.meters["spook"] = 0
    child.memes["fear"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    out.append(f"At the attic door, the 'ghost' turned out to be {ghost.cause}.")
    out.append(f"{child.id} blinked, then laughed so hard {child.pronoun('possessive')} knees wobbled.")
    out.append(f"'A ghost with a job to do,' {child.id} thought, 'is not nearly as scary as a ghost with nowhere to go.'")
    return out


def _comfort_end(world: World) -> list[str]:
    out: list[str] = []
    child = _safe_fact(world, world.facts, "child")
    comfort = _safe_fact(world, world.facts, "comfort")
    if child.memes.get("joy", 0) < THRESHOLD:
        return out
    if ("end", "cozy") in world.fired:
        return out
    world.fired.add(("end", "cozy"))
    out.append(f"{child.id} tucked {child.pronoun('possessive')} {comfort.label} around {child.pronoun('object')} shoulders and waved goodnight to the friendly old house.")
    out.append("By morning, the hallway was only a hallway, the attic was only an attic, and the whole place felt soft as a bedtime song.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_synthesise_spook, _bump_lantern, _reveal_harmless, _comfort_end):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "old_house": Setting(place="the old house", indoors=True, mood="spooky"),
    "attic": Setting(place="the attic", indoors=True, mood="spooky"),
    "hallway": Setting(place="the hallway", indoors=True, mood="spooky"),
}

GHOSTS = {
    "sheet": Ghost(
        id="sheet",
        name="Mister Drift",
        style="flapping sheet",
        spook_kind="fluttering",
        tell="a corner kept flipping like a sleepy bird wing",
        cause="the laundry line caught on a window latch and kept giving the sheet a flappy little dance",
        reveal="the sheet was only stuck on a hook",
        humored_by="silliness",
    ),
    "pipes": Ghost(
        id="pipes",
        name="Mrs. Tappy",
        style="rattling pipes",
        spook_kind="clinking",
        tell="the pipes went tick-tick-tock like a secret spoon orchestra",
        cause="the old pipes cooled down and made tiny knocking sounds",
        reveal="the noise was only the house settling after dinner",
        humored_by="patience",
    ),
    "cat": Ghost(
        id="cat",
        name="Captain Purr",
        style="mischievous cat",
        spook_kind="pattering",
        tell="little feet skittered across the floorboards and vanished again",
        cause="a sleepy cat kept sneaking after a moth",
        reveal="the 'ghost' had whiskers and a very offended tail",
        humored_by="cats",
    ),
}

COMFORTS = {
    "lantern": Comfort(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        helps={"fear", "dark"},
        soothes={"fear"},
        cover="warm light",
    ),
    "blanket": Comfort(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        helps={"fear", "cold"},
        soothes={"fear"},
        cover="cozy warmth",
    ),
    "snack": Comfort(
        id="snack",
        label="snack",
        phrase="a little plate of toast with jam",
        helps={"fear", "hungry"},
        soothes={"fear"},
        cover="sweet courage",
    ),
}

CHILD_NAMES = ["Mina", "Nora", "Theo", "Leo", "Ada", "Owen", "Ivy", "Mila", "Finn", "Zara"]
GHOST_NAMES = ["Mister Drift", "Mrs. Tappy", "Captain Purr", "Lady Hush", "Sir Flutter"]
TRAITS = ["brave", "curious", "funny", "sleepy", "wary", "gentle"]


@dataclass
class StoryParams:
    place: str
    ghost: str
    comfort: str
    name: str
    gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost story world with humor and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    ghost = getattr(args, "ghost", None) or rng.choice(list(GHOSTS))
    comfort = getattr(args, "comfort", None) or rng.choice(list(COMFORTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, ghost=ghost, comfort=comfort, name=name, gender=gender, trait=trait)


def introduce(world: World, child: Entity, ghost: Ghost, comfort: Comfort) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a {child.memes.get('curiosity', 0):.0f}-spark curiosity and a talent for noticing odd things in {world.setting.place}."
    )
    world.say(
        f"That night, {child.id} carried {comfort.phrase} and tried to act as if the shadows were merely doing theater."
    )
    world.say(
        f"Somewhere above, {ghost.tell}."
    )
    world.say(
        f"{child.id} thought, 'I am definitely awake. I am also definitely going to pretend that is normal.'"
    )


def generate_story(world: World) -> None:
    child: Entity = _safe_fact(world, world.facts, "child")
    ghost: Ghost = _safe_fact(world, world.facts, "ghost")
    comfort: Comfort = _safe_fact(world, world.facts, "comfort")
    world.say(f"At {world.setting.place}, {child.id} heard a spooky sound and froze for one tiny second.")
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{child.id} took a careful step and thought, 'If this is a ghost, I hope it likes polite visitors and not screaming ones.'"
    )
    world.say(f"{child.id} followed the fluttering sound until the mystery led to the attic.")
    world.say(f"There, the answer was wonderfully un-ghostly: {ghost.cause}.")
    world.para()
    world.say(
        f"{child.id} laughed, because the house had been trying to be mysterious, but it had only been clumsy."
    )
    world.say(
        f"{child.id} gave the old place a sleepy grin, wrapped up in {comfort.phrase}, and felt proud for being brave enough to check."
    )


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    gender = params.gender
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=gender,
        meters={"curiosity": 1.0, "fear": 0.0, "bravery": 0.0, "joy": 0.0},
        memes={"curiosity": 1.0},
    ))
    ghost = _safe_lookup(GHOSTS, params.ghost)
    comfort = _safe_lookup(COMFORTS, params.comfort)
    world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase=comfort.phrase,
        protective=True,
    ))
    world.facts.update(child=child, ghost=ghost, comfort=comfort)
    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.0
    child.memes["bravery"] = 0.0
    child.memes["joy"] = 0.0
    return world


def story_prompts(world: World) -> list[str]:
    child: Entity = _safe_fact(world, world.facts, "child")
    ghost: Ghost = _safe_fact(world, world.facts, "ghost")
    return [
        f"Write a short ghost story for young children about {child.id}, a spooky house, and a funny mystery.",
        f"Tell a gentle haunted-house tale where {child.id} hears {ghost.tell} and discovers it is harmless.",
        f"Synthesize a playful ghost story with inner monologue, humor, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact(world, world.facts, "child")
    ghost: Ghost = _safe_fact(world, world.facts, "ghost")
    comfort: Comfort = _safe_fact(world, world.facts, "comfort")
    return [
        QAItem(
            question=f"Why did {child.id} feel scared at first?",
            answer=f"{child.id} felt scared at first because {ghost.tell} made the house seem spooky before the mystery was solved.",
        ),
        QAItem(
            question=f"What did {child.id} think to themself while being brave?",
            answer=f"{child.id} thought that {ghost.style} noises were either a real ghost or a very dramatic mistake, and that was funny enough to keep going.",
        ),
        QAItem(
            question=f"What helped {child.id} stay calm?",
            answer=f"{comfort.phrase} helped {child.id} feel calmer and braver in the dark.",
        ),
        QAItem(
            question=f"What was the ghost really doing?",
            answer=f"The ghost turned out to be harmless, because {ghost.cause}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {child.id} laughed, felt proud, and went to bed feeling cozy instead of scared.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a spooky character that seems mysterious, even when the answer turns out to be harmless or funny.",
        ),
        QAItem(
            question="Why do stories sometimes use a flashlight or lantern in the dark?",
            answer="A lantern or flashlight gives warm light, which helps people see and feel braver in a dark place.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = _safe_fact(world, world.facts, "child")
    child.type = params.gender
    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.0
    child.memes["bravery"] = 0.0
    child.memes["joy"] = 0.0
    world.say(f"{child.id} was a little {params.gender} who loved to synthesize clues out of spooky sounds.")
    world.say(f"On a quiet night at {world.setting.place}, {child.id} carried a {world.facts['comfort'].label} and listened.")
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
ghostly(G) :- ghost(G).
comforting(C) :- comfort(C).
curious_child(X) :- child(X), curious(X).
spook_event(X,G) :- curious_child(X), ghostly(G).
safe_reveal(G) :- spook_event(X,G), helps(C,fear), comfort(C).
happy_ending(X) :- safe_reveal(G), child(X).
#show happy_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("curious", "child"))
    for cid, c in COMFORTS.items():
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show happy_ending/1."))
    ok = bool(asp.atoms(model, "happy_ending"))
    if ok:
        print("OK: ASP twin finds a happy ending.")
        return 0
    print("MISMATCH: ASP twin did not find the expected happy ending.")
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="old_house", ghost="sheet", comfort="lantern", name="Mina", gender="girl", trait="curious"),
        StoryParams(place="attic", ghost="pipes", comfort="blanket", name="Theo", gender="boy", trait="funny"),
        StoryParams(place="hallway", ghost="cat", comfort="snack", name="Ivy", gender="girl", trait="brave"),
    ]


CURATED = build_curated()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=getattr(args, "place", None) or rng.choice(list(SETTINGS)),
        ghost=getattr(args, "ghost", None) or rng.choice(list(GHOSTS)),
        comfort=getattr(args, "comfort", None) or rng.choice(list(COMFORTS)),
        name=getattr(args, "name", None) or rng.choice(CHILD_NAMES),
        gender=getattr(args, "gender", None) or rng.choice(["girl", "boy"]),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with humor and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
        return samples
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            i += 1
            continue
        seen.add(sample.story)
        samples.append(sample)
        i += 1
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_ending/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        try:
            import asp
        except Exception as e:
            pass
        model = asp.one_model(asp_program("#show happy_ending/1."))
        print("ASP model:", asp.atoms(model, "happy_ending"))
        return

    samples = generate_many(args)
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
            header = f"### {p.name}: {p.ghost} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
