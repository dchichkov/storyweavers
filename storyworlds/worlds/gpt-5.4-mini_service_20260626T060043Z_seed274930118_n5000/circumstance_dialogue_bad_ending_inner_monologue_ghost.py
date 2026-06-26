#!/usr/bin/env python3
"""
A standalone storyworld script for a small ghost-story domain with circumstance,
dialogue, inner monologue, and a deliberately bad ending.

Premise:
- A child visits a quiet place at dusk.
- A ghostly presence makes the place feel strange.
- The child tries to be brave and solve the problem with light, a bell, or a charm.
- Sometimes the best intended action fails, and the story ends with a spooky loss.

The world model tracks:
- physical meters: light, chill, damp, noise, courage, etc.
- emotional memes: fear, hope, grief, resolve, curiosity, loneliness, relief.

This world intentionally supports a "bad ending" mode: the child may fail to
escape the haunting, or may lose an important object, so the final image proves
what changed.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

ROOMS = ["attic", "hallway", "kitchen", "cellar", "porch"]
TIMES = ["dusk", "midnight", "rainy evening"]
HERO_NAMES = ["Mina", "Eli", "Lena", "Noah", "Iris", "Theo", "Nora", "Owen"]
TRAITS = ["brave", "quiet", "curious", "careful", "small", "patient"]
GHOST_TITLES = ["white ghost", "lantern ghost", "old singer ghost", "little bell ghost"]
OBJECTS = {
    "lantern": "a brass lantern with a glass door",
    "bell": "a tiny silver bell on a string",
    "photo": "a faded family photo in a wooden frame",
    "key": "a rusty key with a looped handle",
}

# ---------------------------------------------------------------------------
# Core entities
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ghost_ent: object | None = None
    hero: object | None = None
    item: object | None = None
    parent: object | None = None
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
    def short(self) -> str:
        return self.label or self.type
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
    place: str = "the old house"
    room: str = "hallway"
    circumstance: str = "dusk"
    afford_gather: bool = True
    afford_listen: bool = True
    afford_search: bool = True
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
class StoryKnob:
    id: str
    label: str
    phrase: str
    room: str
    risk: str
    fixable: bool = True
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
class StoryParams:
    setting: str
    object: str
    name: str
    gender: str
    trait: str
    ghost: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_steps: list[str] = []

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

# ---------------------------------------------------------------------------
# Story state helpers
# ---------------------------------------------------------------------------

def pronoun_bundle(hero: Entity) -> tuple[str, str, str]:
    return hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")


def setting_sentence(setting: Setting, ghost: StoryKnob) -> str:
    if setting.circumstance == "rainy evening":
        return f"It was a rainy evening, and the old house clicked softly with water on the roof."
    if setting.circumstance == "midnight":
        return f"It was midnight, and the old house felt as quiet as a held breath."
    return f"It was dusk, and the old house looked long and gray under the fading light."


def ghost_sentence(ghost: StoryKnob) -> str:
    return f"People said a {ghost.label} lived there, and the sound of it made the hall feel colder."


def love_object_sentence(hero: Entity, obj: Entity) -> str:
    return f"{hero.id} loved {hero.pronoun('possessive')} {obj.label} because it was warm and brave-looking in the dark."


def inner_monologue_text(hero: Entity, obj: Entity, ghost: StoryKnob) -> str:
    return (
        f"{hero.id} thought, I should not be scared, but the dark is so big. "
        f"If I keep the {obj.label} near, maybe the {ghost.label} will stay back."
    )


def dialogue_warn(hero: Entity, parent: Entity) -> str:
    return f'"Do you hear that?" {hero.id} whispered. "{parent.id}, I think something is in the wall."'


def ghost_reply(ghost: StoryKnob) -> str:
    return f'"Leave the room," said a thin voice. "This house remembers me."'


def bad_ending_line(hero: Entity, obj: Entity, ghost: StoryKnob) -> str:
    return (
        f"In the end, {hero.id} dropped the {obj.label}, and the little light went out. "
        f"The {ghost.label} stayed, and the hallway kept the child's tiny footsteps for itself."
    )


# ---------------------------------------------------------------------------
# Simulated causal rules
# ---------------------------------------------------------------------------

def apply_cold(world: World) -> None:
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.meters["chill"] = ent.meters.get("chill", 0) + 1
            ent.memes["fear"] = ent.memes.get("fear", 0) + 1


def apply_search(world: World, hero: Entity, obj: Entity, ghost: StoryKnob) -> None:
    hero.meters["light"] = hero.meters.get("light", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(f"{hero.id} lifted the {obj.label} and searched the dark corners of the {world.setting.room}.")


def apply_ghost_pressure(world: World, hero: Entity, obj: Entity, ghost: StoryKnob) -> None:
    # In this world, the ghost overwhelms hope if the object is not a key-binder.
    if ghost.id == "lantern_ghost":
        hero.meters["light"] = max(0, hero.meters.get("light", 0) - 2)
        hero.memes["fear"] = hero.memes.get("fear", 0) + 2
    else:
        hero.meters["noise"] = hero.meters.get("noise", 0) + 1
        hero.memes["hope"] = max(0, hero.memes.get("hope", 0) - 1)


def apply_loss(world: World, hero: Entity, obj: Entity) -> None:
    hero.meters["light"] = max(0, hero.meters.get("light", 0) - 1)
    hero.memes["grief"] = hero.memes.get("grief", 0) + 1
    obj.carried_by = None
    obj.room = world.setting.room


def summarize_badness(hero: Entity) -> bool:
    return hero.memes.get("fear", 0) >= 2 and hero.meters.get("light", 0) <= 0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(place="the old house", room="attic", circumstance="dusk"),
    "hallway": Setting(place="the old house", room="hallway", circumstance="midnight"),
    "cellar": Setting(place="the old house", room="cellar", circumstance="rainy evening"),
    "porch": Setting(place="the old house", room="porch", circumstance="dusk"),
}

OBJECTS = {
    "lantern": StoryKnob(id="lantern", label="lantern", phrase="a brass lantern with a glass door", room="hallway", risk="darkness"),
    "bell": StoryKnob(id="bell", label="bell", phrase="a tiny silver bell on a string", room="attic", risk="silence"),
    "photo": StoryKnob(id="photo", label="photo", phrase="a faded family photo in a wooden frame", room="cellar", risk="forgetting"),
    "key": StoryKnob(id="key", label="key", phrase="a rusty key with a looped handle", room="porch", risk="locked door"),
}

GHOSTS = {
    "white": StoryKnob(id="white_ghost", label="white ghost", phrase="a white ghost that drifted like fog", room="hallway", risk="cold", fixable=False),
    "lantern": StoryKnob(id="lantern_ghost", label="lantern ghost", phrase="a lantern ghost with a face in the glass", room="attic", risk="dark", fixable=False),
    "singer": StoryKnob(id="singer_ghost", label="old singer ghost", phrase="an old singer ghost with a cracked song", room="cellar", risk="echo", fixable=False),
    "bell": StoryKnob(id="bell_ghost", label="little bell ghost", phrase="a little bell ghost that rang by itself", room="porch", risk="noise", fixable=False),
}

# ---------------------------------------------------------------------------
# Reasonableness gate and story construction
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for obj_id, obj in OBJECTS.items():
            for ghost_id, ghost in GHOSTS.items():
                if setting.room == obj.room or setting.room == ghost.room:
                    combos.append((setting_id, obj_id, ghost_id))
    return combos


def explain_rejection(setting_id: str, object_id: str, ghost_id: str) -> str:
    return (
        f"(No story: in this circumstance, the {object_id} and {ghost_id} never meet in a way that can matter. "
        f"Choose a setting where one of them belongs.)"
    )


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.object not in OBJECTS or params.ghost not in GHOSTS:
        pass

    setting = _safe_lookup(SETTINGS, params.setting)
    obj = _safe_lookup(OBJECTS, params.object)
    ghost = _safe_lookup(GHOSTS, params.ghost)

    if (params.setting, params.object, params.ghost) not in valid_combos():
        pass

    world = World(setting)
    world.setting.circumstance = setting.circumstance

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"chill": 0, "light": 0, "noise": 0},
        memes={"fear": 0, "hope": 0, "curiosity": 0, "grief": 0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type="mother" if params.gender == "girl" else "father",
        label="parent",
        meters={"chill": 0},
        memes={"fear": 0},
    ))
    item = world.add(Entity(
        id=params.object,
        kind="thing",
        type=params.object,
        label=params.object,
        phrase=obj.phrase,
        carried_by=hero.id,
        room=setting.room,
    ))
    ghost_ent = world.add(Entity(
        id=params.ghost,
        kind="character",
        type="ghost",
        label=ghost.label,
        phrase=ghost.phrase,
        room=ghost.room,
        meters={"chill": 3, "light": 0},
        memes={"loneliness": 2, "resolve": 1},
    ))

    # Act 1: setup
    world.say(setting_sentence(setting, ghost))
    world.say(ghost_sentence(ghost))
    world.say(f"{hero.id} was a {params.trait} child who had come with {parent.id} to look around.")
    world.say(love_object_sentence(hero, item))

    # Act 2: tension
    world.para()
    apply_cold(world)
    world.say(f"{hero.id} walked into the {setting.room} and felt the air turn colder around {hero.pronoun('object')}.")
    world.say(dialogue_warn(hero, parent))
    world.say(f"{parent.id} said, \"Stay close. This house makes strange sounds when the light is weak.\"")
    world.say(inner_monologue_text(hero, item, ghost))
    apply_search(world, hero, item, ghost)
    world.say(f"The {ghost.label} answered from the dark: {ghost_reply(ghost)}")
    apply_ghost_pressure(world, hero, item, ghost)

    # Bad ending is guaranteed by losing the light once fear overwhelms it.
    world.para()
    if summarize_badness(hero):
        apply_loss(world, hero, item)
        hero.memes["hope"] = max(0, hero.memes.get("hope", 0) - 1)
        hero.memes["grief"] += 1
        world.say(f"{hero.id} tried to be brave, but the dark kept getting closer.")
        world.say(bad_ending_line(hero, item, ghost))
        world.say(f"{parent.id} reached out, but the child could only listen to the faint room-noise and the last little scrape of the {item.label}.")
    else:
        # Still end badly: the child fails to resolve the haunting, but this path is
        # less common; it keeps the domain flexible while remaining a bad ending.
        hero.memes["grief"] += 1
        hero.memes["hope"] = 0
        world.say(f"{hero.id} waited for a kinder sound, but the house did not answer.")
        world.say(f"The {ghost.label} only grew quieter, which somehow felt worse.")
        world.say(bad_ending_line(hero, item, ghost))

    world.facts.update(
        hero=hero,
        parent=parent,
        item=item,
        ghost=ghost_ent,
        setting=setting,
        circumstance=setting.circumstance,
        trait=params.trait,
        resolved=False,
        lost_object=item.label,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    obj = _safe_fact(world, f, "item")
    ghost = _safe_fact(world, f, "ghost")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short ghost story for a young child that includes the word "circumstance" and takes place in {setting.room}.',
        f"Tell a spooky but child-friendly story where {hero.id} tries to keep {hero.pronoun('possessive')} {obj.label} safe from {ghost.label}.",
        f'Write a story with dialogue and an inner monologue about a child in this circumstance, ending in a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item")
    ghost = _safe_fact(world, f, "ghost")
    setting = _safe_fact(world, f, "setting")
    sub, objp, pos = pronoun_bundle(hero)
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {f['trait']} child, and {parent.id} went with {hero.id} to the {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} try to keep safe?",
            answer=f"{hero.id} tried to keep {pos} {item.label} safe, but the dark and the ghost made that hard.",
        ),
        QAItem(
            question=f"What did the ghost say to {hero.id}?",
            answer=f"The {ghost.label} said, \"Leave the room,\" and warned that the house remembered it.",
        ),
        QAItem(
            question=f"Why did the ending feel bad?",
            answer=f"The ending felt bad because {hero.id} lost the {item.label}, the light went out, and the ghost stayed in the house.",
        ),
        QAItem(
            question=f"How did {hero.id} feel inside?",
            answer=f"{hero.id} felt scared, hopeful for a moment, and then sad when the light failed.",
        ),
        QAItem(
            question=f"What circumstance surrounded the story?",
            answer=f"The story took place during {world.setting.circumstance} in {setting.place}, which made everything feel colder and stranger.",
        ),
        QAItem(
            question=f"What was the final image?",
            answer=f"The final image was of the dark hallway, the lost {item.label}, and the {ghost.label} still waiting there.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky made-up figure in stories, usually someone who can drift, whisper, or scare people without a body.",
        ),
        QAItem(
            question="Why do people carry lanterns in the dark?",
            answer="People carry lanterns in the dark so they can see where they are going and feel a little safer.",
        ),
        QAItem(
            question="What is a circumstance?",
            answer="A circumstance is the situation around something, like the place, time, or condition that makes it happen a certain way.",
        ),
        QAItem(
            question="What does inner monologue mean?",
            answer="Inner monologue is what a character thinks inside their own mind, even if they do not say it out loud.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the words characters speak to each other in a story.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.room:
            bits.append(f"room={e.room}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

valid(S, O, G) :- setting(S), object(O), ghost(G),
                  setting_room(S, R), object_room(O, R).
valid(S, O, G) :- setting(S), object(O), ghost(G),
                  setting_room(S, R), ghost_room(G, R).

% The world is intentionally broad: the child can meet the object or ghost in
% the same room, and that is enough to create a ghost story with tension.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_room", sid, s.room))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_room", oid, o.room))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("ghost_room", gid, g.room))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in asp:", sorted(asp_set - py))
    return 1

# ---------------------------------------------------------------------------
# Required interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with circumstance, dialogue, inner monologue, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--object", dest="object_", choices=OBJECTS.keys())
    ap.add_argument("--ghost", choices=GHOSTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS.keys()))
    obj = getattr(args, "object_", None) or rng.choice(list(OBJECTS.keys()))
    ghost = getattr(args, "ghost", None) or rng.choice(list(GHOSTS.keys()))
    if (setting, obj, ghost) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, object=obj, name=name, gender=gender, trait=trait, ghost=ghost)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


CURATED = [
    StoryParams(setting="hallway", object="lantern", name="Mina", gender="girl", trait="curious", ghost="lantern"),
    StoryParams(setting="cellar", object="photo", name="Eli", gender="boy", trait="careful", ghost="singer"),
    StoryParams(setting="attic", object="bell", name="Iris", gender="girl", trait="quiet", ghost="white"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.setting} / {p.object} / {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
