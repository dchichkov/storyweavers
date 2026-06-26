#!/usr/bin/env python3
"""
storyworlds/worlds/checker_kiddo_low_curiosity_inner_monologue_sharing.py
=========================================================================

A small Space Adventure storyworld about a kiddo, a checker bot, low power,
curiosity, inner monologue, and sharing a thought before a safer choice.

Seed tale:
---
A kiddo on a little space ship notices a blinking checker light on the
navigation panel. The kiddo is curious and wants to poke it, but the ship's
battery is low and the checker bot says the panel should stay closed. The kiddo
thinks hard inside their head, shares the worry with the crew, and helps find
a better way to check the light without breaking anything.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    checker: object | None = None
    kid: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"kid", "kiddo", "child", "boy", "girl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"checker", "robot"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"captain", "pilot", "adult"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Place:
    name: str
    safe_actions: set[str] = field(default_factory=set)
    low_power: bool = True
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
class Action:
    id: str
    verb: str
    request: str
    risk: str
    effect: str
    sensor: str
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
class Tool:
    id: str
    label: str
    phrase: str
    fixes: set[str]
    covers: set[str]
    prep: str
    tail: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    action: str
    tool: str
    name: str
    role: str
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


PLACES = {
    "bridge": Place(name="the bridge", safe_actions={"check_light", "share_signal"}, low_power=True),
    "hangar": Place(name="the hangar", safe_actions={"check_light", "share_signal"}, low_power=True),
    "moonbay": Place(name="the moon bay", safe_actions={"check_light", "share_signal"}, low_power=True),
}

ACTIONS = {
    "check_light": Action(
        id="check_light",
        verb="check the blinking light",
        request="reach for the blinking panel",
        risk="the panel could spark",
        effect="the light might get worse",
        sensor="blink",
        keyword="checker",
        tags={"checker", "light"},
    ),
    "scan_meter": Action(
        id="scan_meter",
        verb="scan the meter",
        request="touch the bright meter",
        risk="the meter could drop lower",
        effect="the power might slip away",
        sensor="meter",
        keyword="low",
        tags={"low", "power"},
    ),
}

TOOLS = {
    "hand_lamp": Tool(
        id="hand_lamp",
        label="a hand lamp",
        phrase="a small hand lamp",
        fixes={"blink", "low"},
        covers={"light", "meter"},
        prep="hold up the hand lamp first",
        tail="held the hand lamp steady",
    ),
    "glove_clip": Tool(
        id="glove_clip",
        label="a clip-on glove light",
        phrase="a clip-on glove light",
        fixes={"blink"},
        covers={"light"},
        prep="clip on a glove light first",
        tail="used the glove light to peek safely",
    ),
    "power_patch": Tool(
        id="power patch",
        label="a power patch",
        phrase="a tiny power patch",
        fixes={"low"},
        covers={"meter"},
        prep="attach a tiny power patch first",
        tail="slipped on the power patch before looking again",
    ),
}

NAMES = ["Milo", "Nia", "Rin", "Tess", "Ari", "Zed"]
ROLES = ["pilot", "captain", "engineer"]


def risk_at_play(action: Action, tool: Tool) -> bool:
    return action.sensor in tool.fixes


def select_tool(action: Action) -> Optional[Tool]:
    for tool in TOOLS.values():
        if risk_at_play(action, tool):
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for act_id in p.safe_actions:
            action = _safe_lookup(ACTIONS, act_id)
            for tool_id, tool in TOOLS.items():
                if risk_at_play(action, tool):
                    combos.append((place, act_id, tool_id))
    return combos


def _begin(world: World, kid: Entity, checker: Entity) -> None:
    world.say(
        f"{kid.id} was a little {kid.role} on {world.place.name}, and {checker.label} "
        f"kept watch over the glowing controls."
    )
    world.say(
        f"{kid.id} liked the ship because every button looked like a tiny mystery."
    )


def _curious(world: World, kid: Entity, action: Action) -> None:
    kid.memes["curiosity"] = kid.memes.get("curiosity", 0.0) + 1
    world.say(
        f"When the {action.keyword} light blinked, {kid.id} felt curiosity tug hard."
    )
    world.say(
        f"{kid.id} wanted to {action.request}, just to see what would happen."
    )


def _inner_monologue(world: World, kid: Entity, action: Action) -> None:
    kid.memes["inner_monologue"] = kid.memes.get("inner_monologue", 0.0) + 1
    world.say(
        f"Inside {kid.pronoun('possessive')} head, {kid.id} thought, "
        f'"Maybe I can help, but {action.risk}."'
    )


def _warn(world: World, checker: Entity, kid: Entity, action: Action) -> None:
    checker.memes["care"] = checker.memes.get("care", 0.0) + 1
    world.say(
        f"{checker.label} beeped softly and said, "
        f'"Please do not poke it yet. The ship is low on power."'
    )
    world.facts["warning"] = True
    world.facts["risk_text"] = action.risk
    world.facts["effect_text"] = action.effect


def _share(world: World, kid: Entity, checker: Entity, action: Action) -> None:
    kid.memes["sharing"] = kid.memes.get("sharing", 0.0) + 1
    world.say(
        f"{kid.id} took a breath and shared the worry out loud. "
        f'"I see the blink, and I do not want to make {action.effect}," '
        f"{kid.pronoun('subject')} said."
    )


def _fix(world: World, kid: Entity, checker: Entity, action: Action) -> Optional[Tool]:
    tool = select_tool(action)
    if tool is None:
        return None
    world.say(
        f"{checker.label} nodded and brought out {tool.phrase}. "
        f"{kid.id} and {checker.label} agreed to {tool.prep}."
    )
    return tool


def _resolve(world: World, kid: Entity, checker: Entity, action: Action, tool: Tool) -> None:
    kid.memes["joy"] = kid.memes.get("joy", 0.0) + 1
    kid.memes["curiosity"] += 0.5
    world.say(
        f"After that, {kid.id} could {action.verb} while {tool.tail}."
    )
    world.say(
        f"The blink turned steady, and the ship stayed safe and quiet."
    )


def tell(place: Place, action: Action, tool_cfg: Tool, name: str, role: str) -> World:
    world = World(place)
    kid = world.add(Entity(id=name, kind="character", type="kiddo", role=role))
    checker = world.add(Entity(id="Checker", kind="character", type="checker", label="the checker bot"))

    _begin(world, kid, checker)
    world.para()
    _curious(world, kid, action)
    _inner_monologue(world, kid, action)
    _warn(world, checker, kid, action)
    _share(world, kid, checker, action)
    tool = _fix(world, kid, checker, action)
    world.para()
    if tool is None:
        pass
    _resolve(world, kid, checker, action, tool)

    world.facts.update(
        kid=kid,
        checker=checker,
        action=action,
        tool=tool,
        place=place,
        resolved=True,
    )
    return world


SETTINGS = {
    "bridge": PLACES["bridge"],
    "hangar": PLACES["hangar"],
    "moonbay": PLACES["moonbay"],
}

CURATED = [
    StoryParams(place="bridge", action="check_light", tool="hand_lamp", name="Milo", role="pilot"),
    StoryParams(place="hangar", action="scan_meter", tool="power_patch", name="Nia", role="engineer"),
    StoryParams(place="moonbay", action="check_light", tool="glove_clip", name="Rin", role="captain"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "action", None) and getattr(args, "tool", None):
        act = _safe_lookup(ACTIONS, getattr(args, "action", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if not risk_at_play(act, tool):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, action, tool_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(place=place, action=action, tool=tool_id, name=name, role=role)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    action = _safe_fact(world, f, "action")
    return [
        f'Write a short Space Adventure story for a young child about a kiddo named {kid.id}, curiosity, inner monologue, and sharing.',
        f'Tell a gentle story where {kid.id} wants to {action.verb} but pauses to think, share the worry, and choose a safer way.',
        f'Write a simple space story that includes the words "checker", "kiddo", and "low".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    checker = _safe_fact(world, f, "checker")
    action = _safe_fact(world, f, "action")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who was the story about on {place.name}?",
            answer=f"It was about {kid.id}, a little {kid.role}, and the checker bot that kept watch beside {kid.pronoun('possessive')} curious thoughts.",
        ),
        QAItem(
            question=f"What did {kid.id} want to do when the light blinked?",
            answer=f"{kid.id} wanted to {action.request}, because curiosity made the blink feel important.",
        ),
        QAItem(
            question=f"How did {kid.id} handle the worry before touching the panel?",
            answer=f"{kid.id} used an inner monologue, shared the concern out loud, and then agreed to use {tool.phrase} first.",
        ),
        QAItem(
            question=f"Why did the checker bot say the panel should stay closed at first?",
            answer=f"The checker bot warned that the ship was low on power, so poking the panel could make the problem worse.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {kid.id} and {checker.label} used a safer tool, the blink turned steady, and the ship stayed safe.",
        ),
    ]


KNOWLEDGE = {
    "checker": [
        QAItem(
            question="What does a checker bot do on a spaceship?",
            answer="A checker bot looks for problems, watches the controls, and helps the crew keep the ship safe.",
        )
    ],
    "kiddo": [
        QAItem(
            question="What is a kiddo?",
            answer="A kiddo is a small child, usually someone young enough to need help and reminders from grown-ups or helpers.",
        )
    ],
    "low": [
        QAItem(
            question="What does low power mean?",
            answer="Low power means a battery or ship has used up much of its energy and may need careful use or a recharge.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        )
    ],
    "inner monologue": [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking you do inside your own head when you are thinking.",
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing a worry mean?",
            answer="Sharing a worry means telling someone else what you are afraid of or what you noticed so they can help.",
        )
    ],
}
KNOWLEDGE_ORDER = ["checker", "kiddo", "low", "curiosity", "inner monologue", "sharing"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    tags.update({"curiosity", "inner monologue", "sharing", "kiddo", "checker", "low"})
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "character":
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_tool(A, T) :- action(A), tool(T), sensor_of(A, S), fixes(T, S).
valid_story(P, A, T) :- place(P), safe_action(P, A), safe_tool(A, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.safe_actions):
            lines.append(asp.fact("safe_action", pid, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sensor_of", aid, action.sensor))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for f in sorted(tool.fixes):
            lines.append(asp.fact("fixes", tid, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space Adventure storyworld: a kiddo, a checker, low power, curiosity, inner monologue, and sharing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(TOOLS, params.tool), params.name, params.role)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = valid_asp_combos()
        print(f"{len(triples)} compatible (place, action, tool) combos:\n")
        for place, action, tool in triples:
            print(f"  {place:8} {action:14} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.action} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
