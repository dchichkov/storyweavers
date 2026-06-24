#!/usr/bin/env python3
"""
Story world: Oodles, Win, Jujube Reconciliation Quest

A small, child-facing, rhyming story domain about a tiny quest that goes wrong,
then gets made right again with a gentle reconciliation.

Core premise:
- A child wants to win a prize on a quest.
- The prize is a jar of jujube jam, or a jujube treat, chosen from a tiny set.
- The quest needs oodles of a resource or careful teamwork.
- A disagreement causes a split.
- Reconciliation repairs the bond, and the quest can be finished together.

This file is self-contained and uses only stdlib plus the shared result helpers.
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
    plural: bool = False
    owner: Optional[str] = None
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid_ent: object | None = None
    friend: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "mother", "woman"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "father", "man"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

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
    place: str
    path: str
    weather: str
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    cost: str
    rhyme: str
    zone: str
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
    id: str
    label: str
    phrase: str
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
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
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
        self.zone: str = ""
        self.path_mood: str = ""

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = self.zone
        clone.path_mood = self.path_mood
        return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def title_line(word: str) -> str:
    return f"A little tale of {word}."


def quest_rhyme(quest: Quest) -> str:
    return {
        "bridge": "over the bridge with a brave little stride",
        "grove": "through the grove where the green leaves glide",
        "hill": "up the hill with a hop and a squeal",
        "river": "by the river with a skip and a reel",
    }.get(quest.id, "on a path that was tidy and neat")


def play_sound(quest: Quest) -> str:
    return {
        "bridge": "clip-clop",
        "grove": "swish-swish",
        "hill": "hop-hop",
        "river": "splish-splash",
    }.get(quest.id, "tap-tap")


def treasure_sound(prize: Prize) -> str:
    return {
        "jar": "sweet and bright",
        "coin": "shiny and light",
        "crown": "golden and spry",
        "star": "sparkling high",
    }.get(prize.id, "small and sweet")


def quest_setup(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Prize) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved to roam, "
        f"and {friend.id} liked to help make the path feel home."
    )
    world.say(
        f"They longed for a quest with oodles of cheer, "
        f"to {quest.verb} the trail and bring the prize near."
    )
    world.say(
        f"The prize was {prize.phrase}, with a shine like spring dew, "
        f"and both of them whispered, \"We'll win it! We will! Whew!\""
    )


def quest_begin(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    world.para()
    world.zone = quest.zone
    world.path_mood = "breezy"
    world.say(
        f"On a bright little morning, they marched to the {world.setting.place}, "
        f"and {play_sound(quest)} went their feet in a rhythmic race."
    )
    world.say(
        f"{hero.id} wanted to {quest.verb}, fast as a bee, "
        f"while {friend.id} said, \"Wait for the clue by the old jujube tree.\""
    )


def quest_tension(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Prize) -> None:
    world.say(
        f"But {hero.id} saw oodles of glow and wanted to win right away, "
        f"so {hero.id} rushed ahead where the soft stones sway."
    )
    hero.memes["greed"] = hero.memes.get("greed", 0.0) + 1.0
    hero.memes["tension"] = hero.memes.get("tension", 0.0) + 1.0
    friend.memes["hurt"] = friend.memes.get("hurt", 0.0) + 1.0
    world.say(
        f"{friend.id} frowned, quite sad in the sun, "
        f"for the quest needed two hearts, not just one."
    )
    world.facts["conflict"] = True
    world.facts["prize"] = prize
    world.facts["quest"] = quest


def advise(world: World, friend: Entity, quest: Quest) -> None:
    world.say(
        f"{friend.id} said, \"A quest is a rhyme, not a dash; "
        f"we need oodles of patience, not a tumble and splash.\""
    )


def reconciling_move(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    hero.memes["guilt"] = hero.memes.get("guilt", 0.0) + 1.0
    world.say(
        f"{hero.id} looked down and knew the right thing to do, "
        f"so {hero.id} took a small breath and spoke, \"I'm sorry to you.\""
    )
    world.say(
        f"Then {hero.id} and {friend.id} shared {aid.label}, bright and kind, "
        f"and the hard little worry unknotted the mind."
    )
    hero.memes["reconciled"] = 1.0
    friend.memes["reconciled"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    hero.memes["tension"] = 0.0
    friend.memes["hurt"] = 0.0


def quest_finish(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Prize) -> None:
    world.say(
        f"Together they went back to the {quest.id} place, "
        f"with oodles of care in each smiling face."
    )
    world.say(
        f"They followed the clue and completed the quest, "
        f"and {prize.label} came home in the very best nest."
    )
    world.say(
        f"{hero.id} did not win alone; {friend.id} won too, "
        f"and their friendship shone like the morning dew."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, quest: Quest, prize: Prize, aid: Aid,
         hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    prize_ent = world.add(Entity(id="prize", type=prize.id, label=prize.label, phrase=prize.phrase, plural=prize.plural))
    aid_ent = world.add(Entity(id=aid.id, type="aid", label=aid.label))
    world.facts.update(hero=hero, friend=friend, prize_ent=prize_ent, aid_ent=aid_ent, prize_cfg=prize, aid_cfg=aid, quest=quest, setting=setting)

    world.say(title_line("jujube"))
    quest_setup(world, hero, friend, quest, prize)
    quest_begin(world, hero, friend, quest)
    quest_tension(world, hero, friend, quest, prize)
    advise(world, friend, quest)
    world.para()
    reconciling_move(world, hero, friend, aid)
    quest_finish(world, hero, friend, quest, prize)
    return world


SETTINGS = {
    "lane": Setting(place="sunny lane", path="lane", weather="bright", affords={"bridge", "grove", "hill", "river"}),
    "orchard": Setting(place="jujube orchard", path="orchard", weather="warm", affords={"grove", "hill"}),
    "meadow": Setting(place="quiet meadow", path="meadow", weather="soft", affords={"bridge", "hill", "river"}),
}

QUESTS = {
    "bridge": Quest(
        id="bridge",
        verb="cross",
        gerund="crossing",
        rush="rush across",
        cost="careful steps",
        rhyme="bridge",
        zone="bridge",
        keyword="quest",
        tags={"quest", "bridge"},
    ),
    "grove": Quest(
        id="grove",
        verb="follow",
        gerund="following",
        rush="dash through",
        cost="gentle steps",
        rhyme="grove",
        zone="grove",
        keyword="jujube",
        tags={"quest", "jujube"},
    ),
    "hill": Quest(
        id="hill",
        verb="climb",
        gerund="climbing",
        rush="run up",
        cost="steady steps",
        rhyme="hill",
        zone="hill",
        keyword="win",
        tags={"quest", "win"},
    ),
    "river": Quest(
        id="river",
        verb="seek",
        gerund="seeking",
        rush="hurry by",
        cost="patient steps",
        rhyme="river",
        zone="river",
        keyword="oodles",
        tags={"quest", "oodles"},
    ),
}

PRIZES = {
    "jar": Prize(id="jar", label="jujube jam", phrase="a jar of jujube jam", region="hands"),
    "coin": Prize(id="coin", label="gold coin", phrase="a tiny gold coin", region="pocket"),
    "star": Prize(id="star", label="paper star", phrase="a paper star with a ribbon", region="bag"),
}

AIDS = {
    "apology": Aid(id="apology", label="an apology", prep="say sorry", tail="they hugged and smiled", guards={"hurt"}),
    "sharing": Aid(id="sharing", label="a shared snack", prep="share a snack", tail="they shared the snack and laughed", guards={"hurt"}),
    "pairing": Aid(id="pairing", label="a pair of hands", prep="work side by side", tail="they worked side by side all the way", guards={"tension"}),
}

NAMES_GIRL = ["Mina", "Lila", "Nora", "Tia", "June"]
NAMES_BOY = ["Pip", "Joss", "Toby", "Ben", "Kai"]
TRAITS = ["brave", "gentle", "cheery", "spry", "curious"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    aid: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("zone_of", qid, q.zone))
        for t in sorted(q.tags):
            lines.append(asp.fact("tagged", qid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region_of", pid, p.region))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for g in sorted(a.guards):
            lines.append(asp.fact("guards", aid, g))
    return "\n".join(lines)


ASP_RULES = r"""
conflict(S,Q,P) :- affords(S,Q), zone_of(Q,Z), region_of(P,Z), quest(Q), prize(P).
has_fix(Q,P) :- conflict(_,Q,P), aid(A), guards(A,tension).
has_repair(Q,P) :- conflict(_,Q,P), aid(A), guards(A,hurt).
valid_story(S,Q,P,A) :- conflict(S,Q,P), aid(A), has_fix(Q,P).
valid_story(S,Q,P,A) :- conflict(S,Q,P), aid(A), has_repair(Q,P).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for qid in s.affords:
            quest = _safe_lookup(QUESTS, qid)
            for pid, prize in PRIZES.items():
                if quest.zone == prize.region:
                    for aid in AIDS:
                        combos.append((sid, qid, pid, aid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(python_valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story about a quest, a jujube prize, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = python_valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if getattr(args, "aid", None):
        combos = [c for c in combos if c[3] == getattr(args, "aid", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, prize, aid = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or ("boy" if hero_type == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    friend_name = getattr(args, "friend_name", None) or rng.choice(NAMES_BOY if friend_type == "boy" else NAMES_GIRL)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, quest, prize, aid, hero_name, hero_type, friend_name, friend_type, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    p: Prize = _safe_fact(world, f, "prize_cfg")
    h: Entity = _safe_fact(world, f, "hero")
    fr: Entity = _safe_fact(world, f, "friend")
    return [
        f'Write a rhyming TinyStories-style tale about a {h.type} named {h.id} on a {q.id} quest with oodles of heart.',
        f"Tell a gentle story where {h.id} and {fr.id} disagree on a {q.verb} quest, then make up and win {p.phrase}.",
        f'Write a short story that includes the words "oodles", "win", and "jujube" and ends in reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h: Entity = _safe_fact(world, f, "hero")
    fr: Entity = _safe_fact(world, f, "friend")
    q: Quest = _safe_fact(world, f, "quest")
    p: Prize = _safe_fact(world, f, "prize_cfg")
    aid: Aid = _safe_fact(world, f, "aid_cfg")
    return [
        QAItem(question=f"What did {h.id} want to win on the {q.id} quest?", answer=f"{h.id} wanted to win {p.phrase}."),
        QAItem(question=f"Why did {fr.id} get upset during the quest?", answer=f"{h.id} rushed ahead and did not keep the shared pace, so {fr.id} felt hurt."),
        QAItem(question=f"How did the friends reconcile?", answer=f"They said sorry, shared {aid.label}, and chose to work side by side again."),
        QAItem(question=f"What changed by the end of the story?", answer=f"The argument ended, the friends worked together, and they won the prize together."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a journey or task you do to reach a goal."),
        QAItem(question="What are jujubes?", answer="Jujubes are small, sweet treats or fruits in this story world."),
        QAItem(question="What does reconciliation mean?", answer="Reconciliation means making up after a disagreement and becoming friends again."),
        QAItem(question="What does oodles mean?", answer="Oodles means a lot or many, like a big pile of something."),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(QUESTS, params.quest),
        _safe_lookup(PRIZES, params.prize),
        _safe_lookup(AIDS, params.aid),
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
    )
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
    StoryParams("orchard", "grove", "jar", "apology", "Mina", "girl", "Pip", "boy", "gentle"),
    StoryParams("lane", "bridge", "coin", "sharing", "Kai", "boy", "Nora", "girl", "brave"),
    StoryParams("meadow", "river", "star", "pairing", "Lila", "girl", "Joss", "boy", "curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} valid stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
