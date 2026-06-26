#!/usr/bin/env python3
"""
storyworlds/worlds/rave_repetition_misunderstanding_curiosity_comedy.py
========================================================================

A small comedy storyworld about a child who gets curious about a rave,
misunderstands what is happening, and keeps repeating the wrong idea until
someone gently clears it up.

The world is built from a tiny simulated premise:
- A child hears about a rave in a bright community hall.
- Their curiosity keeps rising as they repeat a mistaken explanation.
- A helpful adult notices the misunderstanding and explains the real plan.
- The child joins the fun in a safe, silly way, and the ending proves the
  misunderstanding changed into a cheerful, shared laugh.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- shared results import is eager
- ASP helpers are lazy
- typed physical meters and emotional memes
- inline ASP rules mirror the Python reasonableness gate
- trace, QA, JSON, ASP, verify, and show-ASP modes are supported
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def possessive_name(self) -> str:
        return self.label if self.label else self.id
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
    indoor: bool
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
class Event:
    id: str
    label: str
    action: str
    noise: str
    prop: str
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
class Guide:
    id: str
    label: str
    role: str
    explanation: str
    comfort: str
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
        self.history: list[str] = []

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "community_hall": Setting(place="the community hall", indoor=True, affords={"rave"}),
    "school_gym": Setting(place="the school gym", indoor=True, affords={"rave"}),
    "garden_stage": Setting(place="the garden stage", indoor=False, affords={"rave"}),
}

EVENTS = {
    "rave": Event(
        id="rave",
        label="a tiny rave",
        action="dance to the beat",
        noise="thump-thump music",
        prop="glow sticks",
        tags={"rave", "music", "dance"},
    ),
}

GUIDES = {
    "helper": Guide(
        id="helper",
        label="the helper",
        role="grown-up helper",
        explanation="it was a family-friendly dance party, not a wild secret",
        comfort="showed the child where to stand and handed over a glow stick",
    ),
}

CHILD_NAMES = ["Milo", "Nina", "Tara", "Ivy", "Owen", "Jules", "Pia", "Leo"]
ADULT_NAMES = ["Aunt Bea", "Uncle Ray", "Ms. June", "Mr. Finn"]
TRAITS = ["curious", "silly", "bouncy", "chatty", "bright"]


@dataclass
class StoryParams:
    place: str
    event: str
    name: str
    gender: str
    guide: str
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


def reasonableness_gate(place: str, event: str) -> bool:
    return place in SETTINGS and event in EVENTS and event in _safe_lookup(SETTINGS, place).affords


def explain_rejection(place: str, event: str) -> str:
    return f"(No story: {event} does not fit at {place} in this tiny comedy world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy storyworld about rave curiosity, misunderstanding, and repetition."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["helper"])
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
    combos = []
    for place, setting in SETTINGS.items():
        for event in setting.affords:
            if getattr(args, "place", None) and getattr(args, "place", None) != place:
                continue
            if getattr(args, "event", None) and getattr(args, "event", None) != event:
                continue
            if not reasonableness_gate(place, event):
                continue
            combos.append((place, event))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES if gender == "girl" else CHILD_NAMES)
    guide = getattr(args, "guide", None) or "helper"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, event=event, name=name, gender=gender, guide=guide, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ev = _safe_fact(world, f, "event")
    return [
        f'Write a funny story for a small child about "{ev.label}" and a curious kid named {hero.id}.',
        f"Tell a comedy story where {hero.id} keeps repeating the wrong idea about a rave until the helper explains it.",
        f"Write a short child-friendly story about curiosity, misunderstanding, and a silly rave at {world.setting.place}.",
    ]


def _narrate_setup(world: World, hero: Entity, guide: Entity, event: Event) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} child who liked to ask about everything.")
    world.say(f"One day, {hero.id} heard about {event.label} and blinked at the word like it was a noodle.")
    hero.memes["curiosity"] += 1
    world.say(f"{hero.pronoun().capitalize()} wanted to know what the {event.id} was right away.")
    world.say(f"{guide.label} smiled because {hero.id} had already started guessing out loud.")


def _narrate_repetition(world: World, hero: Entity, guide: Entity, event: Event) -> None:
    hero.memes["repetition"] += 1
    hero.memes["misunderstanding"] += 1
    world.say(f'"A rave is a cave," {hero.id} said, nodding very seriously.')
    world.say(f'"No, not a cave," {guide.label} said, laughing. "{event.label} is a dance party."')
    world.say(f'{hero.id} repeated, "A rave is a cave," because the sound of the word kept tickling {hero.pronoun("possessive")} ears.')
    world.say(f"{guide.label} gently shook {hero.pronoun('possessive')} head and repeated the real meaning again.")


def _narrate_turn(world: World, hero: Entity, guide: Entity, event: Event) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"Now {hero.id} was even more curious.")
    world.say(f"{hero.pronoun().capitalize()} looked at the {event.prop} and asked, 'Do caves usually glow like this?'")
    world.say(f"{guide.label} laughed so hard {guide.label.lower()} had to hold the snack table.")
    world.say(f"Then {guide.label} explained that {event.label} meant music, dancing, and funny happy feet.")
    hero.memes["misunderstanding"] = 0.0
    hero.memes["joy"] += 1


def _narrate_resolution(world: World, hero: Entity, guide: Entity, event: Event) -> None:
    world.say(f"{guide.label} handed {hero.pronoun('object')} a glow stick and said, 'You can join the dance party.'")
    world.say(f"{hero.id} did a tiny stomp, then another, and grinned when the beat went thump-thump-thump.")
    world.say(f"Soon {hero.id} was {event.action}, and everyone laughed because the first idea had been so wrong and so funny.")
    world.say(f"At the end, {hero.id} still remembered the joke, but now {hero.pronoun('subject')} knew a rave was not a cave at all.")


def tell_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    event = _safe_lookup(EVENTS, params.event)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait]))
    guide = world.add(Entity(id="Guide", kind="character", type="adult", label=_safe_lookup(ADULT_NAMES, 0), traits=["kind"]))
    world.facts.update(hero=hero, guide=guide, event=event, setting=setting)
    _narrate_setup(world, hero, guide, event)
    world.para()
    _narrate_repetition(world, hero, guide, event)
    world.para()
    _narrate_turn(world, hero, guide, event)
    world.para()
    _narrate_resolution(world, hero, guide, event)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    event = _safe_fact(world, f, "event")
    return [
        QAItem(
            question=f"Why did {hero.id} keep saying a rave was a cave?",
            answer=f"{hero.id} misunderstood the word at first, and {hero.pronoun('subject')} kept repeating the wrong idea because it sounded funny and strange.",
        ),
        QAItem(
            question=f"Who explained what {event.label} really was?",
            answer=f"{guide.label} explained that {event.label} was a dance party with music, glow sticks, and happy feet.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} understood the joke, joined the dancing, and felt cheerful instead of confused.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rave?",
            answer="A rave is a loud dance party with music, lights, and people moving to the beat.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to ask questions and learn more about something new.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what something means.",
        ),
        QAItem(
            question="Why do people repeat words when they are confused?",
            answer="People sometimes repeat words when they are confused because they are trying to make sense of them.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
show_rave(P) :- place(P), affords(P,rave).
valid_story(P,rave) :- show_rave(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for ev in sorted(s.affords):
            lines.append(asp.fact("affords", pid, ev))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, event) for place, setting in SETTINGS.items() for event in setting.affords if reasonableness_gate(place, event))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


CURATED = [
    StoryParams(place="community_hall", event="rave", name="Milo", gender="boy", guide="helper", trait="curious"),
    StoryParams(place="school_gym", event="rave", name="Nina", gender="girl", guide="helper", trait="silly"),
    StoryParams(place="garden_stage", event="rave", name="Owen", gender="boy", guide="helper", trait="chatty"),
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "event", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "event", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    event = getattr(args, "event", None) or "rave"
    if not reasonableness_gate(place, event):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    guide = getattr(args, "guide", None) or "helper"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, event=event, name=name, gender=gender, guide=guide, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, event) combos:\n")
        for place, event in triples:
            print(f"  {place:16} {event}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.event} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
