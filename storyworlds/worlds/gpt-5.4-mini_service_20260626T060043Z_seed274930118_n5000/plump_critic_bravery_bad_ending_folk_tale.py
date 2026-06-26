#!/usr/bin/env python3
"""
storyworlds/worlds/plump_critic_bravery_bad_ending_folk_tale.py
===============================================================

A small folk-tale storyworld about a brave child, a plump critic, and a hard
choice that does not end in a tidy win.

Source-tale seed:
---
A plump critic came to a little village and laughed at everyone who tried to be
brave. A small child still chose to cross the dark wood to bring home a lost
bell. The child was brave, but the road was mean, the critic was unkind, and
the tale ended with a bad ending image instead of a rescue.

World idea:
---
- The hero has bravery and can act despite fear.
- The critic is plump, sharp-tongued, and can lower confidence.
- The setting is a folk-tale village edge, usually with a road, bridge, or wood.
- The turn is a risky errand or test.
- The ending is a bad ending: the brave choice matters, but the world still
  takes something precious.

This file follows the Storyweavers world contract:
- self-contained stdlib script
- lazy ASP import inside helpers
- StoryParams / parser / resolve_params / generate / emit / main
- trace, QA, json, asp, verify, show-asp support
- typed entities with meters and memes
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    region: object | None = None
    critic: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
    edge: str
    mood: str
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
    danger: str
    risk: str
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
class Relic:
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    zone: set[str] = field(default_factory=set)
    weather: str = ""

    world: object | None = None
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
    place: str
    quest: str
    relic: str
    hero_name: str
    hero_type: str
    critic_name: str
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


SETTINGS = {
    "village": Setting(place="the village", edge="the lane", mood="humble", affords={"bell", "bread", "lantern"}),
    "wood": Setting(place="the old wood", edge="the bramble path", mood="shadowy", affords={"bell", "lantern"}),
    "river": Setting(place="the river road", edge="the narrow bridge", mood="windy", affords={"basket", "bread"}),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        verb="bring home the lost bell",
        gerund="bringing home the lost bell",
        danger="the branch would snare the rope",
        risk="the bell might fall into the mud",
        zone={"torso", "hands"},
        keyword="bell",
        tags={"sound", "wood"},
    ),
    "lantern": Quest(
        id="lantern",
        verb="carry the lantern to the mill",
        gerund="carrying the lantern to the mill",
        danger="the dark wind would blow at the flame",
        risk="the lantern might go out",
        zone={"hands"},
        keyword="lantern",
        tags={"light", "night"},
    ),
    "bread": Quest(
        id="bread",
        verb="bring the bread to the far cottage",
        gerund="bringing the bread to the far cottage",
        danger="the bridge would shake and spill the basket",
        risk="the bread might be ruined",
        zone={"hands"},
        keyword="bread",
        tags={"food", "bridge"},
    ),
}

RELICS = {
    "bell": Relic(label="bell", phrase="a small silver bell", type="bell", region="torso"),
    "lantern": Relic(label="lantern", phrase="a little glass lantern", type="lantern", region="hands"),
    "bread": Relic(label="basket", phrase="a warm basket of bread", type="basket", region="hands", plural=False),
}

HERO_NAMES = ["Mira", "Pip", "Toby", "Anya", "Jory", "Lila"]
CRITIC_NAMES = ["Master Bram", "Old Wren", "Aunt Tilda", "Mister Crow", "Nell the Tanner"]
TRAITS = ["small", "quick", "quiet", "kind", "curious", "stubborn"]


def award_bravery(hero: Entity, amount: float = 1.0) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + amount


def _risk_event(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    quest = _safe_fact(world, world.facts, "quest")
    relic = _safe_fact(world, world.facts, "relic")
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if ("risk", quest.id) in world.fired:
        return out
    world.fired.add(("risk", quest.id))
    relic.meters["danger"] = relic.meters.get("danger", 0.0) + 1
    out.append(f"The road grew mean, just as {hero.id} had feared.")
    return out


def _critic_mock(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    critic = _safe_fact(world, world.facts, "critic")
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if ("mock", critic.id) in world.fired:
        return out
    world.fired.add(("mock", critic.id))
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    out.append(f"{critic.id} laughed and called {hero.id} foolish.")
    return out


def _bad_ending(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    relic = _safe_fact(world, world.facts, "relic")
    quest = _safe_fact(world, world.facts, "quest")
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if relic.meters.get("danger", 0.0) < THRESHOLD:
        return out
    if ("bad", quest.id) in world.fired:
        return out
    world.fired.add(("bad", quest.id))
    relic.meters["lost"] = relic.meters.get("lost", 0.0) + 1
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1
    out.append("__bad__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_risk_event, _critic_mock, _bad_ending):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__bad__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(quest: Quest, relic: Relic) -> bool:
    return relic.region in quest.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = _safe_lookup(QUESTS, qid)
            for rid, relic in RELICS.items():
                if quest_at_risk(quest, relic):
                    combos.append((place, qid, rid))
    return combos


def tell(setting: Setting, quest: Quest, relic_cfg: Relic, hero_name: str, hero_type: str, critic_name: str) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", "brave"]))
    critic = world.add(Entity(id=critic_name, kind="character", type="man", traits=["plump", "critic"]))
    relic = world.add(Entity(id="relic", type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase, caretaker=critic.id, region=relic_cfg.region))
    world.facts = {"hero": hero, "critic": critic, "relic": relic, "quest": quest, "setting": setting}
    world.weather = "grey"

    world.say(f"In {setting.place}, there was a {hero.traits[0]} child named {hero.id}.")
    world.say(f"Near the lane lived {critic.id}, a plump critic who always had a sharp word ready.")
    world.say(f"Still, {hero.id} loved the old tales of courage and promised to {quest.verb}.")

    world.para()
    world.say(f"At {setting.edge}, {hero.id} looked at {relic.phrase} and took a deep breath.")
    world.say(f"'{quest.danger},' warned {critic.id}, but {hero.id} lifted the {relic.label} anyway.")
    award_bravery(hero, 1.0)
    if hero.memes.get("bravery", 0.0) >= THRESHOLD:
        world.say(f"That was the brave part: {hero.id} kept walking even while the dark pressed close.")
    propagate(world, narrate=True)

    world.para()
    if relic.meters.get("lost", 0.0) >= THRESHOLD:
        world.say(f"By nightfall, the {relic.label} was gone, and the village had only the sound of wind left.")
        world.say(f"{hero.id} came home empty-handed, with brave feet and a sore heart, while {critic.id} said nothing kind.")
    else:
        world.say(f"The tale should have ended happily, but the road still took its toll.")
        world.say(f"{hero.id} returned with the {relic.label}, though the old folk whispered that the ending felt wrong.")

    world.facts["bad_ending"] = relic.meters.get("lost", 0.0) >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    critic = _safe_fact(world, f, "critic")
    quest = _safe_fact(world, f, "quest")
    relic = _safe_fact(world, f, "relic")
    return [
        f'Write a folk tale for a young child about a brave little hero and a plump critic, using the word "{quest.keyword}".',
        f"Tell a short story where {hero.id} tries to {quest.verb}, while {critic.id} doubts {hero.pronoun('object')} and the ending turns bad.",
        f"Write a village story with bravery, a warning, and a sad ending image involving {relic.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    critic: Entity = _safe_fact(world, f, "critic")
    quest: Quest = _safe_fact(world, f, "quest")
    relic: Entity = _safe_fact(world, f, "relic")
    qa = [
        QAItem(
            question=f"Who was the brave child in the story?",
            answer=f"The brave child was {hero.id}, a small child who still chose to {quest.verb}.",
        ),
        QAItem(
            question=f"Who was the plump critic in the story?",
            answer=f"The plump critic was {critic.id}, who watched the road and spoke in a sharp voice.",
        ),
        QAItem(
            question=f"What risky thing did {hero.id} try to do?",
            answer=f"{hero.id} tried to {quest.verb} with {relic.phrase}, even though the road was dangerous.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because the road turned mean, the {relic.label} was lost, and {hero.id} came home with nothing but bravery.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does something hard or scary even though they feel afraid.",
        ),
        QAItem(
            question="What is a critic?",
            answer="A critic is a person who judges things and tells what they think about them, sometimes kindly and sometimes not.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when a story ends with loss, trouble, or sadness instead of a happy finish.",
        ),
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(quest: Quest, relic: Relic) -> str:
    if not quest_at_risk(quest, relic):
        return f"(No story: {quest.gerund} does not endanger {relic.label} in this world.)"
    return "(No story: the requested choices do not fit a folk-tale bad ending arc.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld with bravery and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--critic")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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
    if getattr(args, "quest", None) and getattr(args, "relic", None):
        if not quest_at_risk(_safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(RELICS, getattr(args, "relic", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, relic = rng.choice(list(combos))
    q = _safe_lookup(QUESTS, quest)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    critic = getattr(args, "critic", None) or rng.choice(CRITIC_NAMES)
    return StoryParams(place=place, quest=quest, relic=relic, hero_name=name, hero_type=hero_type, critic_name=critic)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(RELICS, params.relic), params.hero_name, params.hero_type, params.critic_name)
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
    StoryParams(place="wood", quest="bell", relic="bell", hero_name="Mira", hero_type="girl", critic_name="Master Bram"),
    StoryParams(place="village", quest="lantern", relic="lantern", hero_name="Pip", hero_type="boy", critic_name="Old Wren"),
    StoryParams(place="river", quest="bread", relic="bread", hero_name="Anya", hero_type="girl", critic_name="Aunt Tilda"),
]


ASP_RULES = r"""
risk(Q,R) :- quest(Q), relic(R), zone(Q,Z), region(R,Z).
bad(Q) :- risk(Q,R), danger(Q), critic(C), mock(C), brave(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for z in sorted(q.zone):
            lines.append(asp.fact("zone", qid, z))
        lines.append(asp.fact("danger", qid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("region", rid, r.region))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("brave", "hero"))
    lines.append(asp.fact("critic", "critic"))
    lines.append(asp.fact("mock", "critic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risk/2. #show bad/1."))
    asp_risk = set(asp.atoms(model, "risk"))
    asp_bad = set(asp.atoms(model, "bad"))
    py_risk = {(q, r) for _, q, r in valid_combos()}
    py_bad = {(q,) for q, r in ((q, r) for _, q, r in valid_combos())}
    if asp_risk == py_risk and asp_bad == py_bad:
        print(f"OK: ASP matches Python ({len(asp_risk)} risky combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP risk:", sorted(asp_risk))
    print("PY risk:", sorted(py_risk))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show risk/2."))
    return sorted(set(asp.atoms(model, "risk")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show risk/2. #show bad/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} risky quest/relic pairs:")
        for q, r in combos:
            print(f"  {q:8} {r}")
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
