#!/usr/bin/env python3
"""
A mythic storyworld about an athletic child, a small haggle, and a mystery
that turns into a happy ending through repeated tries and a wise bargain.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
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
class Arena:
    place: str
    season: str
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
class Challenge:
    id: str
    feat: str
    loop: str
    problem: str
    mystery: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    solves: set[str]
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
    def __init__(self, arena: Arena) -> None:
        self.arena = arena
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        w = World(self.arena)
        w.entities = {k: asdict_entity(v) for k, v in self.entities.items()}
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


def asdict_entity(e: Entity) -> Entity:
    return Entity(
        id=e.id,
        kind=e.kind,
        type=e.type,
        label=e.label,
        phrase=e.phrase,
        owner=e.owner,
        caretaker=e.caretaker,
        worn_by=e.worn_by,
        plural=e.plural,
        meters=dict(e.meters),
        memes=dict(e.memes),
    )


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    aid: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "stadium": Arena(place="the sunlit stadium", season="spring", affords={"relay", "race"}),
    "field": Arena(place="the green field", season="spring", affords={"relay", "race", "sprint"}),
    "harbor": Arena(place="the harbor steps", season="windy", affords={"race"}),
}

CHALLENGES = {
    "relay": Challenge(
        id="relay",
        feat="run the relay",
        loop="running the relay again and again",
        problem="the baton keeps slipping away",
        mystery="where the missing baton went",
        zone={"hands", "feet"},
        keyword="relay",
        tags={"athletic", "mystery", "repetition"},
    ),
    "race": Challenge(
        id="race",
        feat="win the race",
        loop="racing the length of the lane again and again",
        problem="the finish line keeps seeming far off",
        mystery="why the track feels longer than it should",
        zone={"feet"},
        keyword="race",
        tags={"athletic", "mystery", "repetition"},
    ),
    "sprint": Challenge(
        id="sprint",
        feat="dash like the wind",
        loop="sprinting in bright, repeating bursts",
        problem="the child tires before the secret mark",
        mystery="how to save enough breath",
        zone={"feet"},
        keyword="sprint",
        tags={"athletic", "mystery", "repetition"},
    ),
}

PRIZES = {
    "crown": Prize(label="crown", phrase="a bright bronze crown", type="crown", region="head"),
    "medal": Prize(label="medal", phrase="a shining medal", type="medal", region="torso"),
    "ribbon": Prize(label="ribbon", phrase="a gold ribbon", type="ribbon", region="torso"),
}

AIDS = {
    "sandals": Aid(
        id="sandals",
        label="running sandals",
        covers={"feet"},
        solves={"race", "sprint"},
        prep="lace on the running sandals first",
        tail="went back to the line with the sandals tied tight",
    ),
    "glove": Aid(
        id="glove",
        label="a grip glove",
        covers={"hands"},
        solves={"relay"},
        prep="put on a grip glove for the baton",
        tail="returned with the glove snug on the hand",
    ),
    "belt": Aid(
        id="belt",
        label="a champion belt",
        covers={"torso"},
        solves={"race", "relay", "sprint"},
        prep="fasten a champion belt before the test",
        tail="came back wearing the champion belt",
    ),
}

GIRLS = ["Ari", "Mina", "Lena", "Nia", "Zora"]
BOYS = ["Kai", "Seth", "Orin", "Taro", "Ezra"]
ELDERS = ["mother", "father", "aunt", "uncle", "grandmother", "grandfather"]
TRAITS = ["athletic", "bold", "curious", "spirited"]


def prize_at_risk(ch: Challenge, pr: Prize) -> bool:
    return pr.region in ch.zone or ch.id == "relay" and pr.label == "crown"


def select_aid(ch: Challenge, pr: Prize) -> Optional[Aid]:
    for aid in AIDS.values():
        if ch.id in aid.solves and pr.region in aid.covers:
            return aid
    return None


def predict(world: World, hero: Entity, ch: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    apply_challenge(sim, sim.get(hero.id), ch, narrate=False)
    prize = sim.entities[prize_id]
    return {"won": sim.facts.get("solved", False), "soiled": prize.meters.get("lost", 0) >= THRESHOLD}


def apply_challenge(world: World, hero: Entity, ch: Challenge, narrate: bool = True) -> None:
    world.zone = set(ch.zone)
    hero.meters[ch.id] = hero.meters.get(ch.id, 0) + 1
    hero.memes["drive"] = hero.memes.get("drive", 0) + 1
    if narrate:
        world.say(f"{hero.id} did {ch.loop}.")
    world.facts["asked_again"] = world.facts.get("asked_again", 0) + 1


def narrate_setup(world: World, hero: Entity, elder: Entity, prize: Entity, ch: Challenge) -> None:
    world.say(f"{hero.id} was a little {hero.type} with an {hero.label} soul, and {hero.pronoun('possessive')} steps loved the road.")
    world.say(f"{hero.pronoun().capitalize()} longed to {ch.feat}, for the day called like a drum from the hills.")
    world.say(f"Before the trial, {elder.label} had given {hero.id} {hero.pronoun('object')} {prize.phrase}.")


def haggle(world: World, elder: Entity, hero: Entity, ch: Challenge, prize: Entity) -> bool:
    pred = predict(world, hero, ch, prize.id)
    if not prize_at_risk(ch, prize):
        return False
    world.facts["mystery"] = ch.mystery
    world.say(f'"If you {ch.feat}," said {elder.label}, "the {prize.label} may be lost, and then the village will wonder where its shine has gone."')
    if pred["won"]:
        return True
    world.say(f"{hero.id} frowned, then haggled softly, because {ch.mystery} was a mystery worth solving.")
    return True


def repeat_try(world: World, hero: Entity, ch: Challenge) -> None:
    world.say(f"{hero.id} tried once, then again, then again, as if the same brave note could wake the gate.")
    apply_challenge(world, hero, ch)
    apply_challenge(world, hero, ch)


def compromise(world: World, elder: Entity, hero: Entity, ch: Challenge, prize: Entity) -> Optional[Aid]:
    aid = select_aid(ch, prize)
    if aid is None:
        return None
    world.say(f"Then {elder.label} smiled and said, 'Let us {aid.prep} and see what the road will teach us.'")
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    return aid


def resolve(world: World, hero: Entity, elder: Entity, ch: Challenge, prize: Entity, aid: Aid) -> None:
    world.facts["solved"] = True
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    world.say(f"{hero.id} agreed, and {hero.pronoun('subject')} {aid.tail}.")
    world.say(f"This time {hero.id} {ch.feat}, and the mystery opened at last: {ch.mystery}.")
    world.say(f"At the end, {hero.id} came home with {prize.phrase}, and {elder.label} laughed with relief. It was a happy ending, bright as dawn.")


def tell(arena: Arena, ch: Challenge, prize_cfg: Prize, hero_name: str, hero_type: str, elder_type: str) -> World:
    world = World(arena)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="athletic heart"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label=f"the {elder_type}"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=elder.id, owner=hero.id))
    narrate_setup(world, hero, elder, prize, ch)
    world.para()
    world.say(f"On the first morning, {hero.id} went to {arena.place}.")
    haggle(world, elder, hero, ch, prize)
    repeat_try(world, hero, ch)
    world.para()
    aid = compromise(world, elder, hero, ch, prize)
    if aid:
        resolve(world, hero, elder, ch, prize, aid)
    world.facts.update(hero=hero, elder=elder, prize=prize, challenge=ch, aid=aid, arena=arena)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story about an athletic child who must {f["challenge"].feat} and solve a small mystery.',
        f"Tell a gentle story where {f['hero'].id} haggles with {f['elder'].label} and finds a happy ending.",
        f'Write a repeated, musical story about "{f["challenge"].keyword}" that ends with a prize and a smile.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, ch = f["hero"], f["elder"], f["prize"], f["challenge"]
    aid = f.get("aid")
    qa = [
        QAItem(
            question=f"Who is this story about?",
            answer=f"It is about {hero.id}, a little {hero.type} who is athletic and brave enough to face a mystery.",
        ),
        QAItem(
            question=f"What was the hard thing {hero.id} wanted to do?",
            answer=f"{hero.id} wanted to {ch.feat}, but the task had a mystery in it and needed careful thought.",
        ),
        QAItem(
            question=f"Why did {elder.label} worry about the {prize.label}?",
            answer=f"{elder.label} worried because if {hero.id} kept trying the {ch.keyword}, the {prize.label} could be lost or ruined.",
        ),
        QAItem(
            question=f"What did {hero.id} do again and again?",
            answer=f"{hero.id} kept {ch.loop}, because repeating the attempt helped {hero.id} learn the secret.",
        ),
    ]
    if aid:
        qa.append(QAItem(
            question=f"How did the {aid.label} help the problem?",
            answer=f"The {aid.label} matched the need in the story, so {hero.id} could keep going without losing the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a happy ending: {hero.id} won the day, solved the mystery, and came home with the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to haggle?", answer="To haggle means to talk back and forth about a choice or price until people reach an agreement."),
        QAItem(question="What is repetition?", answer="Repetition means doing the same thing more than once, often to practice or to make something clear."),
        QAItem(question="What is a mystery?", answer="A mystery is something puzzling that people do not understand yet."),
        QAItem(question="What is a happy ending?", answer="A happy ending is when the trouble gets solved and things finish well."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Declarative twin: a challenge is reasonable when the prize is at risk and an aid exists.
at_risk(C, P) :- challenge(C), prize(P), zone(C, R), region(P, R).
fixable(C, P) :- at_risk(C, P), aid(A), solves(A, C), covers(A, R), region(P, R).
valid_story(Arena, C, P) :- affords(Arena, C), at_risk(C, P), fixable(C, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.solves):
            lines.append(asp.fact("solves", aid.id, c))
        for r in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, r))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for r in sorted(ch.zone):
            lines.append(asp.fact("zone", cid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for sid, ar in SETTINGS.items():
        for c in sorted(ar.affords):
            lines.append(asp.fact("affords", sid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, ar in SETTINGS.items():
        for cid in ar.affords:
            ch = _safe_lookup(CHALLENGES, cid)
            for pid, pr in PRIZES.items():
                if prize_at_risk(ch, pr) and select_aid(ch, pr):
                    combos.append((sid, cid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic athletic haggle storyworld with repetition, mystery, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
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
    filtered = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None)) and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRLS if gender == "girl" else BOYS)
    elder = getattr(args, "elder", None) or rng.choice(ELDERS)
    aid = select_aid(_safe_lookup(CHALLENGES, challenge), _safe_lookup(PRIZES, prize))
    if aid is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, challenge=challenge, prize=prize, aid=aid.id, name=name, gender=gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(PRIZES, params.prize), params.name, "girl" if params.gender == "girl" else "boy", params.elder)
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
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP and Python agree on {len(py_set)} combos.")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        for tpl in sorted(set(asp.atoms(model, "valid_story"))):
            print(tpl)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        for place, ch, prize in valid_combos():
            pr = _safe_lookup(PRIZES, prize)
            aid = select_aid(_safe_lookup(CHALLENGES, ch), pr)
            params = StoryParams(place=place, challenge=ch, prize=prize, aid=aid.id if aid else "", name="Ari", gender="girl", elder="mother")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
