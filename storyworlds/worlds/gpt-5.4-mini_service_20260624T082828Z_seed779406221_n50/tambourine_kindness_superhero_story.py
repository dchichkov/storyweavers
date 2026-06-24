#!/usr/bin/env python3
"""
storyworlds/worlds/tambourine_kindness_superhero_story.py
========================================================

A small standalone story world for a Superhero Story with a tambourine and
Kindness at the center.

Core premise:
- A tiny superhero needs to help a scared child at a busy festival.
- The superhero's tambourine is not used as a noisy gimmick; it is used as a
  gentle signal that, together with kindness, turns fear into trust.
- The story is built from a causal world model: the child's fear, the hero's
  patience, the crowd's attention, and the final safe reunion all change state.

This script follows the Storyweavers world contract:
- stdlib-only storyworld script
- eager results import for QAItem, StoryError, StorySample
- lazy ASP import inside ASP helpers only
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gadget: object | None = None
    hero: object | None = None
    target: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    bustling: bool = True
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Incident:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: str
    mood: str
    keyword: str = "tambourine"
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
class Aid:
    id: str
    label: str
    fit: set[str]
    method: str
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "plaza": Setting(place="the city plaza", bustling=True, tags={"festival", "crowd"}),
    "roof": Setting(place="the museum roof", bustling=False, tags={"wind", "sky"}),
    "station": Setting(place="the train station", bustling=True, tags={"echo", "crowd"}),
}

INCIDENTS = {
    "lost_child": Incident(
        id="lost_child",
        verb="find the lost child",
        gerund="searching for the lost child",
        risk="fear",
        zone="crowd",
        mood="scared",
        keyword="tambourine",
        tags={"kindness", "festival"},
    ),
    "frozen_dog": Incident(
        id="frozen_dog",
        verb="help the frozen dog",
        gerund="helping the frozen dog",
        risk="fear",
        zone="quiet",
        mood="shaky",
        keyword="tambourine",
        tags={"kindness"},
    ),
    "nervous_parade": Incident(
        id="nervous_parade",
        verb="steady the nervous parade",
        gerund="steadying the nervous parade",
        risk="panic",
        zone="crowd",
        mood="trembling",
        keyword="tambourine",
        tags={"kindness", "festival"},
    ),
}

AIDS = {
    "gentle_beat": Aid(
        id="gentle_beat",
        label="the tambourine",
        fit={"fear", "panic"},
        method="tap a gentle beat",
        ending="kept the beat soft and steady",
    ),
    "calm_voice": Aid(
        id="calm_voice",
        label="kind words",
        fit={"fear", "panic"},
        method="speak with kindness",
        ending="let the frightened one hear a safe voice",
    ),
}

HERO_NAMES = ["Maya", "Nia", "Zane", "Ivy", "Arlo", "Luna", "Eli", "Rosa"]
HERO_TYPES = ["girl", "boy"]
SUIT_COLORS = ["red", "blue", "gold", "green", "silver"]


@dataclass
class StoryParams:
    place: str
    incident: str
    aid: str
    name: str
    hero_type: str
    suit_color: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for incident_id, inc in INCIDENTS.items():
            for aid_id, aid in AIDS.items():
                if inc.risk in aid.fit:
                    combos.append((place, incident_id, aid_id))
    return combos


def explain_rejection(incident: Incident, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} does not honestly fit this problem. "
        f"It can help with fear or panic, but not with this particular beat.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small superhero story world about a tambourine and kindness."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--incident", choices=INCIDENTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "incident", None) and getattr(args, "aid", None):
        inc = _safe_lookup(INCIDENTS, getattr(args, "incident", None))
        aid = _safe_lookup(AIDS, getattr(args, "aid", None))
        if inc.risk not in aid.fit:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "incident", None) is None or c[1] == getattr(args, "incident", None))
        and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, incident, aid = rng.choice(list(combos))
    hero_type = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    suit_color = rng.choice(SUIT_COLORS)
    return StoryParams(
        place=place,
        incident=incident,
        aid=aid,
        name=name,
        hero_type=hero_type,
        suit_color=suit_color,
    )


def _do_incident(world: World, hero: Entity, incident: Incident) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    hero.meters["action"] = hero.meters.get("action", 0) + 1


def predict(world: World, hero: Entity, incident: Incident, aid: Aid) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    _do_incident(sim, sim_hero, incident)
    target = sim.get("target")
    target.memes["fear"] = target.memes.get("fear", 0) + 1.5
    target.memes["calm"] = 0
    target.memes["trust"] = target.memes.get("trust", 0) + 1.5
    target.memes["fear"] = 0
    return {"rescued": True, "calm": target.memes["trust"] >= THRESHOLD}


def tell(setting: Setting, incident: Incident, aid: Aid, name: str, hero_type: str, suit_color: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=hero_type,
        label=f"the {suit_color} superhero",
    ))
    target = world.add(Entity(
        id="target",
        kind="character",
        type="girl",
        label="the scared child",
    ))
    gadget = world.add(Entity(
        id="gadget",
        type="thing",
        label="a tambourine",
        phrase="a bright tambourine",
        owner=hero.id,
    ))
    hero.memes["kindness"] = 1.0
    target.memes["fear"] = 1.5
    target.memes["trust"] = 0.0

    world.say(
        f"{hero.id} was a {suit_color} superhero who watched over {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {gadget.phrase} because {hero.pronoun('possessive')} power was Kindness."
    )
    world.say(
        f"One day at {world.setting.place}, {hero.id} spotted {target.label} in the middle of a шумless? crowd? "
    )
    return world


def generate_story_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    incident = _safe_lookup(INCIDENTS, params.incident)
    aid = _safe_lookup(AIDS, params.aid)

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.hero_type,
        label=f"the {params.suit_color} superhero",
    ))
    target = world.add(Entity(
        id="target",
        kind="character",
        type="girl",
        label="the scared child",
    ))
    world.add(Entity(
        id="tambourine",
        type="thing",
        label="tambourine",
        phrase="a bright tambourine",
        owner=hero.id,
    ))

    hero.memes["kindness"] = 1.0
    hero.memes["hope"] = 1.0
    target.memes["fear"] = 1.5
    target.memes["trust"] = 0.0
    target.meters["distance"] = 5.0

    world.say(f"{hero.id} was a {params.suit_color} superhero who watched over {setting.place}.")
    world.say(
        f"{hero.pronoun().capitalize()} carried a bright tambourine, and {hero.pronoun('possessive')} power was Kindness."
    )
    world.say(
        f"One day, {hero.id} noticed {target.label} near {setting.place}, where {incident.gerund} had made the air feel heavy."
    )

    world.para()
    target.memes["fear"] += 1.0
    world.say(
        f"{target.label} looked shaky and close to tears, so {hero.id} walked closer instead of rushing in."
    )
    world.say(
        f"{hero.pronoun().capitalize()} did not shout; {hero.pronoun()} knelt down, smiled, and chose to {aid.method}."
    )
    world.say(
        f"The little beat said, 'You are safe here,' and {hero.id} kept the rhythm slow and warm."
    )

    world.para()
    hero.memes["kindness"] += 1.0
    target.memes["trust"] += 2.0
    target.memes["fear"] = max(0.0, target.memes["fear"] - 2.0)
    target.meters["distance"] = 1.0
    world.say(
        f"{target.label} stopped shaking and listened. The tambourine did not feel noisy at all; it felt like a friendly heart."
    )
    world.say(
        f"{target.label} followed the beat to {hero.id}, and {hero.id} guided {hero.pronoun('object')} back to the bright edge of the plaza."
    )

    world.para()
    hero.meters["action"] += 1.0
    target.memes["joy"] = 1.0
    world.say(
        f"At the end, {hero.id} {aid.ending}, and {target.label} was smiling again."
    )
    world.say(
        f"{hero.id} lifted the tambourine like a tiny trophy, and the city felt calmer because kindness had won the day."
    )

    world.facts.update(hero=hero, target=target, incident=incident, aid=aid, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    incident = f["incident"]
    aid = f["aid"]
    return [
        f'Write a short superhero story for a little child about a tambourine and Kindness.',
        f"Tell a gentle rescue story where {hero.id} uses {aid.label} to help with {incident.gerund}.",
        f'Write a simple superhero story that includes the word "tambourine" and ends with kindness making things better.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    target = f["target"]
    incident = f["incident"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who is the superhero in this story?",
            answer=f"The superhero is {hero.id}, the {hero.label} who cares about kindness.",
        ),
        QAItem(
            question=f"What did {hero.id} carry to help the scared child?",
            answer=f"{hero.id} carried a tambourine and used it to make a gentle beat.",
        ),
        QAItem(
            question=f"Why did the child stop feeling so afraid?",
            answer=f"The child stopped feeling so afraid because {hero.id} used kindness and a soft tambourine rhythm instead of rushing or shouting.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{target.label} was smiling again, and the city felt calmer because {hero.id} helped with kindness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tambourine?",
            answer="A tambourine is a small hand drum with jingles that you shake or tap to make a bright, happy sound.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful so other people feel safe and respected.",
        ),
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero usually helps others, solves problems, and protects people when something goes wrong.",
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
incident_help(I) :- incident(I).
aid_ok(A) :- aid(A), fits(A, fear).
aid_ok(A) :- aid(A), fits(A, panic).
valid(P, I, A) :- place(P), incident(I), aid(A), incident_risk(I, R), fits(A, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for iid, inc in INCIDENTS.items():
        lines.append(asp.fact("incident", iid))
        lines.append(asp.fact("incident_risk", iid, inc.risk))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for r in sorted(aid.fit):
            lines.append(asp.fact("fits", aid_id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="plaza", incident="lost_child", aid="gentle_beat", name="Maya", hero_type="girl", suit_color="gold"),
    StoryParams(place="station", incident="nervous_parade", aid="calm_voice", name="Eli", hero_type="boy", suit_color="blue"),
    StoryParams(place="roof", incident="frozen_dog", aid="gentle_beat", name="Rosa", hero_type="girl", suit_color="red"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, incident, aid) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.name}: {p.incident} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
