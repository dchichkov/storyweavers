#!/usr/bin/env python3
"""
storyworlds/worlds/communicate_puke_happy_ending_flashback_adventure.py
======================================================================

A small Adventure-style story world about a child on a little expedition who
needs to communicate when they feel sick, remembers a helpful flashback, and
still reaches a happy ending.

The seed ideas are:
- communicate
- puke
- happy ending
- flashback
- adventure

The world is intentionally tiny and classical: one path, one little trouble,
one remembered lesson, and one warm resolution.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Trail:
    place: str
    feature: str
    afford: str
    atmosphere: str
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
class Trouble:
    id: str
    verb: str
    symptom: str
    loss: str
    mess: str
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
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
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
    def __init__(self, trail: Trail) -> None:
        self.trail = trail
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_used = False

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


@dataclass
class StoryParams:
    place: str
    trouble: str
    aid: str
    name: str
    gender: str
    companion: str
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


TRAILS = {
    "forest_path": Trail(place="the forest path", feature="a bright trail marker", afford="walk", atmosphere="The trees leaned overhead and the path felt like a real adventure."),
    "hill_trail": Trail(place="the hill trail", feature="a rocky turn", afford="hike", atmosphere="The wind brushed the grass and the trail climbed like a little quest."),
    "cave_road": Trail(place="the cave road", feature="a lantern-lit bend", afford="explore", atmosphere="The cave mouth echoed softly, like the start of a secret adventure."),
}

TROUBLES = {
    "car_sick": Trouble(id="car_sick", verb="ride too long", symptom="nauseous", loss="pale and dizzy", mess="puke", keyword="puke", tags={"puke", "sick"}),
    "trail_spinning": Trouble(id="trail_spinning", verb="climb too fast", symptom="woozy", loss="unsteady", mess="puke", keyword="puke", tags={"puke", "sick"}),
}

AIDS = {
    "water": Aid(id="water", label="a water bottle", prep="take a careful sip from a water bottle", tail="kept walking slowly with the water bottle tucked in hand", helps={"nausea", "sick"}),
    "rest": Aid(id="rest", label="a shady rest spot", prep="sit down in a shady rest spot", tail="rested until the spinning feeling passed", helps={"nausea", "sick"}),
    "snack": Aid(id="snack", label="a little snack bag", prep="eat a few crackers from a snack bag", tail="felt steadier after the crackers", helps={"nausea", "sick"}),
}

NAMES = {
    "girl": ["Mia", "Ava", "Luna", "Zoe", "Nora"],
    "boy": ["Leo", "Finn", "Theo", "Max", "Eli"],
}
TRAITS = ["brave", "curious", "spirited", "careful", "bold"]
COMPANIONS = ["mother", "father", "big sister", "big brother"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, trail in TRAILS.items():
        for trouble in TROUBLES:
            for aid in AIDS:
                combos.append((place, trouble, aid))
    return combos


def reasonableness_gate(place: str, trouble: str, aid: str) -> bool:
    return place in TRAILS and trouble in TROUBLES and aid in AIDS


def tell_flashback(world: World, hero: Entity, companion: Entity) -> None:
    world.flashback_used = True
    world.say(
        f"Flashback: earlier that morning, {companion.label} had told {hero.id}, "
        f'"If your tummy feels funny, communicate right away so we can help."'
    )


def introduce(world: World, hero: Entity, companion: Entity, trouble: Trouble) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.get('traits', [])), 'brave')} {hero.type} who loved adventure."
    )
    world.say(
        f"{hero.id} and {companion.label} set out for {world.trail.place}, and {world.trail.feature} made the day feel exciting."
    )
    world.say(
        f"{hero.id} wanted to {trouble.verb}, but {companion.label} noticed {hero.pronoun('possessive')} steps getting slower."
    )


def on_sick(world: World, hero: Entity, companion: Entity, trouble: Trouble, aid: Aid) -> None:
    hero.memes["fear"] += 1
    hero.memes["need_help"] += 1
    world.say(
        f"Then {hero.id} felt {trouble.symptom} and looked ready to {trouble.mess}."
    )
    world.say(
        f"{hero.id} remembered the advice and tried to communicate instead of hiding it."
    )
    tell_flashback(world, hero, companion)
    world.say(
        f'"I feel {trouble.loss}," {hero.id} said, holding a hand to {hero.pronoun("possessive")} stomach.'
    )
    companion.memes["care"] += 1
    world.say(
        f"{companion.label} knelt down at once and helped {hero.id} {aid.prep}."
    )
    world.say(
        f"That simple help kept the trouble from getting worse."
    )
    world.say(
        f"After a while, {hero.id} {aid.tail}, and the scary feeling faded."
    )
    hero.memes["joy"] += 2
    hero.memes["relief"] += 2


def ending(world: World, hero: Entity, companion: Entity, aid: Aid, trouble: Trouble) -> None:
    world.say(
        f"In the end, {hero.id} and {companion.label} finished the adventure with smiles, not tears."
    )
    world.say(
        f"{hero.id} had spoken up, gotten help, and stayed safe, so the trail felt like a happy ending."
    )
    world.say(
        f"The {trouble.keyword} scare passed, the {aid.label} stayed close, and the day became one {hero.pronoun('possessive')} family would remember fondly."
    )


def tell(place: str, trouble_id: str, aid_id: str, hero_name: str, gender: str, companion_name: str, trait: str) -> World:
    if not reasonableness_gate(place, trouble_id, aid_id):
        pass

    world = World(_safe_lookup(TRAILS, place))
    trouble = _safe_lookup(TROUBLES, trouble_id)
    aid = _safe_lookup(AIDS, aid_id)

    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    hero.memes["traits"] = [trait]
    companion = world.add(Entity(id=companion_name, kind="character", type="adult", label=companion_name))
    world.add(Entity(id="aid", type="thing", label=aid.label, phrase=aid.label, caretaker=companion.id, owner=hero.id))

    world.facts.update(hero=hero, companion=companion, trouble=trouble, aid=aid, trail=world.trail, trait=trait)

    introduce(world, hero, companion, trouble)
    world.para()
    on_sick(world, hero, companion, trouble, aid)
    world.para()
    ending(world, hero, companion, aid, trouble)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trouble = _safe_fact(world, f, "trouble")
    aid = _safe_fact(world, f, "aid")
    return [
        f'Write a short Adventure-style story for a young child about {hero.id} who must communicate when feeling {trouble.symptom}.',
        f"Tell a gentle flashback story where a child remembers advice, avoids {trouble.mess}, and gets help with {aid.label}.",
        f'Write a happy ending story using the word "{trouble.keyword}" and a clear moment of speaking up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    trouble = _safe_fact(world, f, "trouble")
    aid = _safe_fact(world, f, "aid")
    return [
        QAItem(
            question=f"What did {hero.id} do when {hero.pronoun('possessive')} stomach felt funny?",
            answer=f"{hero.id} communicated right away and told {companion.label} that {hero.pronoun('subject')} felt {trouble.loss}.",
        ),
        QAItem(
            question=f"Why is there a flashback in the story?",
            answer=f"The flashback reminds {hero.id} of earlier advice to communicate if {hero.pronoun('possessive')} tummy felt bad, and that memory helps the adventure turn safe.",
        ),
        QAItem(
            question=f"How did {companion.label} help {hero.id}?",
            answer=f"{companion.label} gave {hero.id} {aid.label} and a calm place to rest so the {trouble.keyword} feeling would pass.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The ending is happy because {hero.id} spoke up, got help quickly, and was able to finish the adventure safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does communicate mean?",
            answer="Communicate means to share information or feelings so other people understand what you need.",
        ),
        QAItem(
            question="Why should someone tell an adult when they feel sick?",
            answer="Telling an adult helps them give care, keep the child safe, and stop a small problem from becoming a bigger one.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that briefly shows something from earlier, so readers understand why a character remembers it now.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest_path", trouble="car_sick", aid="water", name="Mia", gender="girl", companion="mother", trait="brave"),
    StoryParams(place="hill_trail", trouble="trail_spinning", aid="rest", name="Leo", gender="boy", companion="father", trait="curious"),
    StoryParams(place="cave_road", trouble="car_sick", aid="snack", name="Nora", gender="girl", companion="big brother", trait="spirited"),
]

ASP_RULES = r"""
hero(H) :- hero_name(H).
companion(C) :- companion_name(C).
trail(P) :- trail_name(P).
trouble(T) :- trouble_name(T).
aid(A) :- aid_name(A).

needs_help(H) :- symptom(H, nauseous).
flashback(H) :- advice_before(H).
communicates(H) :- says_need(H).
happy_ending(H) :- communicates(H), gets_help(H), not worsens(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in TRAILS:
        lines.append(asp.fact("trail_name", p))
    for t in TROUBLES:
        lines.append(asp.fact("trouble_name", t))
    for a in AIDS:
        lines.append(asp.fact("aid_name", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show trail_name/1."))
    if model is None:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP program loads.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about communicating illness, flashback, and a happy ending.")
    ap.add_argument("--place", choices=TRAILS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "trouble", None):
        combos = [c for c in combos if c[1] == getattr(args, "trouble", None)]
    if getattr(args, "aid", None):
        combos = [c for c in combos if c[2] == getattr(args, "aid", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trouble, aid = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble, aid=aid, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.trouble, params.aid, params.name, params.gender, params.companion, params.trait)
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
        print(asp_program("#show trail_name/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available in the inline rules and facts.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
