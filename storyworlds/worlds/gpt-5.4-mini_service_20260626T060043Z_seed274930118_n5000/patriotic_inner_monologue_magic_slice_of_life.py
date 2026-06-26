#!/usr/bin/env python3
"""
patriotic_inner_monologue_magic_slice_of_life.py
================================================

A small slice-of-life story world about a child, a quiet patriotic errand,
a little bit of magic, and an inner monologue that helps turn worry into a
kind, everyday win.

The seed image behind this world:
- A child is helping prepare for a neighborhood patriotic gathering.
- They have a small magical object or habit that can brighten ordinary things.
- They worry whether their handmade decoration is good enough.
- Their inner monologue is part of the story beat, not just decoration.
- The ending proves something changed in the world: a finished banner, a calm
  child, a happier room, or a shared moment in a modest, slice-of-life way.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    magical: bool = False
    patriotic: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    parent: object | None = None
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
class Setting:
    place: str
    indoor: bool = False
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    strain: str
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    patriotic: bool = False
    magical: bool = False
    gives: str = ""
    guards: set[str] = field(default_factory=set)
    answer: object | None = None
    question: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"decorate", "bake"}),
    "porch": Setting(place="the porch", indoor=False, affords={"decorate", "wave"}),
    "classroom": Setting(place="the classroom", indoor=True, affords={"decorate", "sing"}),
    "yard": Setting(place="the yard", indoor=False, affords={"decorate", "wave"}),
}

ACTIVITIES = {
    "decorate": Activity(
        id="decorate",
        verb="hang paper stars",
        gerund="hanging paper stars",
        rush="run to the craft table",
        mess="glitter",
        strain="torn",
        keyword="stars",
        tags={"craft", "patriotic", "magic"},
    ),
    "bake": Activity(
        id="bake",
        verb="bake little treats",
        gerund="baking little treats",
        rush="hurry to the counter",
        mess="flour",
        strain="sticky",
        keyword="cookies",
        tags={"kitchen"},
    ),
    "wave": Activity(
        id="wave",
        verb="wave flags",
        gerund="waving flags",
        rush="dash outside",
        mess="bent",
        strain="rumpled",
        keyword="flags",
        tags={"patriotic"},
    ),
    "sing": Activity(
        id="sing",
        verb="practice a song",
        gerund="practicing a song",
        rush="step to the front",
        mess="nervous",
        strain="shaky",
        keyword="song",
        tags={"patriotic", "music"},
    ),
}

ITEMS = {
    "banner": Item(
        id="banner",
        label="banner",
        phrase="a red, white, and blue paper banner",
        region="torso",
        patriotic=True,
        magical=False,
        gives="pride",
        guards={"glitter"},
    ),
    "pinwheel": Item(
        id="pinwheel",
        label="pinwheel",
        phrase="a tiny star pinwheel",
        region="hand",
        patriotic=True,
        magical=True,
        gives="calm",
        guards={"nervous"},
    ),
    "apron": Item(
        id="apron",
        label="apron",
        phrase="a soft apron with tiny stripes",
        region="torso",
        patriotic=False,
        magical=False,
        gives="clean hands",
        guards={"flour"},
    ),
    "flag_ribbon": Item(
        id="flag_ribbon",
        label="flag ribbon",
        phrase="a small flag ribbon",
        region="wrist",
        patriotic=True,
        magical=True,
        gives="bravery",
        guards={"nervous", "rumpled"},
    ),
}

NAMES = {
    "girl": ["Mia", "Lila", "Nora", "Ivy", "Zoe", "Ava"],
    "boy": ["Theo", "Ben", "Leo", "Noah", "Max", "Finn"],
}

TRAITS = ["quiet", "curious", "careful", "kind", "thoughtful", "shy"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
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


def item_at_risk(activity: Activity, item: Item) -> bool:
    return item.region in {"torso", "hand", "wrist"} and activity.mess in item.guards.union({activity.mess})


def select_help(activity: Activity, item: Item) -> Optional[Item]:
    for candidate in ITEMS.values():
        if candidate.magical and activity.mess in candidate.guards and candidate.region == item.region:
            return candidate
    # broader compatibility for the slice-of-life compromise
    for candidate in ITEMS.values():
        if activity.mess in candidate.guards:
            return candidate
    return None


ASP_RULES = r"""
at_risk(A,I) :- activity(A), item(I), region(I,R), guards(I,M), mess_of(A,M).
helpful(H,A,I) :- at_risk(A,I), item(H), magical(H), guards(H,M), mess_of(A,M), region(H,R), region(I,R).
valid(Place,A,I) :- affords(Place,A), at_risk(A,I), helpful(_,A,I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("region", iid, i.region))
        for g in sorted(i.guards):
            lines.append(asp.fact("guards", iid, g))
        if i.magical:
            lines.append(asp.fact("magical", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item_id, item in ITEMS.items():
                if item_at_risk(act, item) and select_help(act, item):
                    combos.append((place, act_id, item_id))
    return combos


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


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def predict(world: World, actor: Entity, activity: Activity, item_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.entities.get(item_id)
    return {"messy": bool(item and item.meters.get(activity.mess, 0) > 0)}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["energy"] = actor.memes.get("energy", 0) + 1
    if narrate:
        world.say(f"{actor.id} started {activity.gerund}.")
    if activity.id == "decorate":
        for item in world.worn_items(actor):
            if item.magical and item.region == "hand":
                actor.memes["calm"] = actor.memes.get("calm", 0) + 1


def tell(world: World, hero: Entity, parent: Entity, item: Entity, activity: Activity, helper: Optional[Entity]) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait', 'quiet')} {hero.type} who liked small, careful days.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} because it made an ordinary room feel special.")
    world.say(f"That morning, {parent.label or parent.id} brought home {item.phrase}.")
    world.say(f"{hero.id} held {hero.pronoun('possessive')} breath and looked at it like it was already part of the celebration.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} thoughts started to race.")
    if helper:
        world.say(f"In {hero.id}'s pocket was {helper.phrase}, a tiny magic thing that always felt warmer when {hero.id} was worried.")
    else:
        world.say(f"There was no special helper yet, only a quiet room and {hero.id}'s own breathing.")

    pred = predict(world, hero, activity, item.id)
    if pred["messy"]:
        world.say(f'"If I rush, I might make {item.label} {activity.strain}," {hero.pronoun("subject")} told {hero.pronoun("object")}self in a small inner voice.')
        world.say(f'"Slow hands make pretty things," the inner voice answered.')
        world.say(f"{hero.id} took a slower step, then another, and began {activity.gerund} with care.")
    else:
        world.say(f"{hero.id} decided to be careful anyway, because the day felt important in a gentle way.")
        world.say(f"That steady feeling was enough to begin.")

    do_activity(world, hero, activity, narrate=False)

    if helper and helper.magical:
        hero.memes[helper.gives] = hero.memes.get(helper.gives, 0) + 1
        world.say(f"The little magic in {helper.label} made {hero.id} feel {helper.gives}.")
    if item.patriotic:
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1

    world.para()
    if activity.id == "decorate":
        world.say(f"By the time {hero.id} finished, the banner was neat, bright, and straight.")
        world.say(f"{parent.label or parent.id} smiled at the paper stars, and {hero.id} smiled back, pleased to have done a good thing well.")
    elif activity.id == "wave":
        world.say(f"At the end, the flags rested neatly in {hero.id}'s hands, not bent or crumpled.")
        world.say(f"{hero.id} felt taller walking home, with the small patriotic ribbon still fluttering softly.")
    elif activity.id == "sing":
        world.say(f"At the end, {hero.id}'s song came out steadier than before.")
        world.say(f"The tiny pinwheel stayed tucked in place, and the room felt warm with shared pride.")
    else:
        world.say(f"At the end, the little table looked tidy again, and the day felt settled and kind.")

    world.facts.update(hero=hero, parent=parent, item=item, activity=activity, helper=helper, setting=world.setting)


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, activity, item = f["hero"], f["parent"], f["activity"], f["item"]
    return [
        f'Write a short slice-of-life story for a child named {hero.id} who wants to {activity.verb} and uses a little inner monologue to stay calm.',
        f"Tell a gentle patriotic story where {hero.id} notices {item.phrase} and decides how to handle it with care.",
        f"Write a simple magical everyday story in which {hero.id} thinks to {hero.pronoun('object')}self, then finishes a small holiday task with {parent.label or parent.id} nearby.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, activity, item, helper = f["hero"], f["parent"], f["activity"], f["item"], f["helper"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}, and {hero.pronoun().capitalize()} did it carefully after thinking it through.",
        ),
        QAItem(
            question=f"What made {hero.id} pause and think before starting?",
            answer=f"{item.phrase} felt important, so {hero.id} used a quiet inner monologue to slow down and do the job well.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel calmer while {activity.gerund}?",
            answer=f"{helper.phrase} helped {hero.id} feel {helper.gives}, which made the work feel easier and more peaceful.",
        ),
        QAItem(
            question=f"Who was with {hero.id} during the story?",
            answer=f"{parent.label or parent.id} was nearby, and that made the little task feel like a shared everyday moment.",
        ),
    ]
    if helper and helper.magical:
        qa.append(
            QAItem(
                question=f"How did the magic matter in the story?",
                answer=f"The magic in {helper.label} did not do the work for {hero.id}; it simply helped {hero.id} feel {helper.gives} enough to keep going with steady hands.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "patriotic": (
        "What does patriotic mean?",
        "Patriotic means showing love and care for your country, often by taking part in traditions, using its colors, or joining community celebrations.",
    ),
    "magic": (
        "What is magic in a story?",
        "Magic in a story is something special that can make ordinary things feel surprising, gentle, or full of wonder.",
    ),
    "inner": (
        "What is an inner monologue?",
        "An inner monologue is the quiet voice in your head that helps you think about what you are doing or feeling.",
    ),
    "slice": (
        "What is a slice-of-life story?",
        "A slice-of-life story shows a small everyday moment, like a simple job or a family scene, instead of a huge adventure.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        if e.patriotic:
            bits.append("patriotic=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="classroom", activity="decorate", item="banner", name="Mia", gender="girl", parent="teacher", trait="quiet"),
    StoryParams(place="porch", activity="wave", item="flag_ribbon", name="Theo", gender="boy", parent="mom", trait="careful"),
    StoryParams(place="kitchen", activity="bake", item="apron", name="Ava", gender="girl", parent="father", trait="thoughtful"),
    StoryParams(place="yard", activity="sing", item="pinwheel", name="Leo", gender="boy", parent="mother", trait="shy"),
]

def explain_rejection(activity: Activity, item: Item) -> str:
    return f"(No story: {activity.gerund} does not plausibly create a problem for {item.phrase}, so there is no honest slice-of-life tension.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "item", None):
        act, item = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(ITEMS, getattr(args, "item", None))
        if not (item_at_risk(act, item) and select_help(act, item)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "teacher"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    item_cfg = _safe_lookup(ITEMS, params.item)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"trait": params.trait}))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent", label=params.parent))
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type=item_cfg.label,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        patriotic=item_cfg.patriotic,
        magical=item_cfg.magical,
    ))
    helper_cfg = select_help(activity, item_cfg)
    helper = world.add(Entity(
        id=helper_cfg.id, kind="thing", type=helper_cfg.label, label=helper_cfg.label,
        phrase=helper_cfg.phrase, magical=helper_cfg.magical, patriotic=helper_cfg.patriotic
    )) if helper_cfg else None

    if helper:
        helper.worn_by = hero.id

    tell(world, hero, parent, item, activity, helper)

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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life patriotic magic story world with inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "teacher"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, activity, item) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
