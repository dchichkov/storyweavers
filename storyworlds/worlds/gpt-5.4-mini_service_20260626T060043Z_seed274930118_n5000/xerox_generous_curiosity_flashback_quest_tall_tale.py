#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about a curious quest, a generous helper,
a flashback, and a xerox machine that changes the course of the day.

The seed tale behind this world:
A curious child hears a rumor about a lost map to a hilltop spring.
With a generous clerk's help, the child uses an old xerox machine to copy
a faded clue, remembers a forgotten detail in a flashback, and sets off
on a quest that ends with a warm, unusual victory.

This script builds a small simulated world where curiosity pushes the hero
forward, the flashback reveals a useful memory, and the quest resolves
through a concrete physical change in the world.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    art: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "clerk"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    adjective: str
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
class Artifact:
    id: str
    label: str
    phrase: str
    value: str
    copied_by: str = ""
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
    artifact: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _rule_curious_glance(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    artifact = world.entities.get("artifact")
    if not hero or not artifact:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("curious", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["curious"] = True
    out.append(f"{hero.id} kept staring at the {artifact.label}, wondering what secret it held.")
    return out


def _rule_flashback(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("memory", 0.0) < THRESHOLD:
        return out
    sig = ("flashback", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["flashback"] = True
    out.append(
        f"Then came a flashback: {hero.id} remembered a scribbled note tucked into an old lunch pail."
    )
    return out


def _rule_xerox_copy(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    artifact = world.entities.get("artifact")
    if not helper or not artifact:
        return out
    if helper.memes.get("generosity", 0.0) < THRESHOLD:
        return out
    sig = ("xerox", artifact.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    artifact.meters["copies"] = artifact.meters.get("copies", 0.0) + 1
    world.facts["copied"] = True
    out.append(
        f"The generous clerk fed the faded paper into the xerox machine, and out came a bright fresh copy."
    )
    return out


def _rule_quest_complete(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("resolve", 0.0) < THRESHOLD:
        return out
    sig = ("quest", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["quest_complete"] = True
    out.append(
        f"At last, the quest reached the hilltop spring, where the water rang clear as a bell."
    )
    return out


RULES = [
    Rule("curious_glance", _rule_curious_glance),
    Rule("flashback", _rule_flashback),
    Rule("xerox_copy", _rule_xerox_copy),
    Rule("quest_complete", _rule_quest_complete),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "station": Setting(place="the little rail station", adjective="dusty", affords={"xerox", "quest"}),
    "library": Setting(place="the town library", adjective="quiet", affords={"xerox", "quest"}),
    "office": Setting(place="the county office", adjective="busy", affords={"xerox", "quest"}),
}

ARTIFACTS = {
    "map": Artifact(id="map", label="map", phrase="a faded map with a curled corner", value="spring trail"),
    "clue": Artifact(id="clue", label="clue sheet", phrase="a wrinkled clue sheet", value="hidden spring note"),
    "notice": Artifact(id="notice", label="notice", phrase="a torn notice with tiny writing", value="old trail warning"),
}

HERO_NAMES = ["June", "Milo", "Nell", "Otis", "Piper", "Toby"]
HERO_TYPES = ["boy", "girl"]
HELPER_TYPES = ["clerk", "librarian", "stationmaster"]
TRAITS = ["curious", "bold", "bright-eyed", "restless", "wondering"]


def reasonableness_gate(setting: Setting, artifact: Artifact) -> bool:
    return "xerox" in setting.affords and artifact.label in {"map", "clue", "notice"}


def explain_invalid(setting: Setting, artifact: Artifact) -> str:
    if "xerox" not in setting.affords:
        return f"(No story: this place cannot support a xerox machine tale.)"
    return f"(No story: a {artifact.label} does not fit this clue-copying quest well enough.)"


def render_intro(world: World, hero: Entity, helper: Entity, artifact: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who could smell adventure before breakfast."
    )
    world.say(
        f"{hero.id} heard that a {artifact.label} might lead to the hilltop spring, and {hero.pronoun()} wanted to find it."
    )
    world.say(
        f"At {world.setting.place}, {helper.pronoun('subject')} was known as a {helper.label} with a generous heart and a steady hand."
    )


def render_setup(world: World, hero: Entity, helper: Entity, artifact: Entity) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["generosity"] += 1
    artifact.meters["age"] = 1
    world.say(
        f"The day was {world.setting.adjective}, and the old paper looked as thin as a cobweb."
    )
    world.say(
        f"{hero.id} leaned close, hoping to make out the path, but the letters were scratched and pale."
    )


def render_flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"That was when a flashback knocked on {hero.pronoun('possessive')} mind like a woodpecker on a fencepost."
    )
    world.say(
        f"{hero.id} remembered a grandmother's saying: 'If the road vanishes, follow the stone with the blue chip.'"
    )


def render_help(world: World, helper: Entity, artifact: Entity) -> None:
    helper.memes["generosity"] += 1
    world.say(
        f"The generous {helper.label} smiled and said, 'Let's xerox the clue before it fades any farther.'"
    )
    world.say(
        f"Together they carried the {artifact.label} to the humming machine, and the copy came out crisp enough to read by lantern light."
    )


def render_departure(world: World, hero: Entity, artifact: Entity) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"With the fresh copy in hand, {hero.id} set off on the quest down the hill, light on {hero.pronoun('possessive')} feet and big in {hero.pronoun('possessive')} wishes."
    )
    world.say(
        f"The copied clue pointed to a blue stone, then a bend in the cedar path, then the spring itself."
    )


def render_resolution(world: World, hero: Entity) -> None:
    world.say(
        f"At the end, {hero.id} found the spring, and the water sang over the rocks like a silver fiddle."
    )
    world.say(
        f"{hero.id} shared the first cool cup with the generous helper, and the whole town soon knew the tale of the xerox copy that saved the quest."
    )


def tell(setting: Setting, artifact: Artifact, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=[trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type))
    art = world.add(Entity(id="artifact", kind="thing", type=artifact.label, label=artifact.label, phrase=artifact.phrase))
    world.facts.update(hero=hero, helper=helper, artifact=art, setting=setting)

    render_intro(world, hero, helper, art)
    world.para()
    render_setup(world, hero, helper, art)
    propagate(world, narrate=True)
    world.para()
    render_flashback(world, hero)
    propagate(world, narrate=True)
    world.para()
    render_help(world, helper, art)
    render_departure(world, hero, art)
    propagate(world, narrate=True)
    world.para()
    render_resolution(world, hero)
    return world


def build_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    art: Entity = _safe_fact(world, f, "artifact")
    return [
        f'Write a tall-tale style story for a child who is full of curiosity and finds a xerox copy of a {art.label}.',
        f"Tell a gentle adventure about {hero.label}, a {hero.type}, and a generous {helper.label} who help finish a quest.",
        f"Write a short story that includes a flashback, a xerox machine, and a hilltop spring.",
    ]


def build_story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    art: Entity = _safe_fact(world, f, "artifact")
    setting: Setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"What was {hero.label} looking for at {setting.place}?",
            answer=f"{hero.label} was looking for the {art.label} that could lead to the hilltop spring.",
        ),
        QAItem(
            question=f"Who helped {hero.label} make a fresh copy of the clue?",
            answer=f"The generous {helper.label} helped by using the xerox machine.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.label} remember?",
            answer=f"The flashback helped {hero.label} remember the blue stone with the chip in it.",
        ),
        QAItem(
            question=f"Where did the quest end?",
            answer="The quest ended at the hilltop spring, where the water was clear and bright.",
        ),
    ]
    return qa


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a xerox machine do?",
            answer="A xerox machine makes a copy of a paper page so someone can read it again without using the original.",
        ),
        QAItem(
            question="What does generous mean?",
            answer="Generous means willing to share, help, or give something kindly to someone else.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a long, important search or journey for something that matters.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory scene that shows something that happened before the present moment.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more and ask questions.",
        ),
    ]


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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("artifact_label", aid, a.label))
    return "\n".join(lines)


ASP_RULES = r"""
requires_xerox(S,A) :- affords(S,xerox), artifact_label(A,map).
requires_xerox(S,A) :- affords(S,xerox), artifact_label(A,clue).
requires_xerox(S,A) :- affords(S,xerox), artifact_label(A,notice).
valid_story(S,A) :- requires_xerox(S,A).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(sid, aid) for sid, s in SETTINGS.items() for aid, a in ARTIFACTS.items() if reasonableness_gate(s, a)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid story pairs.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: curiosity, flashback, quest, xerox, generosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    artifact = getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS))
    if getattr(args, "setting", None) and getattr(args, "artifact", None) and not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(ARTIFACTS, getattr(args, "artifact", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    return StoryParams(setting=setting, artifact=artifact, hero_name=name, hero_type=hero_type, helper_type=helper_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ARTIFACTS, params.artifact), params.hero_name, params.hero_type, params.helper_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=build_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
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
    StoryParams(setting="station", artifact="map", hero_name="June", hero_type="girl", helper_type="stationmaster", trait="curious"),
    StoryParams(setting="library", artifact="clue", hero_name="Milo", hero_type="boy", helper_type="librarian", trait="wondering"),
    StoryParams(setting="office", artifact="notice", hero_name="Nell", hero_type="girl", helper_type="clerk", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        valid = asp_valid()
        print(f"{len(valid)} compatible story pairs:")
        for sid, aid in valid:
            print(f"  {sid:8} {aid}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
