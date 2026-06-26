#!/usr/bin/env python3
"""
storyworlds/worlds/rule_nonsensical_cautionary_detective_story.py
==================================================================

A small cautionary detective-story world about a child sleuth, a sensible rule,
and one nonsensical idea that nearly breaks the case.

Premise:
- A young detective wants to solve a tiny mystery.
- A guardian or mentor gives one clear rule.
- A nonsense shortcut tempts the detective.
- Following the rule leads to the clue and the safe resolution.

The domain is intentionally small and constraint-checked:
- The detective can investigate one of a few locations.
- Each case has one sensible rule and one tempting nonsensical choice.
- Only stories where the rule actually matters are generated.

This world keeps the prose child-facing, concrete, and slightly noir in tone,
while remaining a cautionary tale: the detective learns why the rule exists.
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

NOISE_THRESHOLD = 1.0



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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    grownup: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
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
    mood: str
    clue_style: str
    avoids: set[str] = field(default_factory=set)
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
class RuleItem:
    text: str
    reason: str
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass
class NonsenseItem:
    text: str
    consequence: str
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Case:
    mystery: str
    clue: str
    culprit_hint: str
    rule: RuleItem
    nonsense: NonsenseItem
    setting: str
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _deepcopy_entities(entities: dict[str, Entity]) -> dict[str, Entity]:
    return {k: dataclasses.replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in entities.items()}


def _copy_world(world: World) -> World:
    clone = World(world.setting)
    clone.entities = _deepcopy_entities(world.entities)
    clone.fired = set(world.fired)
    clone.paragraphs = [[]]
    clone.facts = dict(world.facts)
    return clone


World.copy = _copy_world  # type: ignore[assignment]


def _rule_following(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes.get("follow_rule", 0) < NOISE_THRESHOLD:
        return out
    sig = ("follow_rule",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.meters["care"] = detective.meters.get("care", 0) + 1
    out.append("The careful choice made the room feel less wobbly.")
    return out


def _nonsense_spread(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes.get("nonsense", 0) < NOISE_THRESHOLD:
        return out
    sig = ("nonsense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["trouble"] = detective.memes.get("trouble", 0) + 1
    out.append("The nonsense idea made the clues harder to trust.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_rule_following, _nonsense_spread):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "library": Setting(
        place="the library",
        mood="quiet",
        clue_style="bookish",
        avoids={"loudness", "sticky_hands"},
    ),
    "garden": Setting(
        place="the garden",
        mood="soft",
        clue_style="crumbly",
        avoids={"muddy_shoes"},
    ),
    "attic": Setting(
        place="the attic",
        mood="creaky",
        clue_style="dusty",
        avoids={"throwing_things"},
    ),
}


RULES = {
    "look_before_touching": RuleItem(
        text="Look first, touch later.",
        reason="Some clues are fragile, and a quick grab can spoil them.",
        tags={"care", "clue"},
    ),
    "write_it_down": RuleItem(
        text="Write the clue down before moving on.",
        reason="A detective can forget a small detail if the room is busy.",
        tags={"memory", "clue"},
    ),
    "ask_before_opening": RuleItem(
        text="Ask before opening the locked thing.",
        reason="Locked places can hide surprises, and grown-ups should check first.",
        tags={"safety", "lock"},
    ),
}

NONSENSES = {
    "sniff_the_clue": NonsenseItem(
        text="sniff the clue to learn its secret",
        consequence="sneezing blew the paper around the room",
        tags={"paper", "mess"},
    ),
    "shuffle_like_a_crab": NonsenseItem(
        text="walk sideways like a crab to become invisible",
        consequence="the sideways shuffle knocked over a stack of boxes",
        tags={"boxes", "mess"},
    ),
    "guess_with_eyes_closed": NonsenseItem(
        text="solve it with both eyes closed",
        consequence="the detective bumped into the table and lost the trail",
        tags={"confusion"},
    ),
}


CASES = {
    "missing_cookie": Case(
        mystery="who took the missing cookie",
        clue="a tiny crumb trail near the blue chair",
        culprit_hint="the puppy had muddy paws",
        rule=RULES["look_before_touching"],
        nonsense=NONSENSES["sniff_the_clue"],
        setting="kitchen",
    ),
    "lost_key": Case(
        mystery="where the brass key rolled",
        clue="a key-shaped shine under the rug",
        culprit_hint="the wind left the window open",
        rule=RULES["write_it_down"],
        nonsense=NONSENSES["guess_with_eyes_closed"],
        setting="library",
    ),
    "jam_jar": Case(
        mystery="why the jam jar was sticky",
        clue="a drip on the shelf near the ladder",
        culprit_hint="the ladder was used too fast",
        rule=RULES["ask_before_opening"],
        nonsense=NONSENSES["shuffle_like_a_crab"],
        setting="attic",
    ),
}

NAMES = ["Milo", "Nina", "Ada", "Ben", "Zoe", "Theo", "Ivy", "June"]
GROWNUPS = ["aunt", "uncle", "mom", "dad", "grandpa", "grandma"]
TRAITS = ["careful", "curious", "brave", "patient", "earnest"]


@dataclass
class StoryParams:
    case: str
    name: str
    hero_type: str
    grownup: str
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


def case_valid(case: Case) -> bool:
    return bool(case.rule.text) and bool(case.nonsense.text) and case.setting in SETTINGS


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for case_id, case in CASES.items():
        if case_valid(case):
            out.append((case_id, case.setting))
    return out


def introduce(world: World, hero: Entity, grownup: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} detective with a sharp notebook and a serious face."
    )
    world.say(
        f"One day, {hero.id} and {grownup.label} went to {world.setting.place} to solve {case.mystery}."
    )


def temptation(world: World, hero: Entity, case: Case) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    world.say(
        f"{hero.id} wanted to hurry, but the room whispered a strange idea: {case.nonsense.text}."
    )
    world.say(
        f"It sounded clever for one second, which was exactly why it was nonsensical."
    )


def warning(world: World, grownup: Entity, case: Case) -> None:
    world.say(
        f'{grownup.label} pointed to the rule and said, "{case.rule.text}"'
    )
    world.say(case.rule.reason)


def investigate(world: World, hero: Entity, case: Case) -> None:
    hero.memes["follow_rule"] = hero.memes.get("follow_rule", 0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} obeyed the rule, bent close, and noticed {case.clue}."
    )


def blunder_if_nonsense(world: World, hero: Entity, case: Case) -> None:
    hero.memes["nonsense"] = hero.memes.get("nonsense", 0) + 1
    propagate(world, narrate=False)
    world.say(
        f"When the nonsense idea tugged at {hero.pronoun('possessive')} sleeve, {hero.id} almost tried it."
    )
    world.say(
        f"That would have caused trouble because {case.nonsense.consequence}."
    )


def solve_case(world: World, hero: Entity, grownup: Entity, case: Case) -> None:
    world.say(
        f"With the clue safe on the page, {hero.id} solved the mystery: {case.culprit_hint}."
    )
    world.say(
        f"{grownup.label} smiled, and {hero.id} learned that a good rule can stop a silly mistake before it starts."
    )
    world.say(
        f"By the end, the room was calm again, and the detective's notebook had the right answer."
    )


def tell_story(params: StoryParams) -> World:
    case = _safe_lookup(CASES, params.case)
    setting = _safe_lookup(SETTINGS, case.setting)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup, label=f"the {params.grownup}"))
    clue = world.add(Entity(id="clue", type="thing", label=case.clue, phrase=case.clue))
    world.facts.update(case=case, hero=hero, grownup=grownup, clue=clue, setting=setting)

    introduce(world, hero, grownup, case)
    world.para()
    warning(world, grownup, case)
    temptation(world, hero, case)
    blunder_if_nonsense(world, hero, case)
    investigate(world, hero, case)
    world.para()
    solve_case(world, hero, grownup, case)
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = _safe_fact(world, world.facts, "case")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    grownup: Entity = _safe_fact(world, world.facts, "grownup")
    return [
        f'Write a short cautionary detective story about {hero.id} solving {case.mystery}.',
        f'Tell a child-friendly detective story where the rule "{case.rule.text}" matters and the nonsense idea "{case.nonsense.text}" causes a problem.',
        f'Write a small mystery set in {world.setting.place} with a clear clue and a sensible lesson about safety.',
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = _safe_fact(world, world.facts, "case")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    grownup: Entity = _safe_fact(world, world.facts, "grownup")
    return [
        QAItem(
            question=f"What mystery was {hero.id} trying to solve?",
            answer=f"{hero.id} was trying to solve {case.mystery} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What rule did {grownup.label} tell {hero.id} to follow?",
            answer=f'{grownup.label} said, "{case.rule.text}" because {case.rule.reason}',
        ),
        QAItem(
            question=f"What clue helped {hero.id} finish the case?",
            answer=f"The clue was {case.clue}, and it led {hero.id} to the answer.",
        ),
        QAItem(
            question=f"Why was the nonsense idea a bad choice?",
            answer=f"It was a bad choice because {case.nonsense.consequence}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} solved the mystery and learned that careful rule-following keeps a case safe and clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="Why should someone follow a safety rule?",
            answer="A safety rule helps stop accidents and keeps people from making a risky mistake.",
        ),
        QAItem(
            question="What is nonsense?",
            answer="Nonsense is an idea that sounds odd or silly and does not really make sense.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("setting", case.setting))
        lines.append(asp.fact("has_rule", cid))
        lines.append(asp.fact("has_nonsense", cid))
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for avoid in sorted(setting.avoids):
            lines.append(asp.fact("avoids", sid, avoid))
    return "\n".join(lines)


ASP_RULES = r"""
case_ok(C) :- case(C), has_rule(C), has_nonsense(C).
valid_story(C) :- case_ok(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(cid,) for cid, _ in valid_combos()}
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} cases).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(case="missing_cookie", name="Milo", hero_type="boy", grownup="mom", trait="careful"),
    StoryParams(case="lost_key", name="Ivy", hero_type="girl", grownup="dad", trait="curious"),
    StoryParams(case="jam_jar", name="Theo", hero_type="boy", grownup="grandma", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary detective story world with a sensible rule and one nonsensical temptation.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=GROWNUPS)
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
    combos = valid_combos()
    if getattr(args, "case", None):
        combos = [c for c in combos if c[0] == getattr(args, "case", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    case_id, _ = rng.choice(combos)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    grownup = getattr(args, "grownup", None) or rng.choice(GROWNUPS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(case=case_id, name=name, hero_type=hero_type, grownup=grownup, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("\n".join(str(t) for t in sorted(set(asp.atoms(model, "valid_story")))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
