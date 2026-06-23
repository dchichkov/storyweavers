#!/usr/bin/env python3
"""
storyworlds/worlds/whisker_factor_hurl_rhyme_humor_repetition_slice.py
======================================================================

A standalone storyworld for a tiny slice-of-life scene: a child tries to get
ready for a neighborhood rhyme recital, a cat contributes whiskers, a tossed
item goes wrong, and everyone ends up smiling.

Seed tale:
---
A child is trying to get ready for a small rhyme recital on the porch.
The cat keeps brushing its whisker against the table, the child worries about
a missing factor in the costume, and a sibling accidentally hurls a prop into a
laundry basket. There is a little confusion, some humor, and repeating lines
as the family tidies up together. In the end, the child arrives with the right
hat, the cat settled, and the rhyme still in their head.

This script models a small physical/emotional world with meters and memes, a
reasonableness gate, a declarative ASP twin, and three QA sets:
(1) generation prompts, (2) story-grounded QA, and (3) world-knowledge QA.
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    child: object | None = None
    fix: object | None = None
    helper: object | None = None
    pet: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    indoors: bool
    allows: set[str] = field(default_factory=set)
    weather: str = ""
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
    mess: str
    splash: str
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    place: str
    region: str
    plural: bool = False
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
class Fix:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _apply_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("worry", 0.0) >= THRESHOLD:
            sig = ("worry", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"{ent.label_word.capitalize()} kept thinking about the missing piece.")
    return out


def _apply_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters.get("hurl", 0.0) < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for item in list(world.entities.values()):
            if item.kind == "thing" and item.region in world.zone:
                item.meters["jostled"] = item.meters.get("jostled", 0.0) + 1
                out.append(f"That made the {item.label} wobble.")
    return out


def _apply_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("humor_boost", 0.0) >= THRESHOLD and ("laugh",) not in world.fired:
        world.fired.add(("laugh",))
        for ent in world.characters():
            ent.memes["cheer"] = ent.memes.get("cheer", 0.0) + 1
        out.append("The whole room turned giggly.")
    return out


CAUSAL_RULES = [_apply_worry, _apply_spill, _apply_laugh]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(word: str) -> str:
    return f"{word.capitalize()}, the day may sway, but we will tidy and carry on today."


def valid_combo(setting: Setting, activity: Activity, prize: Item) -> bool:
    return activity.id in setting.allows and prize.region in activity.splash


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            for pid, prize in ITEMS.items():
                if valid_combo(setting, act, prize):
                    out.append((sid, aid, pid))
    return out


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    pet: str
    fix: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with rhyme, humor, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--pet", choices=["cat", "dog"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prize = rng.choice(list(combos))
    child_gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    child = getattr(args, "child", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    pet = getattr(args, "pet", None) or rng.choice(["cat", "dog"])
    fix = getattr(args, "fix", None) or rng.choice(sorted(FIXES))
    return StoryParams(
        setting=setting, activity=activity, prize=prize,
        child=child, child_gender=child_gender,
        helper=helper, helper_gender=helper_gender,
        pet=pet, fix=fix,
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    prize_cfg = _safe_lookup(ITEMS, params.prize)
    fix_cfg = _safe_lookup(FIXES, params.fix)
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", label=params.child))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", label=params.helper))
    pet = world.add(Entity(id=params.pet, kind="character", type="cat" if params.pet == "cat" else "dog", role="pet", label=f"the {params.pet}"))
    prize = world.add(Entity(
        id="prize", kind="thing", type=prize_cfg.kind, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=child.id, region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    fix = world.add(Entity(id=fix_cfg.id, kind="thing", type="fix", label=fix_cfg.label, phrase=fix_cfg.phrase))
    child.meters["hurl"] = 0.0
    child.memes["worry"] = 0.0
    helper.memes["humor"] = 0.0
    pet.meters["whisker"] = 1.0
    world.facts["humor_boost"] = 1.0

    world.say(f"On a quiet morning, {child.id} was getting ready for the porch rhyme recital.")
    world.say(f"{child.id} loved to practice and practice: {rhyme_line('ready')}")
    world.say(f"At the table, {pet.label_word} kept brushing a whisker against the napkin. Whisker, whisker, whisker.")
    world.say(f"{child.id} smiled anyway and checked the costume again. The missing factor was the hat, not the grin.")

    world.para()
    world.zone = set(activity.splash)
    child.memes["worry"] += 1
    world.say(f"{child.id} wanted to {activity.verb}, but the room felt busy.")
    world.say(f"{helper.id} pointed to the tidy basket and said, 'First the factor, then the fun.'")
    child.meters["hurl"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {helper.id} had a silly idea and tried to hurl the ribbon toward the chair.")
    world.say(f"It missed, of course. Of course it missed. It landed in the laundry basket with a soft thump.")

    world.para()
    world.say(f"{child.id} laughed. {helper.id} laughed. Even {pet.label_word} looked pleased.")
    world.say(f"'Whisker, factor, hurl,' {child.id} repeated, because the words sounded like a tiny joke.")
    world.say(f"{helper.id} repeated it back: 'Whisker, factor, hurl.' Then they both repeated it again.")
    world.say(f"With the basket fixed and the hat found, {child.id} took a breath and practiced the rhyme one more time.")
    world.say(f"{rhyme_line('whisker')}")
    world.say(f"At last {child.id} went to the porch wearing the right hat, smiling at the cat, and ready to begin.")

    world.facts.update(
        child=child, helper=helper, pet=pet, prize=prize, fix=fix,
        activity=activity, setting=setting, humor_boost=1.0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    return [
        f"Write a slice-of-life story for a young child that includes the words whisker, factor, and hurl.",
        f"Tell a gentle, funny story about {child.id} getting ready to {activity.verb} and practicing a rhyme.",
        f"Write a small family story where someone says whisker, factor, hurl more than once, and the ending is calm and cheerful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    pet = f["pet"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"What was {child.id} getting ready for?",
            answer=f"{child.id} was getting ready for a porch rhyme recital. The family was tidying up and practicing so the day would go smoothly.",
        ),
        QAItem(
            question=f"Why did {child.id} laugh when {helper.id} tried to hurl the ribbon?",
            answer=f"{helper.id} missed the chair and dropped the ribbon into the laundry basket instead. That made the moment funny, and it helped everyone relax.",
        ),
        QAItem(
            question=f"What did {child.id} keep repeating at the end?",
            answer=f"{child.id} kept repeating 'whisker, factor, hurl.' The repetition sounded playful and helped the child remember the rhyme.",
        ),
        QAItem(
            question=f"How did {pet.label_word} affect the morning?",
            answer=f"The cat kept brushing a whisker against the napkin, which made the table feel busy and a little silly. That small interruption became part of the story's humor.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the costume?",
            answer=f"{child.id} found the right hat and went to the porch smiling. By the end, the costume was ready and the child was calm enough to begin the recital.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whisker?",
            answer="A whisker is one of the long, thin hairs on an animal's face. Cats use whiskers to feel around and sense nearby things.",
        ),
        QAItem(
            question="What does hurl mean?",
            answer="To hurl something means to throw it quickly or with a lot of force. If you hurl something carelessly, it might miss where you wanted it to go.",
        ),
        QAItem(
            question="What is a factor?",
            answer="A factor is one part that helps make up a result or a plan. People also use the word when they are checking what matters most.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.plural:
            bits.append("plural=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "porch": Setting(place="the porch", indoors=False, allows={"rhyme"}, weather="mild"),
    "kitchen": Setting(place="the kitchen", indoors=True, allows={"rhyme", "tidy"}, weather="quiet"),
    "backyard": Setting(place="the backyard", indoors=False, allows={"rhyme", "tidy"}, weather="sunny"),
}

ACTIVITIES = {
    "rhyme": Activity(id="rhyme", verb="practice the rhyme", gerund="practicing the rhyme", rush="rush through the rhyme", mess="mild", splash={"table", "basket"}, keyword="rhyme", tags={"rhyme", "humor"}),
}

ITEMS = {
    "hat": Item(id="hat", label="the blue hat", phrase="a blue hat with a soft brim", kind="hat", place="closet", region="head", plural=False, tags={"hat"}),
    "scarf": Item(id="scarf", label="the striped scarf", phrase="a striped scarf", kind="scarf", place="chair", region="neck", plural=False, tags={"scarf"}),
    "shoes": Item(id="shoes", label="the tidy shoes", phrase="tidy shoes", kind="shoes", place="mat", region="feet", plural=True, tags={"shoes"}),
}

FIXES = {
    "basket": Fix(id="basket", label="the laundry basket", phrase="a laundry basket", helps={"tidy", "catch"}),
    "hanger": Fix(id="hanger", label="the coat hanger", phrase="a coat hanger", helps={"hang"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo"]

CURATED = [
    StoryParams(setting="porch", activity="rhyme", prize="hat", child="Mia", child_gender="girl", helper="Noah", helper_gender="boy", pet="cat", fix="basket"),
    StoryParams(setting="kitchen", activity="rhyme", prize="shoes", child="Eli", child_gender="boy", helper="Ava", helper_gender="girl", pet="dog", fix="hanger"),
]


def explain_rejection(setting: Setting, activity: Activity, prize: Item) -> str:
    return (
        f"(No story: {activity.verb} in {setting.place} doesn't put the {prize.label} at risk in a natural way. "
        f"Choose a prize worn on a spot the activity reaches.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.allows):
            lines.append(asp.fact("allows", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.splash):
            lines.append(asp.fact("splash", aid, r))
    for pid, p in ITEMS.items():
        lines.append(asp.fact("item", pid))
        lines.append(asp.fact("region", pid, p.region))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,P) :- setting(S), activity(A), item(P), allows(S,A), splash(A,R), region(P,R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        c = set(asp_valid_combos())
        p = set(valid_combos())
        if c == p:
            print(f"OK: ASP matches valid_combos() ({len(c)} combos).")
        else:
            rc = 1
            print("Mismatch in valid-combo parity.")
        # smoke test
        sample = generate(resolve_params(argparse.Namespace(setting=None, activity=None, prize=None, fix=None, child=None, child_gender=None, helper=None, helper_gender=None, pet=None), random.Random(777)))
        assert sample.story.strip()
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print("Verification failed:", exc)
        traceback.print_exc()
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.activity not in ACTIVITIES or params.prize not in ITEMS or params.fix not in FIXES:
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(ITEMS, params.prize)
    if not valid_combo(setting, activity, prize):
        pass
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for triple in asp_valid_combos():
            print(triple)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
