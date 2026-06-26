#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bilingual_compare_protect_repetition_rhyme_slice_of.py
==============================================================================================================

A small slice-of-life story world about a bilingual child, a gentle comparison,
and a protective choice that turns a wobbly moment into a cheerful routine.

The seed idea:
- A child who can speak two languages notices a small problem in daily life.
- The child compares two options out loud, repeating a tiny phrase for comfort.
- A caring helper offers something that protects what matters.
- The ending lands on a rhyme or repeated line that proves the mood changed.

This world is intentionally narrow: it aims for a few plausible, grounded stories
instead of a wide-but-weak grab bag.
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

# Physical meter threshold for narratable effects.
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
    protective: bool = False
    protects: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    child: object | None = None
    gear: object | None = None
    helper_ent: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "cold": 0.0, "messy": 0.0, "full": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    indoor: bool
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
    risk: str
    zone: set[str]
    keyword: str
    rhyme: str
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
class ProtectiveItem:
    id: str
    label: str
    phrase: str
    protects: set[str]
    guards: set[str]
    tag: str
    rhyme: str
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


SETTINGS = {
    "kitchen_window": Setting(place="the kitchen window", indoor=True, affords={"rainwatch", "snack"}),
    "bus_stop": Setting(place="the little bus stop", indoor=False, affords={"rainwatch", "snack"}),
    "laundry_room": Setting(place="the laundry room", indoor=True, affords={"folding", "snack"}),
}

ACTIVITIES = {
    "rainwatch": Activity(
        id="rainwatch",
        verb="watch the rain",
        gerund="watching the rain",
        rush="run to the window",
        risk="get a chill by the open draft",
        zone={"torso"},
        keyword="rain",
        rhyme="pane",
        tags={"rain", "wet"},
    ),
    "snack": Activity(
        id="snack",
        verb="have a snack",
        gerund="snacking by the table",
        rush="dash to the table",
        risk="spill crumbs everywhere",
        zone={"hands", "torso"},
        keyword="snack",
        rhyme="plate",
        tags={"snack", "crumbs"},
    ),
    "folding": Activity(
        id="folding",
        verb="fold warm towels",
        gerund="folding warm towels",
        rush="carry the basket",
        risk="get the fresh towels damp",
        zone={"hands", "torso"},
        keyword="towel",
        rhyme="neat",
        tags={"laundry", "tidy"},
    ),
}

PROTECTIVE_ITEMS = {
    "red_scarf": ProtectiveItem(
        id="red_scarf",
        label="red scarf",
        phrase="a soft red scarf",
        protects={"torso"},
        guards={"wet", "cold"},
        tag="scarf",
        rhyme="warm",
    ),
    "blue_napkin": ProtectiveItem(
        id="blue_napkin",
        label="blue napkin",
        phrase="a blue napkin",
        protects={"torso"},
        guards={"crumbs"},
        tag="napkin",
        rhyme="clean",
    ),
    "yellow_apron": ProtectiveItem(
        id="yellow_apron",
        label="yellow apron",
        phrase="a sunny yellow apron",
        protects={"torso", "hands"},
        guards={"crumbs", "wet"},
        tag="apron",
        rhyme="bright",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Iris", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Leo", "Noah", "Ben", "Eli", "Finn", "Theo", "Sam"]


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def protect_reasonable(activity: Activity, item: ProtectiveItem) -> bool:
    return bool(activity.tags & item.guards) and bool(activity.zone & item.protects)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item_id, item in PROTECTIVE_ITEMS.items():
                if protect_reasonable(act, item):
                    out.append((place, act_id, item_id))
    return sorted(out)


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def pronounce_pair() -> tuple[str, str]:
    return ("hello / hola", "please / por favor")


def bilingual_line(name: str, helper: str) -> str:
    a, b = pronounce_pair()
    return f'{name} said "{a}" and {helper} answered "{b}," and both smiles stayed small and steady.'


def rhyme_line(activity: Activity, item: ProtectiveItem) -> str:
    return f"{activity.rhyme}, {item.rhyme}, the day stayed fine."


def predict(world: World, child: Entity, activity: Activity, item: Entity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(child.id), activity, narrate=False)
    target = sim.get(item.id)
    return {
        "ruined": target.meters["wet"] >= THRESHOLD or target.meters["messy"] >= THRESHOLD,
        "worry": sim.get(child.id).memes["worry"],
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["joy"] += 1
    if activity.id == "rainwatch":
        actor.meters["wet"] += 1
        actor.memes["worry"] += 1
        if narrate:
            world.say(f"{actor.id} leaned near the window and {activity.gerund}; the cool air made {actor.pronoun('object')} hug {actor.pronoun('possessive')} sleeves.")
    elif activity.id == "snack":
        actor.meters["messy"] += 1
        if narrate:
            world.say(f"{actor.id} {activity.gerund} with careful bites, but a few crumbs kept hopping onto the table.")
    elif activity.id == "folding":
        actor.meters["full"] += 1
        if narrate:
            world.say(f"{actor.id} was {activity.gerund}, making neat squares that felt calm in the hands.")
    else:
        if narrate:
            world.say(f"{actor.id} spent a quiet minute {activity.gerund}.")


def apply_protection(world: World, child: Entity, item: ProtectiveItem) -> Entity:
    gear = world.add(Entity(
        id=item.id,
        kind="thing",
        type="item",
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
        protective=True,
        protects=set(item.protects),
    ))
    gear.worn_by = child.id
    return gear


def tell(setting: Setting, activity: Activity, item_cfg: ProtectiveItem,
         name: str, gender: str, helper: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper, label=f"the {helper}"))
    item = world.add(Entity(id="protective", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, owner=child.id))

    world.say(f"{child.id} was a little {gender} who could speak in two languages, and {helper_ent.label} always liked that.")
    world.say(f"{child.id} liked to {activity.verb}, especially when the day felt ordinary and calm.")
    world.say(f"At home, {child.id} had {item_cfg.phrase}, and {helper_ent.label} said it would {('protect' if item_cfg.tag else 'help')} what mattered.")

    world.para()
    world.say(f"One afternoon at {setting.place}, {child.id} wanted to {activity.verb}.")
    world.say(bilingual_line(child.id, helper_ent.label))
    world.say(f"{child.id} compared two choices out loud: {activity.verb} now, or wait a minute and stay cozy.")
    child.memes["worry"] += 1
    world.say(f"{helper_ent.label} noticed the worry and offered {item_cfg.phrase} so the little plan could feel safe.")

    world.para()
    gear = apply_protection(world, child, item_cfg)
    pred = predict(world, child, activity, gear)
    if pred["ruined"]:
        pass

    child.memes["comfort"] += 1
    child.memes["pride"] += 1
    world.say(f"{child.id} put on {gear.label} and tried again.")
    do_activity(world, child, activity, narrate=True)
    if activity.id == "rainwatch":
        world.say(f"The glass stayed dry enough, and {child.id} could point at the sky without feeling chilly.")
    elif activity.id == "snack":
        world.say(f"The little mess stayed near the plate, easy to wipe away.")
    else:
        world.say(f"The towels stayed neat, and the room kept its soft, clean smell.")
    world.say(f"{rhyme_line(activity, item_cfg)}")
    world.say(f"{child.id} smiled because the safest choice still felt like a good ordinary day.")

    world.facts.update(
        child=child,
        helper=helper_ent,
        item=gear,
        activity=activity,
        setting=setting,
        protected=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    act = _safe_fact(world, f, "activity")
    item = _safe_fact(world, f, "item")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a slice-of-life story about a bilingual child named {child.id} who compares two choices and learns to protect what matters.',
        f"Tell a gentle story where {child.id} wants to {act.verb}, {helper.label} offers {item.phrase}, and the ending includes a small rhyme.",
        f'Write a short story using the words "bilingual", "compare", and "protect" with a calm, everyday feeling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item")
    act = _safe_fact(world, f, "activity")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the bilingual child in the story?",
            answer=f"The bilingual child is {child.id}. {child.id} can use two languages and likes ordinary moments that feel gentle.",
        ),
        QAItem(
            question=f"What did {child.id} want to do at {setting.place}?",
            answer=f"{child.id} wanted to {act.verb} at {setting.place}. The wish was simple, but the child still needed a safe plan.",
        ),
        QAItem(
            question=f"How did {helper.label} help {child.id}?",
            answer=f"{helper.label.capitalize()} helped by offering {item.phrase}, which could protect what mattered and make the choice feel calmer.",
        ),
        QAItem(
            question=f"Why did the child compare two choices?",
            answer=f"{child.id} compared two choices because one way felt a little risky, and the other way kept the day comfortable and safe.",
        ),
        QAItem(
            question="What made the ending feel cheerful?",
            answer=f"The ending felt cheerful because {child.id} used the protective item, the activity still happened, and the story closed with a little rhyme.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity = _safe_fact(world, f, "activity")
    item = _safe_fact(world, f, "item")
    return [
        QAItem(
            question="What does bilingual mean?",
            answer="Bilingual means someone can use two languages, such as English and Spanish, to talk and understand people.",
        ),
        QAItem(
            question="What does compare mean?",
            answer="To compare is to look at two or more choices and notice how they are alike or different.",
        ),
        QAItem(
            question="What does protect mean?",
            answer="To protect means to keep something safe from harm, like a scarf that keeps you warm or an apron that keeps clothes clean.",
        ),
        QAItem(
            question="Why can a scarf be helpful?",
            answer="A scarf can help protect your neck and chest from cool air, so you feel warmer on a chilly day.",
        ),
        QAItem(
            question=f"Why did the story mention {activity.rhyme} and {item.rhyme}?",
            answer="The rhyme makes the story feel playful and memorable, which is nice in a quiet slice-of-life moment.",
        ),
    ]


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
        if e.protective:
            bits.append(f"protects={sorted(e.protects)}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A protective item is reasonable when it covers an at-risk zone and guards
% against a relevant kind of discomfort.
at_risk(A, I) :- activity(A), protective(I), activity_zone(A, Z), item_protects(I, Z).
helpful(I, A) :- at_risk(A, I), activity_tag(A, T), item_guard(I, T).
valid(Place, A, I) :- affords(Place, A), helpful(I, A).
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
        lines.append(asp.fact("activity_tag", aid, *sorted(a.tags)))
        for z in sorted(a.zone):
            lines.append(asp.fact("activity_zone", aid, z))
    for iid, i in PROTECTIVE_ITEMS.items():
        lines.append(asp.fact("protective", iid))
        for z in sorted(i.protects):
            lines.append(asp.fact("item_protects", iid, z))
        for g in sorted(i.guards):
            lines.append(asp.fact("item_guard", iid, g))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: bilingual compare protect, with repetition and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=PROTECTIVE_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
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
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "item", None):
        combos = [c for c in combos if c[2] == getattr(args, "item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, item = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PROTECTIVE_ITEMS, params.item),
        params.name,
        params.gender,
        params.helper,
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
    StoryParams(place="kitchen_window", activity="rainwatch", item="red_scarf", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="bus_stop", activity="rainwatch", item="red_scarf", name="Leo", gender="boy", helper="father"),
    StoryParams(place="laundry_room", activity="folding", item="yellow_apron", name="Nora", gender="girl", helper="aunt"),
    StoryParams(place="kitchen_window", activity="snack", item="blue_napkin", name="Finn", gender="boy", helper="uncle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, protective-item) combos:")
        for place, act, item in triples:
            print(f"  {place:14} {act:10} {item}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
