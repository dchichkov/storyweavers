#!/usr/bin/env python3
"""
Superhero storyworld: amaze, insinuate, inner monologue, lesson learned, curiosity.

A small simulated domain where a young hero notices a strange clue, hears a
villain try to insinuate that they are not ready, thinks through the problem in
an inner monologue, and learns a lesson about using curiosity with courage.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    handheld: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
        if not hasattr(self, "_tags"):
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
    feature: str
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Power:
    id: str
    label: str
    verb: str
    sparkle: str
    affects: str
    cue: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    risky: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class VillainPlan:
    id: str
    label: str
    insinuation: str
    tactic: str
    counter: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

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
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    sidekick: str
    power: str
    clue: str
    villain: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "rooftop": Setting(place="the rooftop", feature="a blinking antenna", affords={"scan", "fly"}),
    "lab": Setting(place="the bright lab", feature="a glowing console", affords={"scan"}),
    "alley": Setting(place="the narrow alley", feature="a cracked wall", affords={"scan", "sneak"}),
}

POWERS = {
    "scan": Power(
        id="scan",
        label="x-ray scan",
        verb="scan",
        sparkle="a silver spark",
        affects="the hidden clue",
        cue="peered closely",
        tags={"curiosity", "amaze"},
    ),
    "fly": Power(
        id="fly",
        label="sky flight",
        verb="fly",
        sparkle="a blue streak",
        affects="the tall ledge",
        cue="lifted off the ground",
        tags={"amaze"},
    ),
    "sneak": Power(
        id="sneak",
        label="silent step",
        verb="sneak",
        sparkle="a soft shadow",
        affects="the dark corner",
        cue="moved like a whisper",
        tags={"curiosity"},
    ),
}

CLUES = {
    "signal": Clue(
        id="signal",
        label="mysterious signal",
        phrase="a tiny flashing signal in the dust",
        reveals="a trapped kitten",
        risky=False,
    ),
    "door": Clue(
        id="door",
        label="sealed door",
        phrase="a sealed little door behind the pipes",
        reveals="a lost helper robot",
        risky=True,
    ),
    "cape": Clue(
        id="cape",
        label="broken cape clasp",
        phrase="a broken cape clasp hanging from a beam",
        reveals="a safe shortcut across the roof",
        risky=False,
    ),
}

VILLAINS = {
    "murk": VillainPlan(
        id="murk",
        label="Murk the Whisperer",
        insinuation="Maybe you are not brave enough to look closer.",
        tactic="insinuate doubt",
        counter="trust the clue and look anyway",
        tags={"insinuate"},
    ),
    "shade": VillainPlan(
        id="shade",
        label="Shade the Sneer",
        insinuation="Only a clumsy hero would notice that.",
        tactic="insinuate embarrassment",
        counter="smile and keep wondering",
        tags={"insinuate"},
    ),
}

HERO_NAMES = ["Nova", "Milo", "Aria", "Zane", "Tessa", "Kai", "Luna", "Jett"]
SIDEKICKS = ["Pip", "Bolt", "Echo", "Sprite"]
HERO_TYPES = ["hero", "heroine"]
TRAITS = ["curious", "brave", "bright", "lively"]


def hero_pronoun_word(hero_type: str) -> str:
    return "she" if hero_type == "heroine" else "he"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for power_id in setting.affords:
            for clue_id, clue in CLUES.items():
                if power_id == "fly" and clue.risky:
                    continue
                combos.append((place, power_id, clue_id))
    return combos


def explain_rejection(power: Power, clue: Clue) -> str:
    return (
        f"(No story: {power.label} at this setting would not honestly help with "
        f"{clue.label}. The hero needs a clue they can truly investigate.)"
    )


def announce(world: World, hero: Entity, sidekick: Entity, villain: Entity, clue: Entity, power: Power) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved {power.label} and noticed "
        f"every strange detail around {world.setting.place}."
    )
    world.say(
        f"{sidekick.id} stayed close, because curiosity made {hero.id} look twice at "
        f"{clue.phrase}."
    )
    world.say(
        f"Then {villain.label} drifted out of the shadows and said, "
        f"'{villain.memes['insinuation_text']}'"
    )


def _r_amaze(world: World) -> list[str]:
    out = []
    hero = world.get("Hero")
    clue = world.get("Clue")
    if hero.memes.get("amaze_seen", 0) >= 1 and ("amaze", "noticed") not in world.fired:
        world.fired.add(("amaze", "noticed"))
        hero.memes["awe"] = hero.memes.get("awe", 0) + 1
        out.append(f"The sight of {clue.label} made {hero.id} stop and stare.")
    return out


def _r_curiosity(world: World) -> list[str]:
    hero = world.get("Hero")
    if hero.memes.get("curiosity", 0) < 1:
        return []
    if ("curiosity", "focus") in world.fired:
        return []
    world.fired.add(("curiosity", "focus"))
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    return [f"{hero.id} leaned in instead of walking away."]


def _r_insinuate(world: World) -> list[str]:
    hero = world.get("Hero")
    villain = world.get("Villain")
    if hero.memes.get("doubt", 0) < 1:
        return []
    if ("insinuate", "shadow") in world.fired:
        return []
    world.fired.add(("insinuate", "shadow"))
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    return [f"{villain.label} tried to make the idea feel small, but {hero.id} held on to the clue."]


def _r_lesson(world: World) -> list[str]:
    hero = world.get("Hero")
    if hero.memes.get("lesson", 0) >= 1:
        return []
    if hero.memes.get("resolve", 0) < 1 or hero.memes.get("focus", 0) < 1:
        return []
    hero.memes["lesson"] = 1
    return [f"{hero.id} learned that curiosity can be a superpower when it is guided by courage."]


RULES = [_r_amaze, _r_curiosity, _r_insinuate, _r_lesson]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def simulate(world: World, hero: Entity, villain: Entity, clue: Entity, power: Power) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["amaze_seen"] = 1
    world.say(
        f"One evening at {world.setting.place}, {hero.id} spotted {world.setting.feature} and "
        f"felt a spark of curiosity."
    )
    world.say(
        f"{hero.id} used {power.label} and the air flashed with {power.sparkle}."
    )
    world.say(
        f"That let {hero.id} {power.cue}, and it revealed {clue.phrase}."
    )
    world.para()
    hero.memes["doubt"] = 1
    villain.memes["insinuation_text"] = villain.memes.get("insinuation_text", villain.memes.get("insinuation", ""))
    world.say(f"{villain.label} stepped forward and said, '{villain.memes['insinuation_text']}'")
    world.say(
        f"{hero.id} paused for an inner monologue: 'I can be careful, and I can still ask questions.'"
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{hero.id} chose to follow the clue anyway, and {clue.reveals} was safely found."
    )
    if hero.memes.get("lesson", 0) >= 1:
        world.say(
            f"By the end, {hero.id} knew that curiosity and courage could work together, "
            f"and that made the whole city feel brighter."
        )
    else:
        world.say(
            f"By the end, {hero.id} smiled at the answer and felt ready for the next mystery."
        )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type=params.hero_type, label=params.hero))
    sidekick = world.add(Entity(id="Sidekick", kind="character", type="sidekick", label=params.sidekick))
    villain = world.add(Entity(id="Villain", kind="character", type="villain", label=params.villain))
    clue = world.add(Entity(id="Clue", type="clue", label=params.clue, phrase=_safe_lookup(CLUES, params.clue).phrase))
    power = _safe_lookup(POWERS, params.power)
    villain.memes["insinuation"] = VILLAINS["murk"].insinuation if params.villain == "Murk the Whisperer" else VILLAINS["shade"].insinuation
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, clue=clue, power=power, params=params)
    simulate(world, hero, villain, clue, power)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a short superhero story for a young child that includes the words "amaze" and "insinuate".',
        f"Tell a story about {params.hero} using {_safe_lookup(POWERS, params.power).label} at {world.setting.place} while a villain tries to insinuate doubt.",
        f"Write a gentle superhero tale with an inner monologue, a lesson learned, and a curious hero named {params.hero}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    villain: Entity = f["villain"]
    clue: Entity = f["clue"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.hero}, a {p.hero_type} superhero who stays curious even when the mystery feels tricky.",
        ),
        QAItem(
            question=f"What did {villain.label} try to do?",
            answer=f"{villain.label} tried to insinuate doubt and make the hero feel too small to keep looking.",
        ),
        QAItem(
            question=f"What was {p.hero} thinking in the inner monologue?",
            answer=f"{p.hero} thought, 'I can be careful, and I can still ask questions,' which helped {hero.id} keep going.",
        ),
        QAItem(
            question=f"What clue did the hero notice at {world.setting.place}?",
            answer=f"The hero noticed {clue.phrase} and followed it until the answer was safe to find.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that curiosity can be a superpower when it is guided by courage.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, look closer, and ask questions.",
        ),
        QAItem(
            question="What does it mean to insinuate something?",
            answer="To insinuate something is to suggest it in a sneaky or indirect way, often to make someone doubt themselves.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talk in someone's mind, when they think through a choice or a feeling.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a good idea or truth someone understands after something happens.",
        ),
        QAItem(
            question="Why can superhero stories be exciting?",
            answer="Superhero stories are exciting because heroes use special powers, face dangers, and try to help others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rooftop", hero="Nova", hero_type="heroine", sidekick="Pip", power="scan", clue="signal", villain="Murk the Whisperer"),
    StoryParams(place="lab", hero="Milo", hero_type="hero", sidekick="Bolt", power="scan", clue="door", villain="Shade the Sneer"),
    StoryParams(place="alley", hero="Aria", hero_type="heroine", sidekick="Echo", power="sneak", clue="cape", villain="Murk the Whisperer"),
]


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
% Facts supplied by asp_facts():
% setting(Place). afford(Place,Power).
% clue(Clue). power(Power).
% risky_clue(Clue).
% villain(Villain).
% uses(Power,Tag).
% clue_tag(Clue,Tag).

compatible(Place, Power, Clue) :-
    afford(Place, Power),
    clue(Clue),
    power(Power),
    not blocked(Power, Clue).

blocked(fly, Clue) :- risky_clue(Clue).
valid_story(Place, Power, Clue) :- compatible(Place, Power, Clue).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for power in sorted(setting.affords):
            lines.append(asp.fact("afford", place, power))
    for pid, power in POWERS.items():
        lines.append(asp.fact("power", pid))
        for tag in sorted(power.tags):
            lines.append(asp.fact("uses", pid, tag))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.risky:
            lines.append(asp.fact("risky_clue", cid))
        for tag in ("curiosity", "amaze"):
            if cid in {"signal", "door", "cape"}:
                lines.append(asp.fact("clue_tag", cid, tag))
    for vid in VILLAINS:
        lines.append(asp.fact("villain", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_story_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with amaze, insinuate, curiosity, inner monologue, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["hero", "heroine"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--villain", choices=["Murk the Whisperer", "Shade the Sneer"])
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "power", None):
        combos = [c for c in combos if c[1] == getattr(args, "power", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[2] == getattr(args, "clue", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, power, clue = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    villain = getattr(args, "villain", None) or rng.choice(list(VILLAINS.values())).label
    return StoryParams(place=place, hero=hero, hero_type=hero_type, sidekick=sidekick, power=power, clue=clue, villain=villain)


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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
