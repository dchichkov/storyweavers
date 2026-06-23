#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/squatching_defend_booger_dialogue_happy_ending_quest.py
===============================================================================================================================

A tiny storyworld about a child-led quest to help a small forest friend while
squatching through a moonlit trail. The tone is rhyming, child-facing, and
built around dialogue, a quest, and a happy ending.
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
            keys = [upper + "S", upper + "ES"]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    booger: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Place:
    id: str
    label: str
    trail: str
    dark: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    rhyme: str
    problem: str
    clue: str
    ending_image: str
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
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    at_risk: set[str]
    mess: str
    tags: set[str] = field(default_factory=set)
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
    phrase: str
    method: str
    fit_for: set[str]
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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


@dataclass
class StoryParams:
    place: str
    quest: str
    problem: str
    aid: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


PLACES = {
    "moonwood": Place(id="moonwood", label="Moonwood Grove", trail="a silver trail", dark="the mossy hollow", affords={"squash", "find", "help"}),
    "brook": Place(id="brook", label="Brookside Path", trail="a tinkly path", dark="the creek bend", affords={"squash", "find", "help"}),
    "meadow": Place(id="meadow", label="Meadow Gate", trail="a windy lane", dark="the tall grass", affords={"squash", "find", "help"}),
    "hill": Place(id="hill", label="Pinehill Lane", trail="a piney lane", dark="the rooty hill", affords={"squash", "find", "help"}),
}

QUESTS = {
    "lantern": Quest(id="lantern", goal="find the lost lantern", verb="follow the glow", rhyme="glow", problem="dark", clue="a soft shine under leaves", ending_image="the lantern was shining bright in a little satchel", tags={"light", "find"}),
    "song": Quest(id="song", goal="bring home the rain drum song", verb="tap the drum in time", rhyme="tune", problem="quiet", clue="a beat that bounced on bark", ending_image="the drum was tucked under an arm, dry and snug", tags={"sound", "find"}),
    "berries": Quest(id="berries", goal="gather the star berries", verb="pick the ripe red berries", rhyme="glow", problem="high", clue="red dots in a thorny bush", ending_image="the berries rested safe in a round leaf basket", tags={"pick", "find"}),
}

PROBLEMS = {
    "spider": Problem(id="spider", label="a spider snare", phrase="a sticky spider snare", risk="sticky", at_risk={"coat"}, mess="snagged", tags={"sticky"}),
    "mud": Problem(id="mud", label="deep mud", phrase="a deep muddy patch", risk="muddy", at_risk={"boots"}, mess="muddy", tags={"mud"}),
    "branch": Problem(id="branch", label="a low branch", phrase="a low branch with prickly twigs", risk="scratched", at_risk={"hat"}, mess="scratched", tags={"branch"}),
}

AIDS = {
    "leaf": Aid(id="leaf", label="leaf boots", phrase="leaf boots", method="slip on leaf boots and step with care", fit_for={"mud"}, tags={"mud"}),
    "song": Aid(id="song", label="a soft song", phrase="a soft song", method="sing a soft song and move slow", fit_for={"spider", "branch"}, tags={"song"}),
    "glove": Aid(id="glove", label="glove paws", phrase="glove paws", method="wear glove paws and lift with care", fit_for={"branch"}, tags={"glove"}),
}

GIRL_NAMES = ["Mina", "Luna", "Poppy", "Tia", "Zoe"]
BOY_NAMES = ["Finn", "Nico", "Otto", "Rafi", "Jude"]
HELPERS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for q in QUESTS:
            for pr in PROBLEMS:
                if any(pr in aid.fit_for for aid in AIDS.values()):
                    out.append((p, q, pr))
    return out


def explain_rejection(place: str, quest: str, problem: str) -> str:
    return f"(No story: the quest for {_safe_lookup(QUESTS, quest).goal} does not reasonably meet {_safe_lookup(PROBLEMS, problem).phrase} at {_safe_lookup(PLACES, place).label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming quest storyworld with squatching, defend, and booger.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, problem = rng.choice(list(combos))
    aid = getattr(args, "aid", None) or rng.choice(sorted(AIDS))
    if problem not in _safe_lookup(AIDS, aid).fit_for:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["mother", "father"])
    helper_name = getattr(args, "helper", None) or rng.choice(["Mom", "Dad"])
    return StoryParams(place=place, quest=quest, problem=problem, aid=aid,
                       hero_name=name, hero_gender=gender, helper_name=helper_name,
                       helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    problem = _safe_lookup(PROBLEMS, params.problem)
    aid = _safe_lookup(AIDS, params.aid)
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, meters={"miles": 0.0}, memes={"hope": 0.0, "worry": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, meters={}, memes={"care": 0.0}))
    booger = world.add(Entity(id="booger", kind="thing", type="thing", label="booger", meters={"stuck": 0.0, "safe": 0.0}, memes={"lonely": 0.0}, attrs={"problem": problem.id, "quest": quest.id}))
    world.facts = {"hero": hero, "helper": helper, "quest": quest, "problem": problem, "aid": aid, "booger": booger, "place": place, "squatch": False, "solved": False}
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(f"{hero.label} set out from {place.label}, with moonlight gleam and a quest in sight. {helper.label} smiled and said, \"Let's go, my dear; we'll find the missing prize tonight.\"")
    world.say(f"Along {place.trail}, they went to see {quest.clue}, and heard the booger whisper, \"Please defend me, don't pass me by.\"")
    world.para()
    hero.meters["miles"] += 1
    booger.memes["lonely"] += 1
    if problem.id == "mud":
        hero.meters["mud"] = 1.0
    if problem.id == "spider":
        booger.meters["stuck"] = 1.0
    if problem.id == "branch":
        hero.memes["worry"] += 1
    world.say(f"\"We'll defend you,\" said {helper.label}, with a nod and a grin. \"A squatching little quest like this is what we do within.\"")
    world.say(f"\"Then sing,\" said {hero.label}, \"or slip on {aid.label}; we won't leave the booger alone.\"")
    world.say(f"They used {aid.method}, and with a careful move, the trouble turned to stone.")
    world.para()
    booger.meters["safe"] = 1.0
    world.facts["solved"] = True
    world.say(f"The booger popped free with a happy little hop, and {quest.ending_image}.")
    world.say(f"{helper.label} laughed, \"See? A quest can be merry when friends stand near.\"")
    world.say(f"{hero.label} waved at the moon and sang, \"We squatched, we defended, and all ended clear.\"")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "squatching", "defend", and "booger".',
        f"Tell a gentle quest story about {f['hero'].label} and {f['helper'].label} helping a booger at {f['place'].label}.",
        f"Write a happy-ending rhyme where a child and a grown-up defend a small friend and finish the quest with a smile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest, problem, aid, booger, place = f["hero"], f["helper"], f["quest"], f["problem"], f["aid"], f["booger"], f["place"]
    return [
        QAItem(question=f"Who went on the quest at {place.label}?", answer=f"{hero.label} went with {helper.label} on a moonlit quest at {place.label}. They were looking for {quest.goal}, and the little booger needed help along the way."),
        QAItem(question=f"What did they do for the booger?", answer=f"They chose to defend the booger instead of leaving it alone. First they noticed the problem, then they used {aid.label} so the booger could be safe again."),
        QAItem(question=f"How did the story end?", answer=f"It ended happily. The booger was safe, the quest was finished, and {quest.ending_image}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a trip or mission to find, help, or bring back something important."),
        QAItem(question="What does defend mean?", answer="To defend means to protect someone or something from trouble or harm."),
        QAItem(question="What does squatching mean here?", answer="Squatching means moving with a playful, bouncy step through a wild place like a little explorer."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    bits = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    return "\n".join(bits)


ASP_RULES = r"""
valid(P,Q,R) :- place(P), quest(Q), problem(R), aids(A,R).
solved :- valid(P,Q,R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for prid in PROBLEMS:
        lines.append(asp.fact("problem", prid))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.id))
        for fit in aid.fit_for:
            lines.append(asp.fact("aids", aid.id, fit))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        c = set(asp_valid_combos())
        p = set(valid_combos())
        if c != p:
            print("MISMATCH")
            return 1
        sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, problem=None, aid=None, name=None, helper=None, gender=None, helper_gender=None), random.Random(7)))
        if not sample.story.strip():
            print("EMPTY STORY")
            return 1
        print(f"OK: {len(c)} combos, smoke test passed.")
        return 0
    except Exception as e:
        print(str(e))
        return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, quest=q, problem=r, aid=next(iter(AIDS)), hero_name="Mina", hero_gender="girl", helper_name="Mom", helper_gender="mother")) for p, q, r in valid_combos()[:10]]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
