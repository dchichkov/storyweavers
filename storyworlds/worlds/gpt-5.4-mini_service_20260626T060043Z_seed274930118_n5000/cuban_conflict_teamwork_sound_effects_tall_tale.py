#!/usr/bin/env python3
"""
storyworlds/worlds/cuban_conflict_teamwork_sound_effects_tall_tale.py
======================================================================

A tiny tall-tale story world about a Cuban street celebration where a big
problem is solved with teamwork, music, and noisy sound effects.

Premise:
- A child and family are preparing for a Cuban festival.
- A giant parade drum, banner, or cart gets stuck.
- The sound of the jam causes conflict.
- The crowd works together, using clever rhythm and loud sound effects, to fix it.
- The ending proves the neighborhood is bigger and brighter because they helped.

This world keeps the story concrete and state-driven: the drum weighs a lot,
the rope is short, the street is narrow, the crowd gets frustrated, and then
the shared rhythm turns the trouble into a triumph.
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
# World data model
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crowd: object | None = None
    heavy: object | None = None
    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Street:
    place: str = "the Cuban street"
    narrow: bool = True
    colorful: bool = True
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
class SoundTool:
    id: str
    label: str
    sound: str
    use: str
    boost: str
    tags: set[str] = field(default_factory=set)
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
class HeavyThing:
    id: str
    label: str
    phrase: str
    weight: float
    stuck_on: str
    tag: str
    sounds: set[str] = field(default_factory=set)
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
    def __init__(self, street: Street) -> None:
        self.street = street
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

STREETS = {
    "old_havana": Street(place="the old Havana street", narrow=True, colorful=True),
    "seaside": Street(place="the seaside lane", narrow=True, colorful=True),
    "plaza": Street(place="the plaza", narrow=False, colorful=True),
}

TOOLS = {
    "drum": SoundTool(
        id="drum",
        label="a conga drum",
        sound="bam-bam-bam",
        use="beat a brave rhythm on the drum",
        boost="the beat got louder and steadier",
        tags={"cuban", "music", "sound_effects", "teamwork"},
    ),
    "maracas": SoundTool(
        id="maracas",
        label="maracas",
        sound="shake-shake!",
        use="shake the maracas like lightning bugs in a jar",
        boost="the shivers turned into a lively shake",
        tags={"cuban", "music", "sound_effects", "teamwork"},
    ),
    "whistle": SoundTool(
        id="whistle",
        label="a whistle",
        sound="tweet-tweet!",
        use="signal the helpers with a sharp whistle",
        boost="the helpers could hear the cue right away",
        tags={"sound_effects", "teamwork"},
    ),
}

HEAVY_THINGS = {
    "float": HeavyThing(
        id="float",
        label="the parade float",
        phrase="a bright parade float with big paper flowers",
        weight=5.0,
        stuck_on="the corner",
        tag="float",
        sounds={"creak-creak", "heave-ho"},
    ),
    "cart": HeavyThing(
        id="cart",
        label="the music cart",
        phrase="a wooden music cart stacked with drums and ribbons",
        weight=4.0,
        stuck_on="the narrow bend",
        tag="cart",
        sounds={"grunt-grunt", "whoa-now"},
    ),
    "banner": HeavyThing(
        id="banner",
        label="the banner pole",
        phrase="a tall banner pole with a shiny Cuban flag",
        weight=3.0,
        stuck_on="the gate",
        tag="banner",
        sounds={"twang", "thrum"},
    ),
}

NAMES = ["Luz", "Mina", "Tico", "Pablo", "Ana", "Sofia", "Nico", "Rosa"]
TRAITS = ["bright-eyed", "brave", "lively", "curious", "spirited", "stubborn"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid if the place has a heavy thing, the tools make a compatible
% sound plan, and the help set can actually move the heavy thing.
valid(Place, Heavy, Tool) :- street(Place), heavy(Heavy), tool(Tool),
                             on_street(Place, Heavy),
                             helps(Tool, Heavy),
                             can_unstick(Place, Heavy, Tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in STREETS.items():
        lines.append(asp.fact("street", sid))
        if s.narrow:
            lines.append(asp.fact("narrow", sid))
        if s.colorful:
            lines.append(asp.fact("colorful", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sound", tid, t.sound))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tagged", tid, tag))
    for hid, h in HEAVY_THINGS.items():
        lines.append(asp.fact("heavy", hid))
        lines.append(asp.fact("on_street", "old_havana" if hid != "banner" else "plaza", hid))
        for s in sorted(h.sounds):
            lines.append(asp.fact("makes", hid, s))
    lines.append(asp.fact("helps", "drum", "float"))
    lines.append(asp.fact("helps", "maracas", "cart"))
    lines.append(asp.fact("helps", "whistle", "banner"))
    lines.append(asp.fact("can_unstick", "old_havana", "float", "drum"))
    lines.append(asp.fact("can_unstick", "seaside", "cart", "maracas"))
    lines.append(asp.fact("can_unstick", "plaza", "banner", "whistle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    heavy: str
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


class Simulation:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.world = World(_safe_lookup(STREETS, params.place))
        self.hero = self.world.add(Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            meters={"hope": 1.0},
            memes={"joy": 1.0},
        ))
        self.helper = self.world.add(Entity(
            id=params.helper,
            kind="character",
            type="mother" if params.gender == "girl" else "father",
            meters={"strength": 1.0},
            memes={"patience": 1.0},
        ))
        self.crowd = self.world.add(Entity(
            id="crowd",
            kind="character",
            type="people",
            plural=True,
            meters={"strength": 2.0},
            memes={"buzz": 1.0},
        ))
        self.heavy = self.world.add(Entity(
            id=params.heavy,
            label=_safe_lookup(HEAVY_THINGS, params.heavy).label,
            phrase=_safe_lookup(HEAVY_THINGS, params.heavy).phrase,
            meters={"weight": _safe_lookup(HEAVY_THINGS, params.heavy).weight, "stuck": 1.0},
            memes={"frustration": 1.0},
        ))
        self.tool = self.world.add(Entity(
            id=params.tool,
            label=_safe_lookup(TOOLS, params.tool).label,
            meters={"useful": 1.0},
            memes={"music": 1.0},
        ))
        self.world.facts.update(hero=self.hero, helper=self.helper, heavy=self.heavy, tool=self.tool)

    def run(self) -> World:
        p = self.params
        w = self.world
        heavy_cfg = _safe_lookup(HEAVY_THINGS, p.heavy)
        tool_cfg = _safe_lookup(TOOLS, p.tool)

        w.say(f"{p.name} lived where the Cuban wind could turn any corner into a parade.")
        w.say(f"One bright morning, {p.name} spotted {heavy_cfg.phrase} stuck {heavy_cfg.stuck_on}.")
        w.say(f"The crowd went, \"Creak-creak!\" and then \"Ohhh no!\" as the wheels refused to roll.")

        w.para()
        self.hero.memes["worry"] = 1.0
        self.heavy.meters["stuck"] += 1.0
        w.say(f"{p.name} wanted the celebration to go on, but the road said, \"No way.\"")
        w.say(f"Some folks grumbled. Someone else crossed their arms. The air felt prickly with conflict.")

        w.para()
        self.helper.memes["resolve"] = 1.0
        self.helper.meters["strength"] += 1.0
        self.hero.memes["hope"] += 1.0
        w.say(f"Then {p.name}'s {self.helper.type} smiled and said, \"A big problem needs a bigger teamwork.\"")
        w.say(f"\"You tap {tool_cfg.sound}, I pull the rope, and everyone else can answer with {tool_cfg.sound}!\"")

        w.para()
        self.tool.memes["music"] += 1.0
        self.hero.meters["rhythm"] = 1.0
        self.helper.meters["pull"] = 1.0
        self.crowd.meters["pull"] = 2.0
        self.heavy.meters["stuck"] = max(0.0, self.heavy.meters["stuck"] - 1.0)
        self.heavy.meters["weight"] = max(0.0, self.heavy.meters["weight"] - 2.0)
        self.crowd.memes["confidence"] = 1.0
        w.say(f"\"{tool_cfg.sound}!\" went the {tool_cfg.label}, and the helpers answered, \"Heave-ho!\"")
        w.say(f"\"Bam-bam-bam!\" went the drum, and the whole street began to sway like a sleepy palm tree in a storm.")
        w.say(f"With one more tug and a cheerful \"WHOOSH!\", {heavy_cfg.label} rolled free at last.")

        w.para()
        self.hero.memes["joy"] += 2.0
        self.helper.memes["pride"] = 1.0
        self.heavy.meters["stuck"] = 0.0
        w.say(f"The grumbling turned into laughter, and the conflict melted as fast as ice in the sun.")
        w.say(f"{p.name} grinned, {p.name}'s {self.helper.type} clapped, and the crowd danced behind the moving float.")
        w.say(f"By the end, the Cuban street was louder, kinder, and brighter than before.")

        w.facts["resolved"] = True
        return w


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact(world, f, "hero")
    return [
        'Write a tall tale about a Cuban street celebration where a problem is solved with teamwork and noisy sound effects.',
        f"Tell a child-friendly story where {p.id} helps move a stuck parade object by using music and a big team.",
        "Write a short story that starts with conflict, grows into teamwork, and ends with the sound of the street cheering.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    heavy: Entity = _safe_fact(world, f, "heavy")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What was stuck in the story?",
            answer=f"{heavy.label.capitalize()} was stuck, so the celebration could not roll forward until everyone worked together.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.pronoun('subject').capitalize()} helped {hero.id} with patience, strength, and a calm smile.",
        ),
        QAItem(
            question=f"What sound helped turn the conflict into teamwork?",
            answer=f"The {tool.label} made {tool_cfg_sound(tool)} and gave the helpers a beat to follow.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the heavy thing rolling free, the crowd laughing, and the Cuban street sounding full of celebration again.",
        ),
    ]


def tool_cfg_sound(tool: Entity) -> str:
    return {
        "a conga drum": "bam-bam-bam",
        "maracas": "shake-shake!",
        "a whistle": "tweet-tweet!",
    }.get(tool.label, "a cheerful sound")


WORLD_KNOWLEDGE = {
    "cuban": [
        QAItem(
            question="What does Cuban mean in a story like this?",
            answer="Cuban means it connects to Cuba, which is an island country with music, dancing, and lively celebrations.",
        )
    ],
    "sound_effects": [
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like bam, boom, creak, or whoosh that help you hear the action in your mind.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do different jobs to reach the same goal.",
        )
    ],
    "conflict": [
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the part where characters have a problem, disagree, or face something hard before they fix it.",
        )
    ],
    "music": [
        QAItem(
            question="Why can music help people work together?",
            answer="Music can help people share a beat, stay together, and feel brave enough to keep trying.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"cuban", "sound_effects", "teamwork", "conflict", "music"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: Cuban conflict, teamwork, and sound effects.")
    ap.add_argument("--place", choices=STREETS)
    ap.add_argument("--heavy", choices=HEAVY_THINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in STREETS:
        for heavy in HEAVY_THINGS:
            for tool in TOOLS:
                if place == "old_havana" and heavy == "float" and tool == "drum":
                    combos.append((place, heavy, tool))
                if place == "seaside" and heavy == "cart" and tool == "maracas":
                    combos.append((place, heavy, tool))
                if place == "plaza" and heavy == "banner" and tool == "whistle":
                    combos.append((place, heavy, tool))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "heavy", None) is None or c[1] == getattr(args, "heavy", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, heavy, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["Mami", "Papi", "Tia", "Tio"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, heavy=heavy, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    sim = Simulation(params)
    world = sim.run()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def asp_show() -> str:
    return asp_program("#show valid/3.")


CURATED = [
    StoryParams(place="old_havana", heavy="float", tool="drum", name="Luz", gender="girl", helper="Mami", trait="bright-eyed"),
    StoryParams(place="seaside", heavy="cart", tool="maracas", name="Tico", gender="boy", helper="Papi", trait="spirited"),
    StoryParams(place="plaza", heavy="banner", tool="whistle", name="Rosa", gender="girl", helper="Tia", trait="brave"),
]


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
        print(asp_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        items = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(items)} valid story combos:")
        for t in items:
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
            header = f"### {p.name}: {p.heavy} + {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
