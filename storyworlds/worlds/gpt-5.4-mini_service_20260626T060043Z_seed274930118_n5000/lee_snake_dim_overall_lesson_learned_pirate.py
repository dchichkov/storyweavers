#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lee_snake_dim_overall_lesson_learned_pirate.py
===============================================================================================================

A small pirate-tale storyworld with a lesson learned.

Seed tale sketch:
- Lee is a young pirate.
- On a dim evening, Lee finds a snake-dim looking lantern on the deck.
- Lee wants to rush ahead for shiny loot.
- The captain warns that reckless choices can lose the map and scare the crew.
- Lee makes a foolish move, then learns to slow down, light the way, and work together.
- Overall, Lee ends wiser, with the crew safe and the treasure still aboard.

This world models:
- physical meters: light, safety, wetness, damage, treasure_hold, tidiness
- emotional memes: pride, worry, trust, bravery, relief, shame, lesson

The resulting stories are short pirate tales with a clear turn and a lesson learned.
"""

from __future__ import annotations

import argparse
import dataclasses
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


LIGHT_THRESHOLD = 1.0
DANGER_THRESHOLD = 1.0
LESSON_THRESHOLD = 1.0



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    crew: object | None = None
    deck: object | None = None
    lantern: object | None = None
    lee: object | None = None
    map_item: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "captain", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the deck"
    overall: str = "dim"
    night: bool = True
    pitch: str = "the moonless sea"
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
class StoryParams:
    place: str = ""
    overall: str = ""
    name: str = ""
    seed: Optional[int] = None
    sample: object | None = None
    samples: list = field(default_factory=list)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "StoryWorld":
        clone = StoryWorld(self.setting)
        clone.entities = __import__('copy').deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


SETTINGS = {
    "deck": Setting(place="the deck", overall="dim", night=True, pitch="the black sea"),
    "cove": Setting(place="the cove", overall="dim", night=False, pitch="the rocky shore"),
    "harbor": Setting(place="the harbor", overall="overall dim", night=True, pitch="the quiet harbor"),
}

NAMES = ["Lee", "Mara", "Finn", "Bo", "Nell", "Ivy"]
CAPTAINS = ["Captain Salt", "Captain Reed", "Captain Wren"]


def _r_darkness(world: StoryWorld) -> list[str]:
    out = []
    lantern = world.entities.get("lantern")
    if not lantern:
        return out
    if lantern.meters.get("light", 0.0) < LIGHT_THRESHOLD:
        sig = ("darkness",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("crew").memes["worry"] = world.get("crew").memes.get("worry", 0) + 1
            out.append("The deck stayed snake-dim, and everyone had to squint.")
    return out


def _r_slip(world: StoryWorld) -> list[str]:
    out = []
    lee = world.get("lee")
    if lee.memes.get("rush", 0.0) < LESSON_THRESHOLD:
        return out
    if world.get("deck").meters.get("wet", 0.0) < DANGER_THRESHOLD:
        return out
    sig = ("slip",)
    if sig not in world.fired:
        world.fired.add(sig)
        lee.meters["damage"] = lee.meters.get("damage", 0) + 1
        lee.memes["shame"] = lee.memes.get("shame", 0) + 1
        out.append("Lee slipped on the wet boards and clutched the rail.")
    return out


def _r_lesson(world: StoryWorld) -> list[str]:
    out = []
    lee = world.get("lee")
    captain = world.get("captain")
    if lee.memes.get("shame", 0.0) < LESSON_THRESHOLD:
        return out
    sig = ("lesson",)
    if sig not in world.fired:
        world.fired.add(sig)
        lee.memes["lesson"] = lee.memes.get("lesson", 0) + 1
        lee.memes["rush"] = 0
        lee.memes["trust"] = lee.memes.get("trust", 0) + 1
        captain.memes["pride"] = captain.memes.get("pride", 0) + 1
        out.append("Lee learned that slow steps and a steady light keep a pirate safer.")
    return out


CAUSAL_RULES = [
    Rule("darkness", _r_darkness),
    Rule("slip", _r_slip),
    Rule("lesson", _r_lesson),
]


def propagate(world: StoryWorld, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: StoryWorld) -> dict:
    sim = world.copy()
    sim.get("deck").meters["wet"] = 1.0
    sim.get("lee").memes["rush"] = 1.0
    propagate(sim, narrate=False)
    return {
        "slip": sim.get("lee").meters.get("damage", 0) > 0,
        "lesson": sim.get("lee").memes.get("lesson", 0) > 0,
    }


def tell(setting: Setting, name: str) -> StoryWorld:
    world = StoryWorld(setting)

    lee = world.add(Entity(id="lee", kind="character", type="pirate", label=name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=random.choice(CAPTAINS)))
    crew = world.add(Entity(id="crew", kind="group", type="pirate", label="the crew", plural=True))
    deck = world.add(Entity(id="deck", type="thing", label="the deck"))
    lantern = world.add(Entity(id="lantern", type="thing", label="the lantern", phrase="a snake-dim lantern"))
    map_item = world.add(Entity(id="map", type="thing", label="the map", phrase="the old treasure map"))
    treasure = world.add(Entity(id="treasure", type="thing", label="the chest", phrase="a brass chest of coins"))

    deck.meters["wet"] = 1.0
    lantern.meters["light"] = 0.0
    lee.memes["pride"] = 1.0
    lee.memes["rush"] = 1.0
    crew.memes["worry"] = 0.0
    captain.memes["watch"] = 1.0

    world.say(f"Lee was a young pirate on {setting.place} with {setting.overall} skies and {setting.pitch}.")
    world.say(f"Near the mast sat {lantern.phrase}, and even the crew felt the strange snake-dim glow.")
    world.say(f"Lee loved shiny things and wanted the treasure fast, before the tide could change its mind.")

    world.para()
    world.say(f"That evening, {captain.label} pointed at the wet boards and the old map.")
    world.say(f'"If you rush now," {captain.pronoun("subject")} said, "you may lose the map and the trust of the crew."')
    world.say(f"Lee wanted to prove {lee.pronoun('possessive')} courage, so {lee.pronoun('subject')} grabbed the lantern and hurried anyway.")

    world.para()
    propagate(world, narrate=True)

    outcome = predict_outcome(world)
    if outcome["slip"]:
        world.say("The wet deck caught Lee's boot, and the treasure chest thumped hard against the rail.")
    if outcome["lesson"]:
        world.say(f"Lee blinked, took a deep breath, and handed the lantern back to {captain.label}.")
        world.say(f'"Slow steps are smarter," Lee said, and the crew nodded as the light grew steady again.')
        lantern.meters["light"] = 1.0
        deck.meters["wet"] = 0.0
        lee.memes["lesson"] = 1.0
        lee.memes["trust"] = 1.0
        crew.memes["worry"] = 0.0
        world.say(f"Overall, Lee learned that a pirate with patience can protect {map_item.label} and still reach {treasure.label} safely.")
    else:
        world.say("In the end, the tide changed, and the night stayed too dim for any clever rescue.")

    world.facts.update(
        lee=lee,
        captain=captain,
        crew=crew,
        deck=deck,
        lantern=lantern,
        map=map_item,
        treasure=treasure,
        outcome=outcome,
        setting=setting,
    )
    return world


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.night:
            lines.append(asp.fact("night", sid))
        lines.append(asp.fact("overall", sid, s.overall))
    lines.append(asp.fact("character", "lee"))
    lines.append(asp.fact("character", "captain"))
    lines.append(asp.fact("group", "crew"))
    lines.append(asp.fact("thing", "lantern"))
    lines.append(asp.fact("thing", "map"))
    lines.append(asp.fact("thing", "treasure"))
    lines.append(asp.fact("dim_style", "snake_dim"))
    lines.append(asp.fact("lesson_theme", "lesson_learned"))
    lines.append(asp.fact("keyword", "lee"))
    lines.append(asp.fact("keyword", "snake_dim"))
    lines.append(asp.fact("keyword", "overall"))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is sensible when the deck is dim, Lee rushes, and a lesson can be learned.
dim_scene(S) :- setting(S), overall(S, dim).
dim_scene(S) :- setting(S), overall(S, overall_dim).

lesson_possible(S) :- dim_scene(S), character(lee), character(captain), thing(lantern), thing(map), thing(treasure).

story_ok(S) :- lesson_possible(S), night(S).
#show story_ok/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_ok() -> bool:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show story_ok/1."))
    return bool(asp.atoms(model, "story_ok"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    overall = _safe_lookup(SETTINGS, place).overall
    return StoryParams(place=place, overall=overall, name=name)


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "lee").label} learns a lesson on {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place}.',
        f'Write a child-friendly pirate tale that includes the words "lee", "snake-dim", and "overall".',
        f"Tell a story about a dim deck, a stubborn pirate, and a lesson learned in the end.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    lee = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "lee")
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "captain")
    setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        QAItem(
            question=f"Who learned the lesson in the story?",
            answer=f"Lee learned the lesson after rushing around on {setting.place} and seeing why the captain's warning mattered.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry about Lee's choice?",
            answer=f"{captain.label} worried because the deck was wet and snake-dim, so rushing could make Lee slip and risk the map.",
        ),
        QAItem(
            question=f"How did Lee change by the end?",
            answer="Lee slowed down, trusted the captain's warning, and chose the safer way to move with the lantern.",
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when a deck is dim?",
            answer="A dim deck has very little light, so pirates must squint and move carefully.",
        ),
        QAItem(
            question="What is a lantern for on a ship?",
            answer="A lantern gives light so people can see where they are walking and avoid bumps or slips.",
        ),
        QAItem(
            question="Why should pirates be careful on wet boards?",
            answer="Wet boards can be slippery, so careful steps help keep someone from falling over.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} {e.type:10} {' '.join(bits)}")
    return "\n".join(lines)


def verify() -> int:
    if not asp_ok():
        print("ASP gate did not produce a story_ok model.")
        return 1
    sample = generate(StoryParams(place="deck", overall="dim", name="Lee"))
    if "learned" not in sample.story.lower():
        print("Generated story did not include the lesson learned.")
        return 1
    print("OK: ASP gate and story generation look reasonable.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name)
    return StorySample(
        params=params,
        story=world.render(),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/1."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(verify())
    if getattr(args, "asp", None):
        print("story_ok" if asp_ok() else "no models")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=k, overall=v.overall, name="Lee")) for k, v in SETTINGS.items()]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
