#!/usr/bin/env python3
"""
storyworlds/worlds/corral_transformation_cautionary_myth.py
===========================================================

A standalone story world for a small cautionary myth about a corral, a taboo,
and a transformation that teaches care.

The world is built from a simple premise:

- A keeper tends a corral with a rule that must not be broken.
- A curious child or helper ignores the warning and enters at the wrong time.
- The corral's old magic transforms the intruder.
- The ending shows a safer custom, and the transformed state proves what changed.

The generated stories are intentionally compact, classical, and state-driven.
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
    caretaker: Optional[str] = None
    location: str = ""
    transformed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    intruder: object | None = None
    keeper: object | None = None
    thing: object | None = None
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
class Setting:
    place: str = "the corral"
    time: str = "at dusk"
    world: object | None = None
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
class Tension:
    taboo: str
    warning: str
    danger: str
    consequence: str
    location: str = "inside the corral"
    trigger: str = "enter the corral"
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
class Transformation:
    id: str
    label: str
    state_name: str
    reveal: str
    reason: str
    body_part: str
    visible: str
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


@dataclass
class Remedy:
    id: str
    label: str
    rule: str
    action: str
    ending: str
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _default_meters() -> dict[str, float]:
    return {"fear": 0.0, "dust": 0.0, "magic": 0.0, "warning": 0.0}


def _default_memes() -> dict[str, float]:
    return {"curiosity": 0.0, "defiance": 0.0, "regret": 0.0, "awe": 0.0, "grief": 0.0}


def _transformation_rule(world: World) -> list[str]:
    out: list[str] = []
    intruder = world.entities.get("intruder")
    thing = world.entities.get("thing")
    if not intruder or not thing:
        return out
    if intruder.memes.get("defiance", 0.0) < THRESHOLD:
        return out
    if thing.meters.get("magic", 0.0) < THRESHOLD:
        return out
    sig = ("transform", intruder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    intruder.transformed = True
    intruder.meters["fear"] = max(intruder.meters.get("fear", 0.0), 1.0)
    intruder.memes["regret"] += 1.0
    out.append(f"The old power of the corral changed {intruder.id} at once.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_transformation_rule,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def _story_title(setting: Setting) -> str:
    return f"The Corral at {setting.time}"


def _vision_line() -> str:
    return "Old places in myths often keep their own rules."


def tell(params) -> World:
    world = World(Setting())
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=params.keeper_type,
        label=params.keeper_name,
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    intruder = world.add(Entity(
        id="intruder",
        kind="character",
        type=params.intruder_type,
        label=params.intruder_name,
        meters=_default_meters(),
        memes=_default_memes(),
    ))
    thing = world.add(Entity(
        id="thing",
        kind="thing",
        type="horn",
        label=params.transformation.label,
        phrase=params.transformation.reveal,
        meters={"magic": 1.0},
        memes={},
    ))
    world.facts.update(keeper=keeper, intruder=intruder, thing=thing)

    world.say(f"{_story_title(world.setting)} was told beside the corral, where {_vision_line()}")
    world.say(
        f"{keeper.label} kept watch over {params.setting_place}, and people said "
        f"{params.taboo_warning}"
    )
    world.say(
        f"{intruder.label} was young and full of curiosity. {intruder.pronoun().capitalize()} "
        f"kept looking toward the gate, because {params.trigger_reason}"
    )

    world.para()
    world.say(
        f"At {params.setting_time}, when the animals were restless, {intruder.label} "
        f"tried to {params.tension.trigger}."
    )
    intruder.memes["curiosity"] += 1.0
    intruder.memes["defiance"] += 1.0
    keeper.meters["warning"] += 1.0
    world.say(
        f"{keeper.label} called out, '{params.tension.warning}' but {intruder.label} "
        f"did not turn back."
    )
    world.say(
        f"'{params.tension.danger}' {intruder.pronoun('possessive').capitalize()} {params.tension.consequence}"
    )

    propagate(world, narrate=True)

    world.para()
    if intruder.transformed:
        world.say(
            f"When the dust settled, {intruder.label} was no longer the same. "
            f"Where there had been a child, there was now {params.transformation.visible}."
        )
        world.say(
            f"The keeper mourned, for myths are stern when promises are broken."
        )
        world.say(
            f"From that day on, the people remembered {params.remedy.rule}."
        )
        world.say(
            f"Now, when the gate is shut, everyone waits, and {params.remedy.ending}"
        )
    else:
        world.say(
            f"This was not the year for the old magic to wake, and the corral stayed quiet."
        )
        world.say(
            f"Still, the keeper kept the rule, because myths remember what might happen."
        )

    world.facts["transformed"] = intruder.transformed
    return world


@dataclass
class StoryParams:
    setting_place: str
    setting_time: str
    keeper_name: str
    keeper_type: str
    intruder_name: str
    intruder_type: str
    taboo_warning: str
    trigger_reason: str
    tension: Tension
    transformation: Transformation
    remedy: Remedy
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


SETTING_PLACES = [
    "the corral",
    "the sheep corral",
    "the horse corral",
    "the old corral",
]

TIMES = [
    "dusk",
    "sunset",
    "the blue hour",
    "the windless evening",
]

KEEPER_NAMES = ["Mara", "Jon", "Sela", "Pell", "Ivo", "Nera"]
INTRUDER_NAMES = ["Lio", "Tavi", "Rin", "Ari", "Bela", "Oren"]

KEEPER_TYPES = ["woman", "man"]
INTRUDER_TYPES = ["boy", "girl"]

TENSIONS = [
    Tension(
        taboo="No one must enter the corral after dusk.",
        warning="Keep away from the gate after sunset.",
        danger="The old horn hears footsteps.",
        consequence="then the corral will mark you.",
    ),
    Tension(
        taboo="Do not speak the corral's name while the animals are stirred.",
        warning="Be still, and leave the gate alone.",
        danger="The moon listens through the fence.",
        consequence="and the corral may answer.",
    ),
]

TRANSFORMATIONS = [
    Transformation(
        id="stone",
        label="the stone horn",
        state_name="stone",
        reveal="a figure with a face of pale stone",
        reason="the corral was made by an ancient vow",
        body_part="hands",
        visible="a statue with one hand raised in warning",
    ),
    Transformation(
        id="goat",
        label="the goat mask",
        state_name="goat",
        reveal="a child with small horns and a goat's shadow",
        reason="the old magic favors those who ignore wise words",
        body_part="feet",
        visible="a goat-footed child watching the gate forever",
    ),
]

REMEDIES = [
    Remedy(
        id="wait",
        label="waiting at the gate",
        rule="wait for the keeper's lantern before crossing any fence",
        action="waited",
        ending="the lantern comes first, and the gate opens only after the call is answered",
    ),
    Remedy(
        id="ask",
        label="asking first",
        rule="ask the keeper before touching a closed gate",
        action="asked",
        ending="the children ask first, and the corral stays only a place of care",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t.id, r.id) for p in SETTING_PLACES for t in TRANSFORMATIONS for r in REMEDIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    place = getattr(args, "place", None) or rng.choice(SETTING_PLACES)
    trans = next((t for t in TRANSFORMATIONS if t.id == (getattr(args, "transformation", None) or rng.choice([t.id for t in TRANSFORMATIONS]))), None)
    rem = next((r for r in REMEDIES if r.id == (getattr(args, "remedy", None) or rng.choice([r.id for r in REMEDIES]))), None)
    if trans is None or rem is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    keeper_name = getattr(args, "keeper", None) or rng.choice(KEEPER_NAMES)
    intruder_name = getattr(args, "intruder", None) or rng.choice(INTRUDER_NAMES)
    keeper_type = getattr(args, "keeper_type", None) or rng.choice(KEEPER_TYPES)
    intruder_type = getattr(args, "intruder_type", None) or rng.choice(INTRUDER_TYPES)
    time = getattr(args, "time", None) or rng.choice(TIMES)
    taboo_warning = getattr(args, "warning", None) or _safe_lookup(TENSIONS, 0).warning
    trigger_reason = getattr(args, "reason", None) or "the child wanted to see what the animals whispered"
    return StoryParams(
        setting_place=place,
        setting_time=time,
        keeper_name=keeper_name,
        keeper_type=keeper_type,
        intruder_name=intruder_name,
        intruder_type=intruder_type,
        taboo_warning=taboo_warning,
        trigger_reason=trigger_reason,
        tension=_safe_lookup(TENSIONS, 0),
        transformation=trans,
        remedy=rem,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    intruder = _safe_fact(world, f, "intruder")
    keeper = _safe_fact(world, f, "keeper")
    thing = _safe_fact(world, f, "thing")
    return [
        f"Write a short myth about a corral, a warning, and a transformation that happens when {intruder.label} ignores {keeper.label}.",
        f"Tell a cautionary story in a mythic style where a child enters a corral after dusk and becomes {thing.phrase}.",
        f"Write a small myth about {f['thing'].label} and a keeper who warns a curious child to stay away from the gate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    keeper = _safe_fact(world, f, "keeper")
    intruder = _safe_fact(world, f, "intruder")
    thing = _safe_fact(world, f, "thing")
    qa = [
        QAItem(
            question=f"Who kept watch over the corral in the story?",
            answer=f"{keeper.label} kept watch over the corral and tried to keep the old rule.",
        ),
        QAItem(
            question=f"What did {intruder.label} want to do at the corral?",
            answer=f"{intruder.label} wanted to go into the corral even after the warning.",
        ),
        QAItem(
            question=f"What happened after {intruder.label} ignored the warning?",
            answer=f"The corral's old magic changed {intruder.label} into {thing.phrase}.",
        ),
        QAItem(
            question="Why is this story cautionary?",
            answer="It warns that old places with rules can be dangerous when someone ignores a clear warning.",
        ),
    ]
    if f.get("transformed"):
        qa.append(QAItem(
            question=f"How did the story prove the change had really happened?",
            answer=f"It said that where there had been a child, there was now {thing.visible}.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "corral": [
        QAItem(
            question="What is a corral?",
            answer="A corral is a fenced area that keeps animals together and helps people care for them.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is when one thing changes into something else, often in a magical way.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What makes a story cautionary?",
            answer="A cautionary story warns the listener about what can happen if someone ignores a rule or a warning.",
        )
    ],
    "myth": [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains powerful, strange, or sacred things in a memorable way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["corral"] + WORLD_KNOWLEDGE["transformation"] + WORLD_KNOWLEDGE["cautionary"] + WORLD_KNOWLEDGE["myth"]


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
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% If the intruder becomes defiant and the corral's magic is present, the myth
% allows a transformation.
transforms(I) :- intruder(I), defiant(I), magic_object(T), present(T).
cautionary_story(P, T, R) :- setting(P), transforms(T), remedy(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTING_PLACES:
        lines.append(asp.fact("setting", p))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("magic_object", t.id))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary myth about a corral and a transformation.")
    ap.add_argument("--place", choices=SETTING_PLACES)
    ap.add_argument("--time", choices=TIMES)
    ap.add_argument("--transformation", choices=[t.id for t in TRANSFORMATIONS])
    ap.add_argument("--remedy", choices=[r.id for r in REMEDIES])
    ap.add_argument("--keeper")
    ap.add_argument("--intruder")
    ap.add_argument("--keeper-type", choices=KEEPER_TYPES)
    ap.add_argument("--intruder-type", choices=INTRUDER_TYPES)
    ap.add_argument("--warning")
    ap.add_argument("--reason")
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show transforms/1."))
    if model:
        print("OK: ASP program produced a model.")
        return 0
    print("MISMATCH: ASP program produced no model.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(
        setting_place="the corral",
        setting_time="dusk",
        keeper_name="Mara",
        keeper_type="woman",
        intruder_name="Lio",
        intruder_type="boy",
        taboo_warning=_safe_lookup(TENSIONS, 0).warning,
        trigger_reason="he wanted to hear the horses breathe in the dark",
        tension=_safe_lookup(TENSIONS, 0),
        transformation=_safe_lookup(TRANSFORMATIONS, 0),
        remedy=_safe_lookup(REMEDIES, 0),
    ),
    StoryParams(
        setting_place="the old corral",
        setting_time="sunset",
        keeper_name="Jon",
        keeper_type="man",
        intruder_name="Bela",
        intruder_type="girl",
        taboo_warning=_safe_lookup(TENSIONS, 1).warning,
        trigger_reason="she thought the gate was only wood and rope",
        tension=_safe_lookup(TENSIONS, 1),
        transformation=_safe_lookup(TRANSFORMATIONS, 1),
        remedy=_safe_lookup(REMEDIES, 1),
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show transforms/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show cautionary_story/3."))
        print(model)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
