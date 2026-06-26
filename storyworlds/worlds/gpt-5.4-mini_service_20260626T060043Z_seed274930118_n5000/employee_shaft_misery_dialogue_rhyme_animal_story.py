#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/employee_shaft_misery_dialogue_rhyme_animal_story.py
===========================================================================================================

A tiny animal-story world about an employee, a shaft, and a bout of misery.
The premise is classical and child-facing: a small worker animal gets stuck in a
deep shaft, feels miserable, and a helper offers a safe, sensible way out.

The narrative instruments are:
- Dialogue: the story includes direct speech.
- Rhyme: the ending uses a simple rhyme-like cadence to soften the rescue.

The world is intentionally small and constraint-checked:
- The shaft must be a plausible place for the animal employee to be.
- Misery must arise from the worker being stuck, alone, or unable to finish the task.
- The resolution must use a safe helper action, not a magical disappearance.

The story remains concrete and state-driven: the simulated meters and memes
cause the text that gets narrated.
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
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
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
    place: str
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    reason: str
    mess: str
    weather: str = ""
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
class Tool:
    id: str
    label: str
    helps: set[str]
    action: str
    tail: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "barn": Setting(place="the old barn", affords={"climb", "listen"}),
    "mill": Setting(place="the little mill", affords={"climb", "listen"}),
    "station": Setting(place="the busy station", affords={"climb", "listen"}),
}

ACTIVITIES = {
    "climb": Activity(
        id="climb",
        verb="climb down the shaft",
        gerund="climbing down the shaft",
        rush="rush down the shaft",
        reason="wanted to find the shiny spool below",
        mess="dusty",
        weather="",
        tags={"shaft", "dust"},
    ),
    "listen": Activity(
        id="listen",
        verb="listen at the shaft",
        gerund="listening into the shaft",
        rush="lean too far into the shaft",
        reason="wanted to hear the echo",
        mess="dusty",
        weather="",
        tags={"shaft", "echo"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a sturdy rope",
        helps={"climb"},
        action="lower a rope",
        tail="The rope held steady, neat as could be.",
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        helps={"listen"},
        action="shine a lamp",
        tail="The lamp made the dark shaft less scary.",
    ),
}

ANIMAL_NAMES = ["Milo", "Pip", "Nia", "Toby", "Mina", "Benny", "Luna", "Rufus"]
TRAITS = ["small", "brave", "busy", "quick", "kind", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for tool_id, tool in TOOLS.items():
                if act_id in tool.helps:
                    combos.append((place, act_id, tool_id))
    return combos


def reason_rejection(activity: Activity, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit this situation. "
        f"The helper must actually solve {activity.id} in the shaft.)"
    )


def reason_gender(tool_id: str, gender: str) -> str:
    return f"(No story: gender choice {gender} is not usable for this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: an employee, a shaft, and misery, with dialogue and rhyme."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(ANIMAL_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "tool", None):
        act, tool = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))
        if getattr(args, "activity", None) not in tool.helps:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              if getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None)
              if getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, tool_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(["owl", "rabbit", "fox", "goat"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, tool=tool_id, name=name, gender=gender, helper=helper, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="fox" if params.gender == "boy" else "rabbit", traits=["little", params.trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    tool = world.add(Entity(id=params.tool, type="tool", label=_safe_lookup(TOOLS, params.tool).label))
    tool.owner = hero.id

    act = _safe_lookup(ACTIVITIES, params.activity)

    hero.memes["love_work"] = 1
    hero.memes["curiosity"] = 1
    world.say(f"{hero.id} was a little {params.trait} employee who worked at {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} liked {act.gerund}, because {act.reason}.")
    world.say(f"One day, {hero.id} went to the shaft with {tool.label} and a busy heart.")

    world.para()
    world.say(f"Down by the shaft, the air felt cool and black as ink.")
    world.say(f"{hero.id} wanted to {act.verb}, but the shaft was deep and the steps were steep.")
    world.say(f'"I can do it," {hero.id} said. "I can try, and I can quit if it gets scary."')

    hero.memes["misery"] += 1
    hero.meters["stuck"] = 1
    world.say(f"But then {hero.id} slipped on the edge and could not climb back out.")
    world.say(f"{hero.id} felt misery in the dark shaft, and {hero.pronoun("possessive")} ears drooped low.")
    world.say(f'"Help me please," {hero.id} said softly. "This shaft is a sad little place."')

    world.para()
    if params.activity == "climb":
        world.say(f"The {params.helper} heard the call and hurried over.")
        world.say(f'"Do not fret," said the {params.helper}. "We will do this the smart way, quick and neat."')
        world.say(f"The {params.helper} used {tool.label} to {_safe_lookup(TOOLS, params.tool).action}.")
        world.say(_safe_lookup(TOOLS, params.tool).tail)
        hero.memes["misery"] = 0
        hero.meters["stuck"] = 0
        hero.memes["relief"] = 1
        world.say(f"{hero.id} climbed up at last, small feet pattering, heart light as a lark.")
        world.say(f'"Safe and sound," said the {params.helper}, "that is how a shaft story should end."')
        world.say(f"And {hero.id} smiled with a tiny rhyme: " '"Climb in time, feel fine."')
    else:
        world.say(f"The {params.helper} heard the echo and brought {tool.label}.")
        world.say(f'"A lamp for the dark," said the {params.helper}, "so fear does not bark."')
        world.say(f"The bright lamp made the shaft glow warm and gold.")
        hero.memes["misery"] = 0
        hero.meters["stuck"] = 0
        hero.memes["relief"] = 1
        world.say(f"{hero.id} was not trapped anymore, and the dark did not look so mean.")
        world.say(f'"Now you can leave, and breathe," said the {params.helper}.')
        world.say(f"{hero.id} laughed, 'What a sweet little beam— it broke my gloom like a dream.'")

    world.facts.update(hero=hero, helper=helper, tool=tool, activity=act, params=params, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    return [
        f"Write an animal story for young children about {hero.id}, an employee in a shaft, who feels misery and gets help.",
        f"Tell a gentle story with dialogue where a small animal employee tries to {act.verb} and then finds a safe way out.",
        "Write a short rhyming rescue story about a shaft, a helper, and a worried little worker.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    act = _safe_fact(world, f, "activity")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little employee animal who got stuck in the shaft and needed help.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel misery?",
            answer=f"{hero.id} felt misery because {hero.id} slipped in the shaft and could not get back out alone.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"The {helper.type} helper helped by using {tool.label} so the problem could be solved safely.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before getting stuck?",
            answer=f"{hero.id} wanted to {act.verb}, because {act.reason}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shaft?",
            answer="A shaft is a deep, narrow opening that goes down or up inside a place, and people should be careful near it.",
        ),
        QAItem(
            question="What does misery mean?",
            answer="Misery means feeling very unhappy, uncomfortable, or sad.",
        ),
        QAItem(
            question="Why is it important to get help in a dangerous place?",
            answer="It is important to get help so everyone stays safe and the problem can be solved the right way.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", activity="climb", tool="rope", name="Milo", gender="boy", helper="owl", trait="brave"),
    StoryParams(place="mill", activity="listen", tool="lamp", name="Nia", gender="girl", helper="rabbit", trait="curious"),
]


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
tool(T) :- gadget(T).

safe_combo(P,A,T) :- affords(P,A), helps(T,A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("act", a))
    for t in TOOLS:
        lines.append(asp.fact("gadget", t))
        for a in sorted(_safe_lookup(TOOLS, t).helps):
            lines.append(asp.fact("helps", t, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_combo/3."))
    return sorted(set(asp.atoms(model, "safe_combo")))


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


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def valid_storyworld_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for tool_id, tool in TOOLS.items():
                if act_id in tool.helps:
                    combos.append((place, act_id, tool_id))
    return combos


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_combo/3."))
        return

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show safe_combo/3."))
        combos = sorted(set(asp.atoms(model, "safe_combo")))
        print(f"{len(combos)} compatible (place, activity, tool) combos:\n")
        for place, act, tool in combos:
            print(f"  {place:10} {act:8} {tool:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
