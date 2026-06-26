#!/usr/bin/env python3
"""
A tiny space-adventure storyworld about a child crew member, a dim passage,
a cautious crouch, and a lesson learned after a useful flashback.

Premise:
- A young spacer wants to pass through a dim ship passage to reach a goal.
- The passage has a low beam and a half-lit floor guide.
- If the spacer rushes, they may bump the beam or miss the safer path.
- A mentor warns them; a flashback reminds them why careful movement matters.
- They crouch, pass through safely, and learn a lesson about moving slowly
  in tight places.

The world uses typed entities with physical meters and emotional memes, and
generates a complete child-facing story with Q&A plus an ASP parity twin.
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
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    guide: object | None = None
    hero: object | None = None
    trinket: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)
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
    place: str = "the dim passage"
    affordance: str = "pass-dim"
    low_beam: bool = True
    SETTING: object | None = None
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
    mess: str
    soil: str
    risk_region: str
    lesson: str
    keyword: str = ""
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "head"
    plural: bool = False
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
class StoryParams:
    activity: str
    prize: str
    name: str
    gender: str
    mentor: str
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


ACTIVITIES = {
    "pass-dim": Activity(
        id="pass-dim",
        verb="pass through the dim passage",
        gerund="slipping through the dim passage",
        rush="dash down the passage",
        mess="bump",
        soil="scraped and rattled",
        risk_region="head",
        lesson="slow steps help in small places",
        keyword="dim",
    ),
    "crawl-service": Activity(
        id="crawl-service",
        verb="crawl through the service tunnel",
        gerund="crawling through the service tunnel",
        rush="scramble into the tunnel",
        mess="bump",
        soil="scraped and dusty",
        risk_region="back",
        lesson="low tunnels need careful movement",
        keyword="tunnel",
    ),
    "crouch-arch": Activity(
        id="crouch-arch",
        verb="crouch under the archway",
        gerund="moving under the archway in a crouch",
        rush="spring under the archway",
        mess="bump",
        soil="bruised",
        risk_region="head",
        lesson="a crouch can turn a risky path into a safe one",
        keyword="crouch",
    ),
}

PRIZES = {
    "helmet": Prize(label="helmet", phrase="a bright junior helmet", type="helmet"),
    "scanner": Prize(label="scanner", phrase="a small hand scanner", type="scanner"),
    "badge": Prize(label="badge", phrase="a shiny crew badge", type="badge"),
}

SETTING = Setting()

GIRL_NAMES = ["Mina", "Luna", "Tia", "Nia", "Zoe", "Ari"]
BOY_NAMES = ["Kai", "Owen", "Jax", "Rin", "Leo", "Milo"]
TRAITS = ["curious", "brave", "careful", "spunky", "bright"]

ASP_RULES = r"""
risk(A,P) :- activity(A), prize(P), region(A,R), worn_on(P,R).
need_crouch(A) :- activity(A), low_beam.
safe(A) :- need_crouch(A).
lesson_learned(A) :- safe(A).
#show risk/2.
#show need_crouch/1.
#show safe/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("low_beam"))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
        lines.append(asp.fact("region", a.id, a.risk_region))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.label))
        lines.append(asp.fact("worn_on", p.label, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _jsonable_world(world: World) -> dict:
    return {
        "setting": world.setting.__dict__,
        "entities": {
            eid: {
                "id": e.id,
                "kind": e.kind,
                "type": e.type,
                "label": e.label,
                "phrase": e.phrase,
                "owner": e.owner,
                "caretaker": e.caretaker,
                "region": e.region,
                "plural": e.plural,
                "meters": e.meters,
                "memes": e.memes,
            }
            for eid, e in world.entities.items()
        },
        "facts": world.facts,
    }


def _update(world: World, actor: Entity, activity: Activity, prize: Entity) -> None:
    actor.meters["effort"] = actor.meters.get("effort", 0.0) + 1
    actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1
    if activity.id == "pass-dim":
        actor.meters["careful_steps"] = actor.meters.get("careful_steps", 0.0) + 1
    if activity.id == "crouch-arch":
        actor.memes["confidence"] = actor.memes.get("confidence", 0.0) + 1
    if actor.memes.get("rush", 0.0) >= THRESHOLD:
        actor.meters["bump"] = actor.meters.get("bump", 0.0) + 1
        prize.meters["scratched"] = prize.meters.get("scratched", 0.0) + 1


def tell(name: str, gender: str, mentor: str, trait: str, activity: Activity, prize: Prize) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, traits=[]))
    guide = world.add(Entity(id="mentor", kind="character", type=mentor, label="the mentor"))
    trinket = world.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id))
    hero.meters["small"] = 1.0
    hero.memes["curious"] = 1.0
    trinket.meters["shiny"] = 1.0

    world.say(f"{hero.id} was a little {trait} {gender} who worked on a starship with {guide.label_word}.")
    world.say(f"{hero.id} loved the quiet hum of engines and the way {prize.phrase} glinted on the wall hook.")
    world.say(f"One evening, a soft red light blinked near {world.setting.place}, and {hero.id} wanted to {activity.verb}.")

    world.para()
    world.say(f"{guide.label_word} lifted a hand and pointed at the low beam. \"That passage is dim,\" {guide.label_word} said.")
    world.say(f"\"If you {activity.rush}, you might bump your head and scrape {(getattr(prize, 'it')() if callable(getattr(prize, 'it', None)) else getattr(prize, 'it', 'it'))} on the frame.\"")
    world.say(f"The words made {hero.id} pause, because {activity.lesson}.")

    world.para()
    world.say(f"{hero.id} remembered a flashback from earlier that day: a tool cart had rolled too fast, and its corner had knocked a panel.")
    world.say(f"The tiny crash had sounded silly then, but now it felt important. {hero.id} did not want that feeling again.")
    world.say(f"So {hero.id} took a slow breath, bent into a careful crouch, and started to {activity.gerund}.")

    _update(world, hero, activity, trinket)
    hero.meters["careful_steps"] = hero.meters.get("careful_steps", 0.0) + 1
    hero.memes["rush"] = 0.0
    hero.memes["lesson"] = 1.0

    world.para()
    world.say(f"The low light slid over {hero.id}'s shoulders, but {hero.id} stayed below the beam and kept {(getattr(prize, 'it')() if callable(getattr(prize, 'it', None)) else getattr(prize, 'it', 'it'))} safe.")
    world.say(f"{hero.id} passed-dim through the passage, reached the bright control nook, and smiled at the clean finish.")
    world.say(f"From then on, {hero.id} remembered the lesson: when a path is narrow and dim, a crouch can make the trip safe.")

    world.facts.update(
        hero=hero,
        guide=guide,
        prize=trinket,
        activity=activity,
        setting=world.setting,
        lesson=activity.lesson,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    guide = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "guide")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    return [
        QAItem(
            question=f"Why did {hero.id} crouch in the passage?",
            answer=(
                f"{hero.id} crouched because the passage was dim and had a low beam. "
                f"{guide.label_word} warned that rushing could lead to a bump, so {hero.id} chose the safer way."
            ),
        ),
        QAItem(
            question=f"What flashback helped {hero.id} make a careful choice?",
            answer=(
                f"{hero.id} remembered a small cart knocking a panel earlier that day. "
                f"That flashback reminded {hero.id} that fast movement in tight places can cause trouble."
            ),
        ),
        QAItem(
            question=f"What happened to {prize.label} by the end?",
            answer=(
                f"{prize.label.capitalize()} stayed safe and clean while {hero.id} passed through the dim passage. "
                f"The careful crouch kept {(getattr(prize, 'it')() if callable(getattr(prize, 'it', None)) else getattr(prize, 'it', 'it'))} from getting scraped or knocked."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=(
                f"{hero.id} learned that slow steps help in small places. "
                f"That lesson made the dim passage feel less scary and much safer."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dim mean?",
            answer="Dim means there is only a little light, so it is not bright and things can be harder to see.",
        ),
        QAItem(
            question="What is a crouch?",
            answer="A crouch is a bent-down way of moving that helps you fit under something low.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone understands after something happens.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    activity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    return [
        f"Write a small space adventure about {hero.id} who must {activity.verb} and learns a lesson.",
        f"Tell a child-friendly story with foreshadowing, a flashback, and a lesson learned in a dim spaceship passage.",
        f"Write a story where a careful crouch helps a young spacer get through a pass-dim corridor safely.",
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld: crouch, pass-dim, and learn a lesson.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    mentor = getattr(args, "mentor", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(activity=activity, prize=prize, name=name, gender=gender, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.mentor, params.trait, _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize))
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show safe/1.\n#show lesson_learned/1.\n")
    model = asp.one_model(program)
    safe = set(asp.atoms(model, "safe"))
    lesson = set(asp.atoms(model, "lesson_learned"))
    if safe and lesson:
        print("OK: ASP reasoning produced safe movement and a lesson learned.")
        return 0
    print("MISMATCH: ASP reasoning did not produce expected facts.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show safe/1.\n#show lesson_learned/1.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        combos = [
            StoryParams(activity="pass-dim", prize="helmet", name="Mina", gender="girl", mentor="mother", trait="curious"),
            StoryParams(activity="crawl-service", prize="scanner", name="Kai", gender="boy", mentor="father", trait="careful"),
            StoryParams(activity="crouch-arch", prize="badge", name="Luna", gender="girl", mentor="mother", trait="spunky"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.activity}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
