#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a child crew, a shy hippopotamus,
and the kindness that turns a risky night into a safe rescue.

Premise:
- A young pirate loves an evening lantern walk on a docked ship.
- The child also cares about a huge hippopotamus stranded near the quay.
- A kerosene lantern is useful, but it can be dangerous if handled carelessly.
- Kindness helps the crew choose a safer way to light the path and help the animal.

State model:
- Physical meters track things like soot, spill, hunger, and lantern fuel.
- Emotional memes track worry, courage, and kindness.
- The story begins with a simple problem, turns on a warning about kerosene,
  and resolves when the child chooses a kinder, safer rescue.

The world is intentionally tiny and classical:
- One ship, one dock, one hippo, one lantern, one safe compromise.
- Variants are constrained by reasonableness, not by broad random swapping.
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

THRESHOLD = 1.0



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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    hippo: object | None = None
    lantern: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    zone: set[str]
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    ship: str
    place: str
    hero_name: str
    hero_type: str
    companion_name: str
    seed: Optional[int] = None
    params: object | None = None
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
    "dock": Setting(place="the dock", affords={"lantern", "rescue"}),
    "harbor": Setting(place="the harbor", affords={"lantern", "rescue"}),
    "ship": Setting(place="the ship", affords={"lantern", "rescue"}),
}

ACTIVITIES = {
    "lantern": Activity(
        id="lantern",
        verb="carry the kerosene lantern",
        gerund="carrying the kerosene lantern",
        rush="run with the lantern",
        hazard="burned and smoky",
        zone={"hands", "torso"},
        keyword="kerosene",
        tags={"kerosene", "light"},
    ),
    "rescue": Activity(
        id="rescue",
        verb="help the hippopotamus",
        gerund="helping the hippopotamus",
        rush="dash to the hippo",
        hazard="trapped and frightened",
        zone={"hands", "feet"},
        keyword="hippopotamus",
        tags={"hippopotamus", "kindness"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a brass kerosene lantern",
        type="lantern",
        region="hands",
    ),
    "rope": Prize(
        label="rope",
        phrase="a coil of dock rope",
        type="rope",
        region="hands",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="thick gloves",
        covers={"hands"},
        guards={"burned"},
        prep="put on thick gloves first",
        tail="slipped on the thick gloves",
    ),
    Gear(
        id="bucket",
        label="a water bucket",
        covers={"hands"},
        guards={"burned", "smoky"},
        prep="carry a water bucket and keep the lantern low",
        tail="kept a bucket of water close by",
    ),
    Gear(
        id="sheet",
        label="a wet sheet",
        covers={"torso"},
        guards={"smoky"},
        prep="wrap the lantern in a wet sheet for the walk",
        tail="wrapped the lantern in a wet sheet",
    ),
]

HERO_NAMES = ["Finn", "Mara", "Jory", "Nell", "Pip", "Ria"]
COMPANIONS = ["Bluebeard", "Salt", "Wisp", "Moss", "Nico"]


class StoryWorld:
    def __init__(self, world: World) -> None:
        self.world = world

    def worn_items(self, actor: Entity) -> list[Entity]:
        return self.world.worn_items(actor)


def _apply_hazard(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("lantern_fuel", 0) < THRESHOLD:
            continue
        if actor.meters.get("splash", 0) < THRESHOLD:
            continue
        if actor.meters.get("fear", 0) < THRESHOLD:
            continue
        sig = ("hazard", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0) + 1
        out.append(f"The kerosene smell made the lantern feel too risky to rush.")
    return out


def _apply_kindness(world: World) -> list[str]:
    out: list[str] = []
    hippo = next((e for e in world.entities.values() if e.type == "hippopotamus"), None)
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not hippo or not hero:
        return out
    if hero.memes.get("kindness", 0) < THRESHOLD:
        return out
    if hippo.meters.get("trapped", 0) < THRESHOLD:
        return out
    sig = ("kindness", hippo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hippo.meters["rescued"] = 1
    hippo.memes["calm"] = hippo.memes.get("calm", 0) + 1
    out.append("The kind choice steadied the big hippo and made the night gentler.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_hazard, _apply_kindness):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.hazard.startswith("burned"):
            return gear
    return None


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", "brave", "kind"],
    ))
    companion = world.add(Entity(
        id=params.companion_name,
        kind="character",
        type="pirate",
        label="the shipmate",
    ))
    hippo = world.add(Entity(
        id="hippo",
        type="hippopotamus",
        label="the hippopotamus",
        phrase="a huge hippopotamus with kind eyes",
        meters={"trapped": 1},
        memes={"fear": 1},
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a brass kerosene lantern",
        owner=hero.id,
        caretaker=hero.id,
        worn_by=hero.id,
        meters={"lantern_fuel": 1, "splash": 1},
    ))

    world.say(f"{hero.id} was a little pirate who liked the dark blue water by {world.setting.place}.")
    world.say(f"{hero.id} also saw {hippo.phrase}, and {hero.pronoun('possessive')} heart turned soft with kindness.")
    world.say(f"Near the ropes, {hero.id} carried {hero.pronoun('possessive')} {lantern.label}, and the kerosene gave off a sharp little smell.")

    world.para()
    world.say(f"One night, {hero.id} and {companion.label} found the big hippopotamus stuck near the edge of the harbor.")
    world.say(f"{hippo.label.capitalize()} looked lonely and worried, and {hero.id} wanted to {ACTIVITIES['rescue'].verb}.")
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.meters["splash"] = 1
    hero.meters["fear"] = 1
    propagate(world, narrate=True)

    world.para()
    if prize_at_risk(ACTIVITIES["lantern"], lantern):
        gear = select_gear(ACTIVITIES["lantern"], lantern)
        if gear is None:
            gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
        world.say(f"{companion.label.capitalize()} warned that the kerosene lantern could be dangerous if it got bumped or dropped.")
        world.say(f"{hero.id} did not argue. {hero.pronoun().capitalize()} chose kindness over fuss and {gear.prep}.")
        lantern.meters["safe"] = 1
        lantern.meters["lit"] = 1
        world.say(f"With {gear.label}, {hero.id} could still light the deck without shaking the lantern around.")
    else:
        gear = None

    world.para()
    hero.meters["kindness"] = hero.meters.get("kindness", 0) + 1
    hippo.meters["trapped"] = 0
    hippo.meters["rescued"] = 1
    hippo.memes["calm"] = hippo.memes.get("calm", 0) + 1
    world.say(f"Then {hero.id} used the lantern to show the safest path, and the crew guided the hippopotamus toward the shallow water.")
    world.say(f"The hippo stepped free, snorted softly, and leaned toward the deck like a friend saying thank you.")
    world.say(f"In the end, {hero.id}'s kindness shone brighter than the kerosene, and the big hippopotamus floated away safe and calm.")

    world.facts.update(
        hero=hero,
        companion=companion,
        hippo=hippo,
        lantern=lantern,
        gear=gear,
        activity=ACTIVITIES["lantern"],
        rescue=ACTIVITIES["rescue"],
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short pirate story for a young child that includes the word "kerosene" and ends kindly.',
        f"Tell a tiny pirate tale where {hero.id} helps a hippopotamus and handles a kerosene lantern safely.",
        f"Write a gentle ship-and-dock story with a hippopotamus, a lantern, and a kind choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    hippo = f["hippo"]
    lantern = f["lantern"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little pirate who chose kindness and helped {hippo.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry that had kerosene in it?",
            answer=f"{hero.id} carried {lantern.phrase}, which was a kerosene lantern used to light the way.",
        ),
        QAItem(
            question=f"Why did the crew need to be careful with the lantern?",
            answer="They needed to be careful because kerosene lanterns can be risky if they get bumped or dropped.",
        ),
        QAItem(
            question=f"What did {hero.id} help the hippopotamus do at the end?",
            answer=f"{hero.id} helped the hippopotamus get free and move safely toward the water.",
        ),
    ]
    if gear is not None:
        qa.append(
            QAItem(
                question="How did the chosen gear help?",
                answer=f"Using {gear.label} helped keep the lantern safer while the crew guided the hippo.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kerosene used for?",
            answer="Kerosene can be used as fuel for some lamps and lanterns that make light.",
        ),
        QAItem(
            question="What is a hippopotamus?",
            answer="A hippopotamus is a very large animal that likes water and has a big round body.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something gentle and caring to help someone or something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A prize is at risk when the activity touches the region it is worn on.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a safe fix when it covers the at-risk region.
protects(G, A, P) :- prize_at_risk(A, P), gear(G), covers(G, R), worn_on(P, R), guards(G, M), hazard_of(A, M).

valid_story(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
has_fix(A, P) :- protects(_, A, P).

% Kindness is the heart of the resolution in this tiny world.
kind_rescue(H) :- hero(H), kindness(H), sees(H, hippo), helps(H, hippo).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
        lines.append(asp.fact("hazard_of", aid, "burned"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("sees", "hero", "hippo"))
    lines.append(asp.fact("helps", "hero", "hippo"))
    lines.append(asp.fact("worn_on", "lantern", "hands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(_safe_lookup(ACTIVITIES, act_id), prize) and select_gear(_safe_lookup(ACTIVITIES, act_id), prize):
                    combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in clingo:", sorted(clingo_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale world with kerosene, a hippopotamus, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--companion-name", choices=COMPANIONS)
    ap.add_argument("--hero-type", choices=["boy", "girl"], default="boy")
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
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    companion = getattr(args, "companion_name", None) or rng.choice(COMPANIONS)
    return StoryParams(
        ship="ship",
        place=place,
        hero_name=hero_name,
        hero_type=getattr(args, "hero_type", None),
        companion_name=companion,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story triples:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            params = StoryParams(
                ship="ship",
                place=place,
                hero_name=_safe_lookup(HERO_NAMES, 0),
                hero_type="boy",
                companion_name=_safe_lookup(COMPANIONS, 0),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
